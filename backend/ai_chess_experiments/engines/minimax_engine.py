import chess
from .base_engine import BaseChessEngine
from typing import Tuple

class MinimaxEngine(BaseChessEngine):
    """A chess engine using minimax search with alpha-beta pruning.
    
    This engine uses standard chess heuristics:
    - Material counting
    - Piece-square tables for positional evaluation
    - Alpha-beta pruning for faster search
    """
    
    # Standard piece values
    PIECE_VALUES = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000
    }
    
    # Simple piece-square tables for middlegame
    PAWN_TABLE = [
        0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5,  5, 10, 25, 25, 10,  5,  5,
        0,  0,  0, 20, 20,  0,  0,  0,
        5, -5,-10,  0,  0,-10, -5,  5,
        5, 10, 10,-20,-20, 10, 10,  5,
        0,  0,  0,  0,  0,  0,  0,  0
    ]
    
    def __init__(self, depth: int = 3):
        super().__init__()
        self.depth = depth
    
    def evaluate_position(self) -> float:
        """Evaluate the current position from white's perspective."""
        if self.board.is_checkmate():
            return -20000 if self.board.turn else 20000
        
        score = 0
        
        # Material counting
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece is None:
                continue
            
            value = self.PIECE_VALUES[piece.piece_type]
            if piece.color == chess.BLACK:
                value = -value
            
            # Add positional bonus for pawns
            if piece.piece_type == chess.PAWN:
                pos_value = self.PAWN_TABLE[square if piece.color else chess.square_mirror(square)]
                value += pos_value if piece.color == chess.WHITE else -pos_value
            
            score += value
        
        return score
    
    def minimax(self, depth: int, alpha: float, beta: float, maximizing: bool) -> Tuple[float, chess.Move]:
        """Minimax algorithm with alpha-beta pruning."""
        if depth == 0 or self.board.is_game_over():
            return self.evaluate_position(), None
        
        best_move = None
        if maximizing:
            max_eval = float('-inf')
            for move in self.board.legal_moves:
                self.board.push(move)
                eval_score, _ = self.minimax(depth - 1, alpha, beta, False)
                self.board.pop()
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in self.board.legal_moves:
                self.board.push(move)
                eval_score, _ = self.minimax(depth - 1, alpha, beta, True)
                self.board.pop()
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move
    
    def get_move(self) -> chess.Move:
        """Calculate the best move using minimax with alpha-beta pruning."""
        _, best_move = self.minimax(
            self.depth,
            float('-inf'),
            float('inf'),
            self.board.turn == chess.WHITE
        )
        return best_move 