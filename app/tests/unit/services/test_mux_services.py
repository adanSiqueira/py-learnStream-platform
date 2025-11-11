import pytest
from app.services import mux_service as mux_service_module

@pytest.mark.asyncio
async def test_mux_service_create_signed_manifest_url_cache_miss_and_set(monkeypatch):
    """
    Test create_signed_manifest_url when cache miss:
      - get_cache returns None
      - set_cache should be called with the computed signed URL
      - result should contain the playback_id and token/expires query params
    """
    playback_id = "m00abc"
    user_id = "42"
    cache_key = f"signed:{user_id}:{playback_id}"

    # monkeypatch cache functions
    async def fake_get_cache(key):
        assert key == cache_key
        return None

    async def fake_set_cache(key, value, ttl=300):
        assert key == cache_key
        assert "stream.mux.com" in value
        return True

    monkeypatch.setattr(mux_service_module, "get_cache", fake_get_cache)
    monkeypatch.setattr(mux_service_module, "set_cache", fake_set_cache)

    signed = await mux_service_module.create_signed_manifest_url(playback_id, user_id)
    assert isinstance(signed, str)
    assert playback_id in signed
    assert "token=" in signed and "expires=" in signed


@pytest.mark.asyncio
async def test_mux_service_create_signed_manifest_url_cache_hit(monkeypatch):
    """
    When cache returns a value, the function should return it and not call set_cache.
    """
    playback_id = "m01hit"
    user_id = "99"
    cache_key = f"signed:{user_id}:{playback_id}"
    cached_value = f"https://stream.mux.com/{playback_id}.m3u8?token=cached&expires=12345"

    async def fake_get_cache(key):
        assert key == cache_key
        return cached_value

    # set_cache should not be called; we'll monkeypatch it to raise if called
    async def fake_set_cache(key, value, ttl=300):
        raise AssertionError("set_cache should not be called on cache hit")

    monkeypatch.setattr(mux_service_module, "get_cache", fake_get_cache)
    monkeypatch.setattr(mux_service_module, "set_cache", fake_set_cache)
    result = await mux_service_module.create_signed_manifest_url(playback_id, user_id)
    assert result == cached_value