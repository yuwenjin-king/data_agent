from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from app.core.config import settings


def test_sqlite_migrations_allow_chat_message_autoincrement(tmp_path, monkeypatch):
    database_url = f"sqlite:///{tmp_path / 'migration.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", database_url)

    alembic_config = Config("alembic.ini")
    command.upgrade(alembic_config, "head")

    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            agent_id = connection.execute(
                text("INSERT INTO agent (name, status) VALUES ('agent', 'published')")
            ).lastrowid
            connection.execute(
                text(
                    """
                    INSERT INTO chat_session (id, agent_id, title, status)
                    VALUES ('session-1', :agent_id, 'session', 'active')
                    """
                ),
                {"agent_id": agent_id},
            )
            message_id = connection.execute(
                text(
                    """
                    INSERT INTO chat_message (session_id, role, content, message_type)
                    VALUES ('session-1', 'user', 'hi', 'text')
                    """
                )
            ).lastrowid

        assert message_id == 1
    finally:
        engine.dispose()
