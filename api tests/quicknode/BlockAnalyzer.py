import json
import time
from typing import Optional
from solana.rpc.api import Client
from analyzer import SolanaProgramAnalyzer
from db_setup import SolanaProgramDB

class ContinuousBlockAnalyzer:
    def __init__(self, http_url: str, db_path: str = 'solana_programs.db'):
        self.client = Client(http_url)
        self.program_analyzer = SolanaProgramAnalyzer()
        self.db = SolanaProgramDB(db_path)
        
    def get_block_data(self, slot: int) -> Optional[dict]:
        """Fetch block data for a specific slot"""
        try:
            block = self.client.get_block(
                slot,
                encoding="jsonParsed",
                max_supported_transaction_version=0,
            )
            return block.value if block and block.value else None
        except Exception as e:
            print(f"Error fetching block {slot}: {e}")
            return None

    def analyze_block(self, block_data) -> None:
        """Analyze a block and update database"""

        # Analyze transactions in the block
        for tx in block_data.transactions:
            tx_json = json.loads(tx.to_json())
            self.program_analyzer.analyze_transaction(tx_json)

        # Update database with new program data
        for program_id, instructions in self.program_analyzer.program_instructions.items():
            if program_id not in self.program_analyzer.UTILITY_PROGRAMS:
                self.db.update_program_stats(program_id, instructions, self.program_analyzer.program_counts[program_id])

    def print_current_stats(self):
        """Print current analysis stats"""
        stats = self.program_analyzer.get_program_stats()
        print("\nCurrent Analysis Summary:")
        print(f"Total Transactions: {stats['total_transactions']}")
        print(f"Unique Programs: {stats['unique_programs']}")
        
        print("\nTop 10 Programs from Database:")
        top_programs = self.db.get_top_programs(10)
        for program_id, total_calls, protocol_name, category in top_programs:
            print(f"\n{program_id}: {total_calls} calls")
            if protocol_name:
                print(f"Protocol: {protocol_name}")
            if category:
                print(f"Category: {category}")
            instructions = self.db.get_program_instructions(program_id)
            if instructions:
                print("Instructions:", ", ".join(f"{name}({calls} calls)" for name, calls in instructions))

def run_continuous_analysis(http_url: str, num_blocks: int, delay: float = 0.5):
    """
    Run continuous analysis for specified number of blocks
    
    Args:
        http_url (str): RPC endpoint URL
        num_blocks (int): Number of blocks to analyze
        delay (float): Delay between block analysis in seconds
    """
    analyzer = ContinuousBlockAnalyzer(http_url)
    blocks_analyzed = 0
    
    print(f"Starting analysis of {num_blocks} blocks...")
    
    try:
        while blocks_analyzed < num_blocks:
            # Get current slot
            slot_response = analyzer.client.get_slot()
            current_slot = slot_response.value
            
            # Get and analyze block
            print(f"\nAnalyzing block at slot: {current_slot}")
            block_data = analyzer.get_block_data(current_slot)
            
            if block_data:
                analyzer.analyze_block(block_data)
                blocks_analyzed += 1
                print(f"Analyzed {blocks_analyzed}/{num_blocks} blocks")
                
                # Print stats every 5 blocks or at the end
                if blocks_analyzed % 5 == 0 or blocks_analyzed == num_blocks:
                    analyzer.print_current_stats()
            
            # Wait before next block
            time.sleep(delay)
            
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
    except Exception as e:
        print(f"\nError during analysis: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nFinal Statistics:")
        analyzer.print_current_stats()

if __name__ == "__main__":
    # Configuration
    QUICKNODE_HTTP_URL = "https://dimensional-omniscient-needle.solana-mainnet.quiknode.pro/b673c5969121edb8f0170e0025333ad090bc12b3"
    NUM_BLOCKS_TO_ANALYZE = 100  # Adjust as needed
    DELAY_BETWEEN_BLOCKS = 1  # Adjust based on rate limits
    
    # Run analysis
    run_continuous_analysis(
        http_url=QUICKNODE_HTTP_URL,
        num_blocks=NUM_BLOCKS_TO_ANALYZE,
        delay=DELAY_BETWEEN_BLOCKS
    )