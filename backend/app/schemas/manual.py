from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from datetime import datetime
from typing import Optional, List


class ManualBase(BaseModel):
    """Base schema para manual"""
    titulo: str = Field(..., min_length=1, max_length=200)
    versao: Optional[str] = Field(None, max_length=20)
    descricao: Optional[str] = None


class ManualCreate(ManualBase):
    """Schema para criação de manual"""
    maquina_id: int
    arquivo_pdf: str  # caminho do arquivo


class ManualUpdate(BaseModel):
    """Schema para atualização de manual"""
    titulo: Optional[str] = Field(None, min_length=1, max_length=200)
    versao: Optional[str] = Field(None, max_length=20)
    descricao: Optional[str] = None
    arquivo_pdf: Optional[str] = None


class ManualResponse(ManualBase):
    """Schema para resposta da API"""
    id: int
    maquina_id: int
    arquivo_pdf: str
    enviado_em: datetime
    enviado_por_id: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class ManualListResponse(BaseModel):
    """Schema para listagem de manuais"""
    items: List[ManualResponse]
    total: int
    page: int
    size: int


class ManualUploadResponse(BaseModel):
    """Schema para resposta após upload de manual"""
    id: int
    titulo: str
    arquivo_pdf: str
    mensagem: str = "Manual enviado com sucesso"


class ManualDownloadResponse(BaseModel):
    """Schema para resposta ao solicitar download de manual"""
    id: int
    titulo: str
    url_download: str
    expires_in: int = 3600  # tempo em segundos