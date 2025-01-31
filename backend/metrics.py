from prometheus_client import Counter, Gauge, Histogram, start_http_server
import psutil
import threading
import time

# Game metrics
MOVES_TOTAL = Counter('chess_moves_total', 'Total number of moves made', ['engine', 'result'])
GAME_DURATION = Histogram('chess_game_duration_seconds', 'Game duration in seconds')
ACTIVE_GAMES = Gauge('chess_active_games', 'Number of active games')

# Engine metrics
ENGINE_DEPTH = Gauge('chess_engine_depth', 'Current search depth', ['engine'])
NODES_SEARCHED = Counter('chess_nodes_searched_total', 'Total nodes searched', ['engine'])
MOVE_TIME = Histogram('chess_move_time_seconds', 'Time taken for moves', ['engine'])

# System metrics
CPU_USAGE = Gauge('chess_cpu_usage_percent', 'CPU usage percentage')
MEMORY_USAGE = Gauge('chess_memory_usage_bytes', 'Memory usage in bytes')
ENGINE_PROCESS_CPU = Gauge('chess_engine_cpu_percent', 'Engine CPU usage', ['engine'])
ENGINE_PROCESS_MEMORY = Gauge('chess_engine_memory_bytes', 'Engine memory usage', ['engine'])

def start_metrics_server(port: int = 9090):
    """Start the Prometheus metrics server"""
    start_http_server(port)

def start_system_metrics_collection():
    """Collect system metrics in background thread"""
    def collect_metrics():
        while True:
            CPU_USAGE.set(psutil.cpu_percent())
            MEMORY_USAGE.set(psutil.virtual_memory().used)
            time.sleep(1)

    thread = threading.Thread(target=collect_metrics, daemon=True)
    thread.start()

class MetricsCollector:
    """Collect metrics for a specific engine"""
    def __init__(self, engine_name: str):
        self.engine_name = engine_name
        self.move_timer = None

    def start_move(self):
        """Start timing a move"""
        self.move_timer = time.time()

    def end_move(self, depth: int, nodes: int):
        """Record metrics for completed move"""
        if self.move_timer is not None:
            duration = time.time() - self.move_timer
            MOVE_TIME.labels(engine=self.engine_name).observe(duration)
            ENGINE_DEPTH.labels(engine=self.engine_name).set(depth)
            NODES_SEARCHED.labels(engine=self.engine_name).inc(nodes)
            self.move_timer = None

    def record_game_result(self, result: str):
        """Record game result"""
        MOVES_TOTAL.labels(engine=self.engine_name, result=result).inc()

    def update_process_metrics(self, process: psutil.Process):
        """Update process-specific metrics"""
        try:
            ENGINE_PROCESS_CPU.labels(engine=self.engine_name).set(process.cpu_percent())
            ENGINE_PROCESS_MEMORY.labels(engine=self.engine_name).set(process.memory_info().rss)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

def setup_monitoring():
    """Initialize all monitoring"""
    # Start Prometheus metrics server
    start_metrics_server()
    
    # Start system metrics collection
    start_system_metrics_collection()
    
    # Update active games count
    ACTIVE_GAMES.set(0)

# Example usage in engine:
"""
from metrics import MetricsCollector, ACTIVE_GAMES

class ChessEngine:
    def __init__(self, name):
        self.metrics = MetricsCollector(name)
        ACTIVE_GAMES.inc()

    def get_best_move(self, board):
        self.metrics.start_move()
        # ... calculate move ...
        self.metrics.end_move(depth=current_depth, nodes=nodes_searched)
        return best_move

    def quit(self):
        ACTIVE_GAMES.dec()
""" 