import requests
import time


## Fetch data ##

def fetch_transactions_for_day(start_timestamp, end_timestamp, subgraph_url, query):
    """
    Fetch transactions from The Graph for a specific day using a start and end timestamp.
    Queries data in batches of 1000 to handle pagination.
    """
    transactions = []
    skip = 0

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
