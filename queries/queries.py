
### SQL QUERIES ###

def coin_volume_query():
    query = """
    SELECT
        token AS coin,
        SUM(CASE WHEN sold THEN volume ELSE 0 END) AS total_sold,
        SUM(CASE WHEN NOT sold THEN volume ELSE 0 END) AS total_bought,
        SUM(CASE WHEN sold THEN amount_usd ELSE 0 END) AS total_sold_usd,
        SUM(CASE WHEN NOT sold THEN amount_usd ELSE 0 END) AS total_bought_usd
    FROM (
        SELECT
            token0 AS token,
            ABS(amount0) AS volume,
            amount0 < 0 AS sold,
            amount_usd
        FROM transactions
        UNION ALL
        SELECT
            token1 AS token,
            ABS(amount1) AS volume,
            amount1 < 0 AS sold,
            amount_usd
        FROM transactions
    ) AS combined
    GROUP BY token
    HAVING (SUM(CASE WHEN sold THEN amount_usd ELSE 0 END) + 
            SUM(CASE WHEN NOT sold THEN amount_usd ELSE 0 END)) > 0
    ORDER BY (SUM(CASE WHEN sold THEN amount_usd ELSE 0 END) + 
              SUM(CASE WHEN NOT sold THEN amount_usd ELSE 0 END)) DESC;
    """
    return query
  
### THE GRAPH QUERIES ###

def get_swap_query():
    query = """
    query GetSwaps($startTimestamp: Int!, $endTimestamp: Int!, $skip: Int!) {
      transactions(
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
            decimals
            id
          }
          token1 {
            symbol
            decimals
            id
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
