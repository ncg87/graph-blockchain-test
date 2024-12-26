import requests
import time
from queries.queries import get_swap_query

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

def analyze_swap_legitimacy(swap):
    # Check liquidity is substantial (e.g., > $10000)
    liquidity = float(swap['pool']['liquidity']) / 1e18  # Convert from wei
    
    # Verify price relationship
    token0_price = float(swap['pool']['token0Price'])
    token1_price = float(swap['pool']['token1Price'])
    price_relationship = abs(1/token0_price - token1_price) < 0.0001  # Should be close
    
    # Check trade size vs liquidity
    trade_value_usd = float(swap['amountUSD'])
    trade_to_liquidity_ratio = trade_value_usd / liquidity
    
    return {
        "sufficient_liquidity": liquidity > 10000,
        "valid_price_relationship": price_relationship,
        "reasonable_trade_size": trade_to_liquidity_ratio < 0.1,  # Trade < 10% of liquidity
        "usd_value": trade_value_usd
    }
