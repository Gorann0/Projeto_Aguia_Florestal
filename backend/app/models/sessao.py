from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Sessao(Base):
    __tablename__ = "sessoes"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(500), unique=True, nullable=False)
    dispositivo_id = Column(String(100), nullable=False)  # identifica o tablet
    login_em = Column(DateTime(timezone=True), server_default=func.now())
    ultima_ativacao = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    expira_em = Column(DateTime(timezone=True), nullable=False)
    revogado = Column(Boolean,default=False,server_default="false")

    # Relacionamentos
    usuario = relationship("Usuario", back_populates="sessoes")

    # Índices compostos
    __table_args__ = (
    Index('idx_sessoes_usuario_expira', 'usuario_id', 'expira_em'),
    UniqueConstraint(
        "usuario_id",
        "dispositivo_id",
        name="uq_usuario_dispositivo"
        ),
    )

    def __repr__(self):
        return f"<Sessao(id={self.id}, usuario_id={self.usuario_id}, dispositivo='{self.dispositivo_id}')>"