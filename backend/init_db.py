from tortoise import Tortoise, run_async
import csv
import os
import uuid
from .data_model import Entry
from .config import FASTAPI_SERVER_ADDRESS


def try_float(x):
    try:
        return float(x)
    except ValueError:
        return None


def try_int(x):
    try:
        return int(x)
    except ValueError:
        return None


async def init():
    await Tortoise.init(
        db_url="sqlite://db.sqlite3",
        modules={"models": ["backend.data_model"]},
    )
    await Tortoise.generate_schemas()

    with open("backend/image_db_amended.csv") as f:
        r = csv.DictReader(f)
        for l in r:
            e = Entry(
                id=uuid.uuid4().hex,
                prompt_text=l["prompt"],
                filepath=f"http://{FASTAPI_SERVER_ADDRESS}/images/{os.path.basename(l['file'])}",
                upscale=l["upscale"],
                score_mu=try_float(l["mu"]),
                score_sigma=try_float(l["sigma"]),
                width=try_int(l["width"]),
                height=try_int(l["height"]),
                seed=l["seed"],
            )
            await e.save()
    print("DB initialised.")


if __name__ == "__main__":
    run_async(init())
