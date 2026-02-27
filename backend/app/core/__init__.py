# Pacote core - exporta componentes principais
from .config import settings
from .database import SessionLocal, engine, Base, get_db
from .security import create_access_token, verify_password, get_password_hash, verify_token
from .dependencies import get_current_user, get_current_admin_user

__all__ = [
    "settings",
    "SessionLocal",
    "engine",
    "Base",
    "get_db",
    "create_access_token",
    "verify_password",
    "get_password_hash",
    "verify_token",
    "get_current_user",
    "get_current_admin_user",
]