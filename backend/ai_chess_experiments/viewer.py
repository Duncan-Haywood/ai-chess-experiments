from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import chess
import json
from typing import Optional, Dict, List
import aiohttp
import os
from datetime import datetime, timedelta

app = FastAPI()
active_game: Optional[Dict] = None

# Lichess API helpers
LICHESS_API_TOKEN = os.getenv('LICHESS_API_TOKEN')
LICHESS_API_URL = "https://lichess.org/api"

async def get_lichess_data(endpoint: str) -> Dict:
    headers = {"Authorization": f"Bearer {LICHESS_API_TOKEN}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{LICHESS_API_URL}/{endpoint}", headers=headers) as response:
            return await response.json()

@app.get("/api/stats")
async def get_stats():
    """Get bot statistics from Lichess."""
    account = await get_lichess_data("account")
    return {
        "username": account.get("username"),
        "rating": {
            "bullet": account.get("perfs", {}).get("bullet", {}).get("rating", 1500),
            "blitz": account.get("perfs", {}).get("blitz", {}).get("rating", 1500),
            "rapid": account.get("perfs", {}).get("rapid", {}).get("rating", 1500),
        },
        "created_at": account.get("createdAt"),
        "total_games": account.get("count", {}).get("all", 0)
    }

@app.get("/api/games/history")
async def get_game_history(limit: int = 10):
    """Get recent games from Lichess."""
    games = await get_lichess_data(f"account/playing")
    history = []
    
    for game in games.get("nowPlaying", [])[:limit]:
        history.append({
            "id": game.get("gameId"),
            "opponent": game.get("opponent", {}).get("username"),
            "my_color": game.get("color"),
            "last_move": game.get("lastMove"),
            "time_control": f"{game.get('speed')} - {game.get('time')}+{game.get('increment')}",
            "status": game.get("status")
        })
    
    return history

# ... rest of the viewer.py code (HTML and WebSocket handlers) stays the same ... 