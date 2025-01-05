# Global rate limit for RPC requests (in seconds)
RATE_LIMIT = 0.2  # Adjust this value as needed

import websockets
import json
import asyncio
import logging
import requests
from datetime import datetime
from websockets.exceptions import ConnectionClosed, WebSocketException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SolanaStreamClient:
    def __init__(self, websocket_url: str = "wss://api.mainnet-beta.solana.com"):
        self.ws_url = websocket_url
        self.subscription_id = None
        self.connected = False

    async def connect_with_timeout(self):
        """Connect to WebSocket with timeout"""
        try:
            ws = await asyncio.wait_for(
                websockets.connect(self.ws_url),
                timeout=10  # 10 second timeout
            )
            logger.info("Successfully connected to WebSocket")
            return ws
        except asyncio.TimeoutError:
            logger.error("Connection timeout")
            return None
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return None

    async def subscribe_transactions(self, ws):
        """Subscribe to transaction stream with timeout"""
        try:
            subscribe_msg = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "logsSubscribe",
                "params": ["all"]
            }
            
            await asyncio.wait_for(
                ws.send(json.dumps(subscribe_msg)),
                timeout=5
            )
            logger.info("Subscription request sent")
            
            # Wait for subscription confirmation
            response = await asyncio.wait_for(
                ws.recv(),
                timeout=5
            )
            logger.info(f"Received response: {response}")
            
            response_data = json.loads(response)
            if 'result' in response_data:
                self.subscription_id = response_data['result']
                logger.info(f"Successfully subscribed with ID: {self.subscription_id}")
                return True
            else:
                logger.error(f"Subscription failed: {response_data}")
                return False
                
        except asyncio.TimeoutError:
            logger.error("Subscription timeout")
            return False
        except Exception as e:
            logger.error(f"Subscription error: {e}")
            return False

    async def fetch_transaction_details(self, signature):
        """Fetch transaction details using RPC."""
        RPC_URL = "https://api.devnet.solana.com"
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBlock",
            "params": [signature, {"encoding": "jsonParsed"}]
        }
        try:
            response = requests.post(RPC_URL, json=payload)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to fetch transaction details: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error fetching transaction details: {e}")
            return None

    async def fetch_transaction_details_with_rate_limit(self, signature):
        """Fetch transaction details with rate limit."""
        await asyncio.sleep(RATE_LIMIT)  # Use global rate limit
        return await self.fetch_transaction_details(signature)

    def extract_sender_receiver(self, transaction_data):
        """Extract sender and receiver from transaction details."""
        message = transaction_data.get("result", {}).get("transaction", {}).get("message", {})
        sender, receiver = None, None

        # Check for parsed instructions
        instructions = message.get("instructions", [])
        for instruction in instructions:
            parsed = instruction.get("parsed", {})
            if parsed:
                info = parsed.get("info", {})
                sender = info.get("authority")  # Sender
                receiver = info.get("account")  # Receiver
                if sender and receiver:
                    break

        # Fallback to accountKeys if not in instructions
        account_keys = message.get("accountKeys", [])
        if not sender:
            sender = next((key["pubkey"] for key in account_keys if key.get("signer")), None)
        if not receiver:
            receiver = next((key["pubkey"] for key in account_keys if not key.get("signer") and key.get("writable")), None)

        return sender, receiver

    def extract_transaction_details(self, transaction_data):
        """Extract detailed information from the transaction."""
        details = {}

        result = transaction_data.get("result", {})
        transaction = result.get("transaction", {})
        message = transaction.get("message", {})
        meta = result.get("meta", {})

        # Extract accounts
        account_keys = message.get("accountKeys", [])
        details['accounts'] = account_keys

        # Extract instructions
        instructions = message.get("instructions", [])
        details['instructions'] = instructions

        # Extract logs
        logs = meta.get("logMessages", [])
        details['logs'] = logs

        # Extract balances
        pre_balances = meta.get("preBalances", [])
        post_balances = meta.get("postBalances", [])
        details['balances'] = {'pre': pre_balances, 'post': post_balances}

        return details

    async def process_message(self, message):
        """Process incoming message"""
        try:
            data = json.loads(message)

            if 'params' in data and 'result' in data['params']:
                result = data['params']['result']
                value = result.get('value', {})
                signature = value.get('signature', 'None')
                slot = result.get('context', {}).get('slot', 'None')

                print(f"\nTransaction detected:")
                print(f"Signature: {signature}")
                print(f"Slot: {slot}")

                # Fetch transaction details using RPC
                transaction_data = await self.fetch_transaction_details_with_rate_limit(signature)
                if transaction_data:
                    sender, receiver = self.extract_sender_receiver(transaction_data)
                    print(f"Sender: {sender}")
                    print(f"Receiver: {receiver}")

                    # Extract additional details
                    details = self.extract_transaction_details(transaction_data)
                    print(f"Accounts: {details['accounts']}")
                    print(f"Instructions: {details['instructions']}")
                    print(f"Logs: {details['logs']}")
                    print(f"Balances: {details['balances']}")
                else:
                    print("Failed to fetch transaction details")

                # Check for errors
                error = value.get('err', None)
                if error:
                    print(f"Error: {error}")
                else:
                    print("Transaction successful")

                print("-" * 50)

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def listen_for_messages(self, ws):
        """Listen for messages with timeout"""
        while True:
            try:
                message = await asyncio.wait_for(
                    ws.recv(),
                    timeout=30  # 30 second timeout for receiving messages
                )
                await self.process_message(message)
            except asyncio.TimeoutError:
                logger.warning("No messages received for 30 seconds")
                # Send a ping to check connection
                try:
                    ping_msg = {
                        "jsonrpc": "2.0",
                        "id": 999,
                        "method": "ping"
                    }
                    await ws.send(json.dumps(ping_msg))
                except:
                    logger.error("Connection appears to be dead")
                    return
            except Exception as e:
                logger.error(f"Error in message loop: {e}")
                return

    async def start_streaming(self):
        """Main loop with reconnection logic"""
        while True:
            try:
                # Connect to WebSocket
                ws = await self.connect_with_timeout()
                if not ws:
                    logger.error("Failed to connect. Retrying in 5 seconds...")
                    await asyncio.sleep(5)
                    continue

                # Subscribe to transactions
                subscribed = await self.subscribe_transactions(ws)
                if not subscribed:
                    logger.error("Failed to subscribe. Retrying in 5 seconds...")
                    await ws.close()
                    await asyncio.sleep(5)
                    continue

                # Start listening for messages
                logger.info("Starting to listen for messages...")
                await self.listen_for_messages(ws)
                
            except Exception as e:
                logger.error(f"Stream error: {e}")
                
            logger.info("Reconnecting in 5 seconds...")
            await asyncio.sleep(5)

async def main():
    # You can replace this with a different RPC endpoint
    ws_url = "wss://api.devnet.solana.com"
    
    client = SolanaStreamClient(ws_url)
    
    try:
        print("Starting Solana transaction stream...")
        print("Press Ctrl+C to exit")
        await client.start_streaming()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
