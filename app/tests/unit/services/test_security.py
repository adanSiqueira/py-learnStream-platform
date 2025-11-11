# tests/unit/test_security.py
from app.services import security as security_service

def test_hash_password_and_verify():
    pwd = "S3cr3t!"
    hashed = security_service.hash_password(pwd)
    assert isinstance(hashed, str)
    assert security_service.verify_password(pwd, hashed) is True
    assert security_service.verify_password("nope", hashed) is False

def test_create_access_token_and_decode_contains_claims():
    token = security_service.create_access_token(subject=123, extra={"role": "student"})
    payload = security_service.decode_token(token)
    assert payload["sub"] == "123"
    assert payload["role"] == "student"
    assert "exp" in payload

def test_create_refresh_token_has_typ_and_expires():
    token = security_service.create_refresh_token(subject=42)
    payload = security_service.decode_token(token)
    assert payload["sub"] == "42"
    assert payload.get("typ") == "refresh"
    assert "exp" in payload
