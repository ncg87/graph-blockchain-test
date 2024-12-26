def get_all_activity_query():
    """
    Main query to fetch swaps, mints, burns and flash loans within a time period.
    """
    return """
    query GetAllActivity($startTimestamp: Int!, $endTimestamp: Int!, $skip: Int!) {
        # Swaps
        swaps(
            first: 1000,
            skip: $skip,
            orderBy: timestamp,
            orderDirection: asc,
            where: { timestamp_gte: $startTimestamp, timestamp_lte: $endTimestamp }
        ) {
            id
            timestamp
            blockNumber
            sender
            recipient
            token0 {
                id
                symbol
                decimals
            }
            token1 {
                id
                symbol
                decimals
            }
            amount0
            amount1
            amountUSD
            pool {
                token0Price
                token1Price
                liquidity
            }
        }

        # Mints (Liquidity Additions)
        mints(
            first: 1000,
            skip: $skip,
            orderBy: timestamp,
            orderDirection: asc,
            where: { timestamp_gte: $startTimestamp, timestamp_lte: $endTimestamp }
        ) {
            id
            timestamp
            blockNumber
            pool {
                id
                token0 {
                    id
                    symbol
                    decimals
                }
                token1 {
                    id
                    symbol
                    decimals
                }
            }
            amount0
            amount1
            amountUSD
            sender
        }

        # Burns (Liquidity Removals)
        burns(
            first: 1000,
            skip: $skip,
            orderBy: timestamp,
            orderDirection: asc,
            where: { timestamp_gte: $startTimestamp, timestamp_lte: $endTimestamp }
        ) {
            id
            timestamp
            blockNumber
            pool {
                id
                token0 {
                    id
                    symbol
                    decimals
                }
                token1 {
                    id
                    symbol
                    decimals
                }
            }
            amount0
            amount1
            amountUSD
            sender
        }

        # Flash Loans (if supported by the protocol)
        flashLoans(
            first: 1000,
            skip: $skip,
            orderBy: timestamp,
            orderDirection: asc,
            where: { timestamp_gte: $startTimestamp, timestamp_lte: $endTimestamp }
        ) {
            id
            timestamp
            blockNumber
            token {
                id
                symbol
                decimals
            }
            amount
            amountUSD
            initiator
            fee
        }
    }
"""

def get_pool_stats_query():
    """
    Query to fetch pool statistics and liquidity data.
    """
    return """
    query GetPoolStats($startTimestamp: Int!, $endTimestamp: Int!) {
        pools(
            first: 1000,
            orderBy: totalValueLockedUSD,
            orderDirection: desc,
            where: { timestamp_gte: $startTimestamp, timestamp_lte: $endTimestamp }
        ) {
            id
            token0 {
                id
                symbol
                decimals
            }
            token1 {
                id
                symbol
                decimals
            }
            token0Price
            token1Price
            volumeUSD
            totalValueLockedUSD
            totalValueLockedToken0
            totalValueLockedToken1
            txCount
            liquidityProviderCount
        }
    }
"""

def process_graph_response(data):
    """
    Process the GraphQL response and format it for database insertion.
    Returns a dictionary with different event types.
    """
    processed_data = {
        'swaps': [],
        'mints': [],
        'burns': [],
        'flash_loans': []
    }
    
    # Process swaps
    if 'swaps' in data:
        for swap in data['swaps']:
            processed_data['swaps'].append({
                'id': swap['id'],
                'timestamp': int(swap['timestamp']),
                'block_number': int(swap['blockNumber']),
                'sender': swap['sender'],
                'recipient': swap['recipient'],
                'token0_symbol': swap['token0']['symbol'],
                'token1_symbol': swap['token1']['symbol'],
                'amount0': float(swap['amount0']),
                'amount1': float(swap['amount1']),
                'amount_usd': float(swap['amountUSD'])
            })
    
    # Process mints
    if 'mints' in data:
        for mint in data['mints']:
            processed_data['mints'].append({
                'id': mint['id'],
                'timestamp': int(mint['timestamp']),
                'block_number': int(mint['blockNumber']),
                'pool_id': mint['pool']['id'],
                'token0_symbol': mint['pool']['token0']['symbol'],
                'token1_symbol': mint['pool']['token1']['symbol'],
                'amount0': float(mint['amount0']),
                'amount1': float(mint['amount1']),
                'amount_usd': float(mint['amountUSD']),
                'sender': mint['sender']
            })
    
    # Process burns
    if 'burns' in data:
        for burn in data['burns']:
            processed_data['burns'].append({
                'id': burn['id'],
                'timestamp': int(burn['timestamp']),
                'block_number': int(burn['blockNumber']),
                'pool_id': burn['pool']['id'],
                'token0_symbol': burn['pool']['token0']['symbol'],
                'token1_symbol': burn['pool']['token1']['symbol'],
                'amount0': float(burn['amount0']),
                'amount1': float(burn['amount1']),
                'amount_usd': float(burn['amountUSD']),
                'sender': burn['sender']
            })
    
    # Process flash loans
    if 'flashLoans' in data:
        for loan in data['flashLoans']:
            processed_data['flash_loans'].append({
                'id': loan['id'],
                'timestamp': int(loan['timestamp']),
                'block_number': int(loan['blockNumber']),
                'token_symbol': loan['token']['symbol'],
                'amount': float(loan['amount']),
                'amount_usd': float(loan['amountUSD']),
                'fee': float(loan['fee']),
                'initiator': loan['initiator']
            })
    
    return processed_data

def process_swaps(data):
    """Process swap events from GraphQL response."""
    processed_swaps = []
    if 'swaps' in data:
        for swap in data['data']['swaps']:
            processed_swaps.append({
                'id': swap['id'],
                'timestamp': int(swap['timestamp']),
                'block_number': int(swap['blockNumber']),
                'sender': swap['sender'],
                'recipient': swap['recipient'],
                'token0_symbol': swap['token0']['symbol'],
                'token1_symbol': swap['token1']['symbol'],
                'amount0': float(swap['amount0']),
                'amount1': float(swap['amount1']),
                'amount_usd': float(swap['amountUSD'])
            })
    return processed_swaps

def process_mints(data):
    """Process mint events from GraphQL response."""
    processed_mints = []
    if 'mints' in data:
        for mint in data['data']['mints']:
            processed_mints.append({
                'id': mint['id'],
                'timestamp': int(mint['timestamp']),
                'block_number': int(mint['blockNumber']),
                'pool_id': mint['pool']['id'],
                'token0_symbol': mint['pool']['token0']['symbol'],
                'token1_symbol': mint['pool']['token1']['symbol'],
                'amount0': float(mint['amount0']),
                'amount1': float(mint['amount1']),
                'amount_usd': float(mint['amountUSD']),
                'sender': mint['sender']
            })
    return processed_mints

def process_burns(data):
    """Process burn events from GraphQL response."""
    processed_burns = []
    if 'burns' in data:
        for burn in data['data']['burns']:
            processed_burns.append({
                'id': burn['id'],
                'timestamp': int(burn['timestamp']),
                'block_number': int(burn['blockNumber']),
                'pool_id': burn['pool']['id'],
                'token0_symbol': burn['pool']['token0']['symbol'],
                'token1_symbol': burn['pool']['token1']['symbol'],
                'amount0': float(burn['amount0']),
                'amount1': float(burn['amount1']),
                'amount_usd': float(burn['amountUSD']),
                'sender': burn['sender']
            })
    return processed_burns

def process_flashloans(data):
    """Process flash loan events from GraphQL response."""
    processed_flashloans = []
    if 'flashLoans' in data:
        for loan in data['data']['flashLoans']:
            processed_flashloans.append({
                'id': loan['id'],
                'timestamp': int(loan['timestamp']),
                'block_number': int(loan['blockNumber']),
                'token_symbol': loan['token']['symbol'],
                'amount': float(loan['amount']),
                'amount_usd': float(loan['amountUSD']),
                'fee': float(loan['fee']),
                'initiator': loan['initiator']
            })
    return processed_flashloans