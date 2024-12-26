import psycopg2
from psycopg2.extras import execute_batch
import time
from typing import List, Dict, Any

class Database:
    def __init__(self, dbname, user, password, host="localhost", port=5432):
        """Initialize the database connection."""
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.open_connection()
        self._initialize_tables()

    def _initialize_tables(self):
        """Create the necessary tables if they don't exist."""
        create_tables_queries = [
            '''
            CREATE TABLE IF NOT EXISTS transactions_base (
                id TEXT PRIMARY KEY,
                block_number INTEGER,
                timestamp INTEGER,
                transaction_type TEXT CHECK (transaction_type IN ('swap', 'mint', 'burn', 'flashloan')),
                amount_usd NUMERIC
            );
            ''',
            '''
            CREATE TABLE IF NOT EXISTS swaps (
                id TEXT PRIMARY KEY REFERENCES transactions_base(id),
                sender TEXT,
                recipient TEXT,
                token0 TEXT,
                token1 TEXT,
                amount0 NUMERIC,
                amount1 NUMERIC,
                token0_price NUMERIC,
                token1_price NUMERIC,
                pool_liquidity NUMERIC
            );
            ''',
            '''
            CREATE TABLE IF NOT EXISTS mints (
                id TEXT PRIMARY KEY REFERENCES transactions_base(id),
                sender TEXT,
                pool_id TEXT,
                token0 TEXT,
                token1 TEXT,
                amount0 NUMERIC,
                amount1 NUMERIC
            );
            ''',
            '''
            CREATE TABLE IF NOT EXISTS burns (
                id TEXT PRIMARY KEY REFERENCES transactions_base(id),
                sender TEXT,
                pool_id TEXT,
                token0 TEXT,
                token1 TEXT,
                amount0 NUMERIC,
                amount1 NUMERIC
            );
            ''',
            '''
            CREATE TABLE IF NOT EXISTS flashloans (
                id TEXT PRIMARY KEY REFERENCES transactions_base(id),
                initiator TEXT,
                token TEXT,
                amount NUMERIC,
                fee NUMERIC
            );
            '''
        ]
        
        for query in create_tables_queries:
            self.cursor.execute(query)
        self.connection.commit()

    def insert_swaps(self, swaps: List[Dict[str, Any]]):
        """Insert swap transactions into the database."""
        base_query = '''
        INSERT INTO transactions_base (id, block_number, timestamp, transaction_type, amount_usd)
        VALUES (%s, %s, %s, 'swap', %s)
        ON CONFLICT (id) DO NOTHING;
        '''
        
        swap_query = '''
        INSERT INTO swaps (id, sender, recipient, token0, token1, amount0, amount1, 
                         token0_price, token1_price, pool_liquidity)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
        '''
        
        base_data = []
        swap_data = []
        
        for swap in swaps:
            base_data.append((
                swap['id'],
                swap['block_number'],
                swap['timestamp'],
                float(swap['amount_usd'])
            ))
            
            swap_data.append((
                swap['id'],
                swap['sender'],
                swap['recipient'],
                swap['token0_symbol'],
                swap['token1_symbol'],
                float(swap['amount0']),
                float(swap['amount1']),
                float(swap['pool'].get('token0Price', 0)),
                float(swap['pool'].get('token1Price', 0)),
                float(swap['pool'].get('liquidity', 0))
            ))
        
        execute_batch(self.cursor, base_query, base_data)
        execute_batch(self.cursor, swap_query, swap_data)
        self.connection.commit()

    def insert_mints(self, mints: List[Dict[str, Any]]):
        """Insert mint transactions into the database."""
        base_query = '''
        INSERT INTO transactions_base (id, block_number, timestamp, transaction_type, amount_usd)
        VALUES (%s, %s, %s, 'mint', %s)
        ON CONFLICT (id) DO NOTHING;
        '''
        
        mint_query = '''
        INSERT INTO mints (id, sender, pool_id, token0, token1, amount0, amount1)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
        '''
        
        base_data = []
        mint_data = []
        
        for mint in mints:
            base_data.append((
                mint['id'],
                mint['block_number'],
                mint['timestamp'],
                float(mint['amount_usd'])
            ))
            
            mint_data.append((
                mint['id'],
                mint['sender'],
                mint['pool_id'],
                mint['token0_symbol'],
                mint['token1_symbol'],
                float(mint['amount0']),
                float(mint['amount1'])
            ))
        
        execute_batch(self.cursor, base_query, base_data)
        execute_batch(self.cursor, mint_query, mint_data)
        self.connection.commit()

    def insert_burns(self, burns: List[Dict[str, Any]]):
        """Insert burn transactions into the database."""
        base_query = '''
        INSERT INTO transactions_base (id, block_number, timestamp, transaction_type, amount_usd)
        VALUES (%s, %s, %s, 'burn', %s)
        ON CONFLICT (id) DO NOTHING;
        '''
        
        burn_query = '''
        INSERT INTO burns (id, sender, pool_id, token0, token1, amount0, amount1)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
        '''
        
        base_data = []
        burn_data = []
        
        for burn in burns:
            base_data.append((
                burn['id'],
                burn['block_number'],
                burn['timestamp'],
                float(burn['amount_usd'])
            ))
            
            burn_data.append((
                burn['id'],
                burn['sender'],
                burn['pool_id'],
                burn['token0_symbol'],
                burn['token1_symbol'],
                float(burn['amount0']),
                float(burn['amount1'])
            ))
        
        execute_batch(self.cursor, base_query, base_data)
        execute_batch(self.cursor, burn_query, burn_data)
        self.connection.commit()

    def insert_flashloans(self, flashloans: List[Dict[str, Any]]):
        """Insert flashloan transactions into the database."""
        base_query = '''
        INSERT INTO transactions_base (id, block_number, timestamp, transaction_type, amount_usd)
        VALUES (%s, %s, %s, 'flashloan', %s)
        ON CONFLICT (id) DO NOTHING;
        '''
        
        flashloan_query = '''
        INSERT INTO flashloans (id, initiator, token, amount, fee)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
        '''
        
        base_data = []
        flashloan_data = []
        
        for loan in flashloans:
            base_data.append((
                loan['id'],
                loan['block_number'],
                loan['timestamp'],
                float(loan['amount_usd'])
            ))
            
            flashloan_data.append((
                loan['id'],
                loan['initiator'],
                loan['token_symbol'],
                float(loan['amount']),
                float(loan['fee'])
            ))
        
        execute_batch(self.cursor, base_query, base_data)
        execute_batch(self.cursor, flashloan_query, flashloan_data)
        self.connection.commit()

    def get_transaction_stats(self, start_timestamp: int, end_timestamp: int):
        """Get aggregated transaction statistics for visualization."""
        query = '''
        WITH time_series AS (
            SELECT generate_series(
                to_timestamp(%s)::timestamp,
                to_timestamp(%s)::timestamp,
                '1 hour'::interval
            ) AS hour
        ),
        hourly_stats AS (
            SELECT 
                date_trunc('hour', to_timestamp(timestamp)) AS hour,
                transaction_type,
                COUNT(*) as count,
                SUM(amount_usd) as volume_usd
            FROM transactions_base
            WHERE timestamp BETWEEN %s AND %s
            GROUP BY date_trunc('hour', to_timestamp(timestamp)), transaction_type
        )
        SELECT 
            time_series.hour,
            COALESCE(hourly_stats.transaction_type, 'none') as transaction_type,
            COALESCE(hourly_stats.count, 0) as count,
            COALESCE(hourly_stats.volume_usd, 0) as volume_usd
        FROM time_series
        LEFT JOIN hourly_stats ON time_series.hour = hourly_stats.hour
        ORDER BY time_series.hour, transaction_type;
        '''
        
        self.cursor.execute(query, (start_timestamp, end_timestamp, start_timestamp, end_timestamp))
        return self.cursor.fetchall()

    def get_token_volume(self, start_timestamp: int, end_timestamp: int, limit: int = 10):
        """Get top token volumes for visualization."""
        query = '''
        SELECT 
            token0 as token,
            COUNT(*) as transaction_count,
            SUM(ABS(amount0)) as volume,
            SUM(tb.amount_usd) as volume_usd
        FROM swaps s
        JOIN transactions_base tb ON s.id = tb.id
        WHERE tb.timestamp BETWEEN %s AND %s
        GROUP BY token0
        ORDER BY volume_usd DESC
        LIMIT %s;
        '''
        
        self.cursor.execute(query, (start_timestamp, end_timestamp, limit))
        return self.cursor.fetchall()

    def cleanup_old_transactions(self, retention_period: int = 86400):
        """Remove transactions older than the retention period."""
        cutoff_timestamp = int(time.time()) - retention_period
        tables = ['flashloans', 'burns', 'mints', 'swaps', 'transactions_base']
        
        for table in tables:
            if table == 'transactions_base':
                delete_query = f'DELETE FROM {table} WHERE timestamp < %s;'
            else:
                delete_query = f'''
                DELETE FROM {table}
                WHERE id IN (
                    SELECT id FROM transactions_base WHERE timestamp < %s
                );
                '''
            self.cursor.execute(delete_query, (cutoff_timestamp,))
        
        self.connection.commit()

    def open_connection(self):
        """Open a new database connection."""
        self.connection = psycopg2.connect(
            dbname=self.dbname,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port
        )
        self.cursor = self.connection.cursor()

    def close_connection(self):
        """Close the database connection."""
        self.cursor.close()
        self.connection.close()