# 🥭 AutoGen × Spraay: Multi-Agent Batch Payments

A multi-agent system built with [Microsoft AutoGen](https://github.com/microsoft/autogen) that enables AI agents to execute batch cryptocurrency payments using [Spraay](https://spraay.app) — a multi-chain batch payment protocol.

## What is This?

This sample demonstrates how AutoGen agents can collaborate to plan, validate, and execute batch payments across multiple blockchain networks. It showcases:

- **Multi-agent orchestration** — A Payment Planner, Validator, and Executor agent work together
- **MCP integration** — Uses AutoGen's `McpWorkbench` to connect to Spraay's MCP server
- **Custom tools** — Native AutoGen `FunctionTool` implementations for direct Spraay API calls
- **Real blockchain transactions** — Sends actual batch payments on Base, Ethereum, Arbitrum, Unichain, and more

## Architecture

```
User Request ("Pay 5 team members 100 USDC each on Base")
    │
    ▼
┌─────────────────┐
│ Payment Planner  │  ← Plans the batch: validates addresses, calculates totals
│  (AssistantAgent)│     estimates gas savings vs individual transfers
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Validator      │  ← Checks: sufficient balance? valid addresses?
│  (AssistantAgent)│     correct chain? fee estimation?
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Executor      │  ← Executes the batch payment via Spraay contract
│  (AssistantAgent)│     returns transaction hash + receipt
└─────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+
- An RPC provider key (e.g., Alchemy, Infura)
- A wallet with funds on your target chain
- OpenAI API key (for the LLM powering the agents)

### Installation

```bash
pip install autogen-agentchat autogen-ext[openai] web3 requests
```

### Environment Variables

```bash
export OPENAI_API_KEY="sk-..."
export PRIVATE_KEY="your-wallet-private-key"
export RPC_URL="https://mainnet.base.org"  # or any supported chain
```

### Run the Example

```bash
# Multi-agent batch payment crew
python spraay_batch_agents.py

# Simple single-agent with MCP
python spraay_mcp_agent.py
```

## Spraay Overview

[Spraay](https://spraay.app) is a multi-chain batch payment protocol that lets you pay up to 200 recipients in a single transaction with ~80% gas savings.

| Feature | Details |
|---------|---------|
| **Supported Chains** | Base, Ethereum, Arbitrum, Unichain, Plasma, BOB, Bittensor |
| **Token Support** | Native tokens (ETH) + any ERC-20 (USDC, USDT, DAI, etc.) |
| **Max Recipients** | 200 per transaction |
| **Fee** | 0.3% protocol fee |
| **Gas Savings** | ~80% vs individual transfers |
| **MCP Server** | Available on [Smithery](https://smithery.ai) |

### Contract Addresses

| Chain | Address |
|-------|---------|
| Base | `0x1646452F98E36A3c9Cfc3eDD8868221E207B5eEC` |
| Ethereum | Deployed (see [spraay.app](https://spraay.app)) |
| Arbitrum | Deployed |
| Unichain | `0x08fA5D1c16CD6E2a16FC0E4839f262429959E073` |
| Plasma | `0x08fA5D1c16CD6E2a16FC0E4839f262429959E073` |

## Files

| File | Description |
|------|-------------|
| `spraay_batch_agents.py` | Multi-agent crew: Planner → Validator → Executor |
| `spraay_mcp_agent.py` | Single agent using Spraay MCP server via McpWorkbench |
| `spraay_tools.py` | Reusable AutoGen `FunctionTool` wrappers for Spraay |
| `config.py` | Chain configs, contract addresses, ABIs |

## How It Works

1. **User sends a natural language request** — e.g., "Distribute 500 USDC equally to these 5 addresses on Base"
2. **Payment Planner** parses the request, resolves ENS names, calculates per-recipient amounts, and estimates gas savings
3. **Validator** checks wallet balance, verifies addresses, and confirms the batch is within limits (≤200 recipients)
4. **Executor** calls Spraay's `sprayToken()` or `sprayETH()` contract function and returns the transaction hash

## Supported Operations

- `spray_eth` — Batch send native ETH/tokens to multiple recipients
- `spray_token` — Batch send ERC-20 tokens (USDC, DAI, etc.) to multiple recipients
- `estimate_gas_savings` — Compare gas costs: batch vs individual transfers
- `get_supported_chains` — List all chains where Spraay is deployed

## Links

- **Spraay App**: [spraay.app](https://spraay.app)
- **Spraay GitHub**: [github.com/plagtech/spray-app](https://github.com/plagtech/spray-app)
- **Spraay x402 Gateway**: [gateway.spraay.app](https://gateway.spraay.app)
- **AutoGen Docs**: [microsoft.github.io/autogen](https://microsoft.github.io/autogen)
- **Twitter**: [@Spraay_app](https://twitter.com/Spraay_app)

## License

MIT
