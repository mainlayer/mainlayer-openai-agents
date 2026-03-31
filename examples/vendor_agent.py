"""
Vendor agent example
====================

Demonstrates how a vendor uses the Mainlayer Vendor Agent to:
1. Create a new paid API resource on the marketplace.
2. Review 30-day revenue for all owned resources.
3. Verify a specific buyer's entitlement.

Usage
-----
    export MAINLAYER_API_KEY="ml_..."
    export OPENAI_API_KEY="sk-..."
    python examples/vendor_agent.py
"""

from __future__ import annotations

import os

from agents import Runner

from mainlayer_openai_agents import create_vendor_agent


def main() -> None:
    api_key = os.environ.get("MAINLAYER_API_KEY", "")
    if not api_key:
        raise SystemExit("Set MAINLAYER_API_KEY before running this example.")

    agent = create_vendor_agent(api_key=api_key, model="gpt-4o")

    # -----------------------------------------------------------------------
    # Step 1: Create a new resource
    # -----------------------------------------------------------------------
    print("=== Step 1: Creating a resource ===")
    result = Runner.run_sync(
        agent,
        (
            "Create a new Mainlayer resource with the following details:\n"
            "  Name: Real-Time Weather Forecast API\n"
            "  Price: $0.02 per call\n"
            "  Fee model: per_call\n"
            "  Description: Hourly weather forecasts for 50,000+ cities worldwide.\n"
            "Return the resource_id in your response."
        ),
    )
    print(result.final_output)
    print()

    # -----------------------------------------------------------------------
    # Step 2: Revenue report
    # -----------------------------------------------------------------------
    print("=== Step 2: Revenue report (last 30 days) ===")
    result = Runner.run_sync(
        agent,
        "Show me a revenue summary for the last 30 days. Format the total as USD.",
    )
    print(result.final_output)
    print()

    # -----------------------------------------------------------------------
    # Step 3: Check a buyer's entitlement
    # -----------------------------------------------------------------------
    print("=== Step 3: Check buyer entitlement ===")
    result = Runner.run_sync(
        agent,
        (
            "Check whether payer 'user_demo_42' has active access to resource "
            "'res_weather_001'. Tell me clearly yes or no."
        ),
    )
    print(result.final_output)


if __name__ == "__main__":
    main()
