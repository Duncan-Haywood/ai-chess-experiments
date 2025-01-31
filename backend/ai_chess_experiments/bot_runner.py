import chess
import time
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ai_chess_experiments.engines.base_engine import BaseChessEngine
from ai_chess_experiments.engines.minimax_engine import MinimaxEngine

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
engine = MinimaxEngine(depth=3)
engine2 = MinimaxEngine(depth=3)  # Second engine for bot vs bot
board = chess.Board()
game_mode = "human_vs_bot"  # or "bot_vs_bot"

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
    
@app.get("/game")
async def get_game_state():
    """Get current game state."""
    global board, engine, game_mode
    try:
        if board is None:
            board = chess.Board()
            engine.board = board

        # Ensure engine's board is synced
        engine.board = board
        
        # If it's bot vs bot mode and it's bot's turn to move
        if game_mode == "bot_vs_bot" and not board.is_game_over():
            current_engine = engine if board.turn else engine2
            move = current_engine.get_move()
            board.push(move)
            engine.board = board
            engine2.board = board
        
        return {
            "fen": board.fen(),
            "lastMove": board.peek().uci() if len(board.move_stack) > 0 else None,
            "whiteTime": 180,
            "blackTime": 180,
            "whiteName": "Bot 1" if game_mode == "bot_vs_bot" else "You",
            "blackName": "Bot 2" if game_mode == "bot_vs_bot" else "Bot",
            "status": "active" if not board.is_game_over() else "finished",
            "result": board.result() if board.is_game_over() else None,
            "moveCount": len(board.move_stack),
            "gameMode": game_mode
        }
    except chess.BoardError as be:
        raise HTTPException(status_code=500, detail=f"Chess board error: {str(be)}")
    except Exception as e:
        print(f"Error in get_game_state: {str(e)}")  # Log the error
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/move")
async def make_move(move: Dict[str, str]):
    """Make a move in the current game."""
    global board, engine, engine2, game_mode
    try:
        if not board:
            raise HTTPException(status_code=400, detail="No active game")
        
        if game_mode == "bot_vs_bot":
            raise HTTPException(status_code=400, detail="Cannot make moves in bot vs bot mode")
            
        # Convert from/to squares to UCI format
        move_uci = move["from"] + move["to"]
        if "promotion" in move and move["promotion"]:
            move_uci += move["promotion"]
            
        # Create and validate the move
        chess_move = chess.Move.from_uci(move_uci)
        if chess_move not in board.legal_moves:
            raise HTTPException(status_code=400, detail="Illegal move")
            
        # Make player's move
        board.push(chess_move)
        engine.board = board  # Sync engine board
        
        # Let engine make its move if game not over
        if not board.is_game_over():
            engine_move = engine.get_move()
            board.push(engine_move)
            engine.board = board  # Sync engine board again
        
        return {
            "success": True,
            "playerMove": chess_move.uci(),
            "engineMove": engine_move.uci() if not board.is_game_over() else None,
            "gameState": {
                "fen": board.fen(),
                "lastMove": board.peek().uci() if len(board.move_stack) > 0 else None,
                "whiteTime": 180,
                "blackTime": 180,
                "whiteName": "You",
                "blackName": "Bot",
                "status": "active" if not board.is_game_over() else "finished",
                "result": board.result() if board.is_game_over() else None,
                "moveCount": len(board.move_stack),
                "gameMode": game_mode
            }
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/new_game")
async def new_game(mode: str = "human_vs_bot"):
    """Start a new game."""
    global board, engine, engine2, game_mode
    try:
        game_mode = mode
        board = chess.Board()
        engine = MinimaxEngine(depth=3)  # Reset engine for new game
        engine2 = MinimaxEngine(depth=3)  # Reset second engine
        engine.board = board  # Sync engine board
        engine2.board = board  # Sync second engine board
        return {"success": True, "mode": mode}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def main():
    """Run the bot."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main() 