import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
INSTANCES_DIR = BASE_DIR / "instances"
INSTANCES_DIR.mkdir(exist_ok=True)