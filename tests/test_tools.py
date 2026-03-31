"""
Tests for mainlayer_openai_agents tools and HTTP client.

All HTTP calls are intercepted with unittest.mock so no real network
requests are made.  Tests exercise the full call chain from function_tool
down through MainlayerClient.
"""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests

# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------


def make_response(status_code: int, json_body: Any) -> MagicMock:
    """Build a mock requests.Response."""
    mock = MagicMock(spec=requests.Response)
    mock.status_code = status_code
    mock.ok = status_code < 400
    mock.json.return_value = json_body
    mock.text = str(json_body)
    return mock


@pytest.fixture(autouse=True)
def set_env_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure every test starts with a valid API key env var."""
    monkeypatch.setenv("MAINLAYER_API_KEY", "test-api-key-123")


@pytest.fixture(autouse=True)
def reset_default_client() -> None:
    """
    Reset the module-level default client between tests so that one test's
    client state does not leak into the next.
    """
    import mainlayer_openai_agents._client as client_mod

    original = client_mod._default_client
    client_mod._default_client = None
    yield
    client_mod._default_client = original


# ---------------------------------------------------------------------------
# MainlayerClient unit tests
# ---------------------------------------------------------------------------


class TestMainlayerClientInit:
    def test_raises_when_no_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("MAINLAYER_API_KEY", raising=False)
        from mainlayer_openai_agents._client import MainlayerClient

        with pytest.raises(ValueError, match="API key"):
            MainlayerClient()

    def test_uses_env_api_key(self) -> None:
        from mainlayer_openai_agents._client import MainlayerClient

        client = MainlayerClient()
        assert client._api_key == "test-api-key-123"

    def test_explicit_api_key_overrides_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MAINLAYER_API_KEY", "env-key")
        from mainlayer_openai_agents._client import MainlayerClient

        client = MainlayerClient(api_key="explicit-key")
        assert client._api_key == "explicit-key"

    def test_authorization_header_set(self) -> None:
        from mainlayer_openai_agents._client import MainlayerClient

        client = MainlayerClient(api_key="sk-test")
        assert client._session.headers["Authorization"] == "Bearer sk-test"

    def test_custom_base_url(self) -> None:
        from mainlayer_openai_agents._client import MainlayerClient

        client = MainlayerClient(base_url="https://staging.mainlayer.xyz/")
        assert client._base_url == "https://staging.mainlayer.xyz"


class TestMainlayerClientHTTP:
    def test_get_raises_on_4xx(self) -> None:
        from mainlayer_openai_agents._client import MainlayerAPIError, MainlayerClient

        client = MainlayerClient(api_key="key")
        with patch.object(client._session, "get", return_value=make_response(404, {"error": "not found"})):
            with pytest.raises(MainlayerAPIError) as exc_info:
                client.get("/resources/missing")
            assert exc_info.value.status_code == 404

    def test_post_raises_on_5xx(self) -> None:
        from mainlayer_openai_agents._client import MainlayerAPIError, MainlayerClient

        client = MainlayerClient(api_key="key")
        with patch.object(client._session, "post", return_value=make_response(500, {"error": "server error"})):
            with pytest.raises(MainlayerAPIError) as exc_info:
                client.post("/resources", {})
            assert exc_info.value.status_code == 500

    def test_get_returns_json_on_success(self) -> None:
        from mainlayer_openai_agents._client import MainlayerClient

        client = MainlayerClient(api_key="key")
        payload = {"total_revenue_usd": 42.0}
        with patch.object(client._session, "get", return_value=make_response(200, payload)):
            result = client.get("/analytics/revenue")
        assert result == payload

    def test_post_returns_json_on_success(self) -> None:
        from mainlayer_openai_agents._client import MainlayerClient

        client = MainlayerClient(api_key="key")
        payload = {"resource_id": "res_abc"}
        with patch.object(client._session, "post", return_value=make_response(201, payload)):
            result = client.post("/resources", {"name": "Test"})
        assert result == payload


# ---------------------------------------------------------------------------
# create_resource tool tests
# ---------------------------------------------------------------------------


class TestCreateResourceTool:
    def _patch(self, json_body: Any, status: int = 200):
        return patch(
            "mainlayer_openai_agents._client.Session.post",
            return_value=make_response(status, json_body),
        )

    def test_returns_resource_id_on_success(self) -> None:
        from mainlayer_openai_agents.tools import create_resource

        payload = {"resource_id": "res_001", "name": "Weather API", "price_usd": 0.05}
        with self._patch(payload, 201):
            result = create_resource(name="Weather API", price_usd=0.05)
        assert result["resource_id"] == "res_001"

    def test_passes_fee_model_to_api(self) -> None:
        from mainlayer_openai_agents.tools import create_resource

        payload = {"resource_id": "res_002", "fee_model": "per_call"}
        with patch("mainlayer_openai_agents._client.Session.post") as mock_post:
            mock_post.return_value = make_response(201, payload)
            create_resource(name="API", price_usd=0.01, fee_model="per_call")
            call_kwargs = mock_post.call_args
            sent_body = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
            assert sent_body["fee_model"] == "per_call"

    def test_default_fee_model_is_one_time(self) -> None:
        from mainlayer_openai_agents.tools import create_resource

        with patch("mainlayer_openai_agents._client.Session.post") as mock_post:
            mock_post.return_value = make_response(201, {"resource_id": "r"})
            create_resource(name="API", price_usd=1.0)
            sent_body = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1]["json"]
            assert sent_body["fee_model"] == "one_time"

    def test_passes_description_to_api(self) -> None:
        from mainlayer_openai_agents.tools import create_resource

        with patch("mainlayer_openai_agents._client.Session.post") as mock_post:
            mock_post.return_value = make_response(201, {"resource_id": "r"})
            create_resource(name="API", price_usd=1.0, description="Detailed description")
            sent_body = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1]["json"]
            assert sent_body["description"] == "Detailed description"

    def test_returns_error_dict_on_api_error(self) -> None:
        from mainlayer_openai_agents.tools import create_resource

        with self._patch({"error": "Unauthorized"}, 401):
            result = create_resource(name="X", price_usd=1.0)
        assert result["error"] is True
        assert result["status_code"] == 401


# ---------------------------------------------------------------------------
# pay_for_resource tool tests
# ---------------------------------------------------------------------------


class TestPayForResourceTool:
    def test_returns_payment_confirmation(self) -> None:
        from mainlayer_openai_agents.tools import pay_for_resource

        payload = {"payment_id": "pay_abc", "entitlement_id": "ent_xyz"}
        with patch("mainlayer_openai_agents._client.Session.post", return_value=make_response(200, payload)):
            result = pay_for_resource(resource_id="res_001", payer_id="user_42")
        assert result["payment_id"] == "pay_abc"
        assert result["entitlement_id"] == "ent_xyz"

    def test_sends_correct_body(self) -> None:
        from mainlayer_openai_agents.tools import pay_for_resource

        with patch("mainlayer_openai_agents._client.Session.post") as mock_post:
            mock_post.return_value = make_response(200, {"payment_id": "p"})
            pay_for_resource(resource_id="res_001", payer_id="user_42")
            sent_body = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1]["json"]
            assert sent_body["resource_id"] == "res_001"
            assert sent_body["payer_id"] == "user_42"

    def test_returns_error_on_failure(self) -> None:
        from mainlayer_openai_agents.tools import pay_for_resource

        with patch(
            "mainlayer_openai_agents._client.Session.post",
            return_value=make_response(402, {"error": "Insufficient funds"}),
        ):
            result = pay_for_resource(resource_id="res_001", payer_id="broke_user")
        assert result["error"] is True
        assert result["status_code"] == 402


# ---------------------------------------------------------------------------
# check_access tool tests
# ---------------------------------------------------------------------------


class TestCheckAccessTool:
    def test_returns_active_true_when_entitled(self) -> None:
        from mainlayer_openai_agents.tools import check_access

        payload = {"active": True, "entitlement_id": "ent_123"}
        with patch("mainlayer_openai_agents._client.Session.get", return_value=make_response(200, payload)):
            result = check_access(resource_id="res_001", payer_id="user_42")
        assert result["active"] is True

    def test_returns_active_false_when_not_entitled(self) -> None:
        from mainlayer_openai_agents.tools import check_access

        with patch(
            "mainlayer_openai_agents._client.Session.get",
            return_value=make_response(200, {"active": False}),
        ):
            result = check_access(resource_id="res_001", payer_id="stranger")
        assert result["active"] is False

    def test_sends_correct_query_params(self) -> None:
        from mainlayer_openai_agents.tools import check_access

        with patch("mainlayer_openai_agents._client.Session.get") as mock_get:
            mock_get.return_value = make_response(200, {"active": True})
            check_access(resource_id="res_999", payer_id="u_007")
            call_kwargs = mock_get.call_args
            params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
            assert params["resource_id"] == "res_999"
            assert params["payer_id"] == "u_007"

    def test_returns_error_dict_on_api_error(self) -> None:
        from mainlayer_openai_agents.tools import check_access

        with patch(
            "mainlayer_openai_agents._client.Session.get",
            return_value=make_response(404, {"error": "Resource not found"}),
        ):
            result = check_access(resource_id="missing", payer_id="u")
        assert result["error"] is True


# ---------------------------------------------------------------------------
# discover_resources tool tests
# ---------------------------------------------------------------------------


class TestDiscoverResourcesTool:
    def test_returns_list_of_resources(self) -> None:
        from mainlayer_openai_agents.tools import discover_resources

        resources = [
            {"resource_id": "r1", "name": "Weather API", "price_usd": 0.01},
            {"resource_id": "r2", "name": "Stock Quotes", "price_usd": 0.05},
        ]
        with patch("mainlayer_openai_agents._client.Session.get", return_value=make_response(200, resources)):
            result = discover_resources(query="weather", limit=5)
        assert len(result) == 2
        assert result[0]["resource_id"] == "r1"

    def test_handles_wrapped_resources_response(self) -> None:
        from mainlayer_openai_agents.tools import discover_resources

        response_body = {"resources": [{"resource_id": "r3", "name": "Translate API"}]}
        with patch(
            "mainlayer_openai_agents._client.Session.get", return_value=make_response(200, response_body)
        ):
            result = discover_resources()
        assert result[0]["resource_id"] == "r3"

    def test_passes_query_param(self) -> None:
        from mainlayer_openai_agents.tools import discover_resources

        with patch("mainlayer_openai_agents._client.Session.get") as mock_get:
            mock_get.return_value = make_response(200, [])
            discover_resources(query="nlp", limit=3)
            params = mock_get.call_args.kwargs.get("params") or mock_get.call_args[1]["params"]
            assert params["q"] == "nlp"
            assert params["limit"] == 3

    def test_empty_query_not_sent(self) -> None:
        from mainlayer_openai_agents.tools import discover_resources

        with patch("mainlayer_openai_agents._client.Session.get") as mock_get:
            mock_get.return_value = make_response(200, [])
            discover_resources()
            params = mock_get.call_args.kwargs.get("params") or mock_get.call_args[1]["params"]
            assert "q" not in params

    def test_returns_error_list_on_failure(self) -> None:
        from mainlayer_openai_agents.tools import discover_resources

        with patch(
            "mainlayer_openai_agents._client.Session.get",
            return_value=make_response(503, {"error": "Service unavailable"}),
        ):
            result = discover_resources()
        assert isinstance(result, list)
        assert result[0]["error"] is True


# ---------------------------------------------------------------------------
# get_revenue tool tests
# ---------------------------------------------------------------------------


class TestGetRevenueTool:
    def test_returns_revenue_summary(self) -> None:
        from mainlayer_openai_agents.tools import get_revenue

        payload = {
            "total_revenue_usd": 1234.56,
            "transaction_count": 500,
            "period": "30d",
            "breakdown": [],
        }
        with patch("mainlayer_openai_agents._client.Session.get", return_value=make_response(200, payload)):
            result = get_revenue(period="30d")
        assert result["total_revenue_usd"] == 1234.56
        assert result["transaction_count"] == 500

    def test_default_period_is_30d(self) -> None:
        from mainlayer_openai_agents.tools import get_revenue

        with patch("mainlayer_openai_agents._client.Session.get") as mock_get:
            mock_get.return_value = make_response(200, {"total_revenue_usd": 0})
            get_revenue()
            params = mock_get.call_args.kwargs.get("params") or mock_get.call_args[1]["params"]
            assert params["period"] == "30d"

    def test_custom_period_is_passed(self) -> None:
        from mainlayer_openai_agents.tools import get_revenue

        with patch("mainlayer_openai_agents._client.Session.get") as mock_get:
            mock_get.return_value = make_response(200, {"total_revenue_usd": 0})
            get_revenue(period="7d")
            params = mock_get.call_args.kwargs.get("params") or mock_get.call_args[1]["params"]
            assert params["period"] == "7d"

    def test_returns_error_on_unauthorized(self) -> None:
        from mainlayer_openai_agents.tools import get_revenue

        with patch(
            "mainlayer_openai_agents._client.Session.get",
            return_value=make_response(401, {"error": "Unauthorized"}),
        ):
            result = get_revenue()
        assert result["error"] is True
        assert result["status_code"] == 401


# ---------------------------------------------------------------------------
# MAINLAYER_TOOLS registry
# ---------------------------------------------------------------------------


class TestToolRegistry:
    def test_all_five_tools_present(self) -> None:
        from mainlayer_openai_agents.tools import (
            MAINLAYER_TOOLS,
            check_access,
            create_resource,
            discover_resources,
            get_revenue,
            pay_for_resource,
        )

        assert len(MAINLAYER_TOOLS) == 5
        assert create_resource in MAINLAYER_TOOLS
        assert pay_for_resource in MAINLAYER_TOOLS
        assert check_access in MAINLAYER_TOOLS
        assert discover_resources in MAINLAYER_TOOLS
        assert get_revenue in MAINLAYER_TOOLS

    def test_tools_are_callable(self) -> None:
        from mainlayer_openai_agents.tools import MAINLAYER_TOOLS

        for tool in MAINLAYER_TOOLS:
            assert callable(tool)


# ---------------------------------------------------------------------------
# get_default_client / set_default_client
# ---------------------------------------------------------------------------


class TestDefaultClient:
    def test_get_default_client_creates_from_env(self) -> None:
        from mainlayer_openai_agents._client import get_default_client

        client = get_default_client()
        assert client._api_key == "test-api-key-123"

    def test_set_default_client_replaces_singleton(self) -> None:
        from mainlayer_openai_agents._client import MainlayerClient, get_default_client, set_default_client

        custom = MainlayerClient(api_key="custom-key")
        set_default_client(custom)
        assert get_default_client() is custom
