from pydantic import BaseModel
from .usuario import UsuarioResponse


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    usuario: UsuarioResponse