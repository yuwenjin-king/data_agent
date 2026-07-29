"""Tests for read-only SQL execution safety checks."""

import pytest

from app.workflow.sql.executor import SqlNotAllowedError, _validate_read_only


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 1",
        "select * from users where name = 'drop table users'",
        "WITH recent AS (SELECT * FROM orders) SELECT * FROM recent",
        'SELECT "update" AS label FROM metrics',
        "SELECT /* create table x */ count(*) FROM users -- delete later",
    ],
)
def test_validate_read_only_allows_single_selects(sql):
    _validate_read_only(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "",
        "UPDATE users SET name = 'x'",
        "DELETE FROM users",
        "DROP TABLE users",
        "CALL refresh_stats()",
        "SELECT 1; DROP TABLE users",
        "SELECT 1; SELECT 2",
        "INSERT INTO audit SELECT * FROM users",
    ],
)
def test_validate_read_only_rejects_unsafe_statements(sql):
    with pytest.raises(SqlNotAllowedError):
        _validate_read_only(sql)
