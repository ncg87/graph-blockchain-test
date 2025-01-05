from solana.rpc.api import Client

def analyze_latest_block(http_url):
    """Fetch and analyze the latest Solana block"""
    
    # Initialize client
    client = Client(http_url)
    
    try:
        # Get latest slot
        slot_response = client.get_slot()
        current_slot = slot_response.value
        print(f"\nAnalyzing block at slot: {current_slot}")
        
        # Get block data
        block = client.get_block(
            current_slot,
            encoding="jsonParsed",
            max_supported_transaction_version=0,
        )
        
        if not block or not block.value:
            print("Could not get block data")
            return
        
        block_data = block.value
        
        return block_data
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()