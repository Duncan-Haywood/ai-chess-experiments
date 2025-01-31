import chess
from typing import Dict, List, Set, Optional

# Piece values (in centipawns)
PIECE_VALUES: Dict[chess.PieceType, int] = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

# Important squares for evaluation
CENTER_SQUARES = {chess.D4, chess.D5, chess.E4, chess.E5}
EXTENDED_CENTER = {
    chess.C3, chess.D3, chess.E3, chess.F3,
    chess.C4, chess.D4, chess.E4, chess.F4,
    chess.C5, chess.D5, chess.E5, chess.F5,
    chess.C6, chess.D6, chess.E6, chess.F6
}

# Piece-square tables
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

KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]

BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]

ROOK_TABLE = [
    0,  0,  0,  0,  0,  0,  0,  0,
    5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    0,  0,  0,  5,  5,  0,  0,  0
]

QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
    -5,  0,  5,  5,  5,  5,  0, -5,
    0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]

KING_MIDDLE_TABLE = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    20, 20,  0,  0,  0,  0, 20, 20,
    20, 30, 10,  0,  0, 10, 30, 20
]

KING_END_TABLE = [
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50
]

PIECE_SQUARE_TABLES = {
    chess.PAWN: PAWN_TABLE,
    chess.KNIGHT: KNIGHT_TABLE,
    chess.BISHOP: BISHOP_TABLE,
    chess.ROOK: ROOK_TABLE,
    chess.QUEEN: QUEEN_TABLE,
    chess.KING: KING_MIDDLE_TABLE  # Default to middle game
}

def is_endgame(board: chess.Board) -> bool:
    """Determine if the current position is in the endgame phase."""
    queens = len(board.pieces(chess.QUEEN, chess.WHITE)) + len(board.pieces(chess.QUEEN, chess.BLACK))
    minors = len(board.pieces(chess.KNIGHT, chess.WHITE)) + len(board.pieces(chess.BISHOP, chess.WHITE)) + \
            len(board.pieces(chess.KNIGHT, chess.BLACK)) + len(board.pieces(chess.BISHOP, chess.BLACK))
    return queens == 0 or (queens == 2 and minors <= 2)

def get_piece_value(piece: chess.Piece, square: chess.Square, is_endgame: bool = False) -> int:
    """Get the value of a piece on a given square."""
    piece_type = piece.piece_type
    base_value = PIECE_VALUES[piece_type]
    
    # Get position value from piece-square table
    if piece_type == chess.KING and is_endgame:
        position_value = KING_END_TABLE[square if piece.color else chess.square_mirror(square)]
    else:
        position_value = PIECE_SQUARE_TABLES[piece_type][square if piece.color else chess.square_mirror(square)]
    
    return base_value + position_value

def evaluate_position(board: chess.Board) -> float:
    """Evaluate the current chess position.
    
    Args:
        board: Current chess position
        
    Returns:
        float: Evaluation score (positive favors white, negative favors black)
    """
    if board.is_checkmate():
        return -10000 if board.turn else 10000
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    
    score = 0.0
    endgame = is_endgame(board)
    
    # Material and piece-square table evaluation
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is not None:
            value = get_piece_value(piece, square, endgame)
            score += value if piece.color else -value
    
    # Mobility evaluation (if not in endgame)
    if not endgame:
        mobility_score = len(list(board.legal_moves))
        board.push(chess.Move.null())  # Switch sides to count opponent moves
        mobility_score -= len(list(board.legal_moves))
        board.pop()
        score += mobility_score * 10  # Weight mobility
    
    # Pawn structure evaluation
    white_pawns = board.pieces(chess.PAWN, chess.WHITE)
    black_pawns = board.pieces(chess.PAWN, chess.BLACK)
    
    # Doubled pawns penalty
    for file in range(8):
        white_pawns_in_file = sum(1 for sq in white_pawns if chess.square_file(sq) == file)
        black_pawns_in_file = sum(1 for sq in black_pawns if chess.square_file(sq) == file)
        score -= (white_pawns_in_file - 1) * 50 if white_pawns_in_file > 1 else 0
        score += (black_pawns_in_file - 1) * 50 if black_pawns_in_file > 1 else 0
    
    # Isolated pawns penalty
    for file in range(8):
        if file > 0 and file < 7:
            white_isolated = (
                sum(1 for sq in white_pawns if chess.square_file(sq) == file) > 0 and
                sum(1 for sq in white_pawns if chess.square_file(sq) == file - 1) == 0 and
                sum(1 for sq in white_pawns if chess.square_file(sq) == file + 1) == 0
            )
            black_isolated = (
                sum(1 for sq in black_pawns if chess.square_file(sq) == file) > 0 and
                sum(1 for sq in black_pawns if chess.square_file(sq) == file - 1) == 0 and
                sum(1 for sq in black_pawns if chess.square_file(sq) == file + 1) == 0
            )
            score -= white_isolated * 30
            score += black_isolated * 30
    
    # King safety in early/middle game
    if not endgame:
        white_king_square = board.king(chess.WHITE)
        black_king_square = board.king(chess.BLACK)
        if white_king_square and black_king_square:
            # Penalize central king positions
            white_king_file = chess.square_file(white_king_square)
            black_king_file = chess.square_file(black_king_square)
            white_king_rank = chess.square_rank(white_king_square)
            black_king_rank = chess.square_rank(black_king_square)
            
            if white_king_file > 2 and white_king_file < 6:
                score -= 60
            if black_king_file > 2 and black_king_file < 6:
                score += 60
            
            # Reward kings on back rank
            score += 40 if white_king_rank == 0 else -20
            score -= 40 if black_king_rank == 7 else -20
    
    # Add a small random factor to prevent repetition in engine vs engine games
    score += (hash(board.fen()) % 10) * 0.01
    
    return score 