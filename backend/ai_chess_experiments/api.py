from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import chess
from typing import Optional, Dict, Any
import asyncio
from .engines.stockfish_nnue_engine import StockfishNNUEEngine

app = FastAPI()

# Cache for engine instances
engines: Dict[str, Any] = {}

class AnalysisRequest(BaseModel):
    fen: str
    depth: Optional[int] = 15
    engine: str = 'stockfish-nnue'

class AnalysisResponse(BaseModel):
    evaluation: float
    best_move: Optional[str] = None
    depth_reached: Optional[int] = None
    nodes_searched: Optional[int] = None

@app.post("/api/analyze")
async def analyze_position(request: AnalysisRequest) -> AnalysisResponse:
    """Analyze a chess position using the specified engine.
    
    Currently supports:
    - stockfish-nnue: Stockfish with NNUE evaluation (default)
    """
    try:
        # Validate FEN
        board = chess.Board(request.fen)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid FEN string")
        
    # Handle game over positions
    if board.is_game_over():
        if board.is_checkmate():
            return AnalysisResponse(
                evaluation=-100.0 if board.turn == chess.WHITE else 100.0
            )
        return AnalysisResponse(evaluation=0.0)  # Draw
        
    try:
        # Get or create engine instance
        engine_key = f"{request.engine}-{request.depth}"
        if engine_key not in engines:
            if request.engine == 'stockfish-nnue':
                engines[engine_key] = StockfishNNUEEngine(level=request.depth)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported engine: {request.engine}"
                )
            
        engine = engines[engine_key]
        
        # Get evaluation
        move, eval_score = await engine.get_move(board)
        
        return AnalysisResponse(
            evaluation=eval_score,
            best_move=move.uci() if move else None,
            depth_reached=request.depth
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

@app.on_event("shutdown")
async def cleanup():
    """Clean up engine resources on shutdown"""
    for engine in engines.values():
        try:
            await engine.cleanup()
        except:
            pass
    engines.clear() 