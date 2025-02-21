from abc import ABC, abstractmethod
import chess
import time
from typing import Optional, Tuple, Any, Dict, TypedDict
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class EngineMetrics(TypedDict):
    nodes_searched: int
    depth_reached: int
    time_taken: float
    memory_used: int
    cpu_percent: float

class BaseChessEngine(ABC):
    """Base class for all chess engines.
    
    This abstract class defines the interface that all chess engines must implement.
    Different AI approaches (rule-based, ML, etc.) should inherit from this class.
    """
    
    @classmethod
    @abstractmethod
    def get_engine_info(cls) -> Dict[str, Any]:
        """Get information about the engine's capabilities and settings.
        
        Returns:
            Dictionary containing:
            - type: str - Type of level ('depth', 'elo', 'time', etc.)
            - min: int - Minimum level value
            - max: int - Maximum level value
            - default: int - Default level value
            - description: str - Description of what levels mean for this engine
            - step: int - Step size between valid levels (optional)
        """
        pass
    
    def __init__(self, level: Optional[int] = None):
        """Initialize the engine.
        
        Args:
            level: Engine strength/depth level. If None, uses engine's default.
        """
        self.board = chess.Board()
        info = self.get_engine_info()
        self.level = level if level is not None else info['default']
        
        # Initialize metrics
        self.nodes_searched = self.current_depth = self.move_count = 0
        self.last_move_time = self.total_time = 0.0
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if the engine is available on the system."""
        return True  # Default implementation returns True
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((chess.engine.EngineError, TimeoutError, ConnectionError)),
        reraise=True
    )
    async def get_move(self, board: chess.Board) -> Tuple[chess.Move, float]:
        """Get the next move and evaluation score for the given board position.
        
        This method is wrapped with retry logic to handle transient failures:
        - Retries up to 3 times
        - Uses exponential backoff between retries (4-10 seconds)
        - Only retries on specific engine-related errors
        
        Args:
            board: The current chess board position
            
        Returns:
            A tuple containing:
            - The chosen move
            - The evaluation score (positive for white advantage, negative for black)
            
        Raises:
            Exception: If move generation fails after all retries
        """
        self.board = board.copy()
        
        # Reset metrics for new move calculation
        self.nodes_searched = self.current_depth = 0
        start_time = time.time()
        
        try:
            result = await self._get_move_impl(board)
            self.last_move_time = time.time() - start_time
            self.total_time += self.last_move_time
            self.move_count += 1
            return result
        except Exception as e:
            self.last_move_time = time.time() - start_time
            self.total_time += self.last_move_time
            raise e
    
    @abstractmethod
    async def _get_move_impl(self, board: chess.Board) -> Tuple[chess.Move, float]:
        """Implementation of get_move that should be overridden by subclasses."""
        pass
    
    def get_metrics(self) -> EngineMetrics:
        """Get the current engine metrics."""
        return {
            "nodes_searched": self.nodes_searched,
            "depth_reached": self.current_depth,
            "time_taken": self.total_time,
            "memory_used": 0,  # This is tracked at the process level
            "cpu_percent": 0.0  # This is tracked at the process level
        }
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up any resources used by the engine asynchronously.
        
        This method should handle any cleanup that requires async operations.
        It should call sync_cleanup() to ensure all resources are properly cleaned up.
        """
        self.sync_cleanup()

    @abstractmethod
    def sync_cleanup(self) -> None:
        """Synchronous cleanup for use in __del__ and cleanup().
        
        This method should handle any cleanup that can be done synchronously.
        All engine implementations must override this to properly clean up their resources.
        """
        pass
    
    def __del__(self):
        """Ensure synchronous cleanup is called when the object is destroyed."""
        try:
            self.sync_cleanup()
        except:
            pass
    
    def update_board(self, move: chess.Move):
        """Update the internal board state with a move.
        
        Args:
            move: The move to apply to the board
        """
        self.board.push(move)
    
    def set_position(self, fen: str):
        """Set the board to a specific position.
        
        Args:
            fen: The FEN string representing the position
        """
        self.board.set_fen(fen)
    
    def get_legal_moves(self):
        """Get all legal moves in the current position."""
        return list(self.board.legal_moves)
    
    def is_game_over(self) -> bool:
        """Check if the game is over."""
        return self.board.is_game_over()
    
    def get_board_state(self) -> chess.Board:
        """Get the current board state."""
        return self.board.copy()

    def get_level_info(self) -> dict:
        """Get information about the engine's current level/strength."""
        return {
            "depth": self.level,
            "name": self.__class__.__name__,
            "description": "Base chess engine implementation"
        } 