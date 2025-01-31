from typing import Optional, Tuple, cast, Any, Dict, ClassVar
import chess
import chess.engine
import asyncio
import os
from pathlib import Path
from .base_engine import BaseChessEngine

class MaiaEngine(BaseChessEngine):
    """Chess engine using the Maia neural network model.
    
    Maia is a family of neural network chess engines designed to play like humans
    at specific rating levels. Unlike traditional engines that try to play the
    objectively best moves, Maia aims to make human-like decisions and mistakes.
    
    Key Components:
    1. Neural Network Architecture:
       - Based on AlphaZero/Leela Chess Zero design
       - Deep residual network with many layers
       - Trained on millions of human chess games
       - Separate models for different rating levels (1100, 1500, 1900)
    
    2. Policy Network:
       - Predicts probability distribution over possible moves
       - Trained to mimic human move choices
       - Captures typical human patterns and biases
       - More likely to make human-like tactical oversights
    
    3. Value Network:
       - Evaluates positions from a human perspective
       - Less accurate than traditional engines
       - May miss complex tactical sequences
       - Reflects human understanding of positions
    
    4. Rating-Targeted Training:
       - Each model trained on games from specific rating band
       - Learns characteristic mistakes of that level
       - Maintains consistent playing strength
       - Useful for training and practice
    
    The engine works by:
    1. Processing the board position through the neural network
    2. Generating move probabilities from the policy head
    3. Evaluating position value from the value head
    4. Selecting moves that reflect human playing patterns
    
    Strengths:
    - Human-like play style
    - Consistent strength at specific rating levels
    - Makes instructive mistakes similar to humans
    - Good for training and learning
    
    Weaknesses:
    - Not optimized for maximum playing strength
    - Can make human-like blunders
    - Limited to learned patterns
    - May miss complex tactical opportunities
    """
    
    # Available Maia models and their corresponding ELO ratings
    RATING_LEVELS: ClassVar[Dict[int, str]] = {
        1100: "maia-1100",
        1500: "maia-1500",
        1900: "maia-1900"
    }
    
    DEFAULT_RATING: ClassVar[int] = 1500
    
    @classmethod
    def get_level_info(cls) -> Dict[str, Any]:
        """Get information about Maia's rating-based levels.
        
        Maia uses ELO rating-based levels, where each level corresponds to a model
        trained on games from players at that rating level. This makes it play in
        a style similar to human players of that strength.
        
        Available models:
        - 1100: Plays like a beginner/novice player
        - 1500: Plays like an intermediate club player
        - 1900: Plays like a strong club player
        """
        return {
            'type': 'elo',
            'min': min(cls.RATING_LEVELS.keys()),
            'max': max(cls.RATING_LEVELS.keys()),
            'default': cls.DEFAULT_RATING,
            'valid_levels': list(cls.RATING_LEVELS.keys()),
            'description': (
                'ELO rating level that the engine plays at. Each level represents a '
                'model trained on human games at that rating. 1100 plays like a '
                'beginner, 1500 like an intermediate player, and 1900 like a strong '
                'club player.'
            )
        }
    
    def __init__(self, level: Optional[int] = None):
        """Initialize Maia engine with specified rating level.
        
        Args:
            level: ELO rating level to play at. Must be one of: 1100, 1500, or 1900.
                  Default is 1500 (intermediate level).
        """
        super().__init__(level)
        
        # Validate and get model name for the selected rating
        if self.level not in self.RATING_LEVELS:
            valid_levels = ', '.join(map(str, sorted(self.RATING_LEVELS.keys())))
            raise ValueError(
                f"Invalid Maia rating level: {self.level}. "
                f"Must be one of: {valid_levels}"
            )
        
        self.model_name = self.RATING_LEVELS[self.level]
        self.engine: Optional[chess.engine.Protocol] = None
        self.transport: Optional[asyncio.SubprocessTransport] = None
        
        # Path to Maia executable - you'll need to download this separately
        maia_path = Path(__file__).parent.parent.parent / "engines" / self.model_name
        if not maia_path.exists():
            raise FileNotFoundError(f"Maia model not found at {maia_path}")
        self.engine_path = str(maia_path)

    async def initialize(self):
        """Initialize the Maia engine with the selected model"""
        if self.engine is None:
            transport, engine = await chess.engine.popen_uci(self.engine_path)
            self.transport = transport
            self.engine = engine
            
    async def get_move(self, board: chess.Board) -> Tuple[chess.Move, float]:
        """Get move and evaluation from Maia.
        
        The move selection process:
        1. Process position through neural network
        2. Generate probability distribution over moves
        3. Sample from distribution to select move
        4. Calculate confidence score based on move probability
        
        Note: Maia's evaluation is based on move probability rather than traditional
        positional evaluation. A higher score indicates the engine is more confident
        in its move choice, not necessarily that the position is better.
        
        Args:
            board: Current chess position to evaluate
            
        Returns:
            Tuple containing:
            - The selected move
            - Confidence score (-1 to 1, higher means more confident)
        
        Raises:
            RuntimeError: If engine fails to initialize or find a move
        """
        if self.engine is None:
            await self.initialize()
            
        if not self.engine:
            raise RuntimeError("Failed to initialize Maia engine")
            
        # Use a moderate time limit since Maia is primarily probability-based
        result = await self.engine.play(
            board,
            chess.engine.Limit(time=0.1),
            info=chess.engine.INFO_ALL
        )
        
        if result.move is None:
            raise RuntimeError("Maia failed to return a move")
            
        # Maia's evaluation is based on move probability
        # Higher probability (closer to 1.0) means Maia is more confident in the move
        score_value = 0.0
        
        # Try to get move probability from info
        if "score" in result.info:
            score = result.info["score"].relative
            if score.is_mate():
                # Handle mate scores
                mate_score = score.mate()
                score_value = 100.0 if mate_score and mate_score > 0 else -100.0
            else:
                # Use CP score if available, otherwise fallback to material count
                cp_score = score.score()
                if cp_score is not None:
                    score_value = float(cp_score) / 100.0
                else:
                    # Fallback to material count
                    score_value = len(board.piece_map()) * 0.1
            
        return result.move, score_value
        
    async def cleanup(self):
        """Clean up engine resources"""
        if self.engine:
            await self.engine.quit()
            self.engine = None
        if self.transport:
            self.transport = None 