import os
import shutil
import uuid
from fastapi import UploadFile, HTTPException
from pathlib import Path
from app.core.config import settings


UPLOAD_DIR = Path(settings.MANUAL_UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


async def save_upload_file(upload_file: UploadFile) -> str:
    """
    Salva um arquivo enviado em disco e retorna o caminho relativo.
    """
    # Valida extensão
    ext = os.path.splitext(upload_file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Tipo de arquivo não permitido. Apenas PDF.")

    # Valida tamanho (lendo conteúdo)
    contents = await upload_file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"Arquivo muito grande. Máximo {MAX_FILE_SIZE // (1024*1024)}MB.")
    await upload_file.seek(0)  # reset

    # Gera nome único
    file_name = f"{uuid.uuid4()}{ext}"
    file_path = UPLOAD_DIR / file_name

    # Salva
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    return str(file_path)


def delete_file(file_path: str):
    """Remove um arquivo do disco se existir."""
    if os.path.exists(file_path):
        os.remove(file_path)


def get_file_size(file_path: str) -> int:
    """Retorna tamanho do arquivo em bytes."""
    return os.path.getsize(file_path)