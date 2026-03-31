"""
Pre-configured OpenAI Agents for the Mainlayer payments platform.

Two factory functions are provided:

* ``create_vendor_agent`` – an agent focused on publishing and monetising
  resources (creating resources, checking revenue analytics).

* ``create_buyer_agent`` – an agent focused on discovering and purchasing
  resources (searching the marketplace, paying, verifying access).

Both agents use the same underlying Mainlayer function tools but are given
different system instructions and default tool subsets that reflect their
intended role.
"""

from __future__ import annotations

from agents import Agent

from ._client import MainlayerClient, set_default_client
from .tools import (
    MAINLAYER_TOOLS,
    check_access,
    create_resource,
    discover_resources,
    get_revenue,
    pay_for_resource,
)

# ---------------------------------------------------------------------------
# Vendor agent
# ---------------------------------------------------------------------------

_VENDOR_INSTRUCTIONS = """\
You are a Mainlayer vendor agent. Your role is to help API and service
owners monetise their work through the Mainlayer payments platform.

Capabilities you have:
- Create and register new paid resources on the marketplace.
- Check revenue analytics to understand earnings across different time periods.
- Verify whether specific buyers hold active entitlements to your resources.

Guidelines:
- Before creating a resource, confirm the name, price, billing model, and
  description with the user.
- Prices must be positive numbers expressed in US dollars.
- Supported fee models are: one_time, per_call, subscription.
- After creating a resource, always return the resource_id to the user so
  they can reference it later.
- When reporting revenue, present figures clearly and highlight notable trends.
- Never share API keys or sensitive credentials in your responses.
"""

_VENDOR_TOOLS = [create_resource, check_access, get_revenue]


def create_vendor_agent(api_key: str, model: str = "gpt-4o") -> Agent:
    """
    Create a pre-configured OpenAI Agent that can monetise APIs via Mainlayer.

    The agent is given tools for publishing resources, reviewing analytics,
    and verifying buyer entitlements.  All Mainlayer API calls will be
    authenticated with the supplied ``api_key``.

    Parameters
    ----------
    api_key:
        Your Mainlayer API key.
    model:
        The OpenAI model to use (default ``"gpt-4o"``).

    Returns
    -------
    Agent
        A fully configured ``agents.Agent`` instance ready to run.

    Example
    -------
    ::

        from mainlayer_openai_agents import create_vendor_agent
        from agents import Runner

        agent = create_vendor_agent(api_key="ml_...")
        result = Runner.run_sync(agent, "Create a weather API resource for $0.01 per call")
        print(result.final_output)
    """
    set_default_client(MainlayerClient(api_key=api_key))

    return Agent(
        name="Mainlayer Vendor Agent",
        model=model,
        instructions=_VENDOR_INSTRUCTIONS,
        tools=_VENDOR_TOOLS,
    )


# ---------------------------------------------------------------------------
# Buyer agent
# ---------------------------------------------------------------------------

_BUYER_INSTRUCTIONS = """\
You are a Mainlayer buyer agent. Your role is to help users and automated
systems discover, evaluate, and purchase access to resources on the
Mainlayer marketplace.

Capabilities you have:
- Search and browse available resources in the marketplace.
- Purchase access to resources on behalf of a payer.
- Verify whether a payer already holds an active entitlement before
  attempting a duplicate purchase.

Guidelines:
- Always call discover_resources before pay_for_resource to confirm the
  resource exists and to obtain the correct resource_id.
- Always call check_access before pay_for_resource to avoid charging the
  payer twice for an existing entitlement.
- When reporting discovery results, summarise name, price, and fee model
  clearly so the user can make an informed purchasing decision.
- After a successful payment, confirm the entitlement_id and advise the
  user to store it for future reference.
- Never share API keys or sensitive credentials in your responses.
"""

_BUYER_TOOLS = [discover_resources, check_access, pay_for_resource]


def create_buyer_agent(api_key: str, model: str = "gpt-4o") -> Agent:
    """
    Create an OpenAI Agent that can discover and pay for Mainlayer resources.

    The agent is given tools for searching the marketplace, checking existing
    entitlements, and processing payments.  All Mainlayer API calls will be
    authenticated with the supplied ``api_key``.

    Parameters
    ----------
    api_key:
        Your Mainlayer API key.
    model:
        The OpenAI model to use (default ``"gpt-4o"``).

    Returns
    -------
    Agent
        A fully configured ``agents.Agent`` instance ready to run.

    Example
    -------
    ::

        from mainlayer_openai_agents import create_buyer_agent
        from agents import Runner

        agent = create_buyer_agent(api_key="ml_...")
        result = Runner.run_sync(
            agent,
            "Find a weather API and buy access for user user_42"
        )
        print(result.final_output)
    """
    set_default_client(MainlayerClient(api_key=api_key))

    return Agent(
        name="Mainlayer Buyer Agent",
        model=model,
        instructions=_BUYER_INSTRUCTIONS,
        tools=_BUYER_TOOLS,
    )


# ---------------------------------------------------------------------------
# Full-capability agent (all tools)
# ---------------------------------------------------------------------------

_FULL_INSTRUCTIONS = """\
You are a Mainlayer payments agent with full access to the Mainlayer API.
You can create and monetise resources, discover and purchase existing ones,
verify access entitlements, and review revenue analytics.

Use your judgement to select the right tool for each user request.
Always be clear about pricing, resource identifiers, and entitlement status.
Never share API keys or sensitive credentials in your responses.
"""


def create_full_agent(api_key: str, model: str = "gpt-4o") -> Agent:
    """
    Create an OpenAI Agent with access to all Mainlayer tools.

    Suitable for general-purpose usage where the same agent needs to act
    as both vendor and buyer, or when the role is determined at runtime.

    Parameters
    ----------
    api_key:
        Your Mainlayer API key.
    model:
        The OpenAI model to use (default ``"gpt-4o"``).

    Returns
    -------
    Agent
        A fully configured ``agents.Agent`` instance with all five Mainlayer
        tools attached.
    """
    set_default_client(MainlayerClient(api_key=api_key))

    return Agent(
        name="Mainlayer Agent",
        model=model,
        instructions=_FULL_INSTRUCTIONS,
        tools=MAINLAYER_TOOLS,
    )
