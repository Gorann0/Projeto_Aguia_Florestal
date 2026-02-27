from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from datetime import datetime
from typing import Optional, List
from .manual import ManualResponse
from .checklist import ModeloChecklistResponse


class MaquinaBase(BaseModel):
    """Base schema para máquina"""
    nome: str = Field(..., min_length=1, max_length=100)
    modelo: Optional[str] = Field(None, max_length=100)
    fabricante: Optional[str] = Field(None, max_length=100)
    numero_serie: Optional[str] = Field(None, max_length=100)
    ativo: bool = True


class MaquinaCreate(MaquinaBase):
    """Schema para criação de máquina"""
    pass


class MaquinaUpdate(BaseModel):
    """Schema para atualização de máquina"""
    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    modelo: Optional[str] = Field(None, max_length=100)
    fabricante: Optional[str] = Field(None, max_length=100)
    numero_serie: Optional[str] = Field(None, max_length=100)
    ativo: Optional[bool] = None


class MaquinaResponse(MaquinaBase):
    """Schema para resposta da API"""
    id: int
    criado_em: datetime
    criado_por_id: Optional[int] = None
    atualizado_em: Optional[datetime] = None
    atualizado_por_id: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class MaquinaListResponse(BaseModel):
    """Schema para listagem de máquinas"""
    items: List[MaquinaResponse]
    total: int
    page: int
    size: int


class MaquinaComManuaisResponse(MaquinaResponse):
    """Schema para máquina com seus manuais"""
    manuais: List[ManualResponse] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)


class MaquinaComChecklistsResponse(MaquinaResponse):
    """Schema para máquina com seus modelos de checklist"""
    modelos_checklist: List[ModeloChecklistResponse] = []
    
    model_config = ConfigDict(from_attributes=True)