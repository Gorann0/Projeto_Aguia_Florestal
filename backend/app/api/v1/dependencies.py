from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.dependencies import get_current_user as global_get_current_user
from app.models.usuario import Usuario
from app.models.sessao import Sessao
from app.core.config import settings
from app.models.ordem_servico import OrdemServico


# Re-exporta a dependência global de usuário atual
get_current_user = global_get_current_user


async def get_current_admin_user(
    current_user: Usuario = Depends(get_current_user),
) -> Usuario:
    """Verifica se o usuário atual é admin."""
    if current_user.funcao != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operação permitida apenas para administradores",
        )
    return current_user


async def validar_dispositivo(
    dispositivo_id: str,
    db: AsyncSession,
) -> None:
    """
    Valida se o dispositivo (tablet) pode iniciar uma sessão.
    Pode ser usada para limitar número de dispositivos por usuário.
    """
    # Exemplo: contar sessões ativas do dispositivo
    result = await db.execute(
        select(Sessao).where(
            Sessao.dispositivo_id == dispositivo_id,
            Sessao.expira_em > datetime.now(timezone.utc)
        )
    )
    sessoes_ativas = len(result.scalars().all())
    
    # Se houver mais de N sessoes, podemos rejeitar ou invalidar a mais antiga
    MAX_SESSOES_POR_DISPOSITIVO = 1  # apenas uma sessão por tablet
    if sessoes_ativas >= MAX_SESSOES_POR_DISPOSITIVO:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Número máximo de sessões atingido para este dispositivo",
        )


async def get_db_with_user(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> AsyncSession:
    """
    Dependência que injeta a sessão de banco e o usuário atual,
    útil para auditoria (gravar quem fez a ação).
    """
    # Podemos anexar o usuário à sessão se quisermos (ex: via contexto)
    # db.info["usuario_id"] = current_user.id
    return db

async def get_current_user_or_admin_for_os(
    os_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    os = await db.get(OrdemServico, os_id)
    if not os:
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada")

    if current_user.funcao != "admin" and os.operador_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão negada"
        )

    return os