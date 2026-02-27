from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Maquina(Base):
    __tablename__ = "maquinas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    modelo = Column(String(100))
    fabricante = Column(String(100))
    numero_serie = Column(String(100), unique=True)
    ativo = Column(Boolean, default=True)
    
    # Auditoria
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    criado_por_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"))
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())
    atualizado_por_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"))

    # Relacionamentos
    manuais = relationship("Manual", back_populates="maquina", cascade="all, delete-orphan")
    modelos_checklist = relationship("ModeloChecklist", back_populates="maquina", cascade="all, delete-orphan")
    agendamentos = relationship("AgendamentoChecklist", back_populates="maquina", cascade="all, delete-orphan")
    ordens_servico = relationship("OrdemServico", back_populates="maquina", cascade="all, delete-orphan")
    
    # Auto-relacionamento para auditoria
    criado_por = relationship("Usuario", foreign_keys=[criado_por_id])
    atualizado_por = relationship("Usuario", foreign_keys=[atualizado_por_id])

    def __repr__(self):
        return f"<Maquina(id={self.id}, nome='{self.nome}', modelo='{self.modelo}')>"