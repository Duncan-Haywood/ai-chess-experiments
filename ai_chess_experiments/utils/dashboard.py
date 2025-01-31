"""Real-time dashboard for monitoring chess bot performance."""

import time
from typing import Dict, Any, Optional
import psutil
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from prometheus_client import start_http_server, Counter, Gauge, Histogram

# Metrics
MOVES_MADE = Counter('chess_moves_total', 'Total number of moves made')
GAMES_PLAYED = Counter('chess_games_total', 'Total number of games played')
CURRENT_GAMES = Gauge('chess_current_games', 'Number of current games')
MOVE_TIME = Histogram('chess_move_time_seconds', 'Time taken to make moves')
CPU_USAGE = Gauge('chess_cpu_usage_percent', 'CPU usage percentage')
MEMORY_USAGE = Gauge('chess_memory_usage_bytes', 'Memory usage in bytes')

class Dashboard:
    def __init__(self, port: int = 8000):
        """Initialize the dashboard.
        
        Args:
            port: Port for Prometheus metrics server
        """
        self.console = Console()
        self.layout = Layout()
        self.active_games: Dict[str, Dict[str, Any]] = {}
        self.process = psutil.Process()
        
        # Start Prometheus metrics server
        start_http_server(port)
        
        # Configure layout
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3),
        )
        
        self.layout["main"].split_row(
            Layout(name="games", ratio=2),
            Layout(name="stats", ratio=1),
        )
    
    def make_header(self) -> Panel:
        """Create header panel with bot status."""
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_row("Chess Bot Dashboard")
        return Panel(grid, style="white on blue")
    
    def make_games_panel(self) -> Panel:
        """Create panel showing active games."""
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Game ID")
        table.add_column("Opponent")
        table.add_column("Time Control")
        table.add_column("Last Move")
        table.add_column("Status")
        
        for game_id, game in self.active_games.items():
            table.add_row(
                game_id[:8],
                game.get('opponent', 'Unknown'),
                game.get('time_control', '-'),
                game.get('last_move', '-'),
                game.get('status', 'Active'),
            )
        
        return Panel(table, title="Active Games", border_style="green")
    
    def make_stats_panel(self) -> Panel:
        """Create panel showing system and engine stats."""
        # System metrics
        cpu_percent = self.process.cpu_percent()
        mem_info = self.process.memory_info()
        
        # Update Prometheus metrics
        CPU_USAGE.set(cpu_percent)
        MEMORY_USAGE.set(mem_info.rss)
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Metric")
        table.add_column("Value")
        
        table.add_row("CPU Usage", f"{cpu_percent:.1f}%")
        table.add_row("Memory", f"{mem_info.rss / 1024 / 1024:.1f} MB")
        table.add_row("Active Games", str(len(self.active_games)))
        table.add_row("Total Games", f"{GAMES_PLAYED._value.get()}")
        table.add_row("Total Moves", f"{MOVES_MADE._value.get()}")
        
        return Panel(table, title="System Stats", border_style="blue")
    
    def make_footer(self) -> Panel:
        """Create footer panel with controls help."""
        return Panel("Press Ctrl+C to exit", style="white on blue")
    
    def update_content(self) -> Layout:
        """Update all panels with latest data."""
        self.layout["header"].update(self.make_header())
        self.layout["games"].update(self.make_games_panel())
        self.layout["stats"].update(self.make_stats_panel())
        self.layout["footer"].update(self.make_footer())
        return self.layout
    
    def update_game(self, game_id: str, data: Dict[str, Any]) -> None:
        """Update information for a specific game."""
        self.active_games[game_id] = data
        CURRENT_GAMES.set(len(self.active_games))
    
    def remove_game(self, game_id: str) -> None:
        """Remove a game from active games."""
        if game_id in self.active_games:
            del self.active_games[game_id]
            CURRENT_GAMES.set(len(self.active_games))
            GAMES_PLAYED.inc()
    
    def record_move(self, move_time: float) -> None:
        """Record a move and its timing."""
        MOVES_MADE.inc()
        MOVE_TIME.observe(move_time)
    
    def run(self) -> None:
        """Run the dashboard with live updates."""
        with Live(self.update_content(), refresh_per_second=2) as live:
            try:
                while True:
                    live.update(self.update_content())
                    time.sleep(0.5)
            except KeyboardInterrupt:
                pass 