from rest_framework.test import APIClient
import pytest
import fakeredis


@pytest.fixture
def fake_server_rate_limit():
    return fakeredis.FakeServer()

@pytest.fixture
def fake_redis_rate_limit(fake_server_rate_limit):
    return fakeredis.FakeStrictRedis(server=fake_server_rate_limit, decode_responses=True)


@pytest.fixture
def fake_server_app_cache():
    return fakeredis.FakeServer()

@pytest.fixture
def fake_redis_app_cache(fake_server_app_cache):
    return fakeredis.FakeStrictRedis(server=fake_server_app_cache, decode_responses=True)


@pytest.fixture
def fake_server_analytics_cache():
    return fakeredis.FakeServer()

@pytest.fixture
def fake_redis_analytics_cache(fake_server_analytics_cache):
    return fakeredis.FakeStrictRedis(server=fake_server_analytics_cache, decode_responses=True)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def mock_rate_limit_redis(mocker, fake_redis_rate_limit):
    """
    Replaces the application redis client with fakeredis
    """
    mocker.patch("core.clients.redis_client.get_rate_limit_redis_client", return_value=fake_redis_rate_limit)
    mocker.patch("core.rate_limiting.limiter.get_rate_limit_redis_client", return_value=fake_redis_rate_limit)

    return fake_redis_rate_limit


@pytest.fixture
def mock_app_cache_for_jwt_tokens(mocker, fake_redis_app_cache):
    """
    Replaces the application redis client with fakeredis
    """

    mocker.patch("apps.authentication.services.access_token.service.get_app_redis_client", return_value=fake_redis_app_cache)
    mocker.patch("apps.authentication.services.refresh_token.service.get_app_redis_client", return_value=fake_redis_app_cache)
    return fake_redis_app_cache


@pytest.fixture
def fake_ip_address():
    return "206.0.113.1"