import psycopg2
from psycopg2.extras import execute_batch
import time

class Database:
    def __init__(self, dbname, user, password, host="localhost", port=5432):
        """
        Initialize the database connection.
        """
        self.connection = psycopg2.connect(
            dbname=dbname, user=user, password=password, host=host, port=port
        )
        self.cursor = self.connection.cursor()
        self._initialize_tables()

    def _initialize_tables(self):
        """
        Create the transactions table if it doesn't exist.
        """
        create_table_query = '''
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            block_number INTEGER,
            timestamp INTEGER,
            sender TEXT,
            recipient TEXT,
            token0 TEXT,
            token1 TEXT,
            amount_usd NUMERIC,
            amount0 NUMERIC,
            amount1 NUMERIC
        );
        '''
        self.cursor.execute(create_table_query)
        self.connection.commit()

    def insert_transactions(self, transactions):
        """
        Insert a batch of transactions into the database.
        """
        insert_query = '''
        INSERT INTO transactions (
            id, block_number, timestamp, sender, recipient, token0, token1, amount_usd
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
        '''
        # Prepare data for batch insertion
        transaction_data = []
        for txn in transactions:
            for swap in txn["swaps"]:
                try:
                    transaction_data.append((
                        txn["id"],
                        txn["blockNumber"],
                        txn["timestamp"],
                        swap["sender"],
                        swap["recipient"],
                        swap["token0"]["symbol"],
                        swap["token1"]["symbol"],
                        float(swap.get("amountUSD", 0)),
                        float(swap.get("amount0", 0)),
                        float(swap.get("amount1", 0))
                    ))
                except KeyError as e:
                    print(f"Missing field in transaction: {e}, txn: {txn}, swap: {swap}")
                    continue  # Skip incomplete data
        
        # Execute batch insert
        execute_batch(self.cursor, insert_query, transaction_data)
        self.connection.commit()

    def archive_old_transactions(self, retention_period=86400):
        cutoff_timestamp = int(time.time()) - retention_period

        # Insert older transactions into an archive table
        archive_query = '''
        INSERT INTO transactions_archive
        SELECT * 
        FROM transactions
        WHERE timestamp < %s;
        '''
        self.cursor.execute(archive_query, (cutoff_timestamp,))

        # Delete the archived rows from the main table
        delete_query = 'DELETE FROM transactions WHERE timestamp < %s;'
        self.cursor.execute(delete_query, (cutoff_timestamp,))
        self.connection.commit()

    
    def cleanup_old_transactions(self, retention_period=86400):
        """
        Remove transactions older than the retention period (default: 24 hours).
        """
        cutoff_timestamp = int(time.time()) - retention_period
        delete_query = 'DELETE FROM transactions WHERE timestamp < %s;'
        self.cursor.execute(delete_query, (cutoff_timestamp,))
        self.connection.commit()

    def fetch_recent_transactions(self, limit=100):
        """
        Fetch the most recent transactions, limited by the specified number.
        """
        select_query = '''
        SELECT * FROM transactions
        ORDER BY timestamp DESC
        LIMIT %s;
        '''
        self.cursor.execute(select_query, (limit,))
        return self.cursor.fetchall()

    def close_connection(self):
        """
        Close the database connection.
        """
        self.cursor.close()
        self.connection.close()
