from fastapi import FastAPI

from ai_chess_experiments.leaderboard import get_leaderboard

app = FastAPI()


@app.get("/api/leaderboard", tags=["Leaderboard"])
async def leaderboard_endpoint():
    """Endpoint to retrieve the current chess bots leaderboard."""
    return {"leaderboard": get_leaderboard()}


# You can add additional endpoints here (e.g. /health, /api/game, etc.) 