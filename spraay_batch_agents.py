"""
AutoGen × Spraay: Multi-Agent Batch Payment System

A multi-agent crew that plans, validates, and executes batch cryptocurrency
payments using the Spraay protocol. Demonstrates AutoGen's multi-agent
orchestration with real blockchain transactions.

Usage:
    export OPENAI_API_KEY="sk-..."
    export PRIVATE_KEY="your-wallet-private-key"
    python spraay_batch_agents.py
"""

import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.tools import FunctionTool

from spraay_tools import (
    get_supported_chains,
    estimate_gas_savings,
    validate_batch_payment,
    spray_eth,
    spray_token,
)


async def main():
    # --- Model Client ---
    model_client = OpenAIChatCompletionClient(model="gpt-4.1")

    # --- Register Tools ---
    chains_tool = FunctionTool(
        get_supported_chains,
        description="List all blockchain networks where Spraay batch payments are available.",
    )
    estimate_tool = FunctionTool(
        estimate_gas_savings,
        description="Estimate gas savings from using Spraay batch vs individual transfers.",
    )
    validate_tool = FunctionTool(
        validate_batch_payment,
        description="Validate a batch payment: check addresses, amounts, balance, and limits.",
    )
    spray_eth_tool = FunctionTool(
        spray_eth,
        description="Execute a batch native ETH payment to multiple recipients via Spraay.",
    )
    spray_token_tool = FunctionTool(
        spray_token,
        description="Execute a batch ERC-20 token payment to multiple recipients via Spraay.",
    )

    # --- Agent Definitions ---

    planner = AssistantAgent(
        name="PaymentPlanner",
        model_client=model_client,
        description="Plans batch payments by parsing user requests, calculating amounts, and estimating savings.",
        system_message="""You are a Payment Planner agent specialized in cryptocurrency batch payments.

Your role:
1. Parse the user's payment request into structured data (recipients, amounts, chain, token)
2. Use get_supported_chains to verify the target chain is available
3. Use estimate_gas_savings to show the user how much they'll save with batch payments
4. Format the payment plan clearly and pass it to the Validator

Always present amounts in human-readable format (e.g., "100 USDC" not "100000000").
For USDC on Base, use 6 decimals (1 USDC = 1000000 units).
For ETH, use 18 decimals (1 ETH = 1000000000000000000 wei).

When done planning, clearly state "PLAN READY" and list all details.""",
        tools=[chains_tool, estimate_tool],
    )

    validator = AssistantAgent(
        name="PaymentValidator",
        model_client=model_client,
        description="Validates batch payments for correctness, safety, and sufficient funds.",
        system_message="""You are a Payment Validator agent. Your job is to ensure batch payments are safe to execute.

Your role:
1. Take the payment plan from the Planner
2. Use validate_batch_payment to check all addresses, amounts, and limits
3. Flag any errors or warnings
4. If validation passes, clearly state "VALIDATED" and confirm the Executor should proceed
5. If validation fails, explain the issues and ask the Planner to fix them

Never approve a payment that has validation errors. Be strict about safety.""",
        tools=[validate_tool],
    )

    executor = AssistantAgent(
        name="PaymentExecutor",
        model_client=model_client,
        description="Executes validated batch payments on-chain via Spraay smart contracts.",
        system_message="""You are a Payment Executor agent. You execute batch payments ONLY after they've been validated.

Your role:
1. Wait for the Validator to confirm "VALIDATED"
2. Use spray_eth for native ETH payments or spray_token for ERC-20 token payments
3. Report the transaction hash and explorer link
4. Confirm the payment is complete with "PAYMENT COMPLETE"

CRITICAL: Never execute a payment that hasn't been validated. If the Validator hasn't approved, refuse to proceed.

After successful execution, say "PAYMENT COMPLETE" to end the conversation.""",
        tools=[spray_eth_tool, spray_token_tool],
    )

    # --- Team Setup ---
    termination = TextMentionTermination("PAYMENT COMPLETE")

    team = RoundRobinGroupChat(
        participants=[planner, validator, executor],
        termination_condition=termination,
        max_turns=12,
    )

    # --- Run ---
    task = """
    I need to pay my team on Base:
    - 0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B: 50 USDC
    - 0xCA35b7d915458EF540aDe6068dFe2F44E8fa733c: 75 USDC
    - 0x14723A09ACff6D2A60DcdF7aA4AFf308FDDC160C: 100 USDC
    - 0x4B0897b0513fdC7C541B6d9D7E929C4e5364D2dB: 50 USDC
    - 0x583031D1113aD414F02576BD6afaBfb302140225: 25 USDC

    USDC on Base: 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913
    """

    await Console(team.run_stream(task=task))
    await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())
