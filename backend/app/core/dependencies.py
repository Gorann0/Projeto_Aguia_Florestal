from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import verify_token
from app.models.usuario import Usuario
from app.models.sessao import Sessao
from app.core.config import settings
from datetime import datetime, timezone

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Usuario:
    """
    Valida o token JWT, verifica se a sessão está ativa e retorna o usuário autenticado.
    Levanta exceção 401 se inválido.
    """
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    usuario_id: int = payload.get("sub")
    if not usuario_id:
        raise HTTPException(status_code=401, detail="Token não contém identificador do usuário")

    # Verifica se a sessão existe e não expirou
    result = await db.execute(
        select(Sessao).where(Sessao.token == token, Sessao.expira_em > datetime.now(timezone.utc)
    ))
    sessao = result.scalar_one_or_none()
    if not sessao:
        raise HTTPException(status_code=401, detail="Sessão não encontrada ou expirada")

    # Busca o usuário ativo
    result = await db.execute(select(Usuario).where(Usuario.id == usuario_id, Usuario.ativo.is_(True)))
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuário não encontrado ou inativo")

    # Atualiza último acesso da sessão
    sessao.ultima_ativacao = datetime.now(timezone.utc)
    await db.commit()

    return usuario


async def get_current_admin_user(
    current_user: Usuario = Depends(get_current_user),
) -> Usuario:
    """
    Dependência que exige que o usuário logado seja administrador.
    """
    if current_user.funcao != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso permitido apenas para administradores",
        )
    return current_user