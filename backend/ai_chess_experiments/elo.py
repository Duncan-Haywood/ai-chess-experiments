''' 
This module implements Elo rating calculation functions following a chess.com style Elo rating structure.
'''

def expected_score(rating_a: float, rating_b: float) -> float:
    """
    Calculate the expected score for a player with rating 'rating_a' against an opponent with rating 'rating_b'.
    """
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))


def update_rating(rating: float, opponent_rating: float, score: float, k: int = 32) -> float:
    """
    Update rating for one player.
    :param rating: The current rating of the player.
    :param opponent_rating: The opponent's rating.
    :param score: The score achieved by the player (1 for win, 0.5 for draw, 0 for loss).
    :param k: The K-factor used for adjustments (default 32).
    """
    return rating + k * (score - expected_score(rating, opponent_rating))


def update_ratings(rating_a: float, rating_b: float, score_a: float, k: int = 32) -> tuple:
    """
    Update ratings for a match between two players.
    :param rating_a: Rating of player A.
    :param rating_b: Rating of player B.
    :param score_a: Actual score for player A (1 for win, 0.5 for draw, 0 for loss).
    :param k: The K-factor used for adjustments (default 32).
    :return: A tuple (new_rating_a, new_rating_b).
    """
    new_rating_a = update_rating(rating_a, rating_b, score_a, k)
    new_rating_b = update_rating(rating_b, rating_a, 1 - score_a, k)
    return new_rating_a, new_rating_b 