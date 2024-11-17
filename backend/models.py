from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

@dataclass
class ModelInfo:
    name: str
    source: str  # 'huggingface', 'civitai', lub 'local'
    type: str    # 'checkpoint', 'lora', 'vae', etc.
    url: str
    local_path: Path

@dataclass
class Instance:
    id: str
    path: Path
    models: List[ModelInfo]
    status: str = "idle"