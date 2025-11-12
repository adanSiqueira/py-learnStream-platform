import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import create_app

app = create_app()
client = TestClient(app)

@pytest.mark.asyncio
@patch("app.mux_webhooks.router.verify_mux_signature", return_value=True)
@patch("app.mux_webhooks.router.handle_mux_webhook", return_value={"ok": True})
async def test_mux_webhook_valid_signature(mock_handle, mock_verify):
    """ Should process webhook successfully when signature valid."""
    payload = {"type": "video.asset.ready"}
    resp = client.post("/webhooks/mux", json=payload, headers={"x-mux-signature": "validsig"})
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    mock_handle.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.mux_webhooks.router.verify_mux_signature", return_value=False)
async def test_mux_webhook_invalid_signature(mock_verify):
    """ Should reject request when signature invalid."""
    resp = client.post("/webhooks/mux", json={"type": "video.asset.ready"}, headers={"x-mux-signature": "badsig"})
    assert resp.status_code == 401
    assert "Invalid Mux webhook signature" in resp.text


@pytest.mark.asyncio
@patch("app.mux_webhooks.router.verify_mux_signature", return_value=True)
@patch("app.mux_webhooks.router.handle_mux_webhook", side_effect=Exception("boom"))
async def test_mux_webhook_processing_error(mock_handle, mock_verify):
    """ Should return 500 when processing fails."""
    resp = client.post("/webhooks/mux", json={"type": "video.asset.errored"}, headers={"x-mux-signature": "sig"})
    assert resp.status_code == 500
    assert "Error processing webhook" in resp.text
