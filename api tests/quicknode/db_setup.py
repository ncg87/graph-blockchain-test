import sqlite3
from datetime import datetime

class SolanaProgramDB:
    def __init__(self, db_path='solana_programs.db'):
        self.db_path = db_path
        self.setup_database()
    
    def setup_database(self):
        """Create the initial database schema"""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            
            # Create programs table
            c.execute('''
            CREATE TABLE IF NOT EXISTS programs (
                program_id TEXT PRIMARY KEY,
                first_seen TIMESTAMP,
                last_seen TIMESTAMP,
                total_calls INTEGER DEFAULT 0,
                is_verified BOOLEAN DEFAULT 0,
                protocol_name TEXT,
                category TEXT,
                notes TEXT
            )
            ''')
            
            # Create instructions table
            c.execute('''
            CREATE TABLE IF NOT EXISTS instructions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                program_id TEXT,
                instruction_name TEXT,
                first_seen TIMESTAMP,
                total_calls INTEGER DEFAULT 0,
                FOREIGN KEY (program_id) REFERENCES programs (program_id),
                UNIQUE (program_id, instruction_name)
            )
            ''')
            
            # Create daily_stats table for tracking program usage over time
            c.execute('''
            CREATE TABLE IF NOT EXISTS daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                program_id TEXT,
                date DATE,
                call_count INTEGER DEFAULT 0,
                FOREIGN KEY (program_id) REFERENCES programs (program_id),
                UNIQUE (program_id, date)
            )
            ''')
            
            conn.commit()
    
    def update_program_stats(self, program_id, instruction_names=None, count=1):
        """Update program statistics"""
        current_time = datetime.now()
        current_date = current_time.date()
        
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            
            # Update or insert program
            c.execute('''
            INSERT INTO programs (program_id, first_seen, last_seen, total_calls) 
            VALUES (?, ?, ?, ?)
            ON CONFLICT(program_id) DO UPDATE SET 
                last_seen = ?,
                total_calls = total_calls + ?
            ''', (program_id, current_time, current_time, count, current_time, count))
            
            # Update daily stats
            c.execute('''
            INSERT INTO daily_stats (program_id, date, call_count)
            VALUES (?, ?, ?)    
            ON CONFLICT(program_id, date) DO UPDATE SET
                call_count = call_count + ?
            ''', (program_id, current_date, count, count))
            
            # Update instructions if provided
            if instruction_names:
                for inst_name, inst_count in instruction_names.items():
                    c.execute('''
                    INSERT INTO instructions (program_id, instruction_name, first_seen, total_calls)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(program_id, instruction_name) DO UPDATE SET
                        total_calls = total_calls + ?
                    ''', (program_id, inst_name, current_time, inst_count, inst_count))
            
            conn.commit()
    
    def get_top_programs(self, limit=10):
        """Get the most frequently called programs"""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            return c.execute('''
                SELECT program_id, total_calls, protocol_name, category
                FROM programs
                ORDER BY total_calls DESC
                LIMIT ?
            ''', (limit,)).fetchall()
    
    def get_program_instructions(self, program_id):
        """Get all instructions for a specific program"""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            return c.execute('''
                SELECT instruction_name, total_calls
                FROM instructions
                WHERE program_id = ?
                ORDER BY total_calls DESC
            ''', (program_id,)).fetchall()

# Example usage:
def process_transaction_data(tx_data):
    db = SolanaProgramDB()
    
    # Process each program and its instructions
    for program_id, instructions in tx_data.items():
        db.update_program_stats(program_id, instructions)
        
    # Get top programs
    top_programs = db.get_top_programs()
    print("\nMost frequent programs:")
    for prog in top_programs:
        print(f"{prog[0]}: {prog[1]} calls")
        # Get instructions for this program
        instructions = db.get_program_instructions(prog[0])
        if instructions:
            print("Instructions:", ", ".join(f"{i[0]}({i[1]} calls)" for i in instructions))
        print()