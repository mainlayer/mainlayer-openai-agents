"""
OpenAI Agents SDK function tools for the Mainlayer payments API.

Each tool is decorated with ``@function_tool`` so that it can be passed
directly to an ``Agent`` via its ``tools=`` parameter.  The tools call
the Mainlayer REST API through the internal ``MainlayerClient``.

Configuring credentials
-----------------------
Set the ``MAINLAYER_API_KEY`` environment variable **or** call
``set_default_client(MainlayerClient(api_key="..."))`` before the agent
runs.  The latter pattern is preferred when managing multiple API keys
at runtime.
"""

from __future__ import annotations

from typing import Any

from agents import function_tool

from ._client import MainlayerAPIError, get_default_client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _handle_api_error(error: MainlayerAPIError) -> dict[str, Any]:
    """Convert an API error into a structured error dict for the agent."""
    return {
        "error": True,
        "status_code": error.status_code,
        "message": str(error),
        "details": error.response_body,
    }


# ---------------------------------------------------------------------------
# Public function tools
# ---------------------------------------------------------------------------


@function_tool
def create_resource(
    name: str,
    price_usd: float,
    fee_model: str = "one_time",
    description: str = "",
) -> dict[str, Any]:
    """
    Create a Mainlayer resource to monetize an API or service.

    Call this tool when you want to publish a new paid resource on the
    Mainlayer marketplace so that other agents or users can discover and
    purchase access to it.

    Parameters
    ----------
    name:
        Human-readable name of the resource (e.g. "Weather Forecast API").
    price_usd:
        Price in US dollars charged per access grant (e.g. 0.05 for 5 cents).
    fee_model:
        Billing model for the resource.  Accepted values:
        - ``"one_time"``   – pay once, access forever (default).
        - ``"per_call"``   – charged each time the resource is accessed.
        - ``"subscription"`` – recurring monthly charge.
    description:
        Optional plain-text description shown to buyers in the marketplace.

    Returns
    -------
    dict
        The created resource object including its ``resource_id``.
    """
    try:
        return get_default_client().create_resource(
            name=name,
            price_usd=price_usd,
            fee_model=fee_model,
            description=description,
        )
    except MainlayerAPIError as exc:
        return _handle_api_error(exc)


@function_tool
def pay_for_resource(resource_id: str, payer_id: str) -> dict[str, Any]:
    """
    Pay for access to a Mainlayer resource.

    Use this tool to purchase access to a resource on behalf of a payer.
    After a successful payment the payer will hold an active entitlement
    that can be verified with ``check_access``.

    Parameters
    ----------
    resource_id:
        The unique identifier of the resource to purchase
        (returned by ``create_resource`` or ``discover_resources``).
    payer_id:
        Unique identifier for the entity making the payment
        (e.g. an end-user ID, an agent ID, or a session token).

    Returns
    -------
    dict
        Payment confirmation object including ``payment_id`` and
        ``entitlement_id``.
    """
    try:
        return get_default_client().pay_for_resource(
            resource_id=resource_id,
            payer_id=payer_id,
        )
    except MainlayerAPIError as exc:
        return _handle_api_error(exc)


@function_tool
def check_access(resource_id: str, payer_id: str) -> dict[str, Any]:
    """
    Check if a user has active access to a resource.

    Use this tool to gate access to a resource.  It returns whether the
    payer currently holds a valid entitlement, allowing you to decide
    whether to serve or block the request.

    Parameters
    ----------
    resource_id:
        The unique identifier of the resource to check.
    payer_id:
        The identifier of the entity whose entitlement you want to verify.

    Returns
    -------
    dict
        Entitlement status object with at minimum an ``"active"`` boolean
        field.  May include expiry timestamps and entitlement metadata.
    """
    try:
        return get_default_client().check_access(
            resource_id=resource_id,
            payer_id=payer_id,
        )
    except MainlayerAPIError as exc:
        return _handle_api_error(exc)


@function_tool
def discover_resources(query: str = "", limit: int = 10) -> list[dict[str, Any]]:
    """
    Discover available Mainlayer resources.

    Search the Mainlayer marketplace to find resources that match a query.
    Use this tool before purchasing to identify the ``resource_id`` you need.

    Parameters
    ----------
    query:
        Optional free-text search query (e.g. "weather data", "image resize").
        Pass an empty string to browse the most recent resources.
    limit:
        Maximum number of results to return (1–100, default 10).

    Returns
    -------
    list[dict]
        A list of resource objects.  Each item contains at minimum
        ``resource_id``, ``name``, ``price_usd``, and ``fee_model``.
    """
    try:
        return get_default_client().discover_resources(query=query, limit=limit)
    except MainlayerAPIError as exc:
        return [_handle_api_error(exc)]


@function_tool
def get_revenue(period: str = "30d") -> dict[str, Any]:
    """
    Get revenue analytics for your resources.

    Retrieve aggregated earnings for the authenticated vendor account.
    Useful for monitoring monetisation performance and understanding which
    resources generate the most income.

    Parameters
    ----------
    period:
        Time window for the report.  Common values:
        - ``"7d"``  – last 7 days.
        - ``"30d"`` – last 30 days (default).
        - ``"90d"`` – last 90 days.
        - ``"1y"``  – last 12 months.

    Returns
    -------
    dict
        Revenue summary including ``total_revenue_usd``, ``transaction_count``,
        and a ``breakdown`` list with per-resource figures.
    """
    try:
        return get_default_client().get_revenue(period=period)
    except MainlayerAPIError as exc:
        return _handle_api_error(exc)


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

MAINLAYER_TOOLS = [
    create_resource,
    pay_for_resource,
    check_access,
    discover_resources,
    get_revenue,
]
"""
All Mainlayer function tools as a list ready to pass to ``Agent(tools=...)``.

Example::

    from mainlayer_openai_agents import MAINLAYER_TOOLS
    from agents import Agent

    agent = Agent(
        name="my-agent",
        model="gpt-4o",
        tools=MAINLAYER_TOOLS,
    )
"""
