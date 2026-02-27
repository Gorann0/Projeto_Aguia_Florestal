from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ModeloChecklist(Base):
    __tablename__ = "modelos_checklist"
    __table_args__ = (
        UniqueConstraint('maquina_id', 'ordem', name='uq_modelo_maquina_ordem'),
    )

    id = Column(Integer, primary_key=True, index=True)
    maquina_id = Column(Integer, ForeignKey("maquinas.id", ondelete="CASCADE"), nullable=False)
    item_descricao = Column(Text, nullable=False)
    ordem = Column(Integer, nullable=False)
    ativo = Column(Boolean, default=True)
    
    # Auditoria
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    criado_por_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"))
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())
    atualizado_por_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"))

    # Relacionamentos
    maquina = relationship("Maquina", back_populates="modelos_checklist")
    criado_por = relationship("Usuario", foreign_keys=[criado_por_id])
    atualizado_por = relationship("Usuario", foreign_keys=[atualizado_por_id])

    def __repr__(self):
        return f"<ModeloChecklist(id={self.id}, maquina_id={self.maquina_id}, ordem={self.ordem})>"


class AgendamentoChecklist(Base):
    __tablename__ = "agendamentos_checklist"

    id = Column(Integer, primary_key=True, index=True)
    maquina_id = Column(Integer, ForeignKey("maquinas.id", ondelete="CASCADE"), nullable=False)
    data_vencimento = Column(Date, nullable=False, index=True)
    status = Column(String(20), default="pendente")  # pendente, em_andamento, concluido
    observacoes_gerais = Column(Text)
    
    # Auditoria
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    criado_por_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"))
    concluido_em = Column(DateTime(timezone=True))
    concluido_por_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"))

    # Relacionamentos
    maquina = relationship("Maquina", back_populates="agendamentos")
    itens = relationship("ItemChecklist", back_populates="agendamento", cascade="all, delete-orphan")
    criado_por = relationship("Usuario", foreign_keys=[criado_por_id])
    concluido_por = relationship("Usuario", foreign_keys=[concluido_por_id])

    # Check constraint para status
    __table_args__ = (
        CheckConstraint("status IN ('pendente', 'em_andamento', 'concluido')", name='ck_agendamento_status'),
    )

    def __repr__(self):
        return f"<AgendamentoChecklist(id={self.id}, maquina_id={self.maquina_id}, vencimento={self.data_vencimento})>"


class ItemChecklist(Base):
    __tablename__ = "itens_checklist"

    id = Column(Integer, primary_key=True, index=True)
    agendamento_id = Column(Integer, ForeignKey("agendamentos_checklist.id", ondelete="CASCADE"), nullable=False)
    item_descricao = Column(Text, nullable=False)  # cópia do modelo no momento do agendamento
    resposta = Column(String(10))  # 'OK', 'NOK'
    observacao = Column(Text)
    ordem = Column(Integer, nullable=False)
    
    # Auditoria
    respondido_em = Column(DateTime(timezone=True))
    respondido_por_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"))

    # Relacionamentos
    agendamento = relationship("AgendamentoChecklist", back_populates="itens")
    respondido_por = relationship("Usuario", foreign_keys=[respondido_por_id])

    # Check constraint para resposta
    __table_args__ = (
        CheckConstraint("resposta IN ('OK', 'NOK')", name='ck_item_resposta'),
    )

    def __repr__(self):
        return f"<ItemChecklist(id={self.id}, agendamento_id={self.agendamento_id}, resposta='{self.resposta}')>"