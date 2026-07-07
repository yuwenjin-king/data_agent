# Schema Compatibility

This document tracks the compatibility between the original Java DataAgent
entities and the FastAPI refactor SQLAlchemy models.

Status legend:

- `Aligned`: table and main columns exist with compatible names.
- `Type drift`: table and column exist, but Python type differs from original Java/entity intent.
- `Partial`: core columns exist, but behavior, constraints, indexes, or companion APIs are incomplete.
- `Missing`: original capability is not represented yet.

## Summary

The refactor currently covers the main management tables, but it is not a
verified drop-in schema replacement. Existing DataAgent databases should be
validated table by table before use. For an existing database, use
`alembic stamp head` only after validation; for a new development database,
use `alembic upgrade head`.

## Table Matrix

| Table | Original Entity | Refactor Model | Status | Notes |
|---|---|---|---|---|
| `agent` | `Agent` | `Agent` | Aligned | `api_key_enabled` 已从 Boolean 对齐为 Integer。 |
| `business_knowledge` | `BusinessKnowledge` | `BusinessKnowledge` | Aligned | Core fields present. Vector-store behavior is not implemented. |
| `datasource` | `Datasource` | `Datasource` | Partial | Core fields present. Connection test, table/column discovery, type handlers are not implemented. |
| `agent_datasource` | `AgentDatasource` | `AgentDatasource` | Aligned | `is_active` 已从 Boolean 对齐为 Integer。 |
| `agent_datasource_tables` | Mapper/table in original project | `AgentDatasourceTables` | Partial | Table selection stored, but update/toggle APIs are incomplete. |
| `logical_relation` | `LogicalRelation` | `LogicalRelation` | Aligned | `is_deleted` 已从 Boolean 对齐为 Integer。 |
| `semantic_model` | `SemanticModel` | `SemanticModel` | Partial | `status` 已从 Boolean 对齐为 Integer；`updated_time` 命名仍需与原 DDL 核对。 |
| `agent_knowledge` | `AgentKnowledge` | `AgentKnowledge` | Partial | Core metadata present. Upload, splitting, embedding, cleanup and retry workflows are missing. |
| `agent_preset_question` | `AgentPresetQuestion` | `AgentPresetQuestion` | Type drift | `id` and `agent_id` are `Long` in Java, integer in Python. |
| `chat_session` | `ChatSession` | `ChatSession` | Aligned | Core fields present. Session events and title generation are incomplete. |
| `chat_message` | `ChatMessage` | `ChatMessage` | Type drift | Original metadata is a JSON string; Python model maps DB column `metadata` to ORM attribute `metadata_` as JSON. |
| `user_prompt_config` | `UserPromptConfig` | `UserPromptConfig` | Aligned | Core fields present. Active selection and batch enable/disable APIs are incomplete. |
| `model_config` | `ModelConfig` | `ModelConfig` | Aligned | `temperature` is now `Float`, matching Java `Double`. Test/activate/check-ready APIs are incomplete. |

## Known Type Drifts

The original project often uses `Integer` values for flags; the refactor now uses
`Integer` for the documented drift fields as well. Remaining drifts:

- `agent_preset_question.id` and `agent_preset_question.agent_id` are `Long` in
  Java and `Integer` in Python. This is acceptable for most deployments but may
  need `BigInteger` for very large IDs.

Before using an existing database directly, verify the actual column types in the
production DDL against the migration above.

## Missing Schema Verification

The following checks are still required before claiming compatibility:

- Compare SQLAlchemy generated DDL with original `schema.sql` or production DDL.
- Check primary keys, foreign keys, indexes, unique constraints, default values,
  enum values and nullable flags.
- Verify MySQL and PostgreSQL generated DDL separately.
- Validate seed data and existing rows against Pydantic response schemas.

## Migration Policy

- Application startup must not call `Base.metadata.create_all()`.
- All schema changes must go through Alembic.
- Baseline migration `0001_initial_baseline` is for empty refactor databases.
- Existing original DataAgent databases should be stamped only after table
  compatibility is verified:

```bash
cd data_agent_refactored/backend
alembic stamp head
```

## P1 Follow-Up Checklist

- Decide whether strict compatibility requires reverting boolean flag columns to integers.
- Add indexes and unique constraints after comparing original DDL.
- Add API tests for every table listed above.
- Add one fixture that validates loading sample original rows into Python schemas.
