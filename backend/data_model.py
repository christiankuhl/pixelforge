from typing import Self, Dict, List, Optional
from tortoise import fields
from tortoise.models import Model
from abc import ABC
from pydantic import BaseModel
from .config import COMFY_IMAGE_FOLDER
import uuid
import random
import json


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
        out["1"]["inputs"]["seed"] = int(entry.seed)
        out["2"]["inputs"]["image"] = COMFY_IMAGE_FOLDER + entry.orig_filepath
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
        out["1"]["inputs"]["seed"] = int(entry.seed)
        return out


class Entry(Model):
    id = fields.CharField(pk=True, max_length=64)
    prompt_text = fields.TextField()
    filepath = fields.TextField(null=True)
    broken = fields.BooleanField(default=False)
    upscale = fields.CharField(max_length=32, default="none")
    score_mu = fields.FloatField(null=True)
    score_sigma = fields.FloatField(null=True)
    deleted = fields.BooleanField(default=False)
    width = fields.IntField(null=True)
    height = fields.IntField(null=True)
    seed = fields.TextField(null=True, max_length=64)
    orig_filepath = fields.TextField(null=True)

    class Meta:
        table = "entries"

    @property
    def rank(self):
        if self.score_mu is None or self.score_sigma is None:
            return 0
        else:
            return self.score_mu - 3 * self.score_sigma

    def copy(self) -> Self:
        entry = Entry()
        entry.id = uuid.uuid4().hex
        entry.prompt_text = self.prompt_text
        entry.orig_filepath = self.orig_filepath
        return entry

    def delete(self):
        self.filepath = None  # TODO: Decide what to do here...
        self.width = None
        self.height = None
        self.score_mu = None
        self.score_sigma = None
        self.deleted = True

    def generate(self, upscale=False) -> tuple[Self, Prompt]:
        if self.upscale == "is_upscale" or upscale:
            print("Scaling up...")
            workflow = UpscaleSD35
        else:
            print("Regenerating...")
            workflow = Flux
        if (self.broken or self.deleted or not self.filepath) and not upscale:
            print(f"Replacing original... {self}")
            entry = self
            self.score_mu = None
            self.score_sigma = None
        else:
            print("Generating new image...")
            entry = self.copy()
            if upscale:
                entry.orig_filepath = self.filepath
                entry.upscale = "is_upscale"
        if not self.deleted or not self.filepath and self.seed:
            print("New seed...")
            entry.seed = random.randint(0, 0x7FFFFFFF)
        else:
            print("Keeping seed...")
            self.deleted = False
        prompt = workflow.build(entry)
        return entry, prompt


class PairRequest(BaseModel):
    ids: List[str]


class UpdateRequest(BaseModel):
    winner: Optional[str] = None
    loser: Optional[str] = None
    draw: Optional[List[str]] = None
