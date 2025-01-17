import time

import pytest
from hypothesis import given, settings
from hypothesis.strategies import integers
from starlette.testclient import TestClient

from rsserpent.plugins.builtin import example_cache
from rsserpent.utils.cache import get_cache
from rsserpent.utils.ratelimit import RateLimitError
from tests.conftest import Times


def test_example(client: TestClient) -> None:
    """Test the `/_/example` route."""
    response = client.get("/_/example")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/xml"
    assert response.text.count("<item>") == 1


def test_example_cached(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the `/_example/cache` route."""
    monkeypatch.setattr(time, "time", lambda: 0)

    response1 = client.get("/_/example/cache")
    response2 = client.get("/_/example/cache")
    assert response1.text == response2.text
    assert "<title>Example 1</title>" in response1.text

    cache = get_cache(example_cache.provider)
    if cache is not None:
        cache.clear()
    response3 = client.get("/_/example/cache")
    assert response1.text != response3.text
    assert "<title>Example 2</title>" in response3.text


def test_example_ratelimit(client: TestClient) -> None:
    """Test the `/_example/rl` route."""
    assert client.get("/_/example/rl").status_code == 200
    with pytest.raises(RateLimitError):
        client.get("/_/example/rl")


@settings(max_examples=Times.SOME)
@given(n=integers(min_value=1, max_value=10))
def test_example_with_args(client: TestClient, n: int) -> None:
    """Test the `/_/example/{n:int}` route."""
    response = client.get(f"/_/example/{n}")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/xml"
    assert response.text.count("<item>") == n
