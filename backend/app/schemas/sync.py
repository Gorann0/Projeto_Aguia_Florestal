from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

from .ordem_servico import OrdemServicoCreate, OrdemServicoUpdate
from .checklist import ItemChecklistCreate, ItemChecklistUpdate


class SyncRequest(BaseModel):
    """
    Estrutura de dados enviada pelo cliente para sincronização.
    Cada lista contém registros criados ou atualizados localmente.
    """
    ordens_servico: List[OrdemServicoCreate | OrdemServicoUpdate] = Field(default_factory=list)
    itens_checklist: List[ItemChecklistCreate | ItemChecklistUpdate] = Field(default_factory=list)
    # ... outros tipos


class SyncResponse(BaseModel):
    applied: List[dict]
    conflicts: List[dict]
    timestamp: datetime


class SyncPullResponse(BaseModel):
    """
    Estrutura retornada pelo backend quando o cliente solicita
    atualizações do servidor.
    """

    timestamp: datetime

    maquinas: List[dict] = Field(default_factory=list)
    manuais: List[dict] = Field(default_factory=list)
    agendamentos: List[dict] = Field(default_factory=list)
    itens_checklist: List[dict] = Field(default_factory=list)
    ordens_servico: List[dict] = Field(default_factory=list)