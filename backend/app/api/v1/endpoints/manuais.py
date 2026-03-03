import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from datetime import datetime
import uuid

from app.core.database import get_db
from app.models.manual import Manual
from app.models.maquina import Maquina
from app.models.usuario import Usuario
from app.schemas.manual import (
    ManualCreate, ManualUpdate, ManualResponse, ManualListResponse,
    ManualUploadResponse, ManualDownloadResponse
)
from app.api.v1.dependencies import get_current_user, get_current_admin_user

router = APIRouter()

# Configuração do diretório de uploads
UPLOAD_DIR = "uploads/manuais"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/", response_model=ManualListResponse)
async def listar_manuais(
    page: int = 1,
    size: int = 20,
    maquina_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Lista todos os manuais com paginação e filtro opcional por máquina.
    """
    offset = (page - 1) * size
    query = select(Manual)
    count_query = select(func.count()).select_from(Manual)

    if maquina_id:
        query = query.where(Manual.maquina_id == maquina_id)
        count_query = count_query.where(Manual.maquina_id == maquina_id)

    total = await db.scalar(count_query)
    result = await db.execute(
        query.order_by(Manual.titulo).offset(offset).limit(size)
    )
    items = result.scalars().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
    }


@router.post("/upload", response_model=ManualUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_manual(
    maquina_id: int = Form(...),
    titulo: str = Form(...),
    versao: Optional[str] = Form(None),
    descricao: Optional[str] = Form(None),
    arquivo: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user),  # apenas admin
):
    """
    Upload de um novo manual (PDF). Apenas admin pode fazer upload.
    """
    # Verifica se a máquina existe
    maquina = await db.get(Maquina, maquina_id)
    if not maquina:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")

    # Valida extensão do arquivo
    if not arquivo.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são permitidos")

    # Gera nome único para o arquivo
    file_extension = os.path.splitext(arquivo.filename)[1]
    file_name = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    # Salva o arquivo
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(arquivo.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar arquivo: {str(e)}")

    # Cria registro no banco
    manual = Manual(
        maquina_id=maquina_id,
        titulo=titulo,
        versao=versao,
        descricao=descricao,
        arquivo_pdf=file_path,
        enviado_por_id=current_user.id,
    )
    db.add(manual)
    await db.commit()
    await db.refresh(manual)

    return {
        "id": manual.id,
        "titulo": manual.titulo,
        "arquivo_pdf": manual.arquivo_pdf,
        "mensagem": "Manual enviado com sucesso",
    }


@router.get("/download/{manual_id}", response_model=ManualDownloadResponse)
async def download_manual(
    manual_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Gera uma URL temporária para download do manual (ou retorna o arquivo diretamente).
    """
    manual = await db.get(Manual, manual_id)
    if not manual:
        raise HTTPException(status_code=404, detail="Manual não encontrado")

    # Verifica se o arquivo existe
    if not os.path.exists(manual.arquivo_pdf):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no servidor")

    # Retorna o arquivo para download
    return FileResponse(
        path=manual.arquivo_pdf,
        filename=f"{manual.titulo}.pdf",
        media_type='application/pdf'
    )


@router.delete("/{manual_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_manual(
    manual_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user),
):
    """
    Remove um manual (apenas admin). O arquivo físico também é deletado.
    """
    manual = await db.get(Manual, manual_id)
    if not manual:
        raise HTTPException(status_code=404, detail="Manual não encontrado")

    # Remove arquivo físico
    if os.path.exists(manual.arquivo_pdf):
        os.remove(manual.arquivo_pdf)

    await db.delete(manual)
    await db.commit()
    return None


@router.put("/{manual_id}", response_model=ManualResponse)
async def atualizar_manual(
    manual_id: int,
    manual_data: ManualUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user),
):
    """
    Atualiza dados do manual (não substitui o arquivo).
    """
    manual = await db.get(Manual, manual_id)
    if not manual:
        raise HTTPException(status_code=404, detail="Manual não encontrado")

    for field, value in manual_data.model_dump(exclude_unset=True).items():
        setattr(manual, field, value)

    # Não altera o arquivo_pdf nem o enviado_por
    await db.commit()
    await db.refresh(manual)
    return manual