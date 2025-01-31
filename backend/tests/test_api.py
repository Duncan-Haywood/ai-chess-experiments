import pytest
import logging
from fastapi.testclient import TestClient
from ai_chess_experiments.main import app

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)

def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_new_game(client):
    """Test creating a new game."""
    response = client.post("/new_game", params={
        "mode": "human_vs_bot",
        "white_depth_param": 3,
        "black_depth_param": 3
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"]
    assert data["mode"] == "human_vs_bot"
    assert data["white_depth"] == 3
    assert data["black_depth"] == 3
    assert data["white_engine"] == "minimax"
    assert data["black_engine"] == "minimax"

def test_get_game_state(client):
    """Test getting game state."""
    # First create a new game
    client.post("/new_game")
    
    # Then get the state
    response = client.get("/game")
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields
    assert "fen" in data
    assert "whiteTime" in data
    assert "blackTime" in data
    assert "status" in data
    assert "gameMode" in data
    
    # Verify initial state
    assert data["status"] == "active"
    assert abs(data["whiteTime"] - 180) < 0.1  # Allow small time difference
    assert abs(data["blackTime"] - 180) < 0.1  # Allow small time difference
    assert data["fen"] == "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

def test_make_move(client):
    """Test making a move."""
    # Start new game
    response = client.post("/new_game")
    assert response.status_code == 200
    logger.debug("New game response: %s", response.json())
    
    # Make a move
    move_data = {
        "from": "e2",
        "to": "e4"
    }
    logger.debug("Making move: %s", move_data)
    response = client.post("/move", json=move_data)
    if response.status_code != 200:
        logger.error("Move failed with status %d: %s", response.status_code, response.text)
    assert response.status_code == 200
    data = response.json()
    logger.debug("Move response: %s", data)
    
    # Check response structure
    assert data["success"]
    assert data["playerMove"] == "e2e4"
    assert "gameState" in data
    
    # Verify game state after move
    game_state = data["gameState"]
    assert "fen" in game_state
    assert game_state["fen"] != "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    assert game_state["status"] == "active"

def test_invalid_move(client):
    """Test making an invalid move."""
    # Start new game
    client.post("/new_game")
    
    # Try invalid move
    response = client.post("/move", json={
        "from": "e2",
        "to": "e6"
    })
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Illegal move" in data["detail"]

def test_set_engine(client):
    """Test setting engine types."""
    response = client.post("/set_engine", params={
        "white": "minimax",
        "black": "minimax"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"]
    assert data["white_engine"] == "minimax"
    assert data["black_engine"] == "minimax"

def test_set_depth(client):
    """Test setting search depth."""
    response = client.post("/set_depth", params={
        "white": 3,
        "black": 3
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"]
    assert data["white_depth"] == 3
    assert data["black_depth"] == 3

def test_game_flow(client):
    """Test a complete game flow."""
    # Start new game
    response = client.post("/new_game")
    assert response.status_code == 200
    logger.debug("New game response: %s", response.json())
    
    # Make some moves
    moves = [
        {"from": "e2", "to": "e4"},  # 1. e4
        {"from": "e7", "to": "e5"},  # 1...e5
        {"from": "g1", "to": "f3"},  # 2. Nf3
        {"from": "b8", "to": "c6"},  # 2...Nc6
    ]
    
    for move in moves:
        logger.debug("Making move: %s", move)
        response = client.post("/move", json=move)
        if response.status_code != 200:
            logger.error("Move failed with status %d: %s", response.status_code, response.text)
        assert response.status_code == 200, f"Move failed: {move}"
        data = response.json()
        logger.debug("Move response: %s", data)
        assert data["success"]
        
        # Check game state after each move
        game_state = data["gameState"]
        assert game_state["status"] == "active"
        assert game_state["whiteTime"] > 0
        assert game_state["blackTime"] > 0

def test_time_control(client):
    """Test time control functionality."""
    # Start new game
    response = client.post("/new_game")
    assert response.status_code == 200
    logger.debug("New game response: %s", response.json())
    
    # Get initial state
    response = client.get("/game")
    initial_data = response.json()
    initial_white_time = initial_data["whiteTime"]
    initial_black_time = initial_data["blackTime"]
    logger.debug("Initial state: white=%f, black=%f", initial_white_time, initial_black_time)
    
    # Make a move and check time updates
    move_data = {
        "from": "e2",
        "to": "e4"
    }
    logger.debug("Making move: %s", move_data)
    response = client.post("/move", json=move_data)
    if response.status_code != 200:
        logger.error("Move failed with status %d: %s", response.status_code, response.text)
    assert response.status_code == 200
    data = response.json()
    logger.debug("Move response: %s", data)
    game_state = data["gameState"]
    
    # White's time should decrease after their move
    assert game_state["whiteTime"] < initial_white_time
    # Black's time should not change yet
    assert abs(game_state["blackTime"] - initial_black_time) < 0.1 