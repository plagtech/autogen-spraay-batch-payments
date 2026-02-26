"""
AutoGen × Spraay: Single Agent with MCP Server

Demonstrates using AutoGen's McpWorkbench to connect to Spraay's MCP server
on Smithery. This is the simplest way to give an AutoGen agent batch payment
capabilities — just point it at the MCP server.

Usage:
    export OPENAI_API_KEY="sk-..."
    npm install -g @anthropic/smithery-cli  # for Smithery MCP access
    python spraay_mcp_agent.py
"""

import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import McpWorkbench, StdioServerParams


async def main():
    model_client = OpenAIChatCompletionClient(model="gpt-4.1")

    # Connect to Spraay MCP server via Smithery
    # The MCP server provides tools for batch payments on Base, Ethereum,
    # Arbitrum, Unichain, Plasma, BOB, and Bittensor
    server_params = StdioServerParams(
        command="npx",
        args=[
            "-y",
            "@smithery/cli@latest",
            "run",
            "@plagtech/spraay-mcp-server",
            "--config",
            '{"privateKey": "YOUR_PRIVATE_KEY", "rpcUrl": "https://mainnet.base.org"}',
        ],
    )

    async with McpWorkbench(server_params) as spraay_mcp:
        agent = AssistantAgent(
            name="spraay_payment_agent",
            model_client=model_client,
            workbench=spraay_mcp,
            system_message="""You are a crypto payment assistant powered by Spraay.
You help users send batch payments to multiple recipients in a single transaction.

Spraay supports: Base, Ethereum, Arbitrum, Unichain, Plasma, BOB, Bittensor.
Spraay saves ~80% on gas fees compared to individual transfers.
Protocol fee: 0.3% of total amount.
Max recipients per transaction: 200.

Always confirm the payment details with the user before executing.
Show the estimated gas savings when planning a batch payment.""",
            model_client_stream=True,
            max_tool_iterations=10,
        )

        await Console(
            agent.run_stream(
                task="What chains does Spraay support and how much gas can I save sending to 20 recipients?"
            )
        )

    await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())
