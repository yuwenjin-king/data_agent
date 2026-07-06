def test_app_imports_without_database_initialization():
    from app.main import app

    assert app.title == "Data Agent"
