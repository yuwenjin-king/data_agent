from typing import List, Optional, Tuple

from sqlalchemy import create_engine, inspect


def build_sqlalchemy_url(
    type: str,
    host: str,
    port: int,
    database_name: str,
    username: str,
    password: str,
    connection_url: Optional[str] = None,
) -> str:
    """Build a SQLAlchemy URL from datasource fields.

    If ``connection_url`` is provided and non-empty, it is returned as-is.
    """
    if connection_url:
        return connection_url

    driver_map = {
        "mysql": "mysql+pymysql",
        "postgresql": "postgresql+psycopg2",
        "sqlite": "sqlite",
    }

    driver = driver_map.get(type.lower())
    if not driver:
        raise ValueError(f"Unsupported datasource type: {type}")

    if driver == "sqlite":
        return f"{driver}:///{database_name}"

    return f"{driver}://{username}:{password}@{host}:{port}/{database_name}"


def test_connection(url: str) -> Tuple[bool, str]:
    """Attempt to connect to ``url`` and return (ok, message)."""
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        return True, "Connection successful"
    except Exception as exc:
        return False, str(exc)


def list_tables(url: str, schema: Optional[str] = None) -> List[str]:
    engine = create_engine(url)
    inspector = inspect(engine)
    return inspector.get_table_names(schema=schema)


def list_columns(url: str, table_name: str, schema: Optional[str] = None) -> List[str]:
    engine = create_engine(url)
    inspector = inspect(engine)
    columns = inspector.get_columns(table_name, schema=schema)
    return [c["name"] for c in columns]
