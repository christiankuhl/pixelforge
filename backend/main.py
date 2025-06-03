# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import csv
import uuid
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/images", StaticFiles(directory="/home/christian/Bilder"), name="images")

def try_float(x):
    try:
        return float(x)
    except ValueError:
        return 0.0

# Example: return all entries (replace with your data later)
@app.get("/api/entries")
def get_entries():
    with open("../image_db_amended.csv") as f:
        r = csv.DictReader(f)
        res = [
            {
                "id": uuid.uuid4().hex,
                "prompt_text": l["prompt"],
                "filepath": f"http://127.0.0.1:8000/images/{os.path.basename(l['file'])}",
                "upscale": l["upscale"],
                "score_mu": try_float(l["mu"]),
                "score_sigma": try_float(l["sigma"]),
                "width": l["width"],
                "height": l["height"],
            }
            for l in r
        ]
    res[0]["deleted"] = True
    res[1]["broken"] = True
    res[2]["filepath"] = ""
    return res