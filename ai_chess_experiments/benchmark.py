import time
import chess
from engines.random_engine import RandomEngine
from engines.minimax_engine import MinimaxEngine

def benchmark_engine(engine, positions=None, time_limit=30):
    """Benchmark an engine's performance.
    
    Args:
        engine: The chess engine to benchmark
        positions: List of FEN strings to test (uses starting position if None)
        time_limit: Maximum time in seconds to run the benchmark
    """
    if positions is None:
        positions = [chess.STARTING_FEN]
    
    total_moves = 0
    total_time = 0
    start_time = time.time()
    
    print(f"Benchmarking {engine.__class__.__name__}...")
    
    for fen in positions:
        engine.set_position(fen)
        
        while not engine.is_game_over():
            move_start = time.time()
            move = engine.get_move()
            move_time = time.time() - move_start
            
            total_moves += 1
            total_time += move_time
            
            print(f"Position: {fen}")
            print(f"Move: {move}, Time: {move_time:.3f}s")
            
            engine.update_board(move)
            
            if time.time() - start_time > time_limit:
                break
        
        if time.time() - start_time > time_limit:
            break
    
    print(f"\nResults for {engine.__class__.__name__}:")
    print(f"Total moves: {total_moves}")
    print(f"Average time per move: {total_time/total_moves:.3f}s")
    print(f"Moves per second: {total_moves/total_time:.1f}")

def main():
    # Test positions (including some tactical positions)
    test_positions = [
        chess.STARTING_FEN,
        "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    ]
    
    # Benchmark Random Engine (as baseline)
    random_engine = RandomEngine()
    benchmark_engine(random_engine, test_positions)
    
    # Benchmark Minimax Engine with different depths
    for depth in [2, 3, 4]:
        minimax_engine = MinimaxEngine(depth=depth)
        print(f"\nTesting Minimax with depth {depth}")
        benchmark_engine(minimax_engine, test_positions)

if __name__ == "__main__":
    main() 