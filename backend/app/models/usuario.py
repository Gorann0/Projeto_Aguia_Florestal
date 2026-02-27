from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome_completo = Column(String(100), nullable=False)
    apelido = Column(String(50), unique=True, nullable=False, index=True)
    funcao = Column(String(20), nullable=False)  # 'admin' ou 'operador'
    hash_senha = Column(Text, nullable=False)
    icone_perfil = Column(String(255))  # caminho ou nome do ícone
    ativo = Column(Boolean, default=True)
    ultimo_login = Column(DateTime(timezone=True))
    
    # Auditoria
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    criado_por_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"))
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())
    atualizado_por_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"))

    # Relacionamentos
    sessoes = relationship("Sessao", back_populates="usuario", cascade="all, delete-orphan")
    manuais_enviados = relationship("Manual", foreign_keys="Manual.enviado_por_id", back_populates="enviado_por")
    modelos_checklist_criados = relationship("ModeloChecklist", foreign_keys="ModeloChecklist.criado_por_id", back_populates="criado_por")
    agendamentos_criados = relationship("AgendamentoChecklist", foreign_keys="AgendamentoChecklist.criado_por_id", back_populates="criado_por")
    agendamentos_concluidos = relationship("AgendamentoChecklist", foreign_keys="AgendamentoChecklist.concluido_por_id", back_populates="concluido_por")
    itens_respondidos = relationship("ItemChecklist", back_populates="respondido_por")
    ordens_servico_operador = relationship("OrdemServico", foreign_keys="OrdemServico.operador_id", back_populates="operador")
    ordens_servico_criadas = relationship("OrdemServico", foreign_keys="OrdemServico.criado_por_id", back_populates="criado_por")
    
    # Auto-relacionamento para auditoria
    criado_por = relationship("Usuario", foreign_keys=[criado_por_id], remote_side=[id])
    atualizado_por = relationship("Usuario", foreign_keys=[atualizado_por_id], remote_side=[id])

    def __repr__(self):
        return f"<Usuario(id={self.id}, apelido='{self.apelido}', funcao='{self.funcao}')>"