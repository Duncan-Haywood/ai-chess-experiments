import chess
import random
from typing import Optional, Tuple
from .base_engine import BaseChessEngine
from .heuristics import evaluate_position

class MinimaxEngine(BaseChessEngine):
    """A simple minimax chess engine."""

    @classmethod
    def get_engine_info(cls):
        """Get information about the engine's capabilities and settings."""
        return {
            "type": "depth",
            "min": 1,
            "max": 20,
            "default": 3,
            "description": "Search depth in plies",
            "step": 1
        }

    def __init__(self, level: Optional[int] = None):
        """Initialize the minimax engine.
        
        Args:
            level: Search depth in plies. If None, uses default depth.
        """
        super().__init__(level)
        self.piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }

    async def cleanup(self) -> None:
        """Clean up resources."""
        pass  # No cleanup needed for minimax engine

    def evaluate_position(self, board: chess.Board) -> float:
        """Evaluate the current position.
        
        Args:
            board: The board position to evaluate
            
        Returns:
            Score for the position (positive for white advantage)
        """
        if board.is_checkmate():
            return -20000 if board.turn else 20000
        
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
        
        score = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is not None:
                value = self.piece_values[piece.piece_type]
                if piece.color == chess.WHITE:
                    score += value
                else:
                    score -= value
        
        return score

    async def minimax(self, board: chess.Board, depth: int, alpha: float = float('-inf'), beta: float = float('inf'), maximizing: bool = True) -> Tuple[Optional[chess.Move], float]:
        """Minimax algorithm with alpha-beta pruning.
        
        Args:
            board: Current board position
            depth: Remaining search depth
            alpha: Alpha value for pruning
            beta: Beta value for pruning
            maximizing: Whether to maximize or minimize score
            
        Returns:
            Tuple of (best move, evaluation score)
        """
        # Update metrics
        self.nodes_searched += 1
        self.current_depth = max(self.current_depth, self.level - depth)
        
        if depth == 0 or board.is_game_over():
            return None, self.evaluate_position(board)
        
        best_move = None
        if maximizing:
            max_eval = float('-inf')
            for move in board.legal_moves:
                board.push(move)
                _, eval_score = await self.minimax(board, depth - 1, alpha, beta, False)
                board.pop()
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            
            return best_move, max_eval
        else:
            min_eval = float('inf')
            for move in board.legal_moves:
                board.push(move)
                _, eval_score = await self.minimax(board, depth - 1, alpha, beta, True)
                board.pop()
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            return best_move, min_eval

    async def get_move(self, board: chess.Board) -> Tuple[chess.Move, float]:
        """Get the best move for the current position.
        
        Args:
            board: The current board position
            
        Returns:
            Tuple of (chosen move, evaluation score)
        """
        return await super().get_move(board)

    async def _get_move_impl(self, board: chess.Board) -> Tuple[chess.Move, float]:
        """Implementation of get_move that uses minimax algorithm.
        
        Args:
            board: The current board position
            
        Returns:
            Tuple of (chosen move, evaluation score)
        """
        if not board.legal_moves:
            raise ValueError("No legal moves available")
        
        # Use iterative deepening to get faster responses
        best_move = None
        best_score = float('-inf') if board.turn else float('inf')
        
        try:
            for depth in range(1, self.level + 1):
                move, score = await self.minimax(board, depth, maximizing=board.turn)
                if move is not None:
                    best_move = move
                    best_score = score
        except Exception as e:
            print(f"Error in minimax search: {e}")
            if best_move is None:
                # If no move found yet, return a random legal move
                best_move = random.choice(list(board.legal_moves))
                best_score = 0
        
        if best_move is None:
            # Fallback to random move if minimax fails
            best_move = random.choice(list(board.legal_moves))
            best_score = 0
        
        return best_move, best_score 