from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import 
from typing import Optional
from datetime import datetime, timezone

from app.core.database import get_db
from app.models.ordem_servico import OrdemServico
from app.models.maquina import Maquina
from app.models.usuario import Usuario
from app.schemas.ordem_servico import (
    OrdemServicoCreate, OrdemServicoUpdate, OrdemServicoResponse,
    OrdemServicoListResponse, OrdemServicoDetailResponse,
    OrdemServicoStatusUpdate, OrdemServicoRelatorioResponse
)
from app.api.v1.dependencies import get_current_user, get_current_admin_user, get_current_user_or_admin_for_os

router = APIRouter()


@router.get("/", response_model=OrdemServicoListResponse)
async def listar_ordens_servico(
    page: int = 1,
    size: int = 20,
    status: Optional[str] = None,
    maquina_id: Optional[int] = None,
    operador_id: Optional[int] = None,
    data_inicio: Optional[datetime] = None,
    data_fim: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Lista ordens de serviço com filtros.
    """
    offset = (page - 1) * size
    query = select(OrdemServico)
    count_query = select(func.count()).select_from(OrdemServico)

    if status:
        query = query.where(OrdemServico.status == status)
        count_query = count_query.where(OrdemServico.status == status)
    if maquina_id:
        query = query.where(OrdemServico.maquina_id == maquina_id)
        count_query = count_query.where(OrdemServico.maquina_id == maquina_id)
    if operador_id:
        query = query.where(OrdemServico.operador_id == operador_id)
        count_query = count_query.where(OrdemServico.operador_id == operador_id)
    if data_inicio:
        query = query.where(OrdemServico.data_hora_inicio >= data_inicio)
        count_query = count_query.where(OrdemServico.data_hora_inicio >= data_inicio)
    if data_fim:
        query = query.where(OrdemServico.data_hora_inicio <= data_fim)
        count_query = count_query.where(OrdemServico.data_hora_inicio <= data_fim)

    total = await db.scalar(count_query)
    result = await db.execute(
        query.order_by(OrdemServico.data_hora_inicio.desc())
        .offset(offset)
        .limit(size)
    )
    items = result.scalars().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
    }


@router.post("/", response_model=OrdemServicoResponse, status_code=201)
async def criar_ordem_servico(
    os_data: OrdemServicoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Cria uma nova ordem de serviço. Qualquer operador logado pode criar.
    O operador_id pode ser o próprio ou outro (admin define).
    """
    # Verifica máquina
    maquina = await db.get(Maquina, os_data.maquina_id)
    if not maquina:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")

    # Verifica operador
    operador = await db.get(Usuario, os_data.operador_id)
    if not operador or not operador.ativo:
        raise HTTPException(status_code=404, detail="Operador não encontrado ou inativo")

    # Cria OS
    os = OrdemServico(
        **os_data.model_dump(),
        criado_por_id=current_user.id,
    )
    db.add(os)
    await db.commit()
    await db.refresh(os)
    return os


@router.put("/{os_id}", response_model=OrdemServicoResponse)
async def atualizar_ordem_servico(
    os_data: OrdemServicoUpdate,
    os: OrdemServico = Depends(get_current_user_or_admin_for_os),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Atualiza uma OS. Apenas o operador responsável ou admin pode atualizar.
    """

    # Regra extra para concluir
    if os_data.status == "concluida" and not os_data.data_hora_fim and not os.data_hora_fim:
        raise HTTPException(
            status_code=400,
            detail="Para concluir a OS, informe a data/hora de fim"
        )

    for field, value in os_data.model_dump(exclude_unset=True).items():
        setattr(os, field, value)

    os.atualizado_por_id = current_user.id
    os.atualizado_em = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(os)
    return os


@router.patch("/{os_id}/status", response_model=OrdemServicoResponse)
async def atualizar_status_os(
    status_data: OrdemServicoStatusUpdate,
    os: OrdemServico = Depends(get_current_user_or_admin_for_os),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Atualiza apenas o status da OS (útil para iniciar/parar cronômetro).
    """

    # Regras de transição de status
    if status_data.status == "concluida" and not os.data_hora_fim:
        # Se não tem data_fim, define agora
        os.data_hora_fim = datetime.now(timezone.utc)

    os.status = status_data.status
    os.atualizado_por_id = current_user.id
    os.atualizado_em = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(os)
    return os


@router.delete("/{os_id}", status_code=204)
async def deletar_ordem_servico(
    os_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user),  # apenas admin
):
    """
    Remove uma OS (apenas admin).
    """
    os = await db.get(OrdemServico, os_id)
    if not os:
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada")

    await db.delete(os)
    await db.commit()
    return None


@router.get("/relatorios/ppr", response_model=OrdemServicoRelatorioResponse)
async def relatorio_ppr(
    data_inicio: datetime,
    data_fim: datetime,
    operador_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user),  # apenas admin
):
    """
    Gera relatório para cálculo de PPR: total de horas trabalhadas por operador/período.
    """
    # Base query
    query = select(OrdemServico).where(
        OrdemServico.data_hora_inicio >= data_inicio,
        OrdemServico.data_hora_fim <= data_fim,
        OrdemServico.status == "concluida"
    )
    if operador_id:
        query = query.where(OrdemServico.operador_id == operador_id)

    result = await db.execute(query)
    ordens = result.scalars().all()

    # Cálculos
    total_horas = sum(os.horas_trabalhadas or 0 for os in ordens)
    total_os = len(ordens)
    media_horas = total_horas / total_os if total_os > 0 else 0

    # Agrupa por status (só concluídas, mas pode ter variação)
    os_por_status = {"concluida": total_os}

    # Por operador
    from collections import defaultdict
    op_dict = defaultdict(lambda: {"qtd": 0, "horas": 0.0})
    for os in ordens:
        op_dict[os.operador_id]["qtd"] += 1
        op_dict[os.operador_id]["horas"] += os.horas_trabalhadas or 0

    os_por_operador = [
        {"operador_id": k, "quantidade": v["qtd"], "horas_totais": v["horas"]}
        for k, v in op_dict.items()
    ]

    # Por máquina
    maq_dict = defaultdict(lambda: {"qtd": 0, "horas": 0.0})
    for os in ordens:
        maq_dict[os.maquina_id]["qtd"] += 1
        maq_dict[os.maquina_id]["horas"] += os.horas_trabalhadas or 0

    os_por_maquina = [
        {"maquina_id": k, "quantidade": v["qtd"], "horas_totais": v["horas"]}
        for k, v in maq_dict.items()
    ]

    return {
        "total_os": total_os,
        "total_horas": total_horas,
        "media_horas_por_os": media_horas,
        "os_por_status": os_por_status,
        "os_por_operador": os_por_operador,
        "os_por_maquina": os_por_maquina,
        "periodo_inicio": data_inicio,
        "periodo_fim": data_fim,
    }