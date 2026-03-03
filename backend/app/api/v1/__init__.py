from fastapi import APIRouter

from .endpoints import (
    auth,
    usuarios,
    maquinas,
    manuais,
    checklists,
    ordens_servico,
    sync,
)

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["autenticação"])
router.include_router(usuarios.router, prefix="/usuarios", tags=["usuários"])
router.include_router(maquinas.router, prefix="/maquinas", tags=["máquinas"])
router.include_router(manuais.router, prefix="/manuais", tags=["manuais"])
router.include_router(checklists.router, prefix="/checklists", tags=["checklists"])
router.include_router(ordens_servico.router, prefix="/ordens-servico", tags=["ordens de serviço"])
router.include_router(sync.router, prefix="/sync", tags=["sincronização"])