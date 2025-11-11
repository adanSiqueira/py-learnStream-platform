from app.models.sql.refresh_token import RefreshToken
from datetime import datetime

def test_refresh_token_creation():
    """Ensure RefreshToken initializes correctly with defaults."""
    token = RefreshToken(
        user_id=7,
        token_hash="hash_value",
        expires_at=datetime(2025, 12, 1)
    )

    assert token.user_id == 7
    assert token.token_hash == "hash_value"
    assert not token.revoked
    assert isinstance(token.issued_at, datetime)
    assert isinstance(token.expires_at, datetime)
    assert token.__tablename__ == "refresh_tokens"
