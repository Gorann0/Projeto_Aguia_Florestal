from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from .manual import ManualResponse

if TYPE_CHECKING:
    from .checklist import ModeloChecklistResponse

class MaquinaBase(BaseModel):
    """Base schema para máquina"""
    nome: str = Field(..., min_length=1, max_length=100)
    modelo: Optional[str] = Field(None, max_length=100)
    fabricante: Optional[str] = Field(None, max_length=100)
    numero_serie: Optional[str] = Field(None, max_length=100)
    ativo: bool = True

class MaquinaCreate(MaquinaBase):
    pass

class MaquinaUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    modelo: Optional[str] = Field(None, max_length=100)
    fabricante: Optional[str] = Field(None, max_length=100)
    numero_serie: Optional[str] = Field(None, max_length=100)
    ativo: Optional[bool] = None

class MaquinaResponse(MaquinaBase):
    id: int
    criado_em: datetime
    criado_por_id: Optional[int] = None
    atualizado_em: Optional[datetime] = None
    atualizado_por_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)

class MaquinaListResponse(BaseModel):
    items: List[MaquinaResponse]
    total: int
    page: int
    size: int

class MaquinaComManuaisResponse(MaquinaResponse):
    manuais: List[ManualResponse] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)

class MaquinaComChecklistsResponse(MaquinaResponse):
    """Schema para máquina com seus modelos de checklist"""
    modelos_checklist: List['ModeloChecklistResponse'] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)