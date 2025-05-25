"""Refactor Item model with default order_id

Revision ID: 5ebd993fac8b
Revises: 42585ca339a0
Create Date: 2025-05-25 11:45:25.866372

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5ebd993fac8b'
down_revision: Union[str, None] = '42585ca339a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('items') as batch_op:
        batch_op.alter_column(
            'order_id',
            existing_type=sa.INTEGER(),
            nullable=True
        )

def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('items') as batch_op:
        batch_op.alter_column(
            'order_id',
            existing_type=sa.INTEGER(),
            nullable=False
        )
