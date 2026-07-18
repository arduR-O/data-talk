import pytest
from nlp import validate_sql_safety, ensure_demo_db_seeded, create_database_graph

def test_validate_sql_safety():
    # Safe queries
    assert validate_sql_safety("SELECT * FROM employees") is True
    assert validate_sql_safety("SELECT id, name FROM departments WHERE budget > 1000") is True
    assert validate_sql_safety("select count(1) from department") is True
    
    # Destructive/unsafe queries
    assert validate_sql_safety("DROP TABLE employees") is False
    assert validate_sql_safety("DELETE FROM employees WHERE id = 1") is False
    assert validate_sql_safety("UPDATE employees SET salary = 100000") is False
    assert validate_sql_safety("INSERT INTO employees (name) VALUES ('Alice')") is False
    assert validate_sql_safety("ALTER TABLE employees ADD COLUMN age INTEGER") is False
    assert validate_sql_safety("TRUNCATE TABLE logs") is False

def test_ensure_demo_db_seeded_ignored():
    # Should exit early without raising error for non-demo URL
    assert ensure_demo_db_seeded("sqlite:///test_other.db") is None

def test_create_database_graph_raises():
    with pytest.raises(ValueError):
        create_database_graph("")
