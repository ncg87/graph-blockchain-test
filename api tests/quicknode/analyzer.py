import json
from collections import Counter, defaultdict
from typing import Dict, List, Set
from solana.rpc.api import Client

class SolanaProgramAnalyzer:
    # Common utility programs we might want to filter out
    UTILITY_PROGRAMS = {
        'ComputeBudget111111111111111111111111111111',
        'MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr',
        '11111111111111111111111111111111',  # System Program
        'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',  # Token Program
        'Vote111111111111111111111111111111111111111'  # Vote Program
        
    }
    
    def __init__(self):
        self.program_counts = Counter()
        self.program_instructions = {}  # Maps programs to their instruction names
        self.transactions_analyzed = 0
        
    def analyze_transaction(self, transaction_data: dict) -> None:
        """Analyze a single transaction for program IDs and their instructions."""
        self.transactions_analyzed += 1
        
        self.instruction_counts = defaultdict(lambda: defaultdict(int))
        
        # Get instructions from the transaction
        try:
            instructions = transaction_data.get('transaction', {}).get('message', {}).get('instructions', [])
            
            # Count program occurrences and collect instruction data
            for instruction in instructions:
                program_id = instruction.get('programId')
                if program_id:
                    self.program_counts[program_id] += 1
                    
                    # Initialize program instructions list if needed
                    if program_id not in self.program_instructions:
                        self.program_instructions[program_id] = []
                    
                    # Extract instruction type
                    instruction_type = None
                    if isinstance(instruction.get('parsed'), str):
                        instruction_type = instruction['parsed']
                    elif isinstance(instruction.get('parsed'), dict):
                        instruction_type = instruction['parsed'].get('type')
                    
                    # Store instruction type if we found one
                    if instruction_type and instruction_type not in self.program_instructions[program_id]:
                        self.program_instructions[program_id].append(instruction_type)
                        
            # Also check log messages for instruction types
            if 'meta' in transaction_data and 'logMessages' in transaction_data['meta']:
                for log in transaction_data['meta']['logMessages']:
                    if 'Instruction:' in log:
                        instruction_name = log.split('Instruction:')[1].strip()
                        for program_id in self.program_counts:
                            if instruction_name not in self.program_instructions[program_id]:
                                self.program_instructions[program_id].append(instruction_name)
                    
        except Exception as e:
            print(f"Error analyzing transaction: {str(e)}")
    
    def get_top_programs(self, n: int = 10, exclude_utility: bool = True) -> List[tuple]:
        """Get the top N most frequently occurring programs."""
        if exclude_utility:
            filtered_counts = {
                prog: count for prog, count 
                in self.program_counts.items() 
                if prog not in self.UTILITY_PROGRAMS
            }
            return Counter(filtered_counts).most_common(n)
        return self.program_counts.most_common(n)
    
    def get_program_stats(self) -> Dict:
        """Get statistical information about analyzed programs."""
        return {
            'total_transactions': self.transactions_analyzed,
            'unique_programs': len(self.program_counts),
            'total_program_calls': sum(self.program_counts.values()),
            'programs_with_instructions': len([p for p in self.program_instructions if self.program_instructions[p]])
        }
    
    def get_program_instructions(self, program_id: str) -> List[str]:
        """Get all unique instructions seen for a specific program."""
        return self.program_instructions.get(program_id, [])

# Example usage:
def analyze_transactions(transactions_list):
    analyzer = SolanaProgramAnalyzer()
    
    for tx in transactions_list:
        tx_json = json.loads(tx.to_json())
        analyzer.analyze_transaction(tx_json)
    
    # Print summary
    stats = analyzer.get_program_stats()
    print(f"Analysis Summary:")
    print(f"Total Transactions: {stats['total_transactions']}")
    print(f"Unique Programs: {stats['unique_programs']}")
    print(f"\nTop 10 Programs (excluding utility):")
    for program_id, count in analyzer.get_top_programs(10):
        print(f"{program_id}: {count} calls")
        instructions = analyzer.get_program_instructions(program_id)
        if instructions:
            print(f"  Instructions: {', '.join(instructions)}")
            
def analyze_latest_block(http_url):
    """Fetch and analyze the latest Solana block"""
    
    # Initialize client
    client = Client(http_url)
    
    try:
        # Get latest slot
        slot_response = client.get_slot()
        current_slot = slot_response.value
        print(f"\nAnalyzing block at slot: {current_slot}")
        
        # Get block data
        block = client.get_block(
            current_slot,
            encoding="jsonParsed",
            max_supported_transaction_version=0,
        )
        
        if not block or not block.value:
            print("Could not get block data")
            return
        
        block_data = block.value
        
        return block_data
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()