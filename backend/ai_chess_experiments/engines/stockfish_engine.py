import chess
import chess.engine
from pathlib import Path
import shutil
from typing import Optional, Tuple, Dict, Any, cast
from .base_engine import BaseChessEngine

class StockfishEngine(BaseChessEngine):
    """Stockfish chess engine implementation."""
    
    @classmethod
    def get_engine_info(cls) -> Dict[str, Any]:
        """Get information about the engine's capabilities and settings."""
        return {
            "type": "depth",
            "min": 1,
            "max": 30,
            "default": 20,
            "description": "Search depth in plies",
            "step": 1
        }
    
    def __init__(self, depth: Optional[int] = None):
        """Initialize Stockfish engine.
        
        Args:
            depth: Search depth for the engine
        """
        super().__init__(depth)
        self.engine: Optional[chess.engine.SimpleEngine] = None
        self._initialize_engine()
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if Stockfish is available on the system."""
        return shutil.which("stockfish") is not None
    
    def _initialize_engine(self) -> None:
        """Initialize the Stockfish engine process."""
        try:
            stockfish_path = shutil.which("stockfish")
            if not stockfish_path:
                raise RuntimeError("Stockfish not found in system PATH")
            self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Stockfish engine: {str(e)}")
    
    async def _get_move_impl(self, board: chess.Board) -> Tuple[chess.Move, float]:
        """Get the best move from Stockfish for the given position."""
        if not self.engine:
            raise RuntimeError("Engine not initialized")
        
        try:
            result = self.engine.play(board, chess.engine.Limit(depth=self.level))
            if not result.move:
                raise RuntimeError("Stockfish failed to return a move")
            
            # Get evaluation score
            info = self.engine.analyse(board, chess.engine.Limit(depth=self.level))
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
            raise RuntimeError(f"Failed to get move from Stockfish: {str(e)}")
    
    async def cleanup(self) -> None:
        """Clean up the Stockfish engine process."""
        if self.engine:
            try:
                self.engine.quit()
            except Exception as e:
                print(f"Error cleaning up Stockfish engine: {e}")
            finally:
                self.engine = None 

    async def get_move(self, board: chess.Board) -> Tuple[chess.Move, float]:
        """Get the best move for the current position.
        
        Args:
            board: The current board position
            
        Returns:
            Tuple of (chosen move, evaluation score)
        """
        return await super().get_move(board) 