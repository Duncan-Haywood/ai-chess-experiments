import random
import chess
from .base_engine import BaseChessEngine

class RandomEngine(BaseChessEngine):
    """A simple engine that plays random legal moves.
    
    This serves as an example implementation of the BaseChessEngine
    and can be used as a baseline for comparing other engines.
    """
    
    def get_move(self) -> chess.Move:
        """Choose a random legal move.
        
        Returns:
            chess.Move: A randomly selected legal move
        """
        legal_moves = self.get_legal_moves()
        if not legal_moves:
            raise ValueError("No legal moves available")
        return random.choice(legal_moves) 