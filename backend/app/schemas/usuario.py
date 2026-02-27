from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from datetime import datetime
from typing import Optional, List


class UsuarioBase(BaseModel):
    """Base schema para usuário"""
    nome_completo: str = Field(..., min_length=3, max_length=100)
    apelido: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    funcao: str = Field(..., pattern="^(admin|operador)$")
    icone_perfil: Optional[str] = Field(None, max_length=255)
    ativo: bool = True


class UsuarioCreate(UsuarioBase):
    """Schema para criação de usuário (apenas admin)"""
    senha: str = Field(..., min_length=6, max_length=100)


class UsuarioUpdate(BaseModel):
    """Schema para atualização de usuário"""
    nome_completo: Optional[str] = Field(None, min_length=3, max_length=100)
    apelido: Optional[str] = Field(None, min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    funcao: Optional[str] = Field(None, pattern="^(admin|operador)$")
    icone_perfil: Optional[str] = Field(None, max_length=255)
    ativo: Optional[bool] = None
    senha: Optional[str] = Field(None, min_length=6, max_length=100)


class UsuarioInDB(UsuarioBase):
    """Schema para usuário no banco de dados (com hash)"""
    id: int
    hash_senha: str
    ultimo_login: Optional[datetime] = None
    criado_em: datetime
    criado_por_id: Optional[int] = None
    atualizado_em: Optional[datetime] = None
    atualizado_por_id: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class UsuarioResponse(BaseModel):
    """Schema para resposta da API (sem dados sensíveis)"""
    id: int
    nome_completo: str
    apelido: str
    funcao: str
    icone_perfil: Optional[str] = None
    ativo: bool
    ultimo_login: Optional[datetime] = None
    criado_em: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UsuarioListResponse(BaseModel):
    """Schema para listagem de usuários"""
    items: List[UsuarioResponse]
    total: int
    page: int
    size: int


class UsuarioLogin(BaseModel):
    """Schema para login (apelido e senha)"""
    apelido: str
    senha: str
    dispositivo_id: str = Field(..., description="Identificador do tablet")


class UsuarioPerfilResponse(BaseModel):
    """Schema para resposta da tela de perfis (estilo Netflix)"""
    id: int
    apelido: str
    nome_completo: str
    icone_perfil: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)