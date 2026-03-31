# mainlayer-openai-agents

OpenAI Agents SDK integration for [Mainlayer](https://mainlayer.fr) — payment infrastructure for AI agents.

Mainlayer is the easiest way to add monetisation to any API or agent workflow. This package wraps the Mainlayer REST API as `@function_tool`-decorated tools and ships two ready-to-use agent factories so you can go from zero to a paid API in minutes.

---

## Features

- Five plug-and-play `@function_tool` tools compatible with any `agents.Agent`
- Pre-configured **vendor** and **buyer** agent factories with sensible system instructions
- Thin, testable HTTP client (`MainlayerClient`) with clean error handling
- Multi-agent handoff example using the SDK's native `handoffs=` pattern
- Full type annotations and 25+ unit tests (no real network calls)

---

## Installation

```bash
pip install mainlayer-openai-agents
```

Requires Python 3.10+ and the `openai-agents` package.

---

## Quick start

### Vendor: publish a paid API

```python
import os
from agents import Runner
from mainlayer_openai_agents import create_vendor_agent

agent = create_vendor_agent(api_key=os.environ["MAINLAYER_API_KEY"])

result = Runner.run_sync(
    agent,
    "Create a weather forecast API resource for $0.02 per call."
)
print(result.final_output)
```

### Buyer: discover and purchase access

```python
import os
from agents import Runner
from mainlayer_openai_agents import create_buyer_agent

agent = create_buyer_agent(api_key=os.environ["MAINLAYER_API_KEY"])

result = Runner.run_sync(
    agent,
    "Find a weather API and buy access for user 'user_42'."
)
print(result.final_output)
```

### Use individual tools with your own agent

```python
from agents import Agent, Runner
from mainlayer_openai_agents import MAINLAYER_TOOLS

agent = Agent(
    name="my-agent",
    model="gpt-4o",
    tools=MAINLAYER_TOOLS,
)

result = Runner.run_sync(agent, "Check my revenue for the last 7 days.")
print(result.final_output)
```

---

## Authentication

Set the `MAINLAYER_API_KEY` environment variable:

```bash
export MAINLAYER_API_KEY="ml_live_..."
```

Or pass it explicitly to any factory function or the client:

```python
from mainlayer_openai_agents import MainlayerClient, set_default_client

set_default_client(MainlayerClient(api_key="ml_live_..."))
```

---

## Tool reference

All five tools are available individually and as the `MAINLAYER_TOOLS` list.

### `create_resource`

Register a new paid resource on the Mainlayer marketplace.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | required | Human-readable resource name |
| `price_usd` | `float` | required | Price in USD per access grant |
| `fee_model` | `str` | `"one_time"` | `one_time`, `per_call`, or `subscription` |
| `description` | `str` | `""` | Marketplace description shown to buyers |

Returns the created resource object including `resource_id`.

---

### `pay_for_resource`

Purchase access to a resource on behalf of a payer.

| Parameter | Type | Description |
|-----------|------|-------------|
| `resource_id` | `str` | ID of the resource to purchase |
| `payer_id` | `str` | Unique ID of the entity making the payment |

Returns a payment confirmation with `payment_id` and `entitlement_id`.

---

### `check_access`

Verify whether a payer holds a valid entitlement to a resource.

| Parameter | Type | Description |
|-----------|------|-------------|
| `resource_id` | `str` | ID of the resource to check |
| `payer_id` | `str` | ID of the entity to verify |

Returns an entitlement status object with an `"active"` boolean field.

---

### `discover_resources`

Search the Mainlayer marketplace for available resources.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | `""` | Free-text search query |
| `limit` | `int` | `10` | Maximum number of results (1–100) |

Returns a list of resource objects with `resource_id`, `name`, `price_usd`, and `fee_model`.

---

### `get_revenue`

Retrieve aggregated revenue analytics for the authenticated vendor.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `period` | `str` | `"30d"` | Time window: `7d`, `30d`, `90d`, `1y` |

Returns a revenue summary with `total_revenue_usd`, `transaction_count`, and a per-resource `breakdown`.

---

## Agent factories

### `create_vendor_agent(api_key, model="gpt-4o")`

Returns an `Agent` pre-configured with `create_resource`, `check_access`, and `get_revenue` tools and a vendor-focused system prompt.

### `create_buyer_agent(api_key, model="gpt-4o")`

Returns an `Agent` pre-configured with `discover_resources`, `check_access`, and `pay_for_resource` tools and a buyer-focused system prompt.

### `create_full_agent(api_key, model="gpt-4o")`

Returns an `Agent` with all five tools attached — useful when the role is determined at runtime.

---

## Examples

| File | Description |
|------|-------------|
| `examples/vendor_agent.py` | Create a resource, check revenue, verify a buyer entitlement |
| `examples/buyer_agent.py` | Discover resources, check entitlement, purchase access |
| `examples/multi_agent.py` | Handoff pattern: buyer agent hands off to vendor agent |

Run any example after setting your environment variables:

```bash
export MAINLAYER_API_KEY="ml_..."
export OPENAI_API_KEY="sk-..."
python examples/vendor_agent.py
```

---

## Development

```bash
# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src tests examples

# Type-check
mypy src/mainlayer_openai_agents
```

---

## License

MIT — see [LICENSE](LICENSE).

---

## Links

- [Mainlayer website](https://mainlayer.fr)
- [API documentation](https://docs.mainlayer.fr)
- [OpenAI Agents SDK](https://github.com/openai/openai-agents-python)
- [Issue tracker](https://github.com/mainlayer/mainlayer-openai-agents/issues)
