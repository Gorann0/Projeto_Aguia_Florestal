"""initial migration

Revision ID: 001
Revises: 
Create Date: 2025-03-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tabela usuarios
    op.create_table(
        'usuarios',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('nome_completo', sa.String(100), nullable=False),
        sa.Column('apelido', sa.String(50), nullable=False, unique=True),
        sa.Column('funcao', sa.String(20), nullable=False),
        sa.Column('hash_senha', sa.Text, nullable=False),
        sa.Column('icone_perfil', sa.String(255)),
        sa.Column('ativo', sa.Boolean, default=True),
        sa.Column('ultimo_login', sa.DateTime(timezone=True)),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('criado_por_id', sa.Integer, sa.ForeignKey('usuarios.id', ondelete='SET NULL')),
        sa.Column('atualizado_em', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('atualizado_por_id', sa.Integer, sa.ForeignKey('usuarios.id', ondelete='SET NULL')),
    )
    op.create_index('idx_usuarios_apelido', 'usuarios', ['apelido'])
    op.create_index('idx_usuarios_funcao', 'usuarios', ['funcao'])

    # Tabela sessoes
    op.create_table(
        'sessoes',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('usuario_id', sa.Integer, sa.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token', sa.String(500), nullable=False, unique=True),
        sa.Column('dispositivo_id', sa.String(100), nullable=False),
        sa.Column('login_em', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('ultima_ativacao', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('expira_em', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('idx_sessoes_usuario', 'sessoes', ['usuario_id'])
    op.create_index('idx_sessoes_token', 'sessoes', ['token'])
    op.create_index('idx_sessoes_usuario_expira', 'sessoes', ['usuario_id', 'expira_em'])

    # Tabela maquinas
    op.create_table(
        'maquinas',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('nome', sa.String(100), nullable=False),
        sa.Column('modelo', sa.String(100)),
        sa.Column('fabricante', sa.String(100)),
        sa.Column('numero_serie', sa.String(100), unique=True),
        sa.Column('ativo', sa.Boolean, default=True),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('criado_por_id', sa.Integer, sa.ForeignKey('usuarios.id', ondelete='SET NULL')),
        sa.Column('atualizado_em', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('atualizado_por_id', sa.Integer, sa.ForeignKey('usuarios.id', ondelete='SET NULL')),
    )

    # Tabela manuais
    op.create_table(
        'manuais',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('maquina_id', sa.Integer, sa.ForeignKey('maquinas.id', ondelete='CASCADE'), nullable=False),
        sa.Column('titulo', sa.String(200), nullable=False),
        sa.Column('arquivo_pdf', sa.String(500), nullable=False),
        sa.Column('versao', sa.String(20)),
        sa.Column('descricao', sa.Text),
        sa.Column('enviado_em', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('enviado_por_id', sa.Integer, sa.ForeignKey('usuarios.id', ondelete='SET NULL')),
    )
    op.create_index('idx_manuais_maquina', 'manuais', ['maquina_id'])

    # Tabela modelos_checklist
    op.create_table(
        'modelos_checklist',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('maquina_id', sa.Integer, sa.ForeignKey('maquinas.id', ondelete='CASCADE'), nullable=False),
        sa.Column('item_descricao', sa.Text, nullable=False),
        sa.Column('ordem', sa.Integer, nullable=False),
        sa.Column('ativo', sa.Boolean, default=True),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('criado_por_id', sa.Integer, sa.ForeignKey('usuarios.id', ondelete='SET NULL')),
        sa.Column('atualizado_em', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('atualizado_por_id', sa.Integer, sa.ForeignKey('usuarios.id', ondelete='SET NULL')),
        sa.UniqueConstraint('maquina_id', 'ordem', name='uq_modelo_maquina_ordem'),
    )
    op.create_index('idx_modelos_maquina', 'modelos_checklist', ['maquina_id'])

    # Tabela agendamentos_checklist
    op.create_table(
        'agendamentos_checklist',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('maquina_id', sa.Integer, sa.ForeignKey('maquinas.id', ondelete='CASCADE'), nullable=False),
        sa.Column('data_vencimento', sa.Date, nullable=False),
        sa.Column('status', sa.String(20), server_default='pendente'),
        sa.Column('observacoes_gerais', sa.Text),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('criado_por_id', sa.Integer, sa.ForeignKey('usuarios.id', ondelete='SET NULL')),
        sa.Column('concluido_em', sa.DateTime(timezone=True)),
        sa.Column('concluido_por_id', sa.Integer, sa.ForeignKey('usuarios.id', ondelete='SET NULL')),
        sa.CheckConstraint("status IN ('pendente', 'em_andamento', 'concluido')", name='ck_agendamento_status'),
    )
    op.create_index('idx_agendamentos_maquina', 'agendamentos_checklist', ['maquina_id'])
    op.create_index('idx_agendamentos_vencimento', 'agendamentos_checklist', ['data_vencimento'])

    # Tabela itens_checklist
    op.create_table(
        'itens_checklist',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('agendamento_id', sa.Integer, sa.ForeignKey('agendamentos_checklist.id', ondelete='CASCADE'), nullable=False),
        sa.Column('item_descricao', sa.Text, nullable=False),
        sa.Column('resposta', sa.String(10)),
        sa.Column('observacao', sa.Text),
        sa.Column('ordem', sa.Integer, nullable=False),
        sa.Column('respondido_em', sa.DateTime(timezone=True)),
        sa.Column('respondido_por_id', sa.Integer, sa.ForeignKey('usuarios.id', ondelete='SET NULL')),
        sa.CheckConstraint("resposta IN ('OK', 'NOK')", name='ck_item_resposta'),
    )
    op.create_index('idx_itens_agendamento', 'itens_checklist', ['agendamento_id'])

    # Tabela ordens_servico
    op.create_table(
        'ordens_servico',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('maquina_id', sa.Integer, sa.ForeignKey('maquinas.id', ondelete='CASCADE'), nullable=False),
        sa.Column('componente', sa.String(100), nullable=False),
        sa.Column('descricao_falha', sa.Text, nullable=False),
        sa.Column('data_hora_inicio', sa.DateTime(timezone=True), nullable=False),
        sa.Column('data_hora_fim', sa.DateTime(timezone=True)),
        sa.Column('horas_trabalhadas', sa.Numeric(5, 2), sa.Computed("EXTRACT(EPOCH FROM (data_hora_fim - data_hora_inicio)) / 3600")),
        sa.Column('status', sa.String(20), server_default='aberta'),
        sa.Column('operador_id', sa.Integer, sa.ForeignKey('usuarios.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('criado_por_id', sa.Integer, sa.ForeignKey('usuarios.id', ondelete='SET NULL')),
        sa.Column('atualizado_em', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('atualizado_por_id', sa.Integer, sa.ForeignKey('usuarios.id', ondelete='SET NULL')),
        sa.CheckConstraint("status IN ('aberta', 'em_andamento', 'concluida')", name='ck_os_status'),
        sa.CheckConstraint("data_hora_fim IS NULL OR data_hora_fim >= data_hora_inicio", name='ck_os_datas'),
    )
    op.create_index('idx_os_maquina', 'ordens_servico', ['maquina_id'])
    op.create_index('idx_os_operador', 'ordens_servico', ['operador_id'])
    op.create_index('idx_os_status', 'ordens_servico', ['status'])
    op.create_index('idx_os_datas', 'ordens_servico', ['data_hora_inicio', 'data_hora_fim'])


def downgrade() -> None:
    op.drop_table('ordens_servico')
    op.drop_table('itens_checklist')
    op.drop_table('agendamentos_checklist')
    op.drop_table('modelos_checklist')
    op.drop_table('manuais')
    op.drop_table('maquinas')
    op.drop_table('sessoes')
    op.drop_table('usuarios')