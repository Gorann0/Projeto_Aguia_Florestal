from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from app.core.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import (
    UsuarioCreate, UsuarioUpdate, UsuarioResponse, UsuarioListResponse,
    UsuarioPerfilResponse
)
from app.api.v1.dependencies import get_current_admin_user
from app.core.security import get_password_hash

router = APIRouter()


@router.get("/perfis", response_model=List[UsuarioPerfilResponse])
async def listar_perfis_publicos(
    db: AsyncSession = Depends(get_db),
):
    """
    Lista pública de perfis para tela de login (apenas dados básicos).
    """
    result = await db.execute(
        select(Usuario).where(Usuario.ativo == True).order_by(Usuario.nome_completo)
    )
    usuarios = result.scalars().all()
    return usuarios


@router.get("/", response_model=UsuarioListResponse)
async def listar_usuarios(
    page: int = 1,
    size: int = 20,
    funcao: Optional[str] = None,
    ativo: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user),  # só admin
):
    """
    Lista todos os usuários (apenas admin).
    """
    offset = (page - 1) * size
    query = select(Usuario)

    if funcao:
        query = query.where(Usuario.funcao == funcao)
    if ativo is not None:
        query = query.where(Usuario.ativo == ativo)

    # Total de registros
    count_query = select(func.count()).select_from(Usuario)
    if funcao:
        count_query = count_query.where(Usuario.funcao == funcao)
    if ativo is not None:
        count_query = count_query.where(Usuario.ativo == ativo)
    total = await db.scalar(count_query)

    # Paginação
    result = await db.execute(
        query.order_by(Usuario.id).offset(offset).limit(size)
    )
    items = result.scalars().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
    }


@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def criar_usuario(
    usuario_data: UsuarioCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user),
):
    """
    Cria um novo usuário (apenas admin).
    """
    # Verifica se apelido já existe
    result = await db.execute(
        select(Usuario).where(Usuario.apelido == usuario_data.apelido)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apelido já está em uso",
        )

    # Cria usuário
    usuario = Usuario(
        nome_completo=usuario_data.nome_completo,
        apelido=usuario_data.apelido,
        funcao=usuario_data.funcao,
        hash_senha=get_password_hash(usuario_data.senha),
        icone_perfil=usuario_data.icone_perfil,
        ativo=usuario_data.ativo,
        criado_por_id=current_user.id,
    )
    db.add(usuario)
    await db.commit()
    await db.refresh(usuario)
    return usuario


@router.get("/{usuario_id}", response_model=UsuarioResponse)
async def obter_usuario(
    usuario_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user),
):
    """
    Obtém detalhes de um usuário específico.
    """
    usuario = await db.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario


@router.put("/{usuario_id}", response_model=UsuarioResponse)
async def atualizar_usuario(
    usuario_id: int,
    usuario_data: UsuarioUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user),
):
    """
    Atualiza um usuário existente.
    """
    usuario = await db.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Verifica se novo apelido já existe (se foi alterado)
    if usuario_data.apelido and usuario_data.apelido != usuario.apelido:
        result = await db.execute(
            select(Usuario).where(Usuario.apelido == usuario_data.apelido)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Apelido já está em uso")

    # Atualiza campos
    for field, value in usuario_data.model_dump(exclude_unset=True).items():
        if field == "senha" and value:
            setattr(usuario, "hash_senha", get_password_hash(value))
        elif value is not None:
            setattr(usuario, field, value)

    usuario.atualizado_por_id = current_user.id
    await db.commit()
    await db.refresh(usuario)
    return usuario


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_usuario(
    usuario_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user),
):
    """
    Remove um usuário (soft delete ou hard delete? Vamos usar hard delete por simplicidade,
    mas poderia ser soft update ativo=False).
    """
    usuario = await db.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Impedir auto-deleção
    if usuario.id == current_user.id:
        raise HTTPException(status_code=400, detail="Não é possível excluir o próprio usuário")

    await db.delete(usuario)
    await db.commit()
    return None