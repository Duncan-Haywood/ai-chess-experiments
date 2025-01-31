import chess
import time
import logging
import psutil
import os
import uuid
from typing import Optional, Dict, Any, List, TypedDict, Union, cast
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from ai_chess_experiments.engines.base_engine import BaseChessEngine
from ai_chess_experiments.engines.minimax_engine import MinimaxEngine
from ai_chess_experiments.engines.stockfish_engine import StockfishEngine

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class GameState(TypedDict):
    board: chess.Board
    engine: BaseChessEngine
    engine2: BaseChessEngine
    game_mode: str
    game_start_time: float
    white_time: float
    black_time: float
    last_move_time: float
    white_depth: int
    black_depth: int
    white_engine_type: str
    black_engine_type: str
    move_times: List[float]
    engine_metrics: EngineMetrics

class EngineMetrics(TypedDict):
    nodes_searched: int
    depth_reached: int
    time_taken: float
    memory_used: int
    cpu_percent: float

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
games: Dict[str, GameState] = {}

async def create_engine(engine_type: str, depth: int) -> BaseChessEngine:
    """Create a chess engine based on the specified type."""
    try:
        logger.debug("Creating %s engine with depth %d", engine_type, depth)
        if engine_type == 'minimax':
            return MinimaxEngine(depth)
        elif engine_type == 'stockfish' and StockfishEngine.is_available():
            return StockfishEngine(depth)
        else:
            raise ValueError(f"Unknown or unavailable engine type: {engine_type}")
    except Exception as e:
        logger.error("Error creating engine %s: %s", engine_type, e)
        raise

async def cleanup_engine(engine: Optional[BaseChessEngine]):
    """Safely cleanup an engine instance."""
    if engine:
        try:
            await engine.cleanup()
        except Exception as e:
            logger.error("Error cleaning up engine: %s", e)

async def create_game_state(
    mode: str = "human_vs_bot",
    white_depth: Optional[int] = None,
    black_depth: Optional[int] = None
) -> str:
    """Create a new game state and return its ID."""
    game_id = str(uuid.uuid4())
    board = chess.Board()
    
    # Use default depth of 3 if None is provided
    white_depth_val = 3 if white_depth is None else white_depth
    black_depth_val = 3 if black_depth is None else black_depth
    
    engine = await create_engine("minimax", white_depth_val)
    engine2 = await create_engine("minimax", black_depth_val)
    engine.board = board
    engine2.board = board
    
    initial_metrics: EngineMetrics = {
        "nodes_searched": 0,
        "depth_reached": 0,
        "time_taken": 0.0,
        "memory_used": 0,
        "cpu_percent": 0.0
    }
    
    games[game_id] = {
        "board": board,
        "engine": engine,
        "engine2": engine2,
        "game_mode": mode,
        "game_start_time": time.time(),
        "white_time": 180,  # 3 minutes
        "black_time": 180,  # 3 minutes
        "last_move_time": time.time(),
        "white_depth": white_depth_val,
        "black_depth": black_depth_val,
        "white_engine_type": "minimax",
        "black_engine_type": "minimax",
        "move_times": [],
        "engine_metrics": initial_metrics
    }
    return game_id

@app.get("/health")
async def health_check():
    """Health check endpoint to verify server is running."""
    try:
        # Check system resources
        memory = psutil.virtual_memory()
        if memory.percent > 90:  # Memory usage above 90%
            return {"status": "unhealthy", "detail": "High memory usage"}
        
        cpu_percent = psutil.cpu_percent(interval=0.1)
        if cpu_percent > 90:  # CPU usage above 90%
            return {"status": "unhealthy", "detail": "High CPU usage"}
        
        return {
            "status": "healthy",
            "engines": {
                "minimax": True,
                "stockfish": False  # TODO: Add Stockfish support
            },
            "details": {
                "memory_usage": memory.percent,
                "cpu_usage": cpu_percent,
                "active_games": len(games)
            }
        }
    except Exception as e:
        logger.error("Health check failed: %s", e)
        return {"status": "unhealthy", "detail": str(e)}

@app.get("/engine/metrics/{game_id}")
async def get_engine_metrics(game_id: str) -> EngineMetrics:
    """Get current engine performance metrics for a specific game."""
    if game_id not in games:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found"
        )
    
    try:
        game_state = games[game_id]
        process = psutil.Process(os.getpid())
        current_engine = game_state["engine2"] if not game_state["board"].turn else game_state["engine"]
        
        # Create new metrics dictionary
        new_metrics: EngineMetrics = {
            "nodes_searched": getattr(current_engine, 'nodes_searched', 0),
            "depth_reached": getattr(current_engine, 'current_depth', 0),
            "time_taken": float(sum(game_state["move_times"])) if game_state["move_times"] else 0.0,
            "memory_used": process.memory_info().rss,
            "cpu_percent": float(process.cpu_percent(interval=0.1))
        }
        
        # Update game's engine metrics
        game_state["engine_metrics"] = new_metrics
        
        return new_metrics
    except Exception as e:
        logger.error("Error getting engine metrics: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/set_depth")
async def set_search_depth(white: Optional[int] = None, black: Optional[int] = None):
    """Set the search depth for the engines."""
    global engine, engine2, white_depth, black_depth
    try:
        if white is not None:
            if white < 1 or white > 20:
                raise HTTPException(status_code=400, detail="White depth must be between 1 and 20")
            white_depth = white
            old_engine = engine
            engine = await create_engine(white_engine_type, white)
            engine.board = board.copy()
            await cleanup_engine(old_engine)
            
        if black is not None:
            if black < 1 or black > 20:
                raise HTTPException(status_code=400, detail="Black depth must be between 1 and 20")
            black_depth = black
            old_engine2 = engine2
            engine2 = await create_engine(black_engine_type, black)
            engine2.board = board.copy()
            await cleanup_engine(old_engine2)
            
        return {"success": True, "white_depth": white_depth, "black_depth": black_depth}
    except Exception as e:
        logger.error("Error in set_search_depth: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/set_engine")
async def set_engine_type(white: Optional[str] = None, black: Optional[str] = None):
    """Set the engine type for each player."""
    global engine, engine2, white_engine_type, black_engine_type
    
    valid_engines = ["minimax"]
    
    try:
        if white is not None:
            if white not in valid_engines:
                raise HTTPException(status_code=400, detail=f"Invalid engine type for white. Must be one of: {', '.join(valid_engines)}")
            white_engine_type = white
            old_engine = engine
            engine = await create_engine(white, white_depth)
            engine.board = board.copy()
            await cleanup_engine(old_engine)
            
        if black is not None:
            if black not in valid_engines:
                raise HTTPException(status_code=400, detail=f"Invalid engine type for black. Must be one of: {', '.join(valid_engines)}")
            black_engine_type = black
            old_engine2 = engine2
            engine2 = await create_engine(black, black_depth)
            engine2.board = board.copy()
            await cleanup_engine(old_engine2)
            
        return {
            "success": True,
            "white_engine": white_engine_type,
            "black_engine": black_engine_type
        }
    except Exception as e:
        logger.error("Error in set_engine_type: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/game/{game_id}")
async def get_game_state(game_id: str):
    """Get current game state."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game_state = games[game_id]
    board = game_state["board"]
    
    # Update timers if game is active
    current_time = time.time()
    if not board.is_game_over():
        if game_state["last_move_time"]:
            elapsed = current_time - game_state["last_move_time"]
            if board.turn:  # White's turn
                game_state["white_time"] = max(0, game_state["white_time"] - elapsed)
            else:  # Black's turn
                game_state["black_time"] = max(0, game_state["black_time"] - elapsed)

        game_state["last_move_time"] = current_time

    # Calculate average move time
    move_times = game_state["move_times"]
    avg_move_time = sum(move_times) / len(move_times) if move_times else 0

    # Determine game status and result
    status = "active"
    result = None
    result_reason = None
    
    # Check for game over conditions
    if board.is_game_over():
        status = "finished"
        if board.is_checkmate():
            result = "0-1" if board.turn else "1-0"
            result_reason = "Checkmate"
        elif board.is_stalemate():
            result = "1/2-1/2"
            result_reason = "Stalemate"
        elif board.is_insufficient_material():
            result = "1/2-1/2"
            result_reason = "Insufficient material"
        elif board.is_fifty_moves():
            result = "1/2-1/2"
            result_reason = "Fifty-move rule"
        elif board.is_repetition():
            result = "1/2-1/2"
            result_reason = "Threefold repetition"
    elif game_state["white_time"] <= 0:
        status = "finished"
        result = "0-1"
        result_reason = "White lost on time"
    elif game_state["black_time"] <= 0:
        status = "finished"
        result = "1-0"
        result_reason = "Black lost on time"

    return {
        "id": game_id,
        "fen": board.fen(),
        "status": status,
        "result": result,
        "resultReason": result_reason,
        "turn": "white" if board.turn else "black",
        "moveCount": board.fullmove_number,
        "whiteTime": game_state["white_time"],
        "blackTime": game_state["black_time"],
        "averageMoveTime": avg_move_time,
        "isCheck": board.is_check(),
        "isGameOver": board.is_game_over(),
        "legalMoves": [move.uci() for move in board.legal_moves],
        "mode": game_state["game_mode"],
        "engineMetrics": game_state["engine_metrics"]
    }

@app.post("/game/new")
async def new_game(
    white_name: str = "Player 1",
    black_name: str = "Player 2",
    mode: str = "human_vs_bot",
    white_engine: Optional[str] = None,
    black_engine: Optional[str] = None,
    depth: Optional[int] = None
):
    """Create a new game."""
    try:
        white_depth = depth if white_engine else 3
        black_depth = depth if black_engine else 3
        
        game_id = await create_game_state(mode, white_depth, black_depth)
        game = games[game_id]
        
        if white_engine:
            game["white_engine_type"] = white_engine
            old_engine = game["engine"]
            game["engine"] = await create_engine(white_engine, white_depth)
            game["engine"].board = game["board"].copy()
            await cleanup_engine(old_engine)
            
        if black_engine:
            game["black_engine_type"] = black_engine
            old_engine2 = game["engine2"]
            game["engine2"] = await create_engine(black_engine, black_depth)
            game["engine2"].board = game["board"].copy()
            await cleanup_engine(old_engine2)
        
        return {
            "id": game_id,
            "white": white_name,
            "black": black_name,
            "mode": mode,
            "whiteEngine": white_engine,
            "blackEngine": black_engine,
            "depth": depth
        }
    except Exception as e:
        logger.error("Error creating new game: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/game/{game_id}/move")
async def make_move(
    game_id: str,
    move: Dict[str, str],
    white_depth_param: Optional[int] = None,
    black_depth_param: Optional[int] = None
):
    """Make a move in the game."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    board = game["board"]
    
    try:
        # Validate move format
        if "from" not in move or "to" not in move:
            raise HTTPException(status_code=400, detail="Move must include 'from' and 'to' squares")
        
        # Create move string
        move_str = move["from"] + move["to"]
        if "promotion" in move:
            move_str += move["promotion"]
            
        logger.debug("Creating move from %s to %s", move["from"], move["to"])
        chess_move = chess.Move.from_uci(move_str)
        logger.debug("Created move: %s", chess_move.uci())
        
        # Validate it's the correct player's turn
        if game["game_mode"] == "bot_vs_bot":
            raise HTTPException(status_code=400, detail="Cannot make moves in bot vs bot mode")
            
        # Log current state
        logger.debug("Current board state: %s", board.fen())
        logger.debug("Legal moves: %s", [m.uci() for m in board.legal_moves])
        
        # Validate move is legal
        if chess_move not in board.legal_moves:
            logger.error("Illegal move: %s not in %s", chess_move.uci(), [m.uci() for m in board.legal_moves])
            raise HTTPException(status_code=400, detail="Illegal move")
            
        # Make the move
        start_time = time.time()
        board.push(chess_move)
        move_time = time.time() - start_time
        game["move_times"].append(move_time)
        
        # Update engine board states
        game["engine"].board = board.copy()
        game["engine2"].board = board.copy()
        
        # Get engine's response if game is not over
        engine_move = None
        if not board.is_game_over():
            current_engine = game["engine2"] if not board.turn else game["engine"]
            logger.debug("Engine making move")
            engine_move, score = await current_engine.get_move(board)
            if engine_move:
                board.push(engine_move)
                game["engine"].board = board.copy()
                game["engine2"].board = board.copy()
        
        # Update game state
        game_state = await get_game_state(game_id)
        game_state["playerMove"] = chess_move.uci()
        if engine_move:
            game_state["engineMove"] = engine_move.uci()
            
        return game_state
    except ValueError as e:
        logger.error("Invalid move format: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error making move: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

def main():
    """Run the bot."""
    import uvicorn
    import socket
    
    # Find an available port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('0.0.0.0', 0))
    port = sock.getsockname()[1]
    sock.close()
    
    logger.info("Starting server on port %d", port)
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main() 