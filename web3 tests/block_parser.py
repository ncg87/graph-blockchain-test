import asyncio
import json
import logging
import requests
from datetime import datetime
from typing import List
from models import BaseTransaction, SwapEvent, MintEvent, BurnEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SolanaBlockParser:
    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        self.rpc_url = rpc_url

    def fetch_block(self, slot: int):
        """Fetch a block by its slot number."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBlock",
            "params": [
                slot,
                {"transactionDetails": "full", "rewards": False}
            ]
        }
        response = requests.post(self.rpc_url, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to fetch block {slot}: {response.status_code}")
            return None

    def parse_transactions(self, block_data: dict) -> List[dict]:
        """Parse transactions from block data into dictionaries."""
        transactions = []

        for tx in block_data.get("result", {}).get("transactions", []):
            meta = tx.get("meta", {})
            transaction = tx.get("transaction", {})
            message = transaction.get("message", {})

            base_tx = {
                "id": transaction.get("signatures", [None])[0],
                "dex_id": "solana",  # Adjust if needed
                "block_number": block_data.get("result", {}).get("blockHeight"),
                "timestamp": block_data.get("result", {}).get("blockTime"),
                "gas_used": meta.get("computeUnitsConsumed"),
                "gas_price": None,  # Solana doesn't have explicit gas price
                "message": message  # Include the message for parsing
            }
            transactions.append(base_tx)

        return transactions

    def parse_swap_events(self, transactions: List[dict]):
        """Parse swap events from transactions."""
        swap_events = []
        for tx in transactions:
            message = tx.get("message", {})
            for instruction in message.get("instructions", []):
                if instruction.get("program", "") == "spl-token-swap":
                    parsed = instruction.get("parsed", {})
                    if "info" in parsed:
                        info = parsed["info"]
                        swap_event = SwapEvent(
                            parent_transaction=BaseTransaction(
                                id=tx["id"],
                                dex_id=tx["dex_id"],
                                block_number=tx["block_number"],
                                timestamp=tx["timestamp"],
                                gas_used=tx["gas_used"],
                                gas_price=tx["gas_price"]
                            ),
                            timestamp=tx["timestamp"],
                            id=f"swap-{tx['id']}",
                            token0_symbol=info.get("tokenA", {}).get("symbol", ""),
                            token1_symbol=info.get("tokenB", {}).get("symbol", ""),
                            token0_id=info.get("tokenA", {}).get("mint", ""),
                            token1_id=info.get("tokenB", {}).get("mint", ""),
                            token0_name=info.get("tokenA", {}).get("name", ""),
                            token1_name=info.get("tokenB", {}).get("name", ""),
                            amount0=info.get("amountIn", "0"),
                            amount1=info.get("amountOut", "0"),
                            amount_usd="0",  # Calculate if pricing data is available
                            sender=info.get("authority", ""),
                            recipient=info.get("destination", ""),
                            dex_id=tx["dex_id"]
                        )
                        swap_events.append(swap_event)
                        logger.info(f"Parsed Swap Event: {swap_event}")
        return swap_events


    def parse_mint_events(self, transactions: List[dict]):
        """Parse mint events from transactions."""
        mint_events = []
        for tx in transactions:
            message = tx.get("message", {})
            for instruction in message.get("instructions", []):
                if instruction.get("program", "") == "spl-token-mint":
                    parsed = instruction.get("parsed", {})
                    if "info" in parsed:
                        info = parsed["info"]
                        mint_event = MintEvent(
                            parent_transaction=BaseTransaction(
                                id=tx["id"],
                                dex_id=tx["dex_id"],
                                block_number=tx["block_number"],
                                timestamp=tx["timestamp"],
                                gas_used=tx["gas_used"],
                                gas_price=tx["gas_price"]
                            ),
                            timestamp=tx["timestamp"],
                            id=f"mint-{tx['id']}",
                            token0_symbol=info.get("mint", {}).get("symbol", ""),
                            token1_symbol="",
                            token0_id=info.get("mint", {}).get("address", ""),
                            token1_id="",
                            token0_name=info.get("mint", {}).get("name", ""),
                            token1_name="",
                            amount0=info.get("amount", "0"),
                            amount1="0",
                            amount_usd="0",  # Could calculate if pricing data is available
                            owner=info.get("owner", ""),
                            dex_id=tx["dex_id"]
                        )
                        mint_events.append(mint_event)
                        logger.info(f"Parsed Mint Event: {mint_event}")
        return mint_events

    def parse_burn_events(self, transactions: List[dict]):
        """Parse burn events from transactions."""
        burn_events = []
        for tx in transactions:
            message = tx.get("message", {})
            for instruction in message.get("instructions", []):
                if instruction.get("program", "") == "spl-token-burn":
                    parsed = instruction.get("parsed", {})
                    if "info" in parsed:
                        info = parsed["info"]
                        burn_event = BurnEvent(
                            parent_transaction=BaseTransaction(
                                id=tx["id"],
                                dex_id=tx["dex_id"],
                                block_number=tx["block_number"],
                                timestamp=tx["timestamp"],
                                gas_used=tx["gas_used"],
                                gas_price=tx["gas_price"]
                            ),
                            timestamp=tx["timestamp"],
                            id=f"burn-{tx['id']}",
                            token0_symbol=info.get("mint", {}).get("symbol", ""),
                            token1_symbol="",
                            token0_id=info.get("mint", {}).get("address", ""),
                            token1_id="",
                            token0_name=info.get("mint", {}).get("name", ""),
                            token1_name="",
                            amount0=info.get("amount", "0"),
                            amount1="0",
                            amount_usd="0",  # Could calculate if pricing data is available
                            owner=info.get("owner", ""),
                            dex_id=tx["dex_id"]
                        )
                        burn_events.append(burn_event)
                        logger.info(f"Parsed Burn Event: {burn_event}")
        return burn_events


    async def process_blocks(self, start_slot: int, end_slot: int):
        """Fetch and process blocks from start_slot to end_slot."""
        for slot in range(start_slot, end_slot + 1):
            logger.info(f"Processing block {slot}")
            block_data = self.fetch_block(slot)

            if not block_data:
                continue

            transactions = self.parse_transactions(block_data)

            swap_events = self.parse_swap_events(transactions)
            mint_events = self.parse_mint_events(transactions)
            burn_events = self.parse_burn_events(transactions)

            # Print or save events as needed
            logger.info(f"Block {slot} contains {len(transactions)} transactions")
            logger.info(f"Swap Events: {swap_events}")
            logger.info(f"Mint Events: {mint_events}")
            logger.info(f"Burn Events: {burn_events}")

async def main():
    parser = SolanaBlockParser()
    start_slot = 150000000  # Example start slot
    end_slot = 150000010  # Example end slot

    await parser.process_blocks(start_slot, end_slot)

if __name__ == "__main__":
    asyncio.run(main())
