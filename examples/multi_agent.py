"""
Multi-agent handoff example
============================

Demonstrates the OpenAI Agents SDK handoff pattern with Mainlayer:

1. A **buyer agent** discovers and purchases a resource.
2. It hands off to a **vendor agent** which validates the entitlement and
   logs the revenue event.

The handoff is implemented using the SDK's native ``handoffs=`` parameter so
the buyer agent can delegate to the vendor agent at the right moment without
any manual orchestration code.

Usage
-----
    export MAINLAYER_API_KEY="ml_..."
    export OPENAI_API_KEY="sk-..."
    python examples/multi_agent.py
"""

from __future__ import annotations

import os

from agents import Agent, Runner, handoff

from mainlayer_openai_agents import create_buyer_agent, create_vendor_agent
from mainlayer_openai_agents._client import MainlayerClient, set_default_client
from mainlayer_openai_agents.tools import check_access, discover_resources, get_revenue, pay_for_resource


def main() -> None:
    api_key = os.environ.get("MAINLAYER_API_KEY", "")
    if not api_key:
        raise SystemExit("Set MAINLAYER_API_KEY before running this example.")

    # Configure the shared Mainlayer client once so all tools use the same key.
    set_default_client(MainlayerClient(api_key=api_key))

    payer_id = "agent_session_abc123"

    # -----------------------------------------------------------------------
    # Build the vendor agent (receives the handoff)
    # -----------------------------------------------------------------------
    vendor_agent = Agent(
        name="Mainlayer Vendor Agent",
        model="gpt-4o",
        instructions=(
            "You are a Mainlayer vendor agent. "
            "When you receive a handoff you will be given a resource_id and payer_id. "
            "1. Verify the entitlement is active using check_access. "
            "2. Fetch the revenue summary for the last 7 days. "
            "3. Summarise both results clearly for the buyer."
        ),
        tools=[check_access, get_revenue],
    )

    # -----------------------------------------------------------------------
    # Build the buyer agent with a handoff to the vendor agent
    # -----------------------------------------------------------------------
    buyer_agent = Agent(
        name="Mainlayer Buyer Agent",
        model="gpt-4o",
        instructions=(
            "You are a Mainlayer buyer agent. "
            "1. Discover resources matching the user's request. "
            "2. Purchase access for the specified payer_id. "
            "3. Once payment is confirmed, hand off to the Vendor Agent so it can "
            "   verify the entitlement and report revenue."
        ),
        tools=[discover_resources, pay_for_resource],
        handoffs=[handoff(vendor_agent)],
    )

    # -----------------------------------------------------------------------
    # Run the multi-agent workflow
    # -----------------------------------------------------------------------
    print("=== Multi-agent handoff: buyer -> vendor ===")
    prompt = (
        f"Find a data enrichment or NLP API on the Mainlayer marketplace and "
        f"purchase access for payer '{payer_id}'. "
        "After the payment succeeds, hand off to the vendor agent to confirm "
        "the entitlement and show the 7-day revenue summary."
    )

    result = Runner.run_sync(buyer_agent, prompt)

    print("Final output:")
    print(result.final_output)
    print()
    print("Messages exchanged:")
    for message in result.to_input_list():
        role = message.get("role", "unknown")
        content = message.get("content", "")
        if isinstance(content, list):
            content = " ".join(
                part.get("text", "") for part in content if isinstance(part, dict)
            )
        if content:
            print(f"  [{role}] {content[:120]}")


if __name__ == "__main__":
    main()
