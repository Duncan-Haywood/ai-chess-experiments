import pytest
from fastapi.testclient import TestClient
from ai_chess_experiments.main import app, create_engine, cleanup_engine
import chess
from ai_chess_experiments.engines import MinimaxEngine, StockfishEngine
import logging
from pathlib import Path
from ai_chess_experiments.engines.minimax_engine import MinimaxEngine
from ai_chess_experiments.engines.base_engine import BaseChessEngine

# Configure test logging
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_dir / "test.log")
    ]
)

client = TestClient(app=app)

# Game Management Tests
class TestGameManagement:
    """Test suite for game management functionality."""
    
    def test_new_game_starts_with_default_settings(self, client):
        """Verify that a new game starts with expected default settings."""
        response = client.post("/new_game")
        data = response.json()
        
        assert response.status_code == 200
        assert data["success"] == True
        assert data["mode"] == "human_vs_bot"
        assert data["white_depth"] == data["black_depth"] == 3
        assert data["white_engine"] == data["black_engine"] == "minimax"

    def test_game_state_reflects_current_position(self, client):
        """Verify that game state accurately reflects the current position."""
        client.post("/new_game")
        response = client.get("/game")
        data = response.json()
        
        assert response.status_code == 200
        assert data["fen"].startswith("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR")
        assert data["moveCount"] == 0
        assert data["status"] == "active"
        assert data["whiteTime"] == data["blackTime"] == 180

# Engine Management Tests
class TestEngineManagement:
    """Test suite for chess engine management."""
    
    def test_engine_depth_constraints(self, client):
        """Verify that engine depth settings are properly constrained."""
        # Test minimum depth
        response = client.post("/set_depth", params={"white": 0})
        assert response.status_code == 400
        assert "depth must be between 1 and 20" in response.json()["detail"]
        
        # Test maximum depth
        response = client.post("/set_depth", params={"black": 21})
        assert response.status_code == 400
        assert "depth must be between 1 and 20" in response.json()["detail"]
        
        # Test valid depth
        response = client.post("/set_depth", params={"white": 5, "black": 4})
        assert response.status_code == 200
        data = response.json()
        assert data["white_depth"] == 5
        assert data["black_depth"] == 4

    def test_engine_type_validation(self, client):
        """Verify that only valid engine types can be selected."""
        # Test invalid engine
        response = client.post("/set_engine", params={"white": "invalid_engine"})
        assert response.status_code == 400
        assert "Invalid engine type" in response.json()["detail"]
        
        # Test valid engines
        for engine in ["minimax", "stockfish", "mcts", "leela"]:
            response = client.post("/set_engine", params={"white": engine})
            assert response.status_code == 200
            assert response.json()["white_engine"] == engine

# Move Validation Tests
class TestMoveValidation:
    """Test suite for chess move validation and execution."""
    
    def test_basic_move_validation(self, client):
        """Verify that basic move validation works correctly."""
        client.post("/new_game")
        
        # Test valid move
        response = client.post("/move", json={"from": "e2", "to": "e4"})
        assert response.status_code == 200
        assert response.json()["playerMove"] == "e2e4"
        
        # Test invalid move format
        response = client.post("/move", json={"from": "invalid"})
        assert response.status_code == 400
        assert "Move must include" in response.json()["detail"]
        
        # Test illegal move
        response = client.post("/move", json={"from": "e2", "to": "e6"})
        assert response.status_code == 400
        assert "Illegal move" in response.json()["detail"]

    def test_move_restrictions_in_bot_mode(self, client):
        """Verify that moves are properly restricted in bot vs bot mode."""
        client.post("/new_game", params={"mode": "bot_vs_bot"})
        
        response = client.post("/move", json={"from": "e2", "to": "e4"})
        assert response.status_code == 400
        assert "Cannot make moves in bot vs bot mode" in response.json()["detail"]

# Game Progress Tests
class TestGameProgress:
    """Test suite for game progress and completion."""
    
    def test_time_control_management(self, client):
        """Verify that time controls are properly managed."""
        client.post("/new_game")
        
        # Initial time should be 3 minutes
        response = client.get("/game")
        data = response.json()
        assert data["whiteTime"] == data["blackTime"] == 180
        
        # Make a move and verify time updates
        client.post("/move", json={"from": "e2", "to": "e4"})
        response = client.get("/game")
        data = response.json()
        assert data["whiteTime"] <= 180  # Time should have decreased

    def test_game_completion_detection(self, client):
        """Verify that game completion is properly detected."""
        # Test checkmate detection
        client.post("/new_game")
        # Fool's mate sequence
        moves = [
            {"from": "f2", "to": "f3"},
            {"from": "e7", "to": "e5"},
            {"from": "g2", "to": "g4"},
            {"from": "d8", "to": "h4"}
        ]
        for move in moves:
            response = client.post("/move", json=move)
            
        response = client.get("/game")
        data = response.json()
        assert data["status"] == "finished"
        assert data["result"] == "0-1"
        assert data["resultReason"] == "Checkmate"

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_set_depth():
    response = client.post("/set_depth", params={"white": 5, "black": 4})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["white_depth"] == 5
    assert data["black_depth"] == 4

def test_set_invalid_depth():
    response = client.post("/set_depth", params={"white": 21})
    assert response.status_code == 400
    assert "depth must be between 1 and 20" in response.json()["detail"]

def test_set_engine():
    response = client.post("/set_engine", params={"white": "minimax", "black": "minimax"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["white_engine"] == "minimax"
    assert data["black_engine"] == "minimax"

def test_set_invalid_engine():
    response = client.post("/set_engine", params={"white": "invalid_engine"})
    assert response.status_code == 400
    assert "Invalid engine type" in response.json()["detail"]

def test_game_state():
    # First create a new game
    client.post("/new_game")
    
    response = client.get("/game")
    assert response.status_code == 200
    data = response.json()
    assert "fen" in data
    assert data["status"] == "active"
    assert data["gameMode"] == "human_vs_bot"

def test_make_move():
    # First create a new game
    client.post("/new_game")
    
    # Make a valid move (e2 to e4)
    response = client.post(
        "/move",
        json={"from": "e2", "to": "e4"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["playerMove"] == "e2e4"

def test_make_invalid_move():
    # First create a new game
    client.post("/new_game")
    
    # Try to make an invalid move
    response = client.post(
        "/move",
        json={"from": "e2", "to": "e6"}
    )
    assert response.status_code == 400
    assert "Illegal move" in response.json()["detail"]

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture(autouse=True)
def cleanup():
    """Clean up global state after each test."""
    yield
    games.clear()
    engines.clear()

class TestGameInitialization:
    """Test suite for game initialization and setup."""
    
    def test_health_check(self, client):
        """Verify health check endpoint returns correct engine availability."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "engines" in data
        assert all(engine in data["engines"] for engine in ["minimax", "stockfish"])
    
    def test_new_game_human_vs_human(self, client):
        """Test creating a new game between human players."""
        response = client.post("/game/new", params={
            "white_name": "Player 1",
            "black_name": "Player 2"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["white_name"] == "Player 1"
        assert data["black_name"] == "Player 2"
        assert data["status"] == "active"
        assert data["fen"] == chess.Board().fen()
        assert data["id"] in games
    
    def test_new_game_with_minimax_engine(self, client):
        """Test creating a new game with Minimax engine."""
        response = client.post("/game/new", params={
            "white_name": "Player",
            "black_name": "Minimax",
            "black_engine": "minimax",
            "depth": 3
        })
        assert response.status_code == 200
        data = response.json()
        assert data["black_engine"] == "minimax"
        assert data["depth"] == 3
        assert isinstance(engines[data["id"]]["black"], MinimaxEngine)
    
    @pytest.mark.skipif(not StockfishEngine().is_available(), reason="Stockfish not available")
    def test_new_game_with_stockfish_engine(self, client):
        """Test creating a new game with Stockfish engine."""
        response = client.post("/game/new", params={
            "white_name": "Player",
            "black_name": "Stockfish",
            "black_engine": "stockfish"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["black_engine"] == "stockfish"
        assert isinstance(engines[data["id"]]["black"], StockfishEngine)

class TestGameStateManagement:
    """Test suite for game state management and retrieval."""
    
    def test_get_nonexistent_game(self, client):
        """Test attempting to get state of non-existent game."""
        response = client.get("/game/nonexistent")
        assert response.status_code == 404
    
    def test_get_game_state(self, client):
        """Test retrieving game state."""
        # Create a new game
        new_game = client.post("/game/new", params={
            "white_name": "Player 1",
            "black_name": "Player 2"
        }).json()
        
        # Get its state
        response = client.get(f"/game/{new_game['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == new_game["id"]
        assert data["status"] == "active"
        assert data["fen"] == chess.Board().fen()
    
    def test_game_state_after_moves(self, client):
        """Test game state updates correctly after moves."""
        # Create a new game
        new_game = client.post("/game/new", params={
            "white_name": "Player 1",
            "black_name": "Player 2"
        }).json()
        
        # Make a move
        move = "e2e4"
        response = client.post(f"/game/{new_game['id']}/move/{move}")
        assert response.status_code == 200
        data = response.json()
        assert data["last_move"] == move
        assert data["status"] == "active"
        
        # Verify board state
        board = chess.Board()
        board.push_uci(move)
        assert data["fen"] == board.fen()

class TestErrorHandling:
    """Test suite for error handling scenarios."""
    
    def test_invalid_engine_type(self, client):
        """Test handling of invalid engine type."""
        response = client.post("/game/new", params={
            "white_name": "Player",
            "black_name": "Invalid",
            "black_engine": "invalid_engine"
        })
        assert response.status_code == 500
        assert "Failed to create engine" in response.json()["detail"]
    
    def test_invalid_move_format(self, client):
        """Test handling of invalid move format."""
        # Create a new game
        new_game = client.post("/game/new", params={
            "white_name": "Player 1",
            "black_name": "Player 2"
        }).json()
        
        # Try invalid move
        response = client.post(f"/game/{new_game['id']}/move/invalid")
        assert response.status_code == 400
        assert "Invalid move format" in response.json()["detail"]
    
    def test_illegal_move(self, client):
        """Test handling of illegal chess move."""
        # Create a new game
        new_game = client.post("/game/new", params={
            "white_name": "Player 1",
            "black_name": "Player 2"
        }).json()
        
        # Try illegal move
        response = client.post(f"/game/{new_game['id']}/move/e2e5")
        assert response.status_code == 400
        assert "Invalid move" in response.json()["detail"]
    
    def test_move_after_game_over(self, client):
        """Test handling of moves after game is over."""
        # Create a new game with Minimax engine
        new_game = client.post("/game/new", params={
            "white_name": "Player",
            "black_name": "Minimax",
            "black_engine": "minimax",
            "depth": 1
        }).json()
        
        # Scholar's mate
        moves = ["e2e4", "e7e5", "d1h5", "b8c6", "f1c4", "g8f6", "h5f7"]
        
        for move in moves:
            response = client.post(f"/game/{new_game['id']}/move/{move}")
            assert response.status_code == 200
            
        # Game should be over
        game_state = client.get(f"/game/{new_game['id']}").json()
        assert game_state["status"] == "checkmate"
        
        # Try to make another move
        response = client.post(f"/game/{new_game['id']}/move/a2a3")
        assert response.status_code == 400

class TestEngineInteraction:
    """Test suite for chess engine interaction."""
    
    def test_engine_move_generation(self, client):
        """Test that engines generate valid moves."""
        # Create a new game with Minimax engine
        new_game = client.post("/game/new", params={
            "white_name": "Player",
            "black_name": "Minimax",
            "black_engine": "minimax",
            "depth": 2
        }).json()
        
        # Make a move and verify engine responds
        response = client.post(f"/game/{new_game['id']}/move/e2e4")
        assert response.status_code == 200
        data = response.json()
        
        # Verify engine made a move
        board = chess.Board()
        board.push_uci("e2e4")
        assert data["fen"] != board.fen()  # Engine should have moved
        
    def test_engine_depth_setting(self, client):
        """Test engine depth setting affects move generation time."""
        import time
        
        # Create games with different depths
        shallow = client.post("/game/new", params={
            "white_name": "Player",
            "black_name": "Minimax",
            "black_engine": "minimax",
            "depth": 1
        }).json()
        
        deep = client.post("/game/new", params={
            "white_name": "Player",
            "black_name": "Minimax",
            "black_engine": "minimax",
            "depth": 3
        }).json()
        
        # Measure response times
        start = time.time()
        client.post(f"/game/{shallow['id']}/move/e2e4")
        shallow_time = time.time() - start
        
        start = time.time()
        client.post(f"/game/{deep['id']}/move/e2e4")
        deep_time = time.time() - start
        
        assert deep_time > shallow_time  # Deeper search should take longer

    @pytest.mark.skipif(not StockfishEngine().is_available(), reason="Stockfish not available")
    def test_engine_switch_during_game(self, client):
        """Test switching engines during a game."""
        # Start with Minimax
        new_game = client.post("/game/new", params={
            "white_name": "Player",
            "black_name": "Minimax",
            "black_engine": "minimax",
            "depth": 2
        }).json()
        
        # Make a move
        response = client.post(f"/game/{new_game['id']}/move/e2e4")
        assert response.status_code == 200
        
        # Create new game with Stockfish
        new_game = client.post("/game/new", params={
            "white_name": "Player",
            "black_name": "Stockfish",
            "black_engine": "stockfish"
        }).json()
        
        # Make same move
        response = client.post(f"/game/{new_game['id']}/move/e2e4")
        assert response.status_code == 200
        
        # Moves should be different
        assert engines[new_game["id"]]["black"].__class__.__name__ == "StockfishEngine"

class TestMinimaxEngine:
    """Test suite for the Minimax chess engine."""
    
    def test_initialization(self):
        """Test engine initialization."""
        engine = MinimaxEngine()
        assert isinstance(engine, BaseChessEngine)
        assert engine.level == 3  # Default depth
        
        engine = MinimaxEngine(level=5)
        assert engine.level == 5
    
    def test_get_engine_info(self):
        """Test getting engine information."""
        info = MinimaxEngine.get_engine_info()
        assert isinstance(info, dict)
        assert info["type"] == "depth"
        assert info["min"] == 1
        assert info["max"] == 20
        assert info["default"] == 3
        assert "description" in info
        assert "step" in info
    
    @pytest.mark.asyncio
    async def test_get_move(self):
        """Test getting a move from the engine."""
        engine = MinimaxEngine()
        board = chess.Board()
        
        # Test initial position
        move, score = await engine.get_move(board)
        assert isinstance(move, chess.Move)
        assert isinstance(score, float)
        assert move in board.legal_moves
        
        # Test after a few moves
        board.push_san("e4")
        board.push_san("e5")
        board.push_san("Nf3")
        
        move, score = await engine.get_move(board)
        assert isinstance(move, chess.Move)
        assert isinstance(score, float)
        assert move in board.legal_moves
    
    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test engine cleanup."""
        engine = MinimaxEngine()
        await engine.cleanup()  # Should not raise any errors
    
    def test_evaluate_position(self):
        """Test position evaluation."""
        engine = MinimaxEngine()
        board = chess.Board()
        
        # Test initial position
        score = engine.evaluate_position(board)
        assert isinstance(score, float)
        assert score == 0  # Initial position should be equal
        
        # Test winning position for white
        board.set_fen("4k3/4Q3/4K3/8/8/8/8/8 b - - 0 1")  # White to mate in 1
        score = engine.evaluate_position(board)
        assert score > 0  # White is winning
        
        # Test winning position for black
        board.set_fen("8/8/8/8/8/4k3/4q3/4K3 w - - 0 1")  # Black to mate in 1
        score = engine.evaluate_position(board)
        assert score < 0  # Black is winning 