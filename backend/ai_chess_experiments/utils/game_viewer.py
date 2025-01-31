"""Chess game viewer with ASCII board display."""

import chess
from typing import Optional
import os
import time

class GameViewer:
    def __init__(self, use_unicode: bool = True):
        """Initialize the game viewer.
        
        Args:
            use_unicode: Whether to use unicode chess pieces (looks better but might not work in all terminals)
        """
        self.use_unicode = use_unicode
        # Unicode chess pieces
        self.unicode_pieces = {
            'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
            'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
        }
    
    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def format_time(self, seconds: Optional[float]) -> str:
        """Format time in seconds to mm:ss format."""
        if seconds is None:
            return "--:--"
        minutes = int(seconds) // 60
        seconds = int(seconds) % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def display_game(self, board: chess.Board, white_time: Optional[float] = None, 
                    black_time: Optional[float] = None, last_move: Optional[str] = None,
                    white_name: str = "White", black_name: str = "Black"):
        """Display the current game state.
        
        Args:
            board: The chess board to display
            white_time: Remaining time for white in seconds
            black_time: Remaining time for black in seconds
            last_move: Last move played in UCI format
            white_name: Name of white player
            black_name: Name of black player
        """
        self.clear_screen()
        
        # Header with player names and times
        print(f"\n  {black_name} ({self.format_time(black_time)})")
        
        ranks = list('87654321')
        files = list('abcdefgh')
        
        # Print the board
        for rank in range(8):
            print(f"\n {ranks[rank]} ", end='')
            for file in range(8):
                square = chess.square(file, 7-rank)
                piece = board.piece_at(square)
                
                # Background color
                if (rank + file) % 2 == 0:
                    bg = '\033[48;5;180m'  # Light square
                else:
                    bg = '\033[48;5;94m'   # Dark square
                
                # Highlight last move
                if last_move and square in [chess.parse_square(last_move[:2]), 
                                          chess.parse_square(last_move[2:])]:
                    bg = '\033[48;5;228m'  # Yellow highlight
                
                # Piece or empty square
                if piece is None:
                    piece_str = ' '
                else:
                    piece_str = self.unicode_pieces.get(piece.symbol()) if self.use_unicode else piece.symbol()
                
                print(f"{bg} {piece_str} \033[0m", end='')
        
        # Print file labels
        print("\n\n    ", end='')
        print("  ".join(files))
        
        # Print white's name and time
        print(f"\n  {white_name} ({self.format_time(white_time)})")
        
        # Print game status
        if board.is_checkmate():
            print("\n  Checkmate!")
        elif board.is_stalemate():
            print("\n  Stalemate!")
        elif board.is_check():
            print("\n  Check!")
        
        # Print last move if available
        if last_move:
            print(f"\n  Last move: {last_move}")
        
        print()  # Empty line at the bottom 