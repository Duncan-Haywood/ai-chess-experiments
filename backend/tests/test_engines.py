import pytest
import chess
from typing import Type, Dict, Any
from ai_chess_experiments.engines.base_engine import BaseChessEngine
from ai_chess_experiments.engines.minimax_engine import MinimaxEngine
from ai_chess_experiments.engines.stockfish_engine import StockfishEngine

@pytest.mark.parametrize("engine_class,params", [
    (MinimaxEngine, {"level": 3}),
    pytest.param(StockfishEngine, {"depth": 20},
                marks=pytest.mark.skipif(not StockfishEngine.is_available(),
                                      reason="Stockfish not available"))
])
async def test_engine_initialization(engine_class: Type[BaseChessEngine], params: Dict[str, Any]):
    """Test that engines can be initialized with different parameters."""
    engine = engine_class(**params)
    assert engine is not None
    assert isinstance(engine, BaseChessEngine)
    await engine.cleanup()

@pytest.mark.asyncio
async def test_minimax_evaluation():
    """Test minimax position evaluation."""
    engine = MinimaxEngine(level=3)
    board = chess.Board()
    
    # Initial position should be roughly equal
    score = engine.evaluate_position(board)
    assert -100 <= score <= 100  # Allow for some variation in evaluation
    
    # Test mate position
    board.set_fen("k7/8/8/8/8/8/8/K6Q w - - 0 1")  # White has mate in one
    score = engine.evaluate_position(board)
    assert score > 1000  # Should recognize winning position
    
    await engine.cleanup()

@pytest.mark.asyncio
async def test_engine_move_generation():
    """Test that engines can generate legal moves."""
    engines = []
    
    # Always test minimax
    engines.append(MinimaxEngine(level=3))
    
    # Test stockfish if available
    if StockfishEngine.is_available():
        engines.append(StockfishEngine(depth=20))
    
    board = chess.Board()
    
    for engine in engines:
        move, eval_score = await engine.get_move(board)
        assert move in board.legal_moves
        assert isinstance(eval_score, (int, float))
        await engine.cleanup()

@pytest.mark.asyncio
async def test_engine_metrics():
    """Test that engine metrics are properly tracked."""
    engine = MinimaxEngine(level=3)
    board = chess.Board()
    
    # Get initial metrics
    metrics = engine.get_metrics()
    assert metrics["nodes_searched"] == 0
    assert metrics["depth_reached"] == 0
    assert metrics["time_taken"] == 0
    
    # Make a move and check metrics
    await engine.get_move(board)
    metrics = engine.get_metrics()
    assert metrics["nodes_searched"] > 0
    assert metrics["depth_reached"] > 0
    assert metrics["time_taken"] >= 0
    
    await engine.cleanup() 