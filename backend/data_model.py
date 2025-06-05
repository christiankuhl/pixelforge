from dataclasses import dataclass
from typing import Optional, Self, Dict
from abc import ABC
import uuid
import random
import json
import csv
import os

from .config import FASTAPI_SERVER_ADDRESS

FLUX_WORKFLOW = json.load(open("backend/flux_workflow.json"))
UPSCALE_WORKFLOW = json.load(open("backend/upscale_api.json"))

Prompt = Dict


class Workflow(ABC):
    @staticmethod
    def build(entry: "Entry") -> Prompt:
        pass


class UpscaleSD35(Workflow):
    @staticmethod
    def build(entry):
        out = UPSCALE_WORKFLOW.copy()
        # FIXME: properly react to aspect ratio and orientation
        out["2"]["inputs"]["filename_prefix"] = "UpscaleBatch"
        out["1"]["inputs"]["resolution"] = "16:9"
        out["1"]["inputs"]["orientation"] = "landscape"
        out["1"]["inputs"]["positive"] = entry.prompt_text
        out["1"]["inputs"]["seed"] = entry.seed
        out["2"]["inputs"]["image"] = entry.orig_filepath
        return out


class Flux(Workflow):
    @staticmethod
    def build(entry):
        # FIXME: properly react to aspect ratio and orientation
        out = FLUX_WORKFLOW.copy()
        out["2"]["inputs"]["filename_prefix"] = "FluxBatch"
        out["1"]["inputs"]["resolution"] = "16:9"
        out["1"]["inputs"]["orientation"] = "landscape"
        out["1"]["inputs"]["positive"] = entry.prompt_text
        out["1"]["inputs"]["seed"] = entry.seed
        return out


@dataclass
class Entry:
    id: str = uuid.uuid4().hex
    prompt_text: str = ""
    filepath: Optional[str] = None
    broken: bool = False
    upscale: str = "none"
    score_mu: Optional[float] = None
    score_sigma: Optional[float] = None
    deleted: bool = False
    width: Optional[int] = None
    height: Optional[int] = None
    seed: Optional[int] = None
    orig_filepath: Optional[str] = None

    def copy(self) -> Self:
        entry = Entry()
        entry.id = uuid.uuid4().hex
        entry.prompt_text = self.prompt_text
        entry.orig_filepath = self.orig_filepath
        return entry

    def delete(self):
        self.filepath = None
        self.width = None
        self.height = None
        self.score_mu = None
        self.score_sigma = None

    def generate(self) -> tuple[Self, Prompt]:
        if self.upscale == "is_upscale":
            print("Scaling up...")
            workflow = UpscaleSD35
        else:
            print("Regenerating...")
            workflow = Flux
        if self.broken or self.deleted or not self.filepath:
            print(f"Replacing original... {self}")
            entry = self
            self.score_mu = None
            self.score_sigma = None
        else:
            print("Generating new image...")
            entry = self.copy()
        if not self.deleted or not self.filepath and self.seed:
            print("New seed...")
            entry.seed = random.randint(0, 0x7FFFFFFF)
        else:
            print("Keeping seed...")
            self.deleted = False
        prompt = workflow.build(entry)
        return entry, prompt


def try_float(x):
    try:
        return float(x)
    except ValueError:
        return 0.0


def get_all_entries_tmp():
    with open("backend/image_db_amended.csv") as f:
        r = csv.DictReader(f)
        res = [
            Entry(
                id=hex(hash(l.values())),
                prompt_text=l["prompt"],
                filepath=f"http://{FASTAPI_SERVER_ADDRESS}/images/{os.path.basename(l['file'])}",
                upscale=l["upscale"],
                score_mu=try_float(l["mu"]),
                score_sigma=try_float(l["sigma"]),
                width=l["width"],
                height=l["height"],
                seed=l["seed"],
            )
            for l in r
        ]
    res[0].deleted = True
    res[1].broken = True
    res[2].filepath = None
    return res
