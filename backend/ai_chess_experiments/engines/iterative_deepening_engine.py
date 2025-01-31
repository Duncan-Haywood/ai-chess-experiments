import chess
import time
from typing import Optional, Tuple
from .base_engine import BaseChessEngine
from .heuristics import evaluate_position

class IterativeDeepeningEngine(BaseChessEngine):
    """Chess engine using Iterative Deepening with alpha-beta pruning.
    This engine starts with shallow searches and progressively increases depth,
    allowing it to play reasonable moves even if interrupted."""
    
    def __init__(self, max_depth: int = 4, time_limit: float = 1.0):
        """Initialize the Iterative Deepening engine.
        
        Args:
            max_depth: Maximum search depth
            time_limit: Time limit in seconds
        """
        super().__init__()
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.start_time = 0.0
        self.nodes = 0
        
    def get_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Get the best move using iterative deepening."""
        self.board = board.copy()
        if self.board.is_game_over():
            return None
            
        self.start_time = time.time()
        self.nodes = 0
        best_move = None
        
        # Start with depth 1 and increase until max_depth or time limit
        for current_depth in range(1, self.max_depth + 1):
            if time.time() - self.start_time >= self.time_limit:
                break
                
            value, move = self._alphabeta_root(current_depth)
            if move is not None:
                best_move = move
                
        return best_move
    
    def _alphabeta_root(self, depth: int) -> Tuple[float, Optional[chess.Move]]:
        """Alpha-beta search at root node to find best move.
        
        Args:
            depth: Current search depth
            
        Returns:
            Tuple of (evaluation, best_move)
        """
        best_move = None
        best_value = float('-inf')
        alpha = float('-inf')
        beta = float('inf')
        
        for move in self.board.legal_moves:
            if time.time() - self.start_time >= self.time_limit:
                break
                
            self.board.push(move)
            value = -self._alphabeta(depth - 1, -beta, -alpha)
            self.board.pop()
            
            if value > best_value:
                best_value = value
                best_move = move
            alpha = max(alpha, value)
            
        return best_value, best_move
    
    def _alphabeta(self, depth: int, alpha: float, beta: float) -> float:
        """Alpha-beta pruning search.
        
        Args:
            depth: Remaining search depth
            alpha: Alpha value for pruning
            beta: Beta value for pruning
            
        Returns:
            float: Position evaluation
        """
        self.nodes += 1
        
        if depth == 0 or self.board.is_game_over() or \
           time.time() - self.start_time >= self.time_limit:
            return evaluate_position(self.board) * (1 if self.board.turn else -1)
        
        value = float('-inf')
        for move in self.board.legal_moves:
            self.board.push(move)
            value = max(value, -self._alphabeta(depth - 1, -beta, -alpha))
            self.board.pop()
            
            alpha = max(alpha, value)
            if alpha >= beta:
                break
                
        return value
        
    def cleanup(self) -> None:
        """No cleanup needed for Iterative Deepening engine."""
        pass 