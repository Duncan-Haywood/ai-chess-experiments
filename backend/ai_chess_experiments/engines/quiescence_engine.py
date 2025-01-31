import chess
from typing import Optional, List
from .base_engine import BaseChessEngine
from .heuristics import evaluate_position, PIECE_VALUES

class QuiescenceEngine(BaseChessEngine):
    """Chess engine using alpha-beta pruning with quiescence search.
    This engine continues searching captures and checks beyond the normal
    search depth to avoid the horizon effect."""
    
    def __init__(self, depth: int = 3, q_depth: int = 5):
        """Initialize the Quiescence engine.
        
        Args:
            depth: Maximum regular search depth
            q_depth: Maximum additional quiescence search depth
        """
        super().__init__()
        self.depth = depth
        self.q_depth = q_depth
        self.nodes = 0
    
    def get_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Get the best move using alpha-beta with quiescence search."""
        self.board = board.copy()
        if self.board.is_game_over():
            return None
            
        self.nodes = 0
        best_move = None
        best_value = float('-inf')
        alpha = float('-inf')
        beta = float('inf')
        
        for move in self.board.legal_moves:
            self.board.push(move)
            value = -self._alphabeta(self.depth - 1, -beta, -alpha)
            self.board.pop()
            
            if value > best_value:
                best_value = value
                best_move = move
            alpha = max(alpha, value)
            
        return best_move
    
    def _is_capture(self, move: chess.Move) -> bool:
        """Check if a move is a capture or promotion."""
        return self.board.is_capture(move) or move.promotion is not None
    
    def _move_value(self, move: chess.Move) -> int:
        """Calculate a heuristic value for move ordering."""
        if move.promotion is not None:
            return 10000  # Prioritize promotions
            
        if self.board.is_capture(move):
            victim = self.board.piece_at(move.to_square)
            attacker = self.board.piece_at(move.from_square)
            if victim is not None and attacker is not None:
                victim_value = PIECE_VALUES[victim.piece_type]
                attacker_value = PIECE_VALUES[attacker.piece_type]
                return victim_value - attacker_value + 1000  # Prioritize captures
            
        if self.board.gives_check(move):
            return 500  # Then checks
            
        return 0
    
    def _order_moves(self, moves: List[chess.Move]) -> List[chess.Move]:
        """Order moves for better alpha-beta pruning."""
        return sorted(moves, key=self._move_value, reverse=True)
    
    def _alphabeta(self, depth: int, alpha: float, beta: float) -> float:
        """Alpha-beta pruning search with quiescence.
        
        Args:
            depth: Remaining search depth
            alpha: Alpha value for pruning
            beta: Beta value for pruning
            
        Returns:
            float: Position evaluation
        """
        self.nodes += 1
        
        if self.board.is_game_over():
            return evaluate_position(self.board) * (1 if self.board.turn else -1)
            
        if depth <= 0:
            return self._quiescence(alpha, beta, self.q_depth)
        
        value = float('-inf')
        moves = list(self.board.legal_moves)
        ordered_moves = self._order_moves(moves)
        
        for move in ordered_moves:
            self.board.push(move)
            value = max(value, -self._alphabeta(depth - 1, -beta, -alpha))
            self.board.pop()
            
            alpha = max(alpha, value)
            if alpha >= beta:
                break
                
        return value
    
    def _quiescence(self, alpha: float, beta: float, depth: int) -> float:
        """Quiescence search to evaluate only quiet positions.
        
        Args:
            alpha: Alpha value for pruning
            beta: Beta value for pruning
            depth: Maximum remaining quiescence depth
            
        Returns:
            float: Position evaluation
        """
        self.nodes += 1
        
        # Stand-pat score
        stand_pat = evaluate_position(self.board) * (1 if self.board.turn else -1)
        
        if depth <= 0:
            return stand_pat
            
        # Beta cutoff
        if stand_pat >= beta:
            return beta
            
        # Delta pruning
        if stand_pat < alpha - 900:  # Queen value
            return alpha
            
        alpha = max(alpha, stand_pat)
        
        # Only look at captures and checks
        moves = [move for move in self.board.legal_moves if self._is_capture(move) or self.board.gives_check(move)]
        ordered_moves = self._order_moves(moves)
        
        for move in ordered_moves:
            self.board.push(move)
            score = -self._quiescence(-beta, -alpha, depth - 1)
            self.board.pop()
            
            if score >= beta:
                return beta
            alpha = max(alpha, score)
            
        return alpha
        
    def cleanup(self) -> None:
        """No cleanup needed for Quiescence engine."""
        pass 