"""
Buyer agent example
===================

Demonstrates how a buyer agent uses Mainlayer to:
1. Discover available resources matching a search query.
2. Check whether a payer already holds an entitlement (avoiding double charges).
3. Purchase access when the payer does not already have it.

Usage
-----
    export MAINLAYER_API_KEY="ml_..."
    export OPENAI_API_KEY="sk-..."
    python examples/buyer_agent.py
"""

from __future__ import annotations

import os

from agents import Runner

from mainlayer_openai_agents import create_buyer_agent


def main() -> None:
    api_key = os.environ.get("MAINLAYER_API_KEY", "")
    if not api_key:
        raise SystemExit("Set MAINLAYER_API_KEY before running this example.")

    # Identifies the end-user or downstream agent making the purchase.
    payer_id = "user_demo_42"

    agent = create_buyer_agent(api_key=api_key, model="gpt-4o")

    # -----------------------------------------------------------------------
    # Step 1: Discover resources
    # -----------------------------------------------------------------------
    print("=== Step 1: Discover weather resources ===")
    result = Runner.run_sync(
        agent,
        (
            "Search the Mainlayer marketplace for weather-related APIs. "
            "List the top 3 results with their resource_id, name, price, and fee model."
        ),
    )
    print(result.final_output)
    print()

    # -----------------------------------------------------------------------
    # Step 2: Check existing entitlement before buying
    # -----------------------------------------------------------------------
    print("=== Step 2: Check existing entitlement ===")
    result = Runner.run_sync(
        agent,
        (
            f"Check whether payer '{payer_id}' already has access to "
            "resource 'res_weather_001'. "
            "If they do, tell me their entitlement is active and skip the purchase. "
            "If they do not, go ahead and purchase it for them."
        ),
    )
    print(result.final_output)
    print()

    # -----------------------------------------------------------------------
    # Step 3: Purchase a different resource unconditionally
    # -----------------------------------------------------------------------
    print("=== Step 3: Purchase a translation API ===")
    result = Runner.run_sync(
        agent,
        (
            f"Find a translation or language API on the marketplace and purchase "
            f"access for payer '{payer_id}'. "
            "Confirm the entitlement_id after the payment completes."
        ),
    )
    print(result.final_output)


if __name__ == "__main__":
    main()
