import pytest
from fastapi.testclient import TestClient
import chess
from ai_chess_experiments.main import app
from ai_chess_experiments.engines.minimax_engine import MinimaxEngine
from ai_chess_experiments.engines.stockfish_engine import StockfishEngine
from ai_chess_experiments.engines.leela_engine import LeelaEngine

@pytest.fixture
def client():
    """Test client for the FastAPI app."""
    return TestClient(app)

@pytest.fixture
def board():
    """Fresh chess board for each test."""
    return chess.Board()

@pytest.fixture
async def minimax_engine():
    """Minimax engine instance for testing."""
    engine = MinimaxEngine(level=3)
    yield engine
    await engine.cleanup()

@pytest.fixture
async def stockfish_engine():
    """Stockfish engine instance for testing if available."""
    if not StockfishEngine.is_available():
        pytest.skip("Stockfish not available")
    engine = StockfishEngine(depth=20)
    yield engine
    await engine.cleanup()

@pytest.fixture
async def leela_engine():
    """Leela engine instance for testing if available."""
    if not LeelaEngine.is_available():
        pytest.skip("Leela Chess Zero not available")
    engine = LeelaEngine(depth=20)
    yield engine
    await engine.cleanup()

@pytest.fixture
def checkmate_position():
    """Board position with checkmate in one."""
    return chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 0 1")

@pytest.fixture
def stalemate_position():
    """Board position near stalemate."""
    return chess.Board("8/8/8/8/8/4k3/4p3/4K3 w - - 0 1") 