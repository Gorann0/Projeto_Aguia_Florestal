from pydantic import BaseModel, Field, ConfigDict, model_validator
from datetime import datetime, date
from typing import Optional, List, Literal
from .maquina import MaquinaResponse

# ========== Modelos de Checklist ==========

class ModeloChecklistBase(BaseModel):
    """Base schema para modelo de checklist"""
    item_descricao: str = Field(..., min_length=1)
    ordem: int = Field(..., ge=0)
    ativo: bool = True


class ModeloChecklistCreate(ModeloChecklistBase):
    """Schema para criação de modelo de checklist"""
    maquina_id: int


class ModeloChecklistUpdate(BaseModel):
    """Schema para atualização de modelo de checklist"""
    item_descricao: Optional[str] = Field(None, min_length=1)
    ordem: Optional[int] = Field(None, ge=0)
    ativo: Optional[bool] = None


class ModeloChecklistResponse(ModeloChecklistBase):
    """Schema para resposta da API"""
    id: int
    maquina_id: int
    criado_em: datetime
    criado_por_id: Optional[int] = None
    atualizado_em: Optional[datetime] = None
    atualizado_por_id: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class ModeloChecklistListResponse(BaseModel):
    """Schema para listagem de modelos de checklist"""
    items: List[ModeloChecklistResponse]
    total: int
    page: int
    size: int


# ========== Itens de Checklist ==========

class ItemChecklistBase(BaseModel):
    """Base schema para item de checklist"""
    item_descricao: str = Field(..., min_length=1)
    resposta: Optional[Literal["OK", "NOK"]] = None
    observacao: Optional[str] = None
    ordem: int = Field(..., ge=0)


class ItemChecklistCreate(ItemChecklistBase):
    """Schema para criação de item de checklist"""
    agendamento_id: int


class ItemChecklistUpdate(BaseModel):
    """Schema para atualização de item de checklist"""
    resposta: Optional[Literal["OK", "NOK"]] = None
    observacao: Optional[str] = None


class ItemChecklistResponse(ItemChecklistBase):
    """Schema para resposta da API"""
    id: int
    agendamento_id: int
    respondido_em: Optional[datetime] = None
    respondido_por_id: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class ItemChecklistBatchCreate(BaseModel):
    """Schema para criação em lote de itens de checklist"""
    itens: List[ItemChecklistCreate]


# ========== Agendamentos ==========

class AgendamentoBase(BaseModel):
    """Base schema para agendamento de checklist"""
    data_vencimento: date
    status: Literal["pendente", "em_andamento", "concluido"] = "pendente"
    observacoes_gerais: Optional[str] = None


class AgendamentoCreate(AgendamentoBase):
    """Schema para criação de agendamento"""
    maquina_id: int
    copiar_itens_modelo: bool = True  # se True, copia itens do modelo ativo


class AgendamentoUpdate(BaseModel):
    """Schema para atualização de agendamento"""
    data_vencimento: Optional[date] = None
    status: Optional[Literal["pendente", "em_andamento", "concluido"]] = None
    observacoes_gerais: Optional[str] = None


class AgendamentoResponse(AgendamentoBase):
    """Schema para resposta da API"""
    id: int
    maquina_id: int
    criado_em: datetime
    criado_por_id: Optional[int] = None
    concluido_em: Optional[datetime] = None
    concluido_por_id: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class AgendamentoListResponse(BaseModel):
    """Schema para listagem de agendamentos"""
    items: List[AgendamentoResponse]
    total: int
    page: int
    size: int


class AgendamentoPendenteResponse(AgendamentoResponse):
    """Schema para agendamentos pendentes (com dados da máquina)"""
    maquina: MaquinaResponse
    itens_count: int
    itens_respondidos_count: int
    
    model_config = ConfigDict(from_attributes=True)


# ========== Agregados ==========

class AgendamentoComItensResponse(AgendamentoResponse):
    """Schema para agendamento com seus itens"""
    maquina: MaquinaResponse
    itens: List[ItemChecklistResponse] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)


class ChecklistCompletoResponse(BaseModel):
    """Schema para resposta completa de checklist"""
    agendamento: AgendamentoComItensResponse
    progresso: float = Field(0, ge=0, le=100)

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def calculate_progress(self):
        total_itens = len(self.agendamento.itens)

        if total_itens > 0:
            respondidos = sum(
                1 for item in self.agendamento.itens
                if item.resposta is not None
            )
            self.progresso = (respondidos / total_itens) * 100
        else:
            self.progresso = 0

        return self