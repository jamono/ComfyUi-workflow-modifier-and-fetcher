import shutil
import json
import os
from pathlib import Path
from typing import Dict, List
import requests
from models import Instance, ModelInfo

class InstanceManager:
    def __init__(self, instances_dir: Path):
        self.instances_dir = instances_dir
        self.instances: Dict[str, Instance] = {}
        self._load_existing_instances()
    
    def _load_existing_instances(self):
        """Ładuje istniejące instancje z dysku"""
        for instance_dir in self.instances_dir.glob("instance_*"):
            if instance_dir.is_dir():
                instance_id = instance_dir.name.split("_")[1]
                self.instances[instance_id] = Instance(
                    id=instance_id,
                    path=instance_dir,
                    models=self._scan_models_directory(instance_dir / "models")
                )

    def create_instance(self, instance_id: str) -> Instance:
        """Tworzy nową instancję ComfyUI"""
        instance_path = self.instances_dir / f"instance_{instance_id}"
        
        # Klonowanie ComfyUI
        os.system(f"git clone https://github.com/comfyanonymous/ComfyUI.git {instance_path}")
        
        # Tworzenie potrzebnych folderów
        models_dir = instance_path / "models"
        models_dir.mkdir(exist_ok=True)
        
        instance = Instance(
            id=instance_id,
            path=instance_path,
            models=[]
        )
        self.instances[instance_id] = instance
        return instance

    def _scan_models_directory(self, models_dir: Path) -> List[ModelInfo]:
        """Skanuje folder models i zwraca listę znalezionych modeli"""
        models = []
        if models_dir.exists():
            for model_file in models_dir.glob("*"):
                if model_file.is_file() and model_file.suffix in ['.ckpt', '.safetensors']:
                    models.append(ModelInfo(
                        name=model_file.name,
                        source="unknown",
                        url="",
                        local_path=model_file
                    ))
        return models