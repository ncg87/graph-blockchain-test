import asyncio
import json
import logging
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SolanaTransactionSampler:
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

    async def sample_transactions(self, start_slot: int, sample_size: int = 20):
        """Fetch transactions from blocks starting at `start_slot` until `sample_size` is reached."""
        transactions = []
        current_slot = start_slot

        while len(transactions) < sample_size:
            logger.info(f"Fetching block {current_slot}")
            block_data = self.fetch_block(current_slot)

            if not block_data or not block_data.get("result"):
                logger.warning(f"No data for block {current_slot}")
                current_slot += 1
                continue

            block_transactions = block_data.get("result", {}).get("transactions", [])
            transactions.extend(block_transactions)

            # Stop if we've reached the desired sample size
            if len(transactions) >= sample_size:
                break

            current_slot += 1

        # Limit to the sample size
        transactions = transactions[:sample_size]

        # Extract and print detailed transaction information
        for idx, tx in enumerate(transactions, start=1):
            logger.info(f"Transaction {idx}:")
            logger.info("Signatures: %s", tx.get("transaction", {}).get("signatures", []))

            message = tx.get("transaction", {}).get("message", {})
            logger.info("Recent Blockhash: %s", message.get("recentBlockhash"))
            logger.info("Account Keys: %s", message.get("accountKeys", []))

            instructions = message.get("instructions", [])
            for instr_idx, instr in enumerate(instructions, start=1):
                logger.info(f"Instruction {instr_idx}:")
                logger.info("  Program ID Index: %s", instr.get("programIdIndex"))
                logger.info("  Accounts: %s", instr.get("accounts", []))
                logger.info("  Data: %s", instr.get("data"))

            meta = tx.get("meta", {})
            logger.info("Error: %s", meta.get("err"))
            logger.info("Pre-Balances: %s", meta.get("preBalances", []))
            logger.info("Post-Balances: %s", meta.get("postBalances", []))
            logger.info("Log Messages: %s", meta.get("logMessages", []))

    async def run(self, start_slot: int, sample_size: int = 20):
        await self.sample_transactions(start_slot, sample_size)
    
    def parse_transaction_details(transaction):
        # Extract relevant details
        sender = transaction.get("sender")
        receiver = transaction.get("receiver")
        accounts = transaction.get("accounts", [])
        instructions = transaction.get("instructions", [])
        logs = transaction.get("logs", [])
        balances = transaction.get("balances", {"pre": [], "post": []})

        # Calculate balance changes
        balance_changes = [
            post - pre for pre, post in zip(balances["pre"], balances["post"])
        ]

        # Identify token transfers (if any)
        token_transfers = []
        for instruction in instructions:
            parsed = instruction.get("parsed")
            if parsed and parsed.get("type") == "transfer":
                token_transfers.append(parsed["info"])

        return {
            "sender": sender,
            "receiver": receiver,
            "accounts": accounts,
            "instructions": instructions,
            "logs": logs,
            "balance_changes": balance_changes,
            "token_transfers": token_transfers,
        }


async def main():
    sampler = SolanaTransactionSampler()
    start_slot = 150000000  # Example start slot
    sample_size = 20

    await sampler.run(start_slot, sample_size)

if __name__ == "__main__":
    asyncio.run(main())
