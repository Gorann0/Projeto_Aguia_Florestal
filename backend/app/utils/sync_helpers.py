from datetime import datetime
import hashlib
import json


def generate_etag(data: dict) -> str:
    """
    Gera uma tag ETag baseada no conteúdo para controle de versão.
    """
    content = json.dumps(data, sort_keys=True, default=str)
    return hashlib.md5(content.encode()).hexdigest()


def resolve_conflict(local_version: dict, server_version: dict, strategy: str = "last_write_wins") -> dict:
    """
    Resolve conflitos entre duas versões de um registro.
    Estratégias: last_write_wins, merge_fields, etc.
    """
    if strategy == "last_write_wins":
        local_time = local_version.get("atualizado_em") or local_version.get("criado_em")
        server_time = server_version.get("atualizado_em") or server_version.get("criado_em")
        if local_time and server_time:
            if local_time > server_time:
                return local_version
    # Fallback: retorna versão do servidor
    return server_version


def should_sync(last_sync: datetime, record_timestamp: datetime) -> bool:
    """
    Verifica se um registro deve ser sincronizado baseado na última sincronização.
    """
    return record_timestamp > last_sync