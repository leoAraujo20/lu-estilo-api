"""Refactor Item model with default order_idSet order_id in Item as non-nullable and adjust relationship integrity

Revision ID: e3c248cf54f9
Revises: 5ebd993fac8b
Create Date: 2025-05-25 13:05:15.359589

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3c248cf54f9'
down_revision: Union[str, None] = '5ebd993fac8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('items') as batch_op:
        batch_op.alter_column('order_id', existing_type=sa.INTEGER(), nullable=False)

def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('items') as batch_op:
        batch_op.alter_column('order_id', existing_type=sa.INTEGER(), nullable=True)
