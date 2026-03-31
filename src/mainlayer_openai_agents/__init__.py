"""
mainlayer-openai-agents
=======================

OpenAI Agents SDK integration for the Mainlayer payments platform.

Mainlayer is payment infrastructure for AI agents — think Stripe, but built
for the agentic web.  This package provides:

* Five ``@function_tool``-decorated tools that wrap the Mainlayer REST API
  and can be attached to any ``agents.Agent``.
* Two ready-to-use agent factories (vendor and buyer) with sensible default
  instructions and tool subsets.
* A thin HTTP client (``MainlayerClient``) for direct API access when you
  need finer control.

Quick start
-----------
::

    import os
    from agents import Runner
    from mainlayer_openai_agents import create_vendor_agent

    agent = create_vendor_agent(api_key=os.environ["MAINLAYER_API_KEY"])
    result = Runner.run_sync(agent, "Create a paid image-resize API for $0.02 per call")
    print(result.final_output)

Using individual tools
----------------------
::

    from agents import Agent
    from mainlayer_openai_agents import MAINLAYER_TOOLS

    agent = Agent(name="my-agent", model="gpt-4o", tools=MAINLAYER_TOOLS)

Environment variables
---------------------
MAINLAYER_API_KEY
    Your Mainlayer API key.  Required when using the module-level default
    client (i.e. when *not* passing ``api_key=`` to a factory function).
"""

from ._client import MainlayerAPIError, MainlayerClient, get_default_client, set_default_client
from .agent import create_buyer_agent, create_full_agent, create_vendor_agent
from .tools import (
    MAINLAYER_TOOLS,
    check_access,
    create_resource,
    discover_resources,
    get_revenue,
    pay_for_resource,
)

__version__ = "0.1.0"

__all__ = [
    # Tools
    "MAINLAYER_TOOLS",
    "create_resource",
    "pay_for_resource",
    "check_access",
    "discover_resources",
    "get_revenue",
    # Agent factories
    "create_vendor_agent",
    "create_buyer_agent",
    "create_full_agent",
    # Client
    "MainlayerClient",
    "MainlayerAPIError",
    "get_default_client",
    "set_default_client",
    # Metadata
    "__version__",
]
