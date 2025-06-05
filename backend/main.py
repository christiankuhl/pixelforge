from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import WebSocket, WebSocketDisconnect
from dataclasses import asdict
import uuid
import uuid
import json
import urllib.request
import websockets
from .data_model import get_all_entries_tmp
from .config import *

DATA = None

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/images", StaticFiles(directory="/home/christian/Bilder"), name="images")

def load_data():
    global DATA
    if DATA is None:
        DATA = get_all_entries_tmp()
    return DATA

# # Example: return all entries (replace with your data later)
@app.get("/api/entries")
def get_entries():
    return [asdict(d) for d in load_data()]

# @app.post("/api/entry/{id}/toggle_broken")
# def toggle_broken(id: str):
#     print(f"Switch entry {id}")
#     return {"status": "ok", "id": id, "action": "toggle_broken"}

# @app.post("/api/entry/{id}/generate")
# def generate(id: str):
#     # Stub: initiate regeneration logic for this entry
#     print(f"Generating entry {id}")
#     return {"status": "ok", "id": id, "action": "regenerate"}

# @app.delete("/api/entry/{id}")
# def delete_entry(id: str):
#     # Stub: mark entry as deleted
#     print(f"Deleting entry {id}")
#     return {"status": "ok", "id": id, "action": "delete"}


@app.websocket("/ws/generate/{entry_id}")
async def websocket_generate(ws: WebSocket, entry_id: str):
    await ws.accept()
    all_entries = {p.id: p for p in load_data()}
    entry = all_entries[entry_id]
    new_entry, prompt = entry.generate()
    try:
        async with websockets.connect("ws://{}/ws?clientId={}".format(COMFY_SERVER_ADDRESS, CLIENT_ID)) as comfy:
            prompt_id = queue_prompt(prompt)['prompt_id']
            while True:
                message = await comfy.recv()
                message = json.loads(message)
                if message['type'] == 'executing':
                    data = message['data']
                    if data['node'] is None and data['prompt_id'] == prompt_id:
                        break
                    else:
                        await ws.send_json({"type": "log", "message": "executing"})
        output_images = []
        history = get_comfy_history(prompt_id)[prompt_id]
        for node_id in history['outputs']:
            node_output = history['outputs'][node_id]
            if 'images' in node_output:
                for image in node_output['images']:
                    output_images.append(image['filename'])
        assert len(output_images) == 1
        filepath = f"http://{FASTAPI_SERVER_ADDRESS}/images/{output_images[0]}"
        new_entry.filepath = filepath
        await ws.send_json({"type": "result", "data": asdict(new_entry)})
    except WebSocketDisconnect:
        print(f"WebSocket client disconnected: {entry_id}")
    except Exception as e:
        await ws.send_json({"type": "error", "message": str(e)})
        print(f"WebSocket error: {e}")


def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": CLIENT_ID}
    data = json.dumps(p).encode('utf-8')
    req =  urllib.request.Request("http://{}/prompt".format(COMFY_SERVER_ADDRESS), data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_comfy_history(prompt_id):
    with urllib.request.urlopen("http://{}/history/{}".format(COMFY_SERVER_ADDRESS, prompt_id)) as response:
        return json.loads(response.read())

def request_comfy(ws, prompt):
    prompt_id = queue_prompt(prompt)['prompt_id']
    output_images = []
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break
    history = get_comfy_history(prompt_id)[prompt_id]
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        if 'images' in node_output:
            for image in node_output['images']:
                output_images.append(image['filename'])
    return output_images

# if __name__ == "__main__":
    # # ws = websocket.WebSocket()
    # ws.connect()
    # prompt = make_prompt(get_entries()[0])

    # images = request_comfy(ws, prompt)
    # ws.close() # for in case this example is used in an environment where it will be repeatedly called, like in a Gradio app. otherwise, you'll randomly receive connection timeouts
#Commented out code to display the output images:

# for node_id in images:
#     for image_data in images[node_id]:
#         from PIL import Image
#         import io
#         image = Image.open(io.BytesIO(image_data))
#         image.show()
