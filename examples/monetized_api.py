#!/usr/bin/env python
"""
Monetized API Example

Demonstrates how to build a paywalled API endpoint that automatically
verifies payment entitlements before responding to requests.

Setup:
    export MAINLAYER_API_KEY="ml_..."
    export OPENAI_API_KEY="sk-..."
    pip install fastapi uvicorn
    python examples/monetized_api.py

Then test with:
    curl -X POST http://localhost:8000/api/forecast \\
      -H "Content-Type: application/json" \\
      -d '{"query": "weather", "payer": "user_123"}'
"""

from typing import Any

from mainlayer_openai_agents import MainlayerClient


def demo_monetized_endpoint() -> None:
    """
    Simulate a monetized API endpoint that requires payment verification
    before responding to requests.
    """
    api_key = __import__('os').environ.get('MAINLAYER_API_KEY')
    if not api_key:
        raise ValueError('MAINLAYER_API_KEY environment variable is required')

    client = MainlayerClient(api_key=api_key)

    print('=== Monetized API Endpoint Demo ===\n')

    # -----------------------------------------------------------------------
    # Setup: Create a resource representing the API
    # -----------------------------------------------------------------------
    print('📦 Creating API resource...')

    try:
        resource = client.create_resource(
            name='Weather Forecast API',
            price_usd=0.05,
            fee_model='per_call',
            description='Premium weather forecasts with 7-day outlook',
        )

        resource_id = resource['resource_id']
        print(f'✓ Resource created: {resource_id}\n')

        # -----------------------------------------------------------------------
        # Simulate API request with payment verification
        # -----------------------------------------------------------------------
        def handle_api_request(payer_id: str, query: str) -> dict[str, Any]:
            """
            Example API handler that checks payment before responding.
            """
            print(f'📋 API Request received:')
            print(f'   Payer: {payer_id}')
            print(f'   Query: {query}\n')

            # Step 1: Check if payer has entitlement
            print(f'🔐 Verifying payment entitlement...')
            has_access = client.check_access(resource_id, payer_id)

            if not has_access:
                print(f'❌ Access denied. Payer must purchase first.\n')
                return {
                    'error': 'access_denied',
                    'message': f'Purchase access to {resource_id} to use this API',
                }

            print(f'✓ Access verified\n')

            # Step 2: Process request
            print(f'⚙️  Processing request...')
            result = {
                'status': 'success',
                'forecast': 'Sunny, 75°F, Light winds',
                'location': 'San Francisco, CA',
                'confidence': 0.95,
            }
            print(f'✓ Response ready\n')

            return result

        # -----------------------------------------------------------------------
        # Scenario 1: Request without valid entitlement
        # -----------------------------------------------------------------------
        print('--- Scenario 1: Unauthorized Request ---\n')

        response1 = handle_api_request('user_without_access', 'weather forecast')
        print(f'Response: {response1}\n')

        # -----------------------------------------------------------------------
        # Scenario 2: Purchase access and retry
        # -----------------------------------------------------------------------
        print('--- Scenario 2: Purchase Access ---\n')

        payer_id = 'user_with_access'
        print(f'💳 Processing payment for {payer_id}...')

        payment = client.pay_for_resource(resource_id, payer_id)
        print(f'✓ Payment successful: {payment["payment_id"]}\n')

        # -----------------------------------------------------------------------
        # Scenario 3: Authorized request after payment
        # -----------------------------------------------------------------------
        print('--- Scenario 3: Authorized Request ---\n')

        response2 = handle_api_request(payer_id, 'weather forecast')
        print(f'Response: {response2}\n')

    except Exception as err:
        print(f'Error: {err}')
        raise


if __name__ == '__main__':
    demo_monetized_endpoint()
