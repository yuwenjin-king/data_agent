from typing import Dict, List, Optional

from app.workflow.state import ColumnDTO, SchemaDTO, TableDTO
from app.workflow.vectorstore.document import VectorDocument


def build_schema_from_documents(
    table_docs: List[VectorDocument],
    column_docs: List[VectorDocument],
    datasource_id: Optional[int] = None,
    dialect: Optional[str] = None,
) -> SchemaDTO:
    """Build a SchemaDTO from recalled vector documents."""
    tables: Dict[str, TableDTO] = {}

    for doc in table_docs:
        meta = doc.metadata
        table_name = meta.get("table_name") or meta.get("name")
        if not table_name:
            continue
        tables[table_name] = TableDTO(
            name=table_name,
            business_name=meta.get("business_name"),
            description=meta.get("description"),
            columns=[],
            primary_key=meta.get("primary_key"),
            foreign_keys=meta.get("foreign_keys"),
        )

    for doc in column_docs:
        meta = doc.metadata
        table_name = meta.get("table_name")
        if not table_name or table_name not in tables:
            continue
        column = ColumnDTO(
            name=meta.get("column_name") or meta.get("name"),
            data_type=meta.get("data_type"),
            business_name=meta.get("business_name"),
            description=meta.get("description"),
            comment=meta.get("column_comment"),
            samples=meta.get("samples"),
        )
        tables[table_name].columns.append(column)

    return SchemaDTO(
        datasource_id=datasource_id,
        dialect=dialect,
        tables=list(tables.values()),
    )


def format_schema_for_prompt(schema: SchemaDTO) -> str:
    """Format a SchemaDTO as a concise string for LLM prompts."""
    lines = []
    if schema.dialect:
        lines.append(f"数据库方言: {schema.dialect}")
    for table in schema.tables:
        lines.append(f"\n表名: {table.name}")
        if table.business_name:
            lines.append(f"  业务名称: {table.business_name}")
        if table.description:
            lines.append(f"  描述: {table.description}")
        if table.primary_key:
            lines.append(f"  主键: {', '.join(table.primary_key)}")
        if table.columns:
            lines.append("  字段:")
            for col in table.columns:
                col_line = f"    - {col.name}"
                if col.data_type:
                    col_line += f" ({col.data_type})"
                if col.business_name:
                    col_line += f" [{col.business_name}]"
                if col.description:
                    col_line += f": {col.description}"
                lines.append(col_line)
    return "\n".join(lines)
