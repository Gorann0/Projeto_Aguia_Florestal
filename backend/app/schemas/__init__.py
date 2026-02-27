from .usuario import (
    UsuarioBase, UsuarioCreate, UsuarioUpdate, UsuarioInDB, UsuarioResponse,
    UsuarioListResponse, UsuarioLogin, UsuarioPerfilResponse
)
from .maquina import (
    MaquinaBase, MaquinaCreate, MaquinaUpdate, MaquinaResponse, MaquinaListResponse,
    MaquinaComManuaisResponse, MaquinaComChecklistsResponse
)
from .manual import (
    ManualBase, ManualCreate, ManualUpdate, ManualResponse, ManualListResponse,
    ManualUploadResponse, ManualDownloadResponse
)
from .checklist import (
    # Modelos
    ModeloChecklistBase, ModeloChecklistCreate, ModeloChecklistUpdate,
    ModeloChecklistResponse, ModeloChecklistListResponse,
    # Agendamentos
    AgendamentoBase, AgendamentoCreate, AgendamentoUpdate,
    AgendamentoResponse, AgendamentoListResponse, AgendamentoPendenteResponse,
    # Itens
    ItemChecklistBase, ItemChecklistCreate, ItemChecklistUpdate,
    ItemChecklistResponse, ItemChecklistBatchCreate,
    # Agregados
    ChecklistCompletoResponse, AgendamentoComItensResponse
)
from .ordem_servico import (
    OrdemServicoBase, OrdemServicoCreate, OrdemServicoUpdate,
    OrdemServicoResponse, OrdemServicoListResponse, OrdemServicoDetailResponse,
    OrdemServicoStatusUpdate, OrdemServicoRelatorioResponse
)

__all__ = [
    # Usuário
    "UsuarioBase", "UsuarioCreate", "UsuarioUpdate", "UsuarioInDB", "UsuarioResponse",
    "UsuarioListResponse", "UsuarioLogin", "UsuarioPerfilResponse",
    
    # Máquina
    "MaquinaBase", "MaquinaCreate", "MaquinaUpdate", "MaquinaResponse", 
    "MaquinaListResponse", "MaquinaComManuaisResponse", "MaquinaComChecklistsResponse",
    
    # Manual
    "ManualBase", "ManualCreate", "ManualUpdate", "ManualResponse", 
    "ManualListResponse", "ManualUploadResponse", "ManualDownloadResponse",
    
    # Checklist
    "ModeloChecklistBase", "ModeloChecklistCreate", "ModeloChecklistUpdate",
    "ModeloChecklistResponse", "ModeloChecklistListResponse",
    "AgendamentoBase", "AgendamentoCreate", "AgendamentoUpdate",
    "AgendamentoResponse", "AgendamentoListResponse", "AgendamentoPendenteResponse",
    "ItemChecklistBase", "ItemChecklistCreate", "ItemChecklistUpdate",
    "ItemChecklistResponse", "ItemChecklistBatchCreate",
    "ChecklistCompletoResponse", "AgendamentoComItensResponse",
    
    # Ordem de Serviço
    "OrdemServicoBase", "OrdemServicoCreate", "OrdemServicoUpdate",
    "OrdemServicoResponse", "OrdemServicoListResponse", "OrdemServicoDetailResponse",
    "OrdemServicoStatusUpdate", "OrdemServicoRelatorioResponse"
]