import time
import psutil
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
from prometheus_client import Counter, Histogram, start_http_server
from functools import wraps

@dataclass
class EngineMetrics:
    engine_name: str
    nodes_searched: int
    depth_reached: int
    time_taken: float
    memory_used: int
    cpu_percent: float
    timestamp: datetime

class ChessMonitor:
    def __init__(self):
        self.logger = logging.getLogger('chess_monitor')
        self.metrics: Dict[str, List[EngineMetrics]] = {}
        self.start_time = time.time()

    def start_monitoring(self, engine_name: str) -> None:
        """Start monitoring an engine"""
        if engine_name not in self.metrics:
            self.metrics[engine_name] = []
        self.logger.info(f"Started monitoring {engine_name}")

    def record_move_metrics(
        self,
        engine_name: str,
        nodes: int,
        depth: int,
        time_taken: float,
        process: Optional[psutil.Process] = None
    ) -> None:
        """Record metrics for a move"""
        if process is None:
            memory = 0
            cpu = 0
        else:
            memory = process.memory_info().rss
            cpu = process.cpu_percent()

        metric = EngineMetrics(
            engine_name=engine_name,
            nodes_searched=nodes,
            depth_reached=depth,
            time_taken=time_taken,
            memory_used=memory,
            cpu_percent=cpu,
            timestamp=datetime.now()
        )
        
        self.metrics[engine_name].append(metric)
        self.logger.debug(f"Recorded metrics for {engine_name}: {metric}")

    def get_engine_stats(self, engine_name: str) -> Dict:
        """Get statistics for an engine"""
        if engine_name not in self.metrics:
            return {}

        metrics = self.metrics[engine_name]
        if not metrics:
            return {}

        total_nodes = sum(m.nodes_searched for m in metrics)
        total_time = sum(m.time_taken for m in metrics)
        avg_depth = sum(m.depth_reached for m in metrics) / len(metrics)
        avg_memory = sum(m.memory_used for m in metrics) / len(metrics)
        avg_cpu = sum(m.cpu_percent for m in metrics) / len(metrics)

        return {
            'total_moves': len(metrics),
            'total_nodes': total_nodes,
            'nodes_per_second': total_nodes / total_time if total_time > 0 else 0,
            'average_depth': avg_depth,
            'average_time_per_move': total_time / len(metrics),
            'average_memory_mb': avg_memory / (1024 * 1024),
            'average_cpu_percent': avg_cpu
        }

    def get_system_stats(self) -> Dict:
        """Get overall system statistics"""
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'uptime': time.time() - self.start_time,
            'active_engines': len(self.metrics),
            'total_moves': sum(len(m) for m in self.metrics.values())
        }

    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics in specified format"""
        if format == 'json':
            import json
            return json.dumps({
                'system': self.get_system_stats(),
                'engines': {
                    name: self.get_engine_stats(name)
                    for name in self.metrics
                }
            }, indent=2)
        elif format == 'csv':
            import csv
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['engine', 'timestamp', 'nodes', 'depth', 'time', 'memory', 'cpu'])
            for engine, metrics in self.metrics.items():
                for m in metrics:
                    writer.writerow([
                        engine,
                        m.timestamp.isoformat(),
                        m.nodes_searched,
                        m.depth_reached,
                        m.time_taken,
                        m.memory_used,
                        m.cpu_percent
                    ])
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")

    def clear_metrics(self, engine_name: Optional[str] = None) -> None:
        """Clear metrics for specified engine or all engines"""
        if engine_name:
            self.metrics[engine_name] = []
        else:
            self.metrics.clear()
        self.logger.info(f"Cleared metrics for {'all engines' if engine_name is None else engine_name}")

# Global monitor instance
monitor = ChessMonitor()

# Metrics
MOVE_CALCULATION_TIME = Histogram(
    'chess_engine_move_calculation_seconds',
    'Time spent calculating moves',
    ['depth', 'phase']  # phase: opening, middlegame, endgame
)

ENGINE_NODES_SEARCHED = Counter(
    'chess_engine_nodes_searched_total',
    'Total number of nodes searched',
    ['depth']
)

GAME_DURATION = Histogram(
    'chess_game_duration_seconds',
    'Duration of chess games',
    ['game_type']  # human_vs_bot, bot_vs_bot
)

MOVE_COUNTER = Counter(
    'chess_moves_total',
    'Total number of moves made',
    ['move_type']  # capture, check, castle, normal
)

def track_calculation_time(depth: int):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Determine game phase based on move number or piece count
            phase = determine_game_phase(args[0])  # args[0] should be the board
            
            MOVE_CALCULATION_TIME.labels(
                depth=str(depth),
                phase=phase
            ).observe(duration)
            
            return result
        return wrapper
    return decorator

def determine_game_phase(board) -> str:
    """Determine the phase of the game based on the board state."""
    piece_count = sum(1 for _ in str(board) if _.isalpha())
    if piece_count >= 28:  # Most pieces still on board
        return 'opening'
    elif piece_count >= 10:  # Several pieces captured
        return 'middlegame'
    else:
        return 'endgame'

def increment_nodes_searched(depth: int, nodes: int):
    """Track the number of nodes searched at a given depth."""
    ENGINE_NODES_SEARCHED.labels(depth=str(depth)).inc(nodes)

def track_game_duration(game_type: str, duration: float):
    """Record the duration of a completed game."""
    GAME_DURATION.labels(game_type=game_type).observe(duration)

def track_move(move_type: str):
    """Increment the move counter for a specific type of move."""
    MOVE_COUNTER.labels(move_type=move_type).inc()

def init_metrics(port: int = 9090):
    """Start the Prometheus metrics server."""
    start_http_server(port) 