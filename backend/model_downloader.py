import os
import requests
from pathlib import Path
from typing import Optional, Callable
from tqdm import tqdm
import hashlib
from urllib.parse import urlparse
from models import ModelInfo

class ModelDownloader:
    def __init__(self, base_path: Path, api_keys: dict):
        self.base_path = base_path
        self.api_keys = api_keys
        self.chunk_size = 8192
        
    def download_model(self, model_info: ModelInfo, progress_callback: Optional[Callable] = None) -> bool:
        """
        Pobiera model z określonego źródła
        
        Args:
            model_info: Informacje o modelu
            progress_callback: Opcjonalna funkcja do raportowania postępu
        """
        try:
            # Stwórz folder dla modelu jeśli nie istnieje
            model_path = self.base_path / model_info.local_path
            model_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Jeśli plik już istnieje, pomiń pobieranie
            if model_path.exists():
                if progress_callback:
                    progress_callback(model_info.name, 100, "Already exists")
                return True
                
            # Wybierz odpowiednią metodę pobierania
            if model_info.source == "civitai":
                success = self._download_from_civitai(model_info, model_path, progress_callback)
            elif model_info.source == "huggingface":
                success = self._download_from_huggingface(model_info, model_path, progress_callback)
            else:
                raise ValueError(f"Unknown source: {model_info.source}")
                
            return success
            
        except Exception as e:
            print(f"Error downloading model {model_info.name}: {str(e)}")
            if progress_callback:
                progress_callback(model_info.name, 0, f"Error: {str(e)}")
            return False
            
    def _download_from_civitai(self, model_info: ModelInfo, target_path: Path, 
                              progress_callback: Optional[Callable]) -> bool:
        """Pobiera model z Civitai"""
        headers = {}
        if self.api_keys.get("civitai"):
            headers["Authorization"] = f"Bearer {self.api_keys['civitai']}"
            
        return self._download_file(model_info.url, target_path, headers, progress_callback)
            
    def _download_from_huggingface(self, model_info: ModelInfo, target_path: Path, 
                                  progress_callback: Optional[Callable]) -> bool:
        """Pobiera model z HuggingFace"""
        headers = {}
        if self.api_keys.get("huggingface"):
            headers["Authorization"] = f"Bearer {self.api_keys['huggingface']}"
            
        return self._download_file(model_info.url, target_path, headers, progress_callback)
            
    def _download_file(self, url: str, target_path: Path, headers: dict, 
                      progress_callback: Optional[Callable]) -> bool:
        """Ogólna metoda do pobierania plików"""
        try:
            # Najpierw pobierz informacje o pliku
            response = requests.get(url, headers=headers, stream=True)
            response.raise_for_status()
            
            # Pobierz rozmiar pliku
            total_size = int(response.headers.get('content-length', 0))
            
            # Pobierz plik z paskiem postępu
            with open(target_path, 'wb') as f:
                with tqdm(total=total_size, unit='iB', unit_scale=True) as pbar:
                    for data in response.iter_content(chunk_size=self.chunk_size):
                        size = f.write(data)
                        pbar.update(size)
                        if progress_callback:
                            progress = (pbar.n / total_size) * 100 if total_size > 0 else 0
                            progress_callback(target_path.name, progress, "Downloading")
                            
            # Weryfikuj pobrany plik
            if total_size > 0 and os.path.getsize(target_path) != total_size:
                raise Exception("Downloaded file size mismatch")
                
            if progress_callback:
                progress_callback(target_path.name, 100, "Complete")
                
            return True
            
        except Exception as e:
            print(f"Error downloading file {url}: {str(e)}")
            if progress_callback:
                progress_callback(target_path.name, 0, f"Error: {str(e)}")
            return False

    def verify_model(self, model_path: Path, expected_hash: Optional[str] = None) -> bool:
        """Weryfikuje integralność pobranego modelu"""
        if not model_path.exists():
            return False
            
        if expected_hash:
            # Oblicz hash pliku
            file_hash = hashlib.sha256()
            with open(model_path, 'rb') as f:
                for chunk in iter(lambda: f.read(self.chunk_size), b''):
                    file_hash.update(chunk)
            
            return file_hash.hexdigest() == expected_hash
            
        return True