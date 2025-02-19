''' 
Module for managing the chess bot leaderboard using the Glicko-2 rating system.

This module maintains ratings, rating deviations (RD), and volatility for each bot,
providing a more accurate picture of bot strength and rating uncertainty.
'''

from typing import List, TypedDict, Dict
from .glicko2 import Glicko2, GlickoRating, GameResult

class LeaderboardEntry(TypedDict):
    bot: str
    rating: float
    rd: float  # Rating Deviation
    volatility: float

# Initialize Glicko-2 calculator
glicko = Glicko2()

# In-memory leaderboard with default Glicko-2 ratings
leaderboard: Dict[str, GlickoRating] = {}

def get_or_create_rating(bot_name: str) -> GlickoRating:
    """Get existing rating or create default for new bot."""
    if bot_name not in leaderboard:
        leaderboard[bot_name] = GlickoRating.default()
    return leaderboard[bot_name]

def record_match_result(bot_a: str, bot_b: str, score_a: float) -> None:
    """
    Record the result of a match between bot_a and bot_b.

    :param bot_a: Identifier for bot A
    :param bot_b: Identifier for bot B
    :param score_a: Score for bot A (1 for win, 0.5 for draw, 0 for loss)
    """
    # Get or create ratings
    rating_a = get_or_create_rating(bot_a)
    rating_b = get_or_create_rating(bot_b)

    # Update bot A's rating
    result_a = [GameResult(rating_b.rating, rating_b.rd, score_a)]
    leaderboard[bot_a] = glicko.update_rating(rating_a, result_a)

    # Update bot B's rating
    result_b = [GameResult(rating_a.rating, rating_a.rd, 1.0 - score_a)]
    leaderboard[bot_b] = glicko.update_rating(rating_b, result_b)

def get_leaderboard() -> List[LeaderboardEntry]:
    """
    Retrieve the current leaderboard sorted by rating descending.
    Includes rating deviation (RD) to show uncertainty.

    :return: List of LeaderboardEntry with bot names, ratings, and uncertainties
    """
    # Sort by rating, but could also consider rating - 2*RD for conservative ranking
    sorted_board = sorted(
        leaderboard.items(),
        key=lambda x: x[1].rating,
        reverse=True
    )
    
    return [
        {
            "bot": bot,
            "rating": rating.rating,
            "rd": rating.rd,
            "volatility": rating.vol
        }
        for bot, rating in sorted_board
    ] 