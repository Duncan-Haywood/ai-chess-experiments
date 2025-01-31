import chess
from ai_chess_experiments.engines.minimax_engine import MinimaxEngine
import time
from typing import Dict, List
import os

# Unicode chess pieces
PIECES = {
    'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟',
    '.': '·'
}

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_board(board: chess.Board, last_move: chess.Move = None):
    """Print the chess board with Unicode pieces and coordinates."""
    clear_screen()
    
    # Convert FEN to 2D array for easier manipulation
    rows = board.fen().split()[0].split('/')
    board_array = []
    for row in rows:
        board_row = []
        for char in row:
            if char.isdigit():
                board_row.extend(['.'] * int(char))
            else:
                board_row.append(char)
        board_array.append(board_row)
    
    # Print board with coordinates
    print("\n   a b c d e f g h")
    print("   ---------------")
    for i, row in enumerate(board_array):
        print(f"{8-i} |", end=" ")
        for piece in row:
            print(PIECES.get(piece, piece), end=" ")
        print(f"| {8-i}")
    print("   ---------------")
    print("   a b c d e f g h\n")
    
    if last_move:
        print(f"Last move: {last_move.uci()}")

def play_self_game(white_depth: int = 3, black_depth: int = 3, delay: float = 0.5):
    """Run a game between two minimax engines with enhanced visualization.
    
    Args:
        white_depth: Search depth for white engine
        black_depth: Search depth for black engine
        delay: Delay between moves in seconds
    """
    white_engine = MinimaxEngine(depth=white_depth)
    black_engine = MinimaxEngine(depth=black_depth)
    board = chess.Board()
    
    print(f"Starting new game (White depth: {white_depth}, Black depth: {black_depth})...")
    print_board(board)
    
    move_count = 1
    total_time = 0
    last_move = None
    
    while not board.is_game_over():
        # Get current engine
        current_engine = white_engine if board.turn == chess.WHITE else black_engine
        side = "White" if board.turn == chess.WHITE else "Black"
        depth = white_depth if board.turn == chess.WHITE else black_depth
        
        # Get and make move
        start_time = time.time()
        move = current_engine.get_move()
        move_time = time.time() - start_time
        total_time += move_time
        
        board.push(move)
        white_engine.update_board(move)
        black_engine.update_board(move)
        last_move = move
        
        # Print updated board with timing info
        print_board(board, last_move)
        print(f"Move {move_count} - {side} plays: {move.uci()} (took {move_time:.2f}s at depth {depth})")
        
        if board.turn == chess.WHITE:
            move_count += 1
            
        time.sleep(delay)
    
    # Print final state
    print("\nGame Over!")
    print(f"Result: {board.result()}")
    print(f"Total moves: {len(board.move_stack)}")
    print(f"Total thinking time: {total_time:.2f}s")
    print(f"Average time per move: {total_time/len(board.move_stack):.2f}s")
    
if __name__ == "__main__":
    play_self_game() 