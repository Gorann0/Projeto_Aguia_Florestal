from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import date, datetime

from app.core.database import get_db
from app.models.checklist import ModeloChecklist, AgendamentoChecklist, ItemChecklist
from app.models.maquina import Maquina
from app.models.usuario import Usuario
from app.schemas.checklist import (
    ModeloChecklistCreate, ModeloChecklistUpdate, ModeloChecklistResponse,
    AgendamentoCreate, AgendamentoUpdate, AgendamentoResponse,
    AgendamentoComItensResponse, AgendamentoPendenteResponse,
    ItemChecklistCreate, ItemChecklistUpdate, ItemChecklistResponse,
    ChecklistCompletoResponse, AgendamentoListResponse
)
from app.api.v1.dependencies import get_current_user, get_current_admin_user

router = APIRouter()


# ========== Modelos de Checklist (Admin) ==========

@router.get("/modelos", response_model=List[ModeloChecklistResponse])
async def listar_modelos(
    maquina_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Lista os modelos de checklist (itens padrão por máquina).
    """
    query = select(ModeloChecklist).where(ModeloChecklist.ativo == True)
    if maquina_id:
        query = query.where(ModeloChecklist.maquina_id == maquina_id)
    query = query.order_by(ModeloChecklist.maquina_id, ModeloChecklist.ordem)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/modelos", response_model=ModeloChecklistResponse, status_code=201)
async def criar_modelo(
    modelo_data: ModeloChecklistCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user),
):
    """
    Cria um novo item de checklist modelo (admin).
    """
    # Verifica máquina
    maquina = await db.get(Maquina, modelo_data.maquina_id)
    if not maquina:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")

    modelo = ModeloChecklist(
        **modelo_data.model_dump(),
        criado_por_id=current_user.id,
    )
    db.add(modelo)
    await db.commit()
    await db.refresh(modelo)
    return modelo


@router.put("/modelos/{modelo_id}", response_model=ModeloChecklistResponse)
async def atualizar_modelo(
    modelo_id: int,
    modelo_data: ModeloChecklistUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user),
):
    """
    Atualiza um item de checklist modelo.
    """
    modelo = await db.get(ModeloChecklist, modelo_id)
    if not modelo:
        raise HTTPException(status_code=404, detail="Item de checklist não encontrado")

    for field, value in modelo_data.model_dump(exclude_unset=True).items():
        setattr(modelo, field, value)

    modelo.atualizado_por_id = current_user.id
    await db.commit()
    await db.refresh(modelo)
    return modelo


@router.delete("/modelos/{modelo_id}", status_code=204)
async def deletar_modelo(
    modelo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user),
):
    """
    Remove um item de checklist modelo (hard delete).
    """
    modelo = await db.get(ModeloChecklist, modelo_id)
    if not modelo:
        raise HTTPException(status_code=404, detail="Item de checklist não encontrado")

    await db.delete(modelo)
    await db.commit()
    return None


# ========== Agendamentos ==========

@router.get("/agendamentos", response_model=AgendamentoListResponse)
async def listar_agendamentos(
    page: int = 1,
    size: int = 20,
    status: Optional[str] = None,
    maquina_id: Optional[int] = None,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Lista agendamentos de checklist com filtros.
    """
    offset = (page - 1) * size
    query = select(AgendamentoChecklist)
    count_query = select(func.count()).select_from(AgendamentoChecklist)

    if status:
        query = query.where(AgendamentoChecklist.status == status)
        count_query = count_query.where(AgendamentoChecklist.status == status)
    if maquina_id:
        query = query.where(AgendamentoChecklist.maquina_id == maquina_id)
        count_query = count_query.where(AgendamentoChecklist.maquina_id == maquina_id)
    if data_inicio:
        query = query.where(AgendamentoChecklist.data_vencimento >= data_inicio)
        count_query = count_query.where(AgendamentoChecklist.data_vencimento >= data_inicio)
    if data_fim:
        query = query.where(AgendamentoChecklist.data_vencimento <= data_fim)
        count_query = count_query.where(AgendamentoChecklist.data_vencimento <= data_fim)

    total = await db.scalar(count_query)
    result = await db.execute(
        query.order_by(AgendamentoChecklist.data_vencimento).offset(offset).limit(size)
    )
    items = result.scalars().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/agendamentos/pendentes", response_model=List[AgendamentoPendenteResponse])
async def listar_agendamentos_pendentes(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Lista agendamentos pendentes para o operador atual (ou todos se admin).
    """
    # Operador vê apenas pendentes; admin pode ver todos, mas vamos filtrar por pendentes
    query = (
        select(AgendamentoChecklist)
        .where(AgendamentoChecklist.status.in_(["pendente", "em_andamento"]))
        .order_by(AgendamentoChecklist.data_vencimento)
    )
    result = await db.execute(query)
    agendamentos = result.scalars().all()

    response = []
    for ag in agendamentos:
        # Conta itens
        itens_result = await db.execute(
            select(func.count()).select_from(ItemChecklist).where(ItemChecklist.agendamento_id == ag.id)
        )
        total_itens = itens_result.scalar() or 0
        itens_respondidos_result = await db.execute(
            select(func.count()).select_from(ItemChecklist).where(
                and_(
                    ItemChecklist.agendamento_id == ag.id,
                    ItemChecklist.resposta.isnot(None)
                )
            )
        )
        respondidos = itens_respondidos_result.scalar() or 0

        # Carrega máquina
        maquina = await db.get(Maquina, ag.maquina_id)
        response.append({
            **ag.__dict__,
            "maquina": maquina,
            "itens_count": total_itens,
            "itens_respondidos_count": respondidos,
        })
    return response


@router.post("/agendamentos", response_model=AgendamentoResponse, status_code=201)
async def criar_agendamento(
    agendamento_data: AgendamentoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user),  # apenas admin
):
    """
    Cria um novo agendamento de checklist. Se copiar_itens_modelo=True,
    copia os itens do modelo ativo da máquina.
    """
    maquina = await db.get(Maquina, agendamento_data.maquina_id)
    if not maquina:
        raise HTTPException(status_code=404, detail="Máquina não encontrada")

    # Cria agendamento
    agendamento = AgendamentoChecklist(
        maquina_id=agendamento_data.maquina_id,
        data_vencimento=agendamento_data.data_vencimento,
        status=agendamento_data.status,
        observacoes_gerais=agendamento_data.observacoes_gerais,
        criado_por_id=current_user.id,
    )
    db.add(agendamento)
    await db.flush()  # para obter o id

    if agendamento_data.copiar_itens_modelo:
        # Busca itens do modelo ativo
        modelos = await db.execute(
            select(ModeloChecklist)
            .where(
                ModeloChecklist.maquina_id == agendamento_data.maquina_id,
                ModeloChecklist.ativo == True
            )
            .order_by(ModeloChecklist.ordem)
        )
        for modelo in modelos.scalars().all():
            item = ItemChecklist(
                agendamento_id=agendamento.id,
                item_descricao=modelo.item_descricao,
                ordem=modelo.ordem,
            )
            db.add(item)

    await db.commit()
    await db.refresh(agendamento)
    return agendamento


@router.get("/agendamentos/{agendamento_id}", response_model=AgendamentoComItensResponse)
async def obter_agendamento(
    agendamento_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Retorna um agendamento com seus itens.
    """
    agendamento = await db.get(AgendamentoChecklist, agendamento_id)
    if not agendamento:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")

    # Carrega itens
    itens_result = await db.execute(
        select(ItemChecklist).where(ItemChecklist.agendamento_id == agendamento_id)
        .order_by(ItemChecklist.ordem)
    )
    itens = itens_result.scalars().all()

    # Carrega máquina
    maquina = await db.get(Maquina, agendamento.maquina_id)

    # Monta resposta agregada
    response = AgendamentoComItensResponse(
        **agendamento.__dict__,
        maquina=maquina,
        itens=itens
    )
    return response


@router.put("/agendamentos/{agendamento_id}", response_model=AgendamentoResponse)
async def atualizar_agendamento(
    agendamento_id: int,
    agendamento_data: AgendamentoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user),
):
    """
    Atualiza dados do agendamento (admin).
    """
    agendamento = await db.get(AgendamentoChecklist, agendamento_id)
    if not agendamento:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")

    for field, value in agendamento_data.model_dump(exclude_unset=True).items():
        setattr(agendamento, field, value)

    await db.commit()
    await db.refresh(agendamento)
    return agendamento


@router.post("/agendamentos/{agendamento_id}/itens", response_model=ItemChecklistResponse, status_code=201)
async def adicionar_item_avulso(
    agendamento_id: int,
    item_data: ItemChecklistCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user),
):
    """
    Adiciona um item avulso a um agendamento (admin, caso precise de item extra).
    """
    agendamento = await db.get(AgendamentoChecklist, agendamento_id)
    if not agendamento:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")

    item = ItemChecklist(
        **item_data.model_dump(),
        agendamento_id=agendamento_id,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.put("/itens/{item_id}", response_model=ItemChecklistResponse)
async def responder_item(
    item_id: int,
    item_data: ItemChecklistUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Operador responde um item do checklist (OK/NOK + observação).
    """
    item = await db.get(ItemChecklist, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")

    # Verifica se o agendamento está em andamento ou pendente
    agendamento = await db.get(AgendamentoChecklist, item.agendamento_id)
    if agendamento.status == "concluido":
        raise HTTPException(status_code=400, detail="Checklist já concluído")

    # Atualiza resposta
    if item_data.resposta is not None:
        item.resposta = item_data.resposta
    if item_data.observacao is not None:
        item.observacao = item_data.observacao
    item.respondido_em = datetime.utcnow()
    item.respondido_por_id = current_user.id

    # Se todos os itens foram respondidos, atualiza status do agendamento
    await db.flush()
    itens_result = await db.execute(
        select(ItemChecklist).where(ItemChecklist.agendamento_id == agendamento.id)
    )
    todos_itens = itens_result.scalars().all()
    if all(i.resposta is not None for i in todos_itens):
        agendamento.status = "concluido"
        agendamento.concluido_em = datetime.utcnow()
        agendamento.concluido_por_id = current_user.id
    else:
        if agendamento.status == "pendente":
            agendamento.status = "em_andamento"

    await db.commit()
    await db.refresh(item)
    return item


@router.post("/agendamentos/{agendamento_id}/concluir", response_model=AgendamentoResponse)
async def concluir_agendamento(
    agendamento_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Força a conclusão do agendamento (caso todos itens já estejam respondidos ou admin force).
    """
    agendamento = await db.get(AgendamentoChecklist, agendamento_id)
    if not agendamento:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")

    if agendamento.status == "concluido":
        raise HTTPException(status_code=400, detail="Agendamento já está concluído")

    agendamento.status = "concluido"
    agendamento.concluido_em = datetime.utcnow()
    agendamento.concluido_por_id = current_user.id
    await db.commit()
    await db.refresh(agendamento)
    return agendamento