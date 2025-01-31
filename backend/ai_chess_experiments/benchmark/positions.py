"""Standard test positions for benchmarking chess engines."""

# List of interesting positions with their FEN strings and descriptions
TEST_POSITIONS = [
    {
        "name": "Starting Position",
        "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "depth": 4,  # Recommended search depth
        "description": "Standard starting position"
    },
    {
        "name": "Sicilian Dragon",
        "fen": "rnbqkb1r/pp2pp1p/3p1np1/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 7",
        "depth": 4,
        "description": "Complex tactical position from Sicilian Dragon"
    },
    {
        "name": "Mate in 2",
        "fen": "r2qkb1r/pp2nppp/3p4/2pNN1B1/2BnP3/3P4/PPP2PPP/R2bK2R w KQkq - 0 1",
        "depth": 4,
        "description": "Tactical position with forced mate in 2"
    },
    {
        "name": "Endgame",
        "fen": "8/3k4/8/8/8/8/3K1P2/8 w - - 0 1",
        "depth": 5,
        "description": "Simple king and pawn endgame"
    },
    {
        "name": "Material Imbalance",
        "fen": "r1b2rk1/2q1b1pp/p2ppn2/1p6/3QP3/1B6/PPP2PPP/R3K2R w KQ - 0 1",
        "depth": 4,
        "description": "Position with material imbalance (queen vs. multiple pieces)"
    }
]

# Positions specifically for testing evaluation functions
EVALUATION_POSITIONS = [
    {
        "name": "Equal Material",
        "fen": "r1bqkb1r/pppp1ppp/2n2n2/4p3/4P3/2N2N2/PPPP1PPP/R1BQKB1R w KQkq - 4 4",
        "expected_eval": 0.0,
        "description": "Equal position from a standard opening"
    },
    {
        "name": "White Material Up",
        "fen": "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPPQPPP/RNB1KBNR b KQkq - 1 2",
        "expected_eval": 9.0,
        "description": "White is up a queen"
    },
    {
        "name": "Black Material Up",
        "fen": "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
        "expected_eval": -3.0,
        "description": "Black is up a pawn"
    }
]

# Time control test positions (for testing engine speed)
TIME_CONTROL_POSITIONS = [
    {
        "name": "Complex Middlegame",
        "fen": "r1bq1rk1/pp2ppbp/2np1np1/8/3NP3/2N1B3/PPPQ1PPP/R3KB1R w KQ - 0 1",
        "time_limit": 1.0,  # Time limit in seconds
        "description": "Complex position to test engine speed"
    },
    {
        "name": "Tactical Position",
        "fen": "r1bqk2r/pppp1ppp/2n2n2/4p3/1bB1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 4 4",
        "time_limit": 0.5,
        "description": "Tactical position to test move generation speed"
    }
] 