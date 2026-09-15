"""add is_active to users

Revision ID: 0e3ca5f3940e
Revises: bb3d3680b063
Create Date: 2026-08-21 01:23:43.592140
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0e3ca5f3940e"
down_revision: str | Sequence[str] | None = "bb3d3680b063"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "is_active")
