import requests
import time
from queries.queries import get_swap_query


## Fetch data ##

def fetch_transactions_for_day(start_timestamp, end_timestamp, subgraph_url):
    """
    Fetch transactions from The Graph for a specific day using a start and end timestamp.
    Queries data in batches of 1000 to handle pagination.
    """
    transactions = []
    skip = 0
    query = get_swap_query()

    while True:
        # Set up the query variables
        variables = {
            "startTimestamp": start_timestamp,
            "endTimestamp": end_timestamp,
            "skip": skip
        }

        # Send the GraphQL request
        response = requests.post(subgraph_url, json={"query": query, "variables": variables})
        data = response.json()

        if "errors" in data:
            raise Exception(f"GraphQL Error: {data['errors']}")

        # Extract transactions
        fetched_transactions = data["data"]["transactions"]

        if not fetched_transactions:
            break

        transactions.extend(fetched_transactions)
        skip += 1000

    return transactions

def fetch_recent_transactions(subgraph_url, buffer_seconds=300):
    """
    Fetch recent transactions from the last `buffer_seconds` to ensure no gaps in data.
    """
    if isinstance(buffer_seconds, str):
        buffer_seconds = int(buffer_seconds)  # Convert to int if it's a string

    now = int(time.time())
    start_timestamp = now - buffer_seconds
    end_timestamp = now
    return fetch_transactions_for_day(start_timestamp, end_timestamp, subgraph_url)


## Process data ##
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