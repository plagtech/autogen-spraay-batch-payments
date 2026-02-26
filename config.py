"""
Spraay Configuration — Chain deployments, contract addresses, and ABI.

Spraay is deployed on 8 chains. Each entry contains the contract address,
chain ID, RPC URL, and block explorer for that network.
"""

CHAIN_CONFIGS = {
    "base": {
        "contract": "0x1646452F98E36A3c9Cfc3eDD8868221E207B5eEC",
        "chain_id": 8453,
        "rpc": "https://mainnet.base.org",
        "explorer": "https://basescan.org",
    },
    "ethereum": {
        "contract": "0x1646452F98E36A3c9Cfc3eDD8868221E207B5eEC",
        "chain_id": 1,
        "rpc": "https://eth.llamarpc.com",
        "explorer": "https://etherscan.io",
    },
    "arbitrum": {
        "contract": "0x1646452F98E36A3c9Cfc3eDD8868221E207B5eEC",
        "chain_id": 42161,
        "rpc": "https://arb1.arbitrum.io/rpc",
        "explorer": "https://arbiscan.io",
    },
    "unichain": {
        "contract": "0x08fA5D1c16CD6E2a16FC0E4839f262429959E073",
        "chain_id": 130,
        "rpc": "https://mainnet.unichain.org",
        "explorer": "https://uniscan.xyz",
    },
    "plasma": {
        "contract": "0x08fA5D1c16CD6E2a16FC0E4839f262429959E073",
        "chain_id": 10849,
        "rpc": "https://rpc.plasma.io",
        "explorer": "https://plasmascan.io",
    },
    "bob": {
        "contract": "0x08fA5D1c16CD6E2a16FC0E4839f262429959E073",
        "chain_id": 60808,
        "rpc": "https://rpc.gobob.xyz",
        "explorer": "https://explorer.gobob.xyz",
    },
}


# Spraay Contract ABI (essential functions only)
SPRAAY_ABI = [
    {
        "inputs": [
            {"internalType": "address[]", "name": "recipients", "type": "address[]"},
            {"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}
        ],
        "name": "sprayETH",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "token", "type": "address"},
            {"internalType": "address[]", "name": "recipients", "type": "address[]"},
            {"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}
        ],
        "name": "sprayToken",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "owner",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "feePercent",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
]
