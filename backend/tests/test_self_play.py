import pytest
import chess
from ai_chess_experiments.engines import LeelaEngine
from typing import List

@pytest.mark.asyncio
async def test_leela_self_play():
    """Test Leela vs Leela self-play."""
    if not LeelaEngine.is_available():
        pytest.skip("Leela Chess Zero not available")
    
    board = chess.Board()
    engine1 = LeelaEngine(depth=10)
    engine2 = LeelaEngine(depth=10)
    
    # Verify engines are different instances
    assert engine1 is not engine2
    
    moves: List[chess.Move] = []
    try:
        for _ in range(10):  # Play 10 moves
            if board.turn:
                move, _ = await engine1.get_move(board)
            else:
                move, _ = await engine2.get_move(board)
            
            assert move in board.legal_moves
            board.push(move)
            moves.append(move)
        
        # Verify game progressed
        assert len(moves) == 10
        assert board.fen() != chess.Board().fen()
    finally:
        await engine1.cleanup()
        await engine2.cleanup()

@pytest.mark.asyncio
async def test_leela_different_depths():
    """Test Leela vs Leela with different search depths."""
    if not LeelaEngine.is_available():
        pytest.skip("Leela Chess Zero not available")
    
    board = chess.Board()
    engine1 = LeelaEngine(depth=5)  # Shallow search
    engine2 = LeelaEngine(depth=15)  # Deeper search
    
    moves: List[chess.Move] = []
    try:
        for _ in range(10):  # Play 10 moves
            if board.turn:
                move, score1 = await engine1.get_move(board)
            else:
                move, score2 = await engine2.get_move(board)
            
            assert move in board.legal_moves
            board.push(move)
            moves.append(move)
        
        # Verify game progressed
        assert len(moves) == 10
        assert board.fen() != chess.Board().fen()
    finally:
        await engine1.cleanup()
        await engine2.cleanup() 