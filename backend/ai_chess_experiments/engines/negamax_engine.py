import chess
from typing import Optional, Tuple
from .base_engine import BaseChessEngine
from .heuristics import evaluate_position

class NegamaxEngine(BaseChessEngine):
    """Chess engine using the Negamax algorithm with alpha-beta pruning.
    Negamax is a variant of minimax that relies on the zero-sum property of chess:
    max(a,b) = -min(-a,-b). This allows for a more elegant implementation."""
    
    def __init__(self, depth: int = 3):
        """Initialize the Negamax engine.
        
        Args:
            depth: Maximum search depth
        """
        super().__init__()
        self.depth = depth
        self.nodes = 0  # Add node counter
        
    def get_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Get the best move using negamax with alpha-beta pruning."""
        self.board = board.copy()
        if self.board.is_game_over():
            return None
            
        self.nodes = 0  # Reset node counter
        best_move = None
        best_value = float('-inf')
        alpha = float('-inf')
        beta = float('inf')
        
        for move in self.board.legal_moves:
            self.board.push(move)
            value = -self._negamax(self.depth - 1, -beta, -alpha)
            self.board.pop()
            
            if value > best_value:
                best_value = value
                best_move = move
                
            alpha = max(alpha, value)
            
        return best_move
    
    def _negamax(self, depth: int, alpha: float, beta: float) -> float:
        """Negamax algorithm with alpha-beta pruning.
        
        Args:
            depth: Remaining search depth
            alpha: Alpha value for pruning
            beta: Beta value for pruning
            
        Returns:
            float: Position evaluation from current player's perspective
        """
        self.nodes += 1  # Increment node counter
        
        if depth == 0 or self.board.is_game_over():
            # Negate if it's black's turn since evaluate_position is from white's perspective
            return evaluate_position(self.board) * (1 if self.board.turn else -1)
        
        value = float('-inf')
        for move in self.board.legal_moves:
            self.board.push(move)
            value = max(value, -self._negamax(depth - 1, -beta, -alpha))
            self.board.pop()
            
            alpha = max(alpha, value)
            if alpha >= beta:
                break
                
        return value
        
    def cleanup(self) -> None:
        """No cleanup needed for Negamax engine."""
        pass 