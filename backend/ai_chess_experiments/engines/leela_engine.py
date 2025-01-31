import chess
import chess.engine
import shutil
from typing import Optional, Tuple, Dict, Any, cast
from pathlib import Path
from .base_engine import BaseChessEngine

class LeelaEngine(BaseChessEngine):
    """Leela Chess Zero engine implementation."""
    
    @classmethod
    def get_engine_info(cls) -> Dict[str, Any]:
        """Get information about the engine's capabilities and settings."""
        return {
            "type": "depth",
            "min": 1,
            "max": 30,
            "default": 20,
            "description": "Search depth in nodes (multiplied by 1000)",
            "step": 1
        }
    
    def __init__(self, depth: Optional[int] = None):
        """Initialize Leela Chess Zero engine.
        
        Args:
            depth: Search depth (will be multiplied by 1000 for node count)
        """
        super().__init__(depth)
        self.engine: Optional[chess.engine.SimpleEngine] = None
        self._initialize_engine()
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if Leela Chess Zero is available on the system."""
        return shutil.which("lc0") is not None
    
    def _initialize_engine(self) -> None:
        """Initialize the Leela Chess Zero engine process."""
        try:
            lc0_path = shutil.which("lc0")
            if not lc0_path:
                raise RuntimeError("Leela Chess Zero (lc0) not found in system PATH")
            self.engine = chess.engine.SimpleEngine.popen_uci(lc0_path)
            
            # Configure Leela-specific options
            if self.engine:
                self.engine.configure({
                    "Threads": 4,  # Number of CPU threads to use
                    "MinibatchSize": 256,  # Neural network batch size
                    "Backend": "blas",  # Use BLAS for neural network computations
                    "NNCacheSize": 200000,  # Neural network cache size in bytes
                })
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Leela Chess Zero engine: {str(e)}")
    
    async def _get_move_impl(self, board: chess.Board) -> Tuple[chess.Move, float]:
        """Get the best move from Leela for the given position."""
        if not self.engine:
            raise RuntimeError("Engine not initialized")
        
        try:
            # Convert depth to node count (depth * 1000)
            nodes = self.level * 1000
            
            # Get move with node limit
            result = self.engine.play(board, chess.engine.Limit(nodes=nodes))
            if not result.move:
                raise RuntimeError("Leela failed to return a move")
            
            # Get evaluation score
            info = self.engine.analyse(board, chess.engine.Limit(nodes=nodes))
            score = 0.0
            if "score" in info:
                score_obj = cast(chess.engine.PovScore, info["score"])
                mate_score = score_obj.relative.mate()
                if mate_score is not None:
                    # Convert mate score to pawns (positive or negative based on if we're winning or losing)
                    score = 10000.0 if mate_score > 0 else -10000.0
                else:
                    # Regular centipawn score
                    cp_score = score_obj.relative.score()
                    score = float(cp_score) / 100.0 if cp_score is not None else 0.0
            
            return result.move, score
        except Exception as e:
            raise RuntimeError(f"Failed to get move from Leela: {str(e)}")
    
    async def get_move(self, board: chess.Board) -> Tuple[chess.Move, float]:
        """Get the best move for the current position.
        
        Args:
            board: The current board position
            
        Returns:
            Tuple of (chosen move, evaluation score)
        """
        return await super().get_move(board)
    
    async def cleanup(self) -> None:
        """Clean up the Leela Chess Zero engine process."""
        if self.engine:
            try:
                self.engine.quit()
            except Exception as e:
                print(f"Error cleaning up Leela engine: {e}")
            finally:
                self.engine = None 