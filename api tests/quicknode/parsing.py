from solana.rpc.api import Client
import json
from datetime import datetime

# Known program IDs and their associations
DEX_PROGRAMS = {
    'srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX': 'Serum DEX',
    '675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8': 'Raydium',
    'JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB': 'Jupiter',
    'whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc': 'Orca',
    '9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP': 'Raydium Swap',
}

# Known CEX wallet addresses (examples)
CEX_WALLETS = {
    '7KBVh9TqtkQHJkMA6dxNLjphVF1jzUE3E3YEBRKgEHmL': 'Binance Hot Wallet',
    'SysvarC1ock11111111111111111111111111111111': 'Kraken Hot Wallet',
    # Add more known CEX wallets
}

def identify_transaction_type(tx_json):
    """Identify if transaction is DEX, CEX, or other"""
    transaction = tx_json['transaction']
    meta = tx_json['meta']
    
    transaction_types = set()
    
    # Check program IDs
    for inst in transaction['message']['instructions']:
        program_id = inst['programId']
        if program_id in DEX_PROGRAMS:
            transaction_types.add(f"DEX ({DEX_PROGRAMS[program_id]})")
    
    # Check account involvement
    for account in transaction['message']['accountKeys']:
        if account['pubkey'] in CEX_WALLETS:
            transaction_types.add(f"CEX ({CEX_WALLETS[account['pubkey']]})")
    
    # Check for token program involvement
    if 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA' in [acc['pubkey'] for acc in transaction['message']['accountKeys']]:
        transaction_types.add("Token Transfer")
    
    return list(transaction_types) if transaction_types else ["Unknown"]

def analyze_transaction(tx):
    """Analyze a single transaction and return structured data"""
    tx_json = json.loads(tx.to_json())
    
    tx_info = {
        'signature': tx_json['transaction']['signatures'][0],
        'status': 'Success' if tx_json['meta']['status'].get('Ok') is not None else 'Failed',
        'fee': tx_json['meta']['fee'],
        'transaction_types': identify_transaction_type(tx_json),
        'instructions_count': len(tx_json['transaction']['message']['instructions'])
    }
    
    # Add token transfer analysis
    if tx_json['meta'].get('preTokenBalances') and tx_json['meta'].get('postTokenBalances'):
        tx_info['token_transfers'] = []
        for pre, post in zip(tx_json['meta']['preTokenBalances'], tx_json['meta']['postTokenBalances']):
            if pre['uiTokenAmount']['uiAmount'] != post['uiTokenAmount']['uiAmount']:
                tx_info['token_transfers'].append({
                    'mint': pre['mint'],
                    'pre_amount': pre['uiTokenAmount']['uiAmount'],
                    'post_amount': post['uiTokenAmount']['uiAmount'],
                    'change': (post['uiTokenAmount']['uiAmount'] or 0) - (pre['uiTokenAmount']['uiAmount'] or 0)
                })
    
    return tx_info

def analyze_latest_block(http_url):
    client = Client(http_url)
    
    try:
        slot_response = client.get_slot()
        current_slot = slot_response.value
        print(f"\nAnalyzing block at slot: {current_slot}")
        
        block = client.get_block(current_slot,
                                 encoding="jsonParsed",
                                 max_supported_transaction_version=0,
                                 )
        
        if not block or not block.value:
            print("Could not get block data")
            return
        
        block_data = block.value
        
        print(f"\nBlock Overview:")
        print(f"Number of Transactions: {len(block_data.transactions)}")
        
        # Track transaction types in block
        transaction_type_counts = {}
        
        for idx, tx in enumerate(block_data.transactions, 1):
            tx_info = analyze_transaction(tx)
            
            # Update transaction type counts
            for tx_type in tx_info['transaction_types']:
                transaction_type_counts[tx_type] = transaction_type_counts.get(tx_type, 0) + 1
            
            print(f"\nTransaction {idx}:")
            print(f"Signature: {tx_info['signature']}")
            print(f"Type: {', '.join(tx_info['transaction_types'])}")
            print(f"Status: {tx_info['status']}")
            
            if 'token_transfers' in tx_info:
                print("Token Transfers:")
                for transfer in tx_info['token_transfers']:
                    print(f"  Mint: {transfer['mint']}")
                    print(f"  Change: {transfer['change']}")
            
            if idx >= 5:  # Limit output for clarity
                break
        
        print("\nTransaction Type Summary:")
        for tx_type, count in transaction_type_counts.items():
            print(f"{tx_type}: {count} transactions")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    QUICKNODE_HTTP_URL = "YOUR_QUICKNODE_HTTP_URL"
    analyze_latest_block(QUICKNODE_HTTP_URL)

if __name__ == "__main__":
    main()