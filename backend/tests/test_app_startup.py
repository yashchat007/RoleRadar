def test_app_import_registers_api_routes():
    from app.main import app

    paths = app.openapi()["paths"]
    assert "/api/v1/settings" in paths
    assert "get" in paths["/api/v1/settings"]
    assert "patch" in paths["/api/v1/settings"]
