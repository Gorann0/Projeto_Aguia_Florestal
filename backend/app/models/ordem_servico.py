from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class OrdemServico(Base):
    __tablename__ = "ordens_servico"

    id = Column(Integer, primary_key=True, index=True)
    maquina_id = Column(Integer, ForeignKey("maquinas.id", ondelete="CASCADE"), nullable=False)
    componente = Column(String(100), nullable=False)
    descricao_falha = Column(Text, nullable=False)
    data_hora_inicio = Column(DateTime(timezone=True), nullable=False)
    data_hora_fim = Column(DateTime(timezone=True))
    
    # Coluna gerada para horas trabalhadas (PostgreSQL 12+)
    horas_trabalhadas = Column(
        Numeric(5, 2),
        server_default=func.extract('epoch', func.coalesce(data_hora_fim, func.now()) - data_hora_inicio) / 3600,
        deferred=True  # Não carrega automaticamente se não for solicitado
    )
    
    status = Column(String(20), default="aberta")  # aberta, em_andamento, concluida
    operador_id = Column(Integer, ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    
    # Auditoria
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    criado_por_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"))
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())
    atualizado_por_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"))

    # Relacionamentos
    maquina = relationship("Maquina", back_populates="ordens_servico")
    operador = relationship("Usuario", foreign_keys=[operador_id])
    criado_por = relationship("Usuario", foreign_keys=[criado_por_id])
    atualizado_por = relationship("Usuario", foreign_keys=[atualizado_por_id])

    # Constraints e índices
    __table_args__ = (
        CheckConstraint("status IN ('aberta', 'em_andamento', 'concluida')", name='ck_os_status'),
        CheckConstraint("data_hora_fim IS NULL OR data_hora_fim >= data_hora_inicio", name='ck_os_datas'),
        Index('idx_os_datas', 'data_hora_inicio', 'data_hora_fim'),
    )

    def __repr__(self):
        return f"<OrdemServico(id={self.id}, maquina_id={self.maquina_id}, status='{self.status}')>"