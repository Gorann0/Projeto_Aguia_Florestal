from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.models.usuario import Usuario
from app.models.maquina import Maquina
from app.models.manual import Manual
from app.models.checklist import AgendamentoChecklist, ItemChecklist
from app.models.ordem_servico import OrdemServico
from app.schemas.sync import SyncRequest, SyncResponse  # (precisamos criar)
from app.api.v1.dependencies import get_current_user

router = APIRouter()


@router.post("/pull")
async def pull_updates(
    last_sync: datetime,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Endpoint para o cliente buscar dados atualizados desde last_sync.
    Retorna todos os registros modificados após a data.
    """
    # Lista de entidades que podem ser sincronizadas
    # Aqui você pode implementar a lógica de acordo com as necessidades de negócio
    # Exemplo simplificado:
    
    # Máquinas
    maquinas_result = await db.execute(
        select(Maquina).where(
            (Maquina.criado_em >= last_sync) | (Maquina.atualizado_em >= last_sync)
        )
    )
    maquinas = maquinas_result.scalars().all()

    # Manuais
    manuais_result = await db.execute(
        select(Manual).where(Manual.enviado_em >= last_sync)
    )
    manuais = manuais_result.scalars().all()

    # Agendamentos (incluindo itens)
    agendamentos_result = await db.execute(
        select(AgendamentoChecklist).where(
            (AgendamentoChecklist.criado_em >= last_sync) |
            (AgendamentoChecklist.atualizado_em >= last_sync) |
            (AgendamentoChecklist.concluido_em >= last_sync)
        )
    )
    agendamentos = agendamentos_result.scalars().all()

    # Itens de checklist
    itens_result = await db.execute(
        select(ItemChecklist).where(ItemChecklist.respondido_em >= last_sync)
    )
    itens = itens_result.scalars().all()

    # Ordens de serviço
    os_result = await db.execute(
        select(OrdemServico).where(
            (OrdemServico.criado_em >= last_sync) |
            (OrdemServico.atualizado_em >= last_sync)
        )
    )
    ordens = os_result.scalars().all()

    return {
        "timestamp": datetime.utcnow(),
        "maquinas": maquinas,
        "manuais": manuais,
        "agendamentos": agendamentos,
        "itens_checklist": itens,
        "ordens_servico": ordens,
    }


@router.post("/push")
async def push_updates(
    sync_data: SyncRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Endpoint para o cliente enviar alterações locais (criadas/atualizadas offline).
    O servidor aplica as mudanças e retorna conflitos se houver.
    """
    conflicts = []
    applied = []

    # Exemplo de processamento de ordens de serviço
    for os_data in sync_data.ordens_servico:
        # Verifica se já existe
        existing = await db.get(OrdemServico, os_data.id)
        if existing:
            # Se existir, compara timestamps para resolver conflito (last write wins)
            if os_data.atualizado_em and existing.atualizado_em and os_data.atualizado_em > existing.atualizado_em:
                # Atualiza
                for key, value in os_data.model_dump(exclude_unset=True).items():
                    setattr(existing, key, value)
                existing.atualizado_por_id = current_user.id
                existing.atualizado_em = datetime.utcnow()
                applied.append({"id": os_data.id, "tipo": "ordem_servico", "acao": "atualizado"})
            else:
                # Conflito: versão local mais antiga
                conflicts.append({
                    "id": os_data.id,
                    "tipo": "ordem_servico",
                    "mensagem": "Versão local mais antiga que a do servidor"
                })
        else:
            # Novo registro
            nova_os = OrdemServico(**os_data.model_dump(), criado_por_id=current_user.id)
            db.add(nova_os)
            applied.append({"id": os_data.id, "tipo": "ordem_servico", "acao": "criado"})

    # Processar outros tipos (itens, agendamentos, etc.)
    # ...

    await db.commit()

    return {
        "applied": applied,
        "conflicts": conflicts,
        "timestamp": datetime.utcnow()
    }