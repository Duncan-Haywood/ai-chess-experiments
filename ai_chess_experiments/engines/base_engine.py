from abc import ABC, abstractmethod
import chess

class BaseChessEngine(ABC):
    """Base class for all chess engines.
    
    This abstract class defines the interface that all chess engines must implement.
    Different AI approaches (rule-based, ML, etc.) should inherit from this class.
    """
    
    def __init__(self):
        self.board = chess.Board()
    
    @abstractmethod
    def get_move(self) -> chess.Move:
        """Calculate and return the next move.
        
        Returns:
            chess.Move: The chosen move in the current position
        """
        pass
    
    def update_board(self, move: chess.Move):
        """Update the internal board state with a move.
        
        Args:
            move: The move to apply to the board
        """
        self.board.push(move)
    
    def set_position(self, fen: str):
        """Set the board to a specific position.
        
        Args:
            fen: The FEN string representing the position
        """
        self.board.set_fen(fen)
    
    def get_legal_moves(self):
        """Get all legal moves in the current position."""
        return list(self.board.legal_moves)
    
    def is_game_over(self) -> bool:
        """Check if the game is over."""
        return self.board.is_game_over()
    
    def get_board_state(self) -> chess.Board:
        """Get the current board state."""
        return self.board.copy() 