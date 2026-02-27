from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Manual(Base):
    __tablename__ = "manuais"

    id = Column(Integer, primary_key=True, index=True)
    maquina_id = Column(Integer, ForeignKey("maquinas.id", ondelete="CASCADE"), nullable=False)
    titulo = Column(String(200), nullable=False)
    arquivo_pdf = Column(String(500), nullable=False)  # caminho relativo ao storage
    versao = Column(String(20))
    descricao = Column(Text)
    
    # Auditoria
    enviado_em = Column(DateTime(timezone=True), server_default=func.now())
    enviado_por_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"))

    # Relacionamentos
    maquina = relationship("Maquina", back_populates="manuais")
    enviado_por = relationship("Usuario", foreign_keys=[enviado_por_id])

    def __repr__(self):
        return f"<Manual(id={self.id}, titulo='{self.titulo}', maquina_id={self.maquina_id})>"