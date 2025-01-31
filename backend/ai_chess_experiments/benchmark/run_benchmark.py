#!/usr/bin/env python3
"""Command-line interface for running chess engine benchmarks."""

import argparse
from typing import List
import json
from ..engines.random_engine import RandomEngine
from ..engines.minimax_engine import MinimaxEngine
from .engine_benchmark import EngineBenchmark, compare_engines

def get_engine(engine_name: str, **kwargs):
    """Get engine instance by name."""
    engines = {
        'random': RandomEngine,
        'minimax': MinimaxEngine,
    }
    
    if engine_name not in engines:
        raise ValueError(f"Unknown engine: {engine_name}. Available engines: {list(engines.keys())}")
    
    return engines[engine_name](**kwargs)

def main():
    parser = argparse.ArgumentParser(description='Benchmark chess engines')
    parser.add_argument('--engines', nargs='+', default=['minimax'],
                      help='Engines to benchmark (random, minimax)')
    parser.add_argument('--depth', type=int, default=3,
                      help='Search depth for minimax engine')
    parser.add_argument('--compare', action='store_true',
                      help='Compare multiple engines')
    parser.add_argument('--output', type=str,
                      help='Output file for results (JSON)')
    
    args = parser.parse_args()
    
    # Create engine instances
    engine_instances = []
    for engine_name in args.engines:
        kwargs = {'depth': args.depth} if engine_name == 'minimax' else {}
        engine = get_engine(engine_name, **kwargs)
        engine_instances.append(engine)
    
    if args.compare and len(engine_instances) > 1:
        # Compare multiple engines
        results = compare_engines(engine_instances)
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
    else:
        # Benchmark single engine
        engine = engine_instances[0]
        benchmark = EngineBenchmark(engine)
        results = benchmark.run_full_benchmark()
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)

if __name__ == "__main__":
    main() 