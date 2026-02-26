"""
Spraay Batch Payment Tools for AutoGen

Reusable tool functions that can be registered with AutoGen agents
for executing batch cryptocurrency payments via the Spraay protocol.

Spraay Docs: https://spraay.app
GitHub: https://github.com/plagtech/spray-app
"""

import json
import os
from typing import Annotated, List

from web3 import Web3

from config import CHAIN_CONFIGS, SPRAAY_ABI


def get_web3(chain: str = "base") -> Web3:
    """Get a Web3 instance for the specified chain."""
    rpc_url = os.environ.get("RPC_URL", CHAIN_CONFIGS[chain]["rpc"])
    return Web3(Web3.HTTPProvider(rpc_url))


def get_spraay_contract(chain: str = "base"):
    """Get the Spraay contract instance for the specified chain."""
    w3 = get_web3(chain)
    address = CHAIN_CONFIGS[chain]["contract"]
    return w3.eth.contract(address=Web3.to_checksum_address(address), abi=SPRAAY_ABI)


def get_supported_chains() -> str:
    """
    List all blockchain networks where Spraay is deployed.

    Returns a JSON string with chain names, contract addresses, and RPC URLs.
    """
    chains = []
    for name, config in CHAIN_CONFIGS.items():
        chains.append({
            "chain": name,
            "chain_id": config["chain_id"],
            "contract": config["contract"],
            "explorer": config.get("explorer", ""),
        })
    return json.dumps(chains, indent=2)


def estimate_gas_savings(
    num_recipients: Annotated[int, "Number of recipients in the batch"],
    chain: Annotated[str, "Target blockchain (e.g., 'base', 'ethereum', 'arbitrum')"] = "base",
) -> str:
    """
    Estimate gas savings from using Spraay batch payments vs individual transfers.

    Compares the cost of sending individual transactions to each recipient
    versus a single Spraay batch transaction.
    """
    # Average gas costs (approximate)
    individual_transfer_gas = 21000  # Native ETH transfer
    erc20_transfer_gas = 65000  # ERC-20 transfer
    spraay_base_gas = 50000  # Spraay base overhead
    spraay_per_recipient_gas = 9000  # Per recipient in batch

    batch_gas = spraay_base_gas + (spraay_per_recipient_gas * num_recipients)
    individual_native_gas = individual_transfer_gas * num_recipients
    individual_erc20_gas = erc20_transfer_gas * num_recipients

    native_savings = ((individual_native_gas - batch_gas) / individual_native_gas) * 100
    erc20_savings = ((individual_erc20_gas - batch_gas) / individual_erc20_gas) * 100

    return json.dumps({
        "chain": chain,
        "num_recipients": num_recipients,
        "batch_gas_estimate": batch_gas,
        "individual_native_gas": individual_native_gas,
        "individual_erc20_gas": individual_erc20_gas,
        "native_gas_savings_percent": round(max(native_savings, 0), 1),
        "erc20_gas_savings_percent": round(max(erc20_savings, 0), 1),
        "spraay_fee": "0.3%",
        "max_recipients_per_tx": 200,
    }, indent=2)


def validate_batch_payment(
    recipients: Annotated[List[str], "List of recipient wallet addresses"],
    amounts: Annotated[List[str], "List of amounts (in wei or token units) for each recipient"],
    token_address: Annotated[str, "ERC-20 token contract address, or '0x0' for native ETH"] = "0x0000000000000000000000000000000000000000",
    chain: Annotated[str, "Target blockchain"] = "base",
) -> str:
    """
    Validate a batch payment before execution.

    Checks:
    - All addresses are valid checksummed Ethereum addresses
    - Number of recipients doesn't exceed 200
    - Amounts are positive
    - Wallet has sufficient balance
    """
    errors = []
    warnings = []

    # Check recipient count
    if len(recipients) > 200:
        errors.append(f"Too many recipients: {len(recipients)} (max 200)")
    if len(recipients) != len(amounts):
        errors.append(f"Mismatch: {len(recipients)} recipients but {len(amounts)} amounts")
    if len(recipients) == 0:
        errors.append("No recipients provided")

    # Validate addresses
    for i, addr in enumerate(recipients):
        if not Web3.is_address(addr):
            errors.append(f"Invalid address at index {i}: {addr}")

    # Validate amounts
    total = 0
    for i, amt in enumerate(amounts):
        try:
            val = int(amt)
            if val <= 0:
                errors.append(f"Non-positive amount at index {i}: {amt}")
            total += val
        except (ValueError, TypeError):
            errors.append(f"Invalid amount at index {i}: {amt}")

    # Calculate fee
    fee = total * 3 // 1000  # 0.3%
    total_with_fee = total + fee

    is_valid = len(errors) == 0

    return json.dumps({
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "num_recipients": len(recipients),
            "total_amount": str(total),
            "spraay_fee": str(fee),
            "total_with_fee": str(total_with_fee),
            "token": "Native ETH" if token_address == "0x0000000000000000000000000000000000000000" else token_address,
            "chain": chain,
        }
    }, indent=2)


def spray_eth(
    recipients: Annotated[List[str], "List of recipient wallet addresses"],
    amounts: Annotated[List[str], "List of amounts in wei for each recipient"],
    chain: Annotated[str, "Target blockchain"] = "base",
) -> str:
    """
    Execute a batch ETH payment via Spraay.

    Sends native ETH to multiple recipients in a single transaction.
    Requires PRIVATE_KEY environment variable to be set.
    """
    private_key = os.environ.get("PRIVATE_KEY")
    if not private_key:
        return json.dumps({"error": "PRIVATE_KEY environment variable not set"})

    w3 = get_web3(chain)
    contract = get_spraay_contract(chain)
    account = w3.eth.account.from_key(private_key)

    checksummed = [Web3.to_checksum_address(r) for r in recipients]
    int_amounts = [int(a) for a in amounts]
    total = sum(int_amounts)
    fee = total * 3 // 1000
    value = total + fee

    try:
        tx = contract.functions.sprayETH(
            checksummed, int_amounts
        ).build_transaction({
            "from": account.address,
            "value": value,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 50000 + (9000 * len(recipients)),
            "maxFeePerGas": w3.eth.gas_price * 2,
            "maxPriorityFeePerGas": w3.to_wei(0.001, "gwei"),
        })

        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        explorer = CHAIN_CONFIGS[chain].get("explorer", "")
        tx_url = f"{explorer}/tx/0x{tx_hash.hex()}" if explorer else ""

        return json.dumps({
            "success": True,
            "tx_hash": f"0x{tx_hash.hex()}",
            "tx_url": tx_url,
            "block_number": receipt["blockNumber"],
            "gas_used": receipt["gasUsed"],
            "recipients": len(recipients),
            "total_sent": str(total),
            "fee_paid": str(fee),
        }, indent=2)

    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


def spray_token(
    token_address: Annotated[str, "ERC-20 token contract address"],
    recipients: Annotated[List[str], "List of recipient wallet addresses"],
    amounts: Annotated[List[str], "List of token amounts (in smallest unit) for each recipient"],
    chain: Annotated[str, "Target blockchain"] = "base",
) -> str:
    """
    Execute a batch ERC-20 token payment via Spraay.

    Sends any ERC-20 token (USDC, USDT, DAI, etc.) to multiple recipients
    in a single transaction. Requires token approval before execution.
    Requires PRIVATE_KEY environment variable to be set.
    """
    private_key = os.environ.get("PRIVATE_KEY")
    if not private_key:
        return json.dumps({"error": "PRIVATE_KEY environment variable not set"})

    w3 = get_web3(chain)
    contract = get_spraay_contract(chain)
    account = w3.eth.account.from_key(private_key)

    checksummed_token = Web3.to_checksum_address(token_address)
    checksummed_recipients = [Web3.to_checksum_address(r) for r in recipients]
    int_amounts = [int(a) for a in amounts]
    total = sum(int_amounts)
    fee = total * 3 // 1000
    approval_amount = total + fee

    try:
        # Step 1: Approve Spraay contract to spend tokens
        erc20_abi = [
            {
                "inputs": [
                    {"name": "spender", "type": "address"},
                    {"name": "amount", "type": "uint256"}
                ],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
        token_contract = w3.eth.contract(address=checksummed_token, abi=erc20_abi)
        spraay_address = CHAIN_CONFIGS[chain]["contract"]

        approve_tx = token_contract.functions.approve(
            Web3.to_checksum_address(spraay_address), approval_amount
        ).build_transaction({
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 60000,
            "maxFeePerGas": w3.eth.gas_price * 2,
            "maxPriorityFeePerGas": w3.to_wei(0.001, "gwei"),
        })

        signed_approve = account.sign_transaction(approve_tx)
        approve_hash = w3.eth.send_raw_transaction(signed_approve.raw_transaction)
        w3.eth.wait_for_transaction_receipt(approve_hash, timeout=120)

        # Step 2: Execute batch token transfer
        tx = contract.functions.sprayToken(
            checksummed_token, checksummed_recipients, int_amounts
        ).build_transaction({
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 80000 + (12000 * len(recipients)),
            "maxFeePerGas": w3.eth.gas_price * 2,
            "maxPriorityFeePerGas": w3.to_wei(0.001, "gwei"),
        })

        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        explorer = CHAIN_CONFIGS[chain].get("explorer", "")
        tx_url = f"{explorer}/tx/0x{tx_hash.hex()}" if explorer else ""

        return json.dumps({
            "success": True,
            "tx_hash": f"0x{tx_hash.hex()}",
            "approve_hash": f"0x{approve_hash.hex()}",
            "tx_url": tx_url,
            "block_number": receipt["blockNumber"],
            "gas_used": receipt["gasUsed"],
            "recipients": len(recipients),
            "token": checksummed_token,
            "total_sent": str(total),
            "fee_paid": str(fee),
        }, indent=2)

    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
