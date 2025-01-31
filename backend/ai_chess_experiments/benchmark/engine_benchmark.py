"""Comprehensive benchmarking tool for chess engines."""

import time
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import chess
import numpy as np
from ..engines.base_engine import BaseChessEngine
from .positions import TEST_POSITIONS, EVALUATION_POSITIONS, TIME_CONTROL_POSITIONS

class EngineBenchmark:
    def __init__(self, engine: BaseChessEngine, log_file: Optional[str] = None):
        """Initialize the benchmark.
        
        Args:
            engine: The chess engine to benchmark
            log_file: Optional file to save results
        """
        self.engine = engine
        self.log_file = log_file or f"logs/benchmark_{engine.__class__.__name__}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.results: Dict[str, Any] = {}
    
    def benchmark_position(self, fen: str, depth: int = 4, time_limit: Optional[float] = None) -> Dict[str, Any]:
        """Benchmark a single position.
        
        Args:
            fen: The FEN string of the position
            depth: Search depth for the engine
            time_limit: Optional time limit in seconds
        """
        self.engine.set_position(fen)
        
        # Time the move generation
        start_time = time.time()
        if hasattr(self.engine, 'depth'):
            original_depth = self.engine.depth
            self.engine.depth = depth
        
        try:
            move = self.engine.get_move()
            end_time = time.time()
            
            result = {
                "move": move.uci(),
                "time_taken": end_time - start_time,
                "nodes_searched": getattr(self.engine, 'nodes_searched', None),
                "depth_reached": depth,
                "evaluation": None
            }
            
            # Get position evaluation if available
            if hasattr(self.engine, 'evaluate_position'):
                result["evaluation"] = self.engine.evaluate_position()
            
            return result
        
        finally:
            if hasattr(self.engine, 'depth'):
                self.engine.depth = original_depth
    
    def benchmark_evaluation(self) -> Dict[str, Any]:
        """Benchmark evaluation function accuracy."""
        results = []
        
        for pos in EVALUATION_POSITIONS:
            self.engine.set_position(pos["fen"])
            if hasattr(self.engine, 'evaluate_position'):
                eval_score = self.engine.evaluate_position()
                error = abs(eval_score - pos["expected_eval"])
                results.append({
                    "position": pos["name"],
                    "actual_eval": eval_score,
                    "expected_eval": pos["expected_eval"],
                    "error": error
                })
        
        return {
            "positions": results,
            "mean_error": np.mean([r["error"] for r in results]),
            "max_error": max(r["error"] for r in results)
        }
    
    def benchmark_speed(self) -> Dict[str, Any]:
        """Benchmark engine speed in various positions."""
        results = []
        
        for pos in TIME_CONTROL_POSITIONS:
            moves_made = 0
            total_time = 0
            start_time = time.time()
            
            while total_time < pos["time_limit"]:
                result = self.benchmark_position(pos["fen"])
                moves_made += 1
                total_time = time.time() - start_time
            
            results.append({
                "position": pos["name"],
                "moves_per_second": moves_made / total_time,
                "total_moves": moves_made,
                "time_taken": total_time
            })
        
        return {
            "positions": results,
            "average_moves_per_second": np.mean([r["moves_per_second"] for r in results])
        }
    
    def run_full_benchmark(self) -> Dict[str, Any]:
        """Run a complete benchmark suite."""
        print(f"Starting benchmark for {self.engine.__class__.__name__}")
        
        # Test standard positions
        position_results = []
        for pos in TEST_POSITIONS:
            print(f"\nTesting position: {pos['name']}")
            result = self.benchmark_position(pos["fen"], pos["depth"])
            position_results.append({
                "position": pos["name"],
                "description": pos["description"],
                **result
            })
            print(f"Move chosen: {result['move']}, Time: {result['time_taken']:.3f}s")
        
        # Test evaluation accuracy
        print("\nTesting evaluation accuracy...")
        eval_results = self.benchmark_evaluation()
        print(f"Mean evaluation error: {eval_results['mean_error']:.2f}")
        
        # Test speed
        print("\nTesting engine speed...")
        speed_results = self.benchmark_speed()
        print(f"Average moves per second: {speed_results['average_moves_per_second']:.1f}")
        
        # Compile results
        self.results = {
            "engine": self.engine.__class__.__name__,
            "timestamp": datetime.now().isoformat(),
            "standard_positions": position_results,
            "evaluation": eval_results,
            "speed": speed_results
        }
        
        # Save results
        self.save_results()
        
        return self.results
    
    def save_results(self):
        """Save benchmark results to file."""
        with open(self.log_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\nResults saved to {self.log_file}")

def compare_engines(engines: List[BaseChessEngine]) -> Dict[str, Any]:
    """Compare multiple engines against each other.
    
    Args:
        engines: List of engines to compare
    """
    results = {}
    
    for engine in engines:
        benchmark = EngineBenchmark(engine)
        results[engine.__class__.__name__] = benchmark.run_full_benchmark()
    
    # Save comparison results
    comparison_file = f"logs/engine_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(comparison_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results 