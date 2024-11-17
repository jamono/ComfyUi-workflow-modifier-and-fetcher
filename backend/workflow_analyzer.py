import json
from pathlib import Path
from typing import List, Dict
from models import ModelInfo

class WorkflowAnalyzer:
    """Analizator workflow ComfyUI"""
    
    MODEL_NODE_TYPES = {
        "CheckpointLoaderSimple": "checkpoint",
        "LoraLoader": "lora",
        "CLIPTextEncode": "clip",
        "VAELoader": "vae",
        "ControlNetLoader": "controlnet",
        "UNETLoader": "unet",
        "UpscaleModelLoader": "upscale"
    }

    def __init__(self, workflow_path: Path):
        self.workflow_path = workflow_path

    def analyze(self) -> List[ModelInfo]:
        """Analizuje workflow i zwraca listę wymaganych modeli"""
        try:
            print("Rozpoczęcie analizy workflow")
            with open(self.workflow_path, 'r', encoding='utf-8') as f:
                workflow_data = json.load(f)
            
            print("Wczytano dane workflow:", json.dumps(workflow_data, indent=2))
            required_models = []
            
            # Analizuj każdy węzeł
            for node_id, node_data in workflow_data.items():
                if isinstance(node_data, dict):
                    print(f"\nAnalizowanie węzła {node_id}:", json.dumps(node_data, indent=2))
                    node_type = node_data.get("class_type")
                    
                    if node_type in self.MODEL_NODE_TYPES:
                        model_info = self._extract_model_info(node_data, self.MODEL_NODE_TYPES[node_type])
                        if model_info and model_info not in required_models:
                            required_models.append(model_info)
                            print(f"Znaleziono model:", model_info)

            print("Zakończono analizę. Znalezione modele:", required_models)
            return required_models
            
        except Exception as e:
            print(f"Błąd podczas analizy workflow: {str(e)}")
            raise

    def _extract_model_info(self, node_data: Dict, model_type: str) -> ModelInfo:
        """Wyciąga informacje o modelu z węzła"""
        try:
            node_type = node_data.get("class_type")
            inputs = node_data.get("inputs", {})
            
            # Określ nazwę modelu na podstawie typu węzła
            model_name = None
            if node_type == "CheckpointLoaderSimple":
                model_name = inputs.get("ckpt_name")
            elif node_type == "LoraLoader":
                model_name = inputs.get("lora_name")
            elif node_type == "VAELoader":
                model_name = inputs.get("vae_name")
            elif node_type == "ControlNetLoader":
                model_name = inputs.get("control_net_name")
            elif node_type == "UpscaleModelLoader":
                model_name = inputs.get("model_name")
            elif node_type == "CLIPTextEncode":
                # Sprawdź czy używane są embeddingi
                text = inputs.get("text", "")
                if "embedding:" in text:
                    model_name = text.split("embedding:")[1].split()[0]
                    model_type = "embedding"

            if not model_name:
                print(f"Nie znaleziono nazwy modelu dla węzła typu {node_type}")
                return None

            # Określ źródło i URL modelu
            if "civitai.com" in model_name or model_name.startswith("civitai://"):
                source = "civitai"
                url = model_name.replace("civitai://", "https://civitai.com/api/download/models/")
            elif "/" in model_name:  # prawdopodobnie model z HuggingFace
                source = "huggingface"
                url = f"https://huggingface.co/{model_name}/resolve/main/model.safetensors"
            else:
                source = "local"
                url = ""

            return ModelInfo(
                name=model_name,
                source=source,
                type=model_type,
                url=url,
                local_path=Path(f"models/{model_type}/{model_name}")
            )
            
        except Exception as e:
            print(f"Błąd podczas ekstrakcji informacji o modelu: {str(e)}")
            return None

    def _get_model_path(self, model_name: str, model_type: str) -> str:
        """Generuje ścieżkę dla modelu"""
        # Konwertuj znaki specjalne
        safe_name = model_name.replace('/', '_').replace('\\', '_')
        return f"models/{model_type}/{safe_name}"

    def _determine_model_type(self, node_type: str) -> str:
        """Określa typ modelu na podstawie typu węzła"""
        return self.MODEL_NODE_TYPES.get(node_type, "unknown")