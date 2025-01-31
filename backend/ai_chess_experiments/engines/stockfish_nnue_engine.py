from typing import Optional, Tuple, cast, Any, Dict, ClassVar
import chess
import chess.engine
import asyncio
import os
from pathlib import Path
from .base_engine import BaseChessEngine

class StockfishNNUEEngine(BaseChessEngine):
    """Chess engine using Stockfish with NNUE evaluation.
    
    The Stockfish NNUE engine combines traditional alpha-beta search with an efficiently
    updatable neural network for position evaluation. This creates a powerful hybrid
    that maintains the tactical strength of classical engines while adding sophisticated
    positional understanding.
    
    Key Components:
    1. NNUE (Efficiently Updatable Neural Network):
       - A specialized neural network architecture that can be incrementally updated
       - Input features are based on piece positions and relationships
       - Hidden layers capture complex positional patterns
       - Output provides a refined evaluation score
    
    2. Alpha-Beta Search:
       - Depth-first tree search examining possible moves and responses
       - Pruning of branches that cannot affect the final decision
       - Typically searches 20-30 ply deep in middlegame positions
    
    3. Advanced Search Techniques:
       - Null Move Pruning: Skip moves to prove positions are already good/bad
       - Late Move Reduction: Search less promising moves with reduced depth
       - Futility Pruning: Skip moves unlikely to improve position
       - Multi-PV: Consider multiple promising variations
    
    4. Move Ordering Optimizations:
       - Hash Move: Best move from previous searches
       - Killer Moves: Good moves found at same depth
       - Counter Moves: Moves that historically refute opponent moves
       - History Heuristics: Statistical tracking of move strength
    
    The engine uses these components together to:
    1. Generate all legal moves in a position
    2. Order moves by likelihood of being best
    3. Search deeply along promising variations
    4. Evaluate positions using the NNUE network
    5. Back up scores through the game tree
    6. Select the move leading to best evaluated position
    
    Strengths:
    - Extremely strong tactical and positional play
    - Efficient evaluation of positions
    - Strong endgame play with tablebase support
    
    Weaknesses:
    - High computational requirements
    - Complex configuration needed for optimal performance
    """
    
    # Class-level constants for level configuration
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
    
    def __init__(self, level: Optional[int] = None):
        """Initialize the Stockfish NNUE engine.
        
        Args:
            level: Search depth in plies (1-30). Higher values give stronger
                  but slower play. Default is 20.
        """
        super().__init__(level)
        self.engine: Optional[chess.engine.Protocol] = None
        self.transport: Optional[asyncio.SubprocessTransport] = None
        
        # Path to Stockfish executable - you'll need to download this separately
        stockfish_path = Path(__file__).parent.parent.parent / "engines" / "stockfish"
        if not stockfish_path.exists():
            raise FileNotFoundError(f"Stockfish executable not found at {stockfish_path}")
        self.engine_path = str(stockfish_path)

    async def initialize(self):
        """Initialize the Stockfish engine with NNUE evaluation"""
        if self.engine is None:
            transport, engine = await chess.engine.popen_uci(self.engine_path)
            self.transport = transport
            self.engine = engine
            
            # Enable NNUE evaluation
            if self.engine:
                await self.engine.configure({"Use NNUE": True})
            
    async def get_move(self, board: chess.Board) -> Tuple[chess.Move, float]:
        """Get the best move and evaluation from Stockfish NNUE.
        
        The evaluation process:
        1. Search game tree to specified depth
        2. Use NNUE network to evaluate leaf positions
        3. Back up scores through alpha-beta search
        4. Return best move and evaluation
        
        Args:
            board: Current chess position to evaluate
            
        Returns:
            Tuple containing:
            - The best move found
            - Position evaluation in pawns (positive for white, negative for black)
              Typical range is -5 to 5, with larger values indicating decisive advantage
        
        Raises:
            RuntimeError: If engine fails to initialize or find a move
        """
        if self.engine is None:
            await self.initialize()
            
        if not self.engine:
            raise RuntimeError("Failed to initialize Stockfish engine")
            
        # Get the move from the engine using configured depth
        result = await self.engine.play(
            board,
            chess.engine.Limit(depth=self.level),
            info=chess.engine.INFO_SCORE
        )
        
        # Get evaluation in centipawns
        if result.move is None:
            raise RuntimeError("Stockfish failed to return a move")
            
        score_value = 0.0
        if "score" in result.info:
            score = result.info["score"].relative
            if score.is_mate():
                # Handle mate scores
                mate_score = score.mate()
                score_value = 100.0 if mate_score and mate_score > 0 else -100.0
            else:
                # Regular evaluation in centipawns
                cp_score = score.score()
                if cp_score is not None:
                    score_value = float(cp_score) / 100.0
            
        return result.move, score_value
        
    async def cleanup(self):
        """Clean up engine resources"""
        if self.engine:
            await self.engine.quit()
            self.engine = None
        if self.transport:
            self.transport = None 