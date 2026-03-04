"""Add dataset_relationship_custom table

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-03-04

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'dataset_relationship_custom' not in inspector.get_table_names():
        op.create_table(
            'dataset_relationship_custom',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('subject_id', sa.String(36), sa.ForeignKey('package.id', ondelete='CASCADE'), nullable=False),
            sa.Column('object_id', sa.String(36), sa.ForeignKey('package.id', ondelete='CASCADE'), nullable=False),
            sa.Column('created', sa.DateTime),
            sa.UniqueConstraint('subject_id', 'object_id', name='uq_dataset_relationship_custom'),
        )


def downgrade():
    op.drop_table('dataset_relationship_custom')
