from pathlib import Path
import os

def ensure_model(model_name:str) -> str:
    """ Ensure the model directory exists, return its path or an error message """
    base_dir = Path(os.environ.get("OCTOPY_CACHE", os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache")))) / "octopy"
    model_dir = base_dir / model_name
    if not model_dir.exists():
        return f"[LLM_LOADER] Ruta directa no existe: {model_dir}\n"
    return str(model_dir)

