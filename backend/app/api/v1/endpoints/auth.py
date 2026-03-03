from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime, timedelta
from typing import List

from app.core.database import get_db
from app.core.security import create_access_token, verify_password, get_password_hash
from app.core.config import settings
from app.models.usuario import Usuario
from app.models.sessao import Sessao
from app.schemas.usuario import UsuarioLogin, UsuarioPerfilResponse, UsuarioResponse
from app.schemas.token import TokenResponse  # (precisamos criar este schema)
from app.api.v1.dependencies import validar_dispositivo

router = APIRouter()


@router.get("/perfis", response_model=List[UsuarioPerfilResponse])
async def listar_perfis(
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna a lista de perfis (usuários ativos) para a tela de login estilo Netflix.
    """
    result = await db.execute(
        select(Usuario).where(Usuario.ativo == True).order_by(Usuario.nome_completo)
    )
    usuarios = result.scalars().all()
    return usuarios


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UsuarioLogin,
    db: AsyncSession = Depends(get_db),
    dispositivo_valido: bool = Depends(lambda: validar_dispositivo(login_data.dispositivo_id)),
):
    """
    Realiza o login do usuário com apelido e senha, gerando token JWT.
    """
    if not dispositivo_valido:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Número máximo de sessões atingido para este dispositivo",
        )

    # Busca usuário pelo apelido
    result = await db.execute(
        select(Usuario).where(Usuario.apelido == login_data.apelido, Usuario.ativo == True)
    )
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Apelido ou senha incorretos",
        )

    # Verifica senha
    if not verify_password(login_data.senha, usuario.hash_senha):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Apelido ou senha incorretos",
        )

    # Limitar número de sessões simultâneas por usuário
    result = await db.execute(
        select(Sessao).where(
            Sessao.usuario_id == usuario.id,
            Sessao.expira_em > datetime.utcnow()
        )
    )
    sessoes_ativas = result.scalars().all()
    if len(sessoes_ativas) >= settings.MAX_SESSIONS_PER_USER:
        # Opção: invalidar a sessão mais antiga
        sessoes_ativas.sort(key=lambda s: s.login_em)
        sessao_antiga = sessoes_ativas[0]
        await db.delete(sessao_antiga)
        await db.commit()

    # Cria token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(usuario.id), "funcao": usuario.funcao},
        expires_delta=access_token_expires,
    )

    # Salva sessão no banco
    sessao = Sessao(
        usuario_id=usuario.id,
        token=access_token,
        dispositivo_id=login_data.dispositivo_id,
        expira_em=datetime.utcnow() + access_token_expires,
    )
    db.add(sessao)

    # Atualiza último login
    usuario.ultimo_login = datetime.utcnow()
    await db.commit()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "usuario": UsuarioResponse.model_validate(usuario),
    }


@router.post("/logout")
async def logout(
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")),
    db: AsyncSession = Depends(get_db),
):
    """
    Invalida a sessão atual (logout).
    """
    result = await db.execute(select(Sessao).where(Sessao.token == token))
    sessao = result.scalar_one_or_none()
    if sessao:
        await db.delete(sessao)
        await db.commit()
    return {"message": "Logout realizado com sucesso"}


@router.post("/refresh")
async def refresh_token(
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")),
    db: AsyncSession = Depends(get_db),
):
    """
    Renova o token de acesso (gera um novo e invalida o antigo).
    """
    # Busca sessão pelo token
    result = await db.execute(
        select(Sessao).where(Sessao.token == token, Sessao.expira_em > datetime.utcnow())
    )
    sessao = result.scalar_one_or_none()
    if not sessao:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )

    # Busca usuário
    usuario = await db.get(Usuario, sessao.usuario_id)
    if not usuario or not usuario.ativo:
        raise HTTPException(status_code=401, detail="Usuário inativo")

    # Cria novo token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_token = create_access_token(
        data={"sub": str(usuario.id), "funcao": usuario.funcao},
        expires_delta=access_token_expires,
    )

    # Atualiza sessão: novo token e nova expiração
    sessao.token = new_token
    sessao.expira_em = datetime.utcnow() + access_token_expires
    sessao.ultima_ativacao = datetime.utcnow()
    await db.commit()

    return {
        "access_token": new_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }