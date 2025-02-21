from typing import Optional, Tuple, Any, Dict, ClassVar
import chess
import chess.engine
import asyncio
import os
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .base_engine import BaseChessEngine

class StockfishNNUEEngine(BaseChessEngine):
    """Chess engine using Stockfish with NNUE evaluation.
    
    Combines alpha-beta search with neural network evaluation:
    - NNUE for efficient position evaluation
    - Alpha-beta search with advanced pruning
    - Strong tactical and positional play
    - Configurable search depth (1-30)
    """
    
    MIN_DEPTH: ClassVar[int] = 1
    MAX_DEPTH: ClassVar[int] = 30
    DEFAULT_DEPTH: ClassVar[int] = 20
    
    @classmethod
    def get_level_info(cls) -> Dict[str, Any]:
        """Get information about Stockfish's depth settings.
        
        Stockfish uses depth-based levels, where higher depth means stronger but slower play.
        Typical ranges:
        - 1-5: Very fast but weak play
        - 6-10: Quick analysis, good for casual games
        - 11-15: Moderate strength, good balance
        - 16-20: Strong play, tournament time controls
        - 21-30: Very strong but slow analysis
        """
        return {
            'type': 'depth',
            'min': cls.MIN_DEPTH,
            'max': cls.MAX_DEPTH,
            'default': cls.DEFAULT_DEPTH,
            'step': 1,
            'description': (
                'Search depth in plies (half-moves). Higher values mean stronger but '
                'slower play. Values 1-5 are very fast but weak, 6-15 good for casual '
                'play, 16-20 for serious games, 21-30 for deep analysis.'
            )
        }
    
    @classmethod
    def get_engine_info(cls) -> Dict[str, Any]:
        return {
            "name": "Stockfish NNUE",
            "version": "16",
            "author": "The Stockfish Team",
            "min_level": cls.MIN_DEPTH,
            "max_level": cls.MAX_DEPTH,
            "default_level": cls.DEFAULT_DEPTH
        }

    def __init__(self, level: Optional[int] = None):
        super().__init__(level)
        self.engine = self.transport = None
        self.depth = min(max(level or self.DEFAULT_DEPTH, self.MIN_DEPTH), self.MAX_DEPTH)
        
        stockfish_path = Path(__file__).parent.parent.parent / "engines" / "stockfish"
        if not stockfish_path.exists():
            raise FileNotFoundError(f"Stockfish not found at {stockfish_path}")
        self.engine_path = str(stockfish_path)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((chess.engine.EngineError, TimeoutError, ConnectionError))
    )
    async def initialize(self):
        """Initialize Stockfish with retry on failures."""
        try:
            self.transport, self.engine = await chess.engine.popen_uci(self.engine_path)
            await self.engine.configure({
                "Hash": 128,
                "Threads": os.cpu_count() or 1,
                "UCI_LimitStrength": True,
                "UCI_Elo": 1500 + (self.depth * 100)
            })
        except Exception as e:
            if self.transport:
                self.transport.close()
            raise chess.engine.EngineError(f"Failed to initialize Stockfish: {e}")

    async def get_move(self, board: chess.Board) -> Tuple[chess.Move, float]:
        """Get best move and evaluation from Stockfish."""
        if not self.engine:
            await self.initialize()
            if not self.engine:
                raise RuntimeError("Failed to initialize Stockfish")
            
        result = await self.engine.play(
            board,
            chess.engine.Limit(depth=self.level),
            info=chess.engine.INFO_SCORE
        )
        
        if not result.move:
            raise RuntimeError("Stockfish failed to return a move")
            
        score = result.info.get("score", chess.engine.Score(None)).relative
        score_value = (
            (100.0 if score.mate() > 0 else -100.0)
            if score.is_mate()
            else float(score.score() or 0) / 100.0
        )
            
        return result.move, score_value
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((chess.engine.EngineError, TimeoutError, ConnectionError))
    )
    async def cleanup(self):
        """Clean up engine resources with retry."""
        try:
            if self.engine:
                await self.engine.quit()
        finally:
            if self.transport:
                self.transport.close()
            self.engine = self.transport = None 