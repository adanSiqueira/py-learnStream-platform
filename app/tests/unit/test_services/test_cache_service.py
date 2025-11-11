from unittest.mock import AsyncMock, Mock, patch
from app.services import cache_service as cache_service_module
import asyncio

def test_cache_service_wrappers_set_get_monkeypatched(monkeypatch):
    """
    Test cache_service wrappers by monkeypatching the global redis client
    to an object with async set/get methods.
    """
    fake_redis = Mock()
    # create async functions
    async def aget(k):
        return "val"
    async def aset(k, v, ex=None):
        return True

    fake_redis.get = AsyncMock(side_effect=aget)
    fake_redis.set = AsyncMock(side_effect=aset)

    # monkeypatch the global redis variable in module
    monkeypatch.setattr(cache_service_module, "redis", fake_redis)

    # run wrappers
    async def run():
        await cache_service_module.set_cache("k", "v", ttl=10)
        val = await cache_service_module.get_cache("k")
        assert val == "val"

    asyncio.get_event_loop().run_until_complete(run())