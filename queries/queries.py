
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

def get_swaps_query():
    """
    Query to fetch swap events within a time period.
    """
    return """
    query GetSwaps($startTimestamp: Int!, $endTimestamp: Int!, $skip: Int!) {
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
    }
    """

def get_mints_query():
    """
    Query to fetch mint (liquidity addition) events within a time period.
    """
    return """
    query GetMints($startTimestamp: Int!, $endTimestamp: Int!, $skip: Int!) {
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
    }
    """

def get_burns_query():
    """
    Query to fetch burn (liquidity removal) events within a time period.
    """
    return """
    query GetBurns($startTimestamp: Int!, $endTimestamp: Int!, $skip: Int!) {
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
    }
    """

def get_flashloans_query():
    """
    Query to fetch flash loan events within a time period.
    """
    return """
    query GetFlashLoans($startTimestamp: Int!, $endTimestamp: Int!, $skip: Int!) {
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