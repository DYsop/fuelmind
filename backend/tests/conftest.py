from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


@pytest.fixture()
def configured_app(tmp_path, monkeypatch):
    db_path = tmp_path / "fuelmind-test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("ENABLE_SCHEDULER", "false")
    monkeypatch.setenv("ALLOW_PUBLIC_API", "true")
    monkeypatch.setenv("TANKERKOENIG_API_KEY", "")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6390/0")

    for module_name in [
        "app.core.config",
        "app.db.models",
        "app.db.session",
        "app.main",
    ]:
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])

    import app.core.config as config_module
    import app.main as main_module

    config_module.get_settings.cache_clear()
    app = main_module.create_app()
    with TestClient(app) as client:
        yield app, client


@pytest.fixture()
async def db_session(configured_app):
    import app.db.session as session_module

    async with session_module.SessionLocal() as session:
        yield session
