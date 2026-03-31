"""
Internal HTTP client for the Mainlayer API.

All requests are authenticated with a Bearer token and directed at
https://api.mainlayer.xyz. This module is intentionally private; callers
should use the public function tools in tools.py instead.
"""

from __future__ import annotations

import os
from typing import Any

import requests
from requests import Response, Session

BASE_URL = "https://api.mainlayer.xyz"
DEFAULT_TIMEOUT = 30  # seconds


class MainlayerAPIError(Exception):
    """Raised when the Mainlayer API returns a non-2xx response."""

    def __init__(self, status_code: int, message: str, response_body: Any = None) -> None:
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(f"Mainlayer API error {status_code}: {message}")


class MainlayerClient:
    """
    Thin HTTP client wrapping the Mainlayer REST API.

    Parameters
    ----------
    api_key:
        Bearer token for the Mainlayer API. If omitted the value of the
        ``MAINLAYER_API_KEY`` environment variable is used.
    base_url:
        Override the default API base URL (useful for testing).
    timeout:
        Per-request timeout in seconds.
    session:
        Optional pre-configured ``requests.Session`` (useful for testing).
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
        session: Session | None = None,
    ) -> None:
        resolved_key = api_key or os.environ.get("MAINLAYER_API_KEY", "")
        if not resolved_key:
            raise ValueError(
                "A Mainlayer API key is required. Pass api_key= or set the "
                "MAINLAYER_API_KEY environment variable."
            )

        self._api_key = resolved_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = session or Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "mainlayer-openai-agents/0.1.0",
            }
        )

    # ------------------------------------------------------------------
    # Low-level request helpers
    # ------------------------------------------------------------------

    def _url(self, path: str) -> str:
        return f"{self._base_url}/{path.lstrip('/')}"

    def _raise_for_status(self, response: Response) -> None:
        if response.ok:
            return
        try:
            body = response.json()
            message = body.get("error") or body.get("message") or response.text
        except Exception:
            message = response.text or "Unknown error"
        raise MainlayerAPIError(response.status_code, message, response_body=body if response.text else None)

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Send a GET request and return the parsed JSON body."""
        response = self._session.get(
            self._url(path),
            params=params,
            timeout=self._timeout,
        )
        self._raise_for_status(response)
        return response.json()

    def post(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        """Send a POST request and return the parsed JSON body."""
        response = self._session.post(
            self._url(path),
            json=payload or {},
            timeout=self._timeout,
        )
        self._raise_for_status(response)
        return response.json()

    # ------------------------------------------------------------------
    # Mainlayer-specific API methods
    # ------------------------------------------------------------------

    def create_resource(
        self,
        name: str,
        price_usd: float,
        fee_model: str = "one_time",
        description: str = "",
    ) -> dict[str, Any]:
        """
        POST /resources

        Register a new monetized resource on Mainlayer.
        """
        return self.post(
            "/resources",
            {
                "name": name,
                "price_usd": price_usd,
                "fee_model": fee_model,
                "description": description,
            },
        )

    def pay_for_resource(self, resource_id: str, payer_id: str) -> dict[str, Any]:
        """
        POST /pay

        Initiate a payment for a resource on behalf of a payer.
        """
        return self.post(
            "/pay",
            {
                "resource_id": resource_id,
                "payer_id": payer_id,
            },
        )

    def check_access(self, resource_id: str, payer_id: str) -> dict[str, Any]:
        """
        GET /entitlements/check

        Verify whether a payer currently holds a valid entitlement.
        """
        return self.get(
            "/entitlements/check",
            params={"resource_id": resource_id, "payer_id": payer_id},
        )

    def discover_resources(self, query: str = "", limit: int = 10) -> list[dict[str, Any]]:
        """
        GET /discover

        Search the Mainlayer marketplace for available resources.
        """
        params: dict[str, Any] = {"limit": limit}
        if query:
            params["q"] = query
        result = self.get("/discover", params=params)
        # The API may return {"resources": [...]} or a bare list.
        if isinstance(result, list):
            return result
        return result.get("resources", result.get("data", []))

    def get_revenue(self, period: str = "30d") -> dict[str, Any]:
        """
        GET /analytics/revenue

        Retrieve aggregated revenue analytics for the authenticated vendor.
        """
        return self.get("/analytics/revenue", params={"period": period})


# ---------------------------------------------------------------------------
# Module-level singleton helpers
# ---------------------------------------------------------------------------

_default_client: MainlayerClient | None = None


def get_default_client() -> MainlayerClient:
    """
    Return the process-level default client, constructing it from the
    ``MAINLAYER_API_KEY`` environment variable the first time it is called.
    """
    global _default_client
    if _default_client is None:
        _default_client = MainlayerClient()
    return _default_client


def set_default_client(client: MainlayerClient) -> None:
    """
    Replace the process-level default client.

    Useful in tests or when the API key is obtained at runtime rather than
    from the environment.
    """
    global _default_client
    _default_client = client
