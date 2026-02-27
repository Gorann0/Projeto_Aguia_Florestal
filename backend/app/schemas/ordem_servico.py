from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from datetime import datetime
from typing import Optional, List
from .maquina import MaquinaResponse
from .usuario import UsuarioResponse


class OrdemServicoBase(BaseModel):
    """Base schema para ordem de serviço"""
    componente: str = Field(..., min_length=1, max_length=100)
    descricao_falha: str = Field(..., min_length=1)
    data_hora_inicio: datetime
    data_hora_fim: Optional[datetime] = None
    status: str = Field("aberta", pattern="^(aberta|em_andamento|concluida)$")


class OrdemServicoCreate(OrdemServicoBase):
    """Schema para criação de ordem de serviço"""
    maquina_id: int
    operador_id: int  # ID do operador que executará a OS
    
    @model_validator(mode="after")
    def validate_datas(self):
        if self.data_hora_inicio and self.data_hora_fim:
            if self.data_hora_fim < self.data_hora_inicio:
                raise ValueError(
                'data_hora_fim deve ser posterior a data_hora_inicio'
            )
    return self


class OrdemServicoUpdate(BaseModel):
    """Schema para atualização de ordem de serviço"""
    componente: Optional[str] = Field(None, min_length=1, max_length=100)
    descricao_falha: Optional[str] = Field(None, min_length=1)
    data_hora_inicio: Optional[datetime] = None
    data_hora_fim: Optional[datetime] = None
    status: Optional[str] = Field(None, pattern="^(aberta|em_andamento|concluida)$")
    

class OrdemServicoStatusUpdate(BaseModel):
    """Schema para atualização apenas do status"""
    status: str = Field(..., pattern="^(aberta|em_andamento|concluida)$")


class OrdemServicoResponse(OrdemServicoBase):
    """Schema para resposta da API"""
    id: int
    maquina_id: int
    operador_id: int
    horas_trabalhadas: Optional[float] = None
    criado_em: datetime
    criado_por_id: Optional[int] = None
    atualizado_em: Optional[datetime] = None
    atualizado_por_id: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class OrdemServicoListResponse(BaseModel):
    """Schema para listagem de ordens de serviço"""
    items: List[OrdemServicoResponse]
    total: int
    page: int
    size: int


class OrdemServicoDetailResponse(OrdemServicoResponse):
    """Schema para detalhamento de ordem de serviço"""
    maquina: MaquinaResponse
    operador: UsuarioResponse
    criado_por: Optional[UsuarioResponse] = None
    atualizado_por: Optional[UsuarioResponse] = None
    
    model_config = ConfigDict(from_attributes=True)


class OrdemServicoRelatorioResponse(BaseModel):
    """Schema para relatório de ordens de serviço"""
    total_os: int
    total_horas: float
    media_horas_por_os: float
    os_por_status: dict
    os_por_operador: List[dict]
    os_por_maquina: List[dict]
    periodo_inicio: datetime
    periodo_fim: datetime