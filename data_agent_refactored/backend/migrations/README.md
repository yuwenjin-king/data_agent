# Alembic Migrations

This directory owns database schema changes for the FastAPI refactor.

For a new empty database:

```bash
cd backend
alembic upgrade head
```

For a database that already uses the original DataAgent schema, first validate
`docs/schema-compatibility.md`, then mark the baseline without recreating tables:

```bash
cd backend
alembic stamp head
```
