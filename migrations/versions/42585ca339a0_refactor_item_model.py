"""Refactor Item model

Revision ID: 42585ca339a0
Revises: 09d06f58bc32
Create Date: 2025-05-25 10:23:29.066783

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '42585ca339a0'
down_revision: Union[str, None] = '09d06f58bc32'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Use batch_alter_table para compatibilidade com SQLite
    with op.batch_alter_table('items') as batch_op:
        batch_op.alter_column(
            'order_id',
            existing_type=sa.INTEGER(),
            nullable=False
        )

def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('items') as batch_op:
        batch_op.alter_column(
            'order_id',
            existing_type=sa.INTEGER(),
            nullable=True
        )
