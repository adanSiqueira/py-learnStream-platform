import sys
import os
from pathlib import Path
import pytest
from unittest.mock import AsyncMock
from app.models.sql.user import UserRole
from fastapi.testclient import TestClient
from main import app
from app.auth.deps import get_current_user

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Ensure root directory (where main.py lives) is in sys.path
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

# Helper: fake result object mimicking SQLAlchemy Result with scalars().first()
class FakeResult:
    def __init__(self, value):
        self._value = value

    def scalars(self):
        class Scalar:
            def __init__(self, value): self.value = value
            def first(self): return self.value
        return Scalar(self._value)

@pytest.fixture(autouse=True)
def mock_auth(monkeypatch):
    """
    Automatically replaces `get_current_user` dependency in all modules
    with a fake authenticated user for unit testing.
    """
    fake_user = {
        "id": 1,
        "email": "admin@example.com",
        "role": UserRole.admin  # or a string like "admin"
    }

    monkeypatch.setattr(
        "app.auth.deps.get_current_user",
        AsyncMock(return_value=fake_user)
    )
    yield

@pytest.fixture(scope="session", autouse=True)
def override_auth_dependencies():
    """Globally disable authentication for tests that don't patch it."""
    def fake_get_current_user():
        return {"id": 1, "email": "test@example.com", "role": "admin"}

    app.dependency_overrides = {}
    app.dependency_overrides[get_current_user] = fake_get_current_user
    yield
    app.dependency_overrides = {}

@pytest.fixture(scope="session", autouse=True)
def override_get_current_user():
    """
    Overrides the authentication dependency globally for all tests.
    Simulates an authenticated user (student or admin) to bypass 401s.
    """
    async def fake_user():
        return AsyncMock(id=1, email="test@example.com", role="admin")

    app.dependency_overrides[get_current_user] = fake_user
    yield
    app.dependency_overrides.pop(get_current_user, None)

@pytest.fixture(scope="session")
def client():
    """Return FastAPI test client."""
    return TestClient(app)