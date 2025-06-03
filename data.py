from dataclasses import dataclass
from typing import Optional

@dataclass
class Entry:
    id: str
    prompt_text: str
    filepath: Optional[str] = None  # None or empty if not generated yet
    broken: Optional[bool] = None
    is_upscale: bool = False
    upscale_of: Optional[str] = None
    has_upscale: bool = False
    score_mu: float = 0.0
    score_sigma: float = 0.0
    deleted: bool = False
    width: Optional[int] = None
    height: Optional[int] = None
    seed: Optional[int] = None