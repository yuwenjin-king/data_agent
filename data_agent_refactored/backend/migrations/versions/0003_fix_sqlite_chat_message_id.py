"""fix sqlite chat_message autoincrement id.

Revision ID: 0003_fix_sqlite_chat_message_id
Revises: 0002_users
Create Date: 2026-07-30
"""

import sqlalchemy as sa
from alembic import op


revision = "0003_fix_sqlite_chat_message_id"
down_revision = "0002_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        return

    op.create_table(
        "_chat_message_sqlite_fix",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("message_type", sa.String(length=50), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column(
            "create_time",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["session_id"], ["chat_session.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        """
        INSERT INTO _chat_message_sqlite_fix
            (id, session_id, role, content, message_type, metadata, create_time)
        SELECT id, session_id, role, content, message_type, metadata, create_time
        FROM chat_message
        """
    )
    op.drop_table("chat_message")
    op.rename_table("_chat_message_sqlite_fix", "chat_message")


def downgrade() -> None:
    # Keep the SQLite-safe primary key type on downgrade; reverting would restore
    # the runtime insert failure that this migration fixes.
    return
