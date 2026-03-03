from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List

from app.core.database import get_db
from app.models.maquina import Maquina
from app.models.manual import Manual
from app.schemas.maquina import (
    MaquinaCreate, MaquinaUpdate, MaquinaResponse, MaquinaListResponse,
    MaquinaComManuaisResponse, MaquinaComChecklistsResponse
)
from app.api.v1.dependencies import get_current_user, get_current_admin_user
from app.models.usuario import Usuario

router = APIRouter()


@router.get("/", response_model=MaquinaListResponse)
async def listar_maquinas(
    page: int = 1,
    size: int = 20,
    ativo: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),  # qualquer usuário logado
):
    """
    Lista todas as máquinas (com paginação).
    """
    offset = (page - 1) * size
    query = select(Maquina)

    if ativo is not None:
        query = query.where(Maquina.ativo == ativo)

    count_query = select(func.count()).select_from(Maquina)
    if ativo is not None:
        count_query = count_query.where(Maquina.ativo == ativo)
    total = await db.scalar(count_query)

    result = await db.execute(
        query.order_by(Maquina.nome).offset(offset).limit(size)
    )
    items = result.scalars().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
    }


@router.post("/", response_model=MaquinaResponse, status_code=status.HTTP_201_CREATED)
async def criar_maquina(
    maquina_data: MaquinaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user),  # só admin
):
    """
    Cria uma nova máquina.
    """
    # Verifica se número de série já existe (se fornecido)
    if maquina_data.numero_serie:
        result = await db.execute(
            select(Maquina).where(Maquina.numero_serie == maquina_data.numero_serie)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="Número de série já cadastrado",
            )

    maquina = Maquina(
        **maquina_data.model_dump(),
        criado_por_id=current_user.id,
    )
    db.add(maquina)
    await db.commit()
    await db.refresh(maquina)
    return maquina


@router.get("/{maquina_id}", response_model=MaquinaResponse)
async def obter_maquina(
    maquina_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Obtém detalhes de uma máquina específica.
    """
    maquina = await db.get(Maquina, maquina_id)
    if not maquina:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")
    return maquina


@router.put("/{maquina_id}", response_model=MaquinaResponse)
async def atualizar_maquina(
    maquina_id: int,
    maquina_data: MaquinaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user),
):
    """
    Atualiza uma máquina existente.
    """
    maquina = await db.get(Maquina, maquina_id)
    if not maquina:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")

    # Verifica número de série único
    if maquina_data.numero_serie and maquina_data.numero_serie != maquina.numero_serie:
        result = await db.execute(
            select(Maquina).where(Maquina.numero_serie == maquina_data.numero_serie)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Número de série já cadastrado")

    for field, value in maquina_data.model_dump(exclude_unset=True).items():
        setattr(maquina, field, value)

    maquina.atualizado_por_id = current_user.id
    await db.commit()
    await db.refresh(maquina)
    return maquina


@router.delete("/{maquina_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_maquina(
    maquina_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user),
):
    """
    Remove uma máquina (hard delete). 
    Em produção, talvez seja melhor soft delete (ativo=False).
    """
    maquina = await db.get(Maquina, maquina_id)
    if not maquina:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")

    await db.delete(maquina)
    await db.commit()
    return None


@router.get("/{maquina_id}/manuais", response_model=List[MaquinaComManuaisResponse])
async def listar_manuais_da_maquina(
    maquina_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Retorna a máquina com seus manuais.
    """
    maquina = await db.get(Maquina, maquina_id)
    if not maquina:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")

    # Carrega manuais
    result = await db.execute(
        select(Manual).where(Manual.maquina_id == maquina_id)
    )
    manuais = result.scalars().all()

    # Converte para o schema agregado
    response = MaquinaComManuaisResponse.model_validate(maquina)
    response.manuais = manuais
    return response