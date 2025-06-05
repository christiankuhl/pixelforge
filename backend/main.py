from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import WebSocket, WebSocketDisconnect
from tortoise.contrib.fastapi import register_tortoise
from dataclasses import asdict
import json
import urllib.request
import websockets
from .data_model import Entry
from .config import *

DATA = None

app = FastAPI()

register_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["backend.data_model"]},  # Assuming your models are in `data_model.py`
    generate_schemas=True,
    add_exception_handlers=True,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/images", StaticFiles(directory="/home/christian/Bilder"), name="images")

@app.get("/api/entries")
async def get_entries():
    entries = await Entry.all()
    return [entry.__dict__ for entry in entries]

@app.post("/api/entry/{id}/toggle_broken")
async def toggle_broken(id: str):
    print(f"Switch entry {id}")
    entry = await Entry.get(id=id)
    entry.broken = not entry.broken
    await entry.save()
    return {"status": "ok", "id": id, "action": "toggle_broken"}

@app.delete("/api/entry/{id}")
async def delete_entry(id: str):
    print(f"Deleting entry {id}")
    entry = await Entry.get(id=id)
    entry.delete()
    await entry.save()
    return {"status": "ok", "id": id, "action": "delete"}


@app.websocket("/ws/generate/{entry_id}")
async def websocket_generate(ws: WebSocket, entry_id: str):
    await ws.accept()
    entry = await Entry.get(id=entry_id)
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
        await new_entry.save()
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

