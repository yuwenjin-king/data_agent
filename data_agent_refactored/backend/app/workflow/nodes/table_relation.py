from typing import Optional

from langchain_core.runnables import RunnableConfig
from sqlalchemy.orm import Session

from app.models.knowledge import SemanticModel
from app.services.datasource_service import logical_relation_crud
from app.workflow.prompts.loader import PromptLoader
from app.workflow.sql.schema_builder import build_schema_from_documents
from app.workflow.sql.utils import (
    get_datasource_url_and_dialect,
    map_dialect_to_sql_dialect,
    resolve_agent_datasource,
)
from app.workflow.state import SchemaDTO, WorkflowState


async def table_relation_node(
    state: WorkflowState,
    config: Optional[RunnableConfig] = None,
) -> WorkflowState:
    configurable = (config or {}).get("configurable", {})
    db: Optional[Session] = configurable.get("db")

    table_docs = state.get("table_documents_for_schema", [])
    column_docs = state.get("column_documents_for_schema", [])
    agent_id = state.get("agent_id")

    if not db or not table_docs:
        return {
            "table_relation_output": SchemaDTO(),
            "db_dialect_type": "mysql",
            "generated_semantic_model_prompt": "",
        }

    agent_datasource = resolve_agent_datasource(db, agent_id)
    datasource_id = agent_datasource.datasource_id if agent_datasource else None
    _, datasource_type = (
        get_datasource_url_and_dialect(db, agent_datasource) if agent_datasource else (None, None)
    )
    dialect = map_dialect_to_sql_dialect(datasource_type)

    schema = build_schema_from_documents(
        table_docs=table_docs,
        column_docs=column_docs,
        datasource_id=datasource_id,
        dialect=dialect,
    )

    # Enrich with logical relations.
    if datasource_id:
        relations = logical_relation_crud.get_multi_by_datasource(db, datasource_id=datasource_id)
        table_names = {table.name for table in schema.tables}
        for table in schema.tables:
            table.foreign_keys = []
        for relation in relations:
            if relation.source_table_name in table_names:
                for table in schema.tables:
                    if table.name == relation.source_table_name and table.foreign_keys is not None:
                        table.foreign_keys.append(
                            {
                                "source_column": relation.source_column_name,
                                "target_table": relation.target_table_name,
                                "target_column": relation.target_column_name,
                                "relation_type": relation.relation_type,
                            }
                        )

    # Load semantic models for recalled tables.
    semantic_model_text = ""
    if agent_id and schema.tables:
        table_names = [table.name for table in schema.tables]
        semantic_models = (
            db.query(SemanticModel)
            .filter(
                SemanticModel.agent_id == agent_id,
                SemanticModel.table_name.in_(table_names),
                SemanticModel.status == 1,
            )
            .all()
        )
        if semantic_models:
            lines = []
            for sm in semantic_models:
                lines.append(
                    f"- 表:{sm.table_name} 列:{sm.column_name} "
                    f"业务名:{sm.business_name or ''} "
                    f"同义词:{sm.synonyms or ''} "
                    f"描述:{sm.business_description or ''}"
                )
            loader = PromptLoader()
            semantic_model_text = loader.render("semantic-model", semantic_model="\n".join(lines))

    return {
        "table_relation_output": schema,
        "db_dialect_type": dialect,
        "generated_semantic_model_prompt": semantic_model_text,
        "table_relation_retry_count": 0,
    }
