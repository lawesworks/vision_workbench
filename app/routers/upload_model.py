from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import shutil
import re


#from app.core.model import MODEL

# import the module and read MODEL from it at request time.  the above method produces a stale import reference
# the router gets whatever MODEL was at import time. If later your app reassigns MODEL in app.core.model, 
# that router may still be looking at the old object.
from app.core import model as model_state

router = APIRouter(prefix="/models", tags=["Models"])

BASE_DIR = Path(__file__).resolve().parents[2]
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_filename(filename: str) -> str:
    """
    Keep only the base filename and replace unsafe characters.
    """
    safe_name = Path(filename).name
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", safe_name)
    return safe_name


def ensure_pt_extension(filename: str) -> None:
    """
    Validate that the uploaded file is a .pt file.
    """
    if not filename.lower().endswith(".pt"):
        raise HTTPException(status_code=400, detail="Only .pt files are allowed.")


def get_unique_model_path(directory: Path, filename: str) -> Path:
    """
    If filename already exists, append _1, _2, etc.
    Example:
      model.pt -> model_1.pt
    """
    candidate = directory / filename

    if not candidate.exists():
        return candidate

    stem = Path(filename).stem
    suffix = Path(filename).suffix

    counter = 1
    while True:
        new_name = f"{stem}_{counter}{suffix}"
        candidate = directory / new_name
        if not candidate.exists():
            return candidate
        counter += 1


@router.post("/upload")
async def upload_model(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file was uploaded.")

    original_name = file.filename
    safe_name = sanitize_filename(original_name)

    ensure_pt_extension(safe_name)

    save_path = get_unique_model_path(MODELS_DIR, safe_name)

    # If ever I prefer to reject duplicates instead of renaming them
    """
    save_path = MODELS_DIR / safe_name
    if save_path.exists():
        raise HTTPException(status_code=400, detail="Model already exists.")
    """

    try:
        with save_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save uploaded model: {str(e)}"
        )
    finally:
        await file.close()

    return {
        "status": "success",
        "original_filename": original_name,
        "saved_filename": save_path.name,
        "path": str(save_path)
    }



@router.delete("/delete/{filename}")
def delete_model(filename: str):
    safe_name = Path(filename).name.strip().lower()

    if not safe_name.endswith(".pt"):
        raise HTTPException(status_code=400, detail="Only .pt files can be deleted.")

    try:
        current_model_name = Path(model_state.MODEL.model.pt_path).name.strip().lower()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not determine active model: {str(e)}"
        )

    if safe_name == current_model_name:
        raise HTTPException(status_code=400, detail="Cannot delete the active model.")

    file_path = MODELS_DIR / safe_name

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Model not found.")

    try:
        file_path.unlink()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete model: {str(e)}")

    return {
        "status": "deleted",
        "filename": safe_name
    }