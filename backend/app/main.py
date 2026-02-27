from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.endpoints import (
    auth,
    usuarios,
    maquinas,
    manuais,
    checklists,
    ordens_servico,
    sync,
)

app = FastAPI(
    title="Águia Florestal PCM",
    version="1.0.0",
    description="API do sistema de Planejamento e Controle de Manutenção",
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusão dos routers por módulo
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Autenticação"])
app.include_router(usuarios.router, prefix="/api/v1/usuarios", tags=["Usuários"])
app.include_router(maquinas.router, prefix="/api/v1/maquinas", tags=["Máquinas"])
app.include_router(manuais.router, prefix="/api/v1/manuais", tags=["Manuais"])
app.include_router(checklists.router, prefix="/api/v1/checklists", tags=["Checklists"])
app.include_router(ordens_servico.router, prefix="/api/v1/ordens-servico", tags=["Ordens de Serviço"])
app.include_router(sync.router, prefix="/api/v1/sync", tags=["Sincronização"])


@app.get("/")
async def root():
    return {"message": "API Águia Florestal PCM - Online"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}