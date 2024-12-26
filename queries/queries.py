def swap_query(subgraph_url):
    query = """
    query GetSwaps($startTimestamp: Int!, $endTimestamp: Int!, $skip: Int!) {
      swaps(
        first: 1000,
        skip: $skip,
        orderBy: timestamp,
        orderDirection: asc,
        where: { timestamp_gte: $startTimestamp, timestamp_lte: $endTimestamp }
      ) {
        id
        blockNumber
        timestamp
        swaps {
          sender
          recipient
          token0 {
            symbol
          }
          token1 {
            symbol
          }
          amountUSD
        }
      }
    }
    """
    
    return query

def liquidity_query(subgraph_url):
    query = """
    query LiquidityVolumes($startTimestamp: Int!, $endTimestamp: Int!) {
        mints(first: 1000, orderBy: timestamp, orderDirection: desc, where: {timestamp_gte: $startTimestamp, timestamp_lte: $endTimestamp}) {
            token0 {
            id
            symbol
            }
            token1 {
            id
            symbol
            }
            amount0
            amount1
        }
        burns(first: 1000, orderBy: timestamp, orderDirection: desc, where: {timestamp_gte: $startTimestamp, timestamp_lte: $endTimestamp}) {
            token0 {
            id
            symbol
            }
            token1 {
            id
            symbol
            }
            amount0
            amount1
        }
    }
    """
    return query
