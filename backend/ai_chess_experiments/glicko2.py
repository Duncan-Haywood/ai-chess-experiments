"""
Glicko-2 rating system implementation.

The Glicko-2 system tracks three values for each player:
- rating (r): The player's actual rating
- rating deviation (RD): The uncertainty in the rating
- volatility (σ): How consistent the player performs

Reference: http://www.glicko.net/glicko/glicko2.pdf
"""

import math
from typing import NamedTuple
from dataclasses import dataclass

@dataclass
class GlickoRating:
    rating: float  # r
    rd: float     # rating deviation (φ)
    vol: float    # volatility (σ)

    @classmethod
    def default(cls) -> 'GlickoRating':
        """Create a default rating for a new player."""
        return cls(
            rating=1500.0,  # default rating
            rd=350.0,       # maximum uncertainty
            vol=0.06        # default volatility
        )

class GameResult(NamedTuple):
    opponent_rating: float
    opponent_rd: float
    score: float  # 1.0 for win, 0.5 for draw, 0.0 for loss

class Glicko2:
    """
    Glicko-2 rating system calculator.
    
    Uses the standard Glicko-2 scale (μ=1500, φ=350, σ=0.06, τ=0.5).
    """
    
    def __init__(self, tau: float = 0.5):
        self.tau = tau  # system constant, constrains volatility change
        
    def _g(self, rd: float) -> float:
        """Scale factor for rating deviation."""
        return 1.0 / math.sqrt(1 + (3 * rd**2) / (math.pi**2))
        
    def _E(self, rating: float, opp_r: float, opp_rd: float) -> float:
        """Expected score."""
        return 1.0 / (1 + math.exp(-self._g(opp_rd) * (rating - opp_r) / 400.0))
        
    def _v_inv(self, rating: float, results: list[GameResult]) -> float:
        """Estimated variance of rating based on game outcomes."""
        v_inv = 0.0
        for opp_r, opp_rd, _ in results:
            E = self._E(rating, opp_r, opp_rd)
            g = self._g(opp_rd)
            v_inv += (g**2) * E * (1 - E)
        return v_inv
        
    def update_rating(self, rating: GlickoRating, results: list[GameResult]) -> GlickoRating:
        """
        Update a player's rating based on game results.
        
        Args:
            rating: Current GlickoRating
            results: List of game results against opponents
            
        Returns:
            Updated GlickoRating
        """
        if not results:
            # If no games played, increase uncertainty
            return GlickoRating(
                rating=rating.rating,
                rd=min(math.sqrt(rating.rd**2 + rating.vol**2), 350.0),
                vol=rating.vol
            )
            
        # Step 1: Calculate variance
        v = 1.0 / self._v_inv(rating.rating, results)
        
        # Step 2: Calculate improvement
        delta = v * sum(
            self._g(opp_rd) * (score - self._E(rating.rating, opp_r, opp_rd))
            for opp_r, opp_rd, score in results
        )
        
        # Step 3: Update volatility
        vol_new = self._update_volatility(rating, v, delta)
        
        # Step 4: Update rating deviation
        rd_star = math.sqrt(rating.rd**2 + vol_new**2)
        rd_new = 1.0 / math.sqrt(1.0/rd_star**2 + 1.0/v)
        
        # Step 5: Update rating
        rating_new = rating.rating + (rd_new**2 * sum(
            self._g(opp_rd) * (score - self._E(rating.rating, opp_r, opp_rd))
            for opp_r, opp_rd, score in results
        ))
        
        return GlickoRating(
            rating=rating_new,
            rd=min(rd_new, 350.0),  # cap RD at 350
            vol=vol_new
        )
        
    def _update_volatility(self, rating: GlickoRating, v: float, delta: float) -> float:
        """
        Update volatility using iterative algorithm.
        
        This implements the iteration algorithm from step 5.1 of Glickman's paper.
        """
        a = math.log(rating.vol**2)
        eps = 0.000001
        
        def f(x: float) -> float:
            """The function to find the zero of."""
            ex = math.exp(x)
            num = ex * (delta**2 - rating.rd**2 - v - ex)
            den = 2 * (rating.rd**2 + v + ex)**2
            return x - a - (num/den) / self.tau**2
            
        # Find bounds
        A = a
        if delta**2 > rating.rd**2 + v:
            B = math.log(delta**2 - rating.rd**2 - v)
        else:
            k = 1
            while f(a - k * self.tau) < 0:
                k += 1
            B = a - k * self.tau
            
        # Binary search
        fa = f(A)
        fb = f(B)
        while abs(B - A) > eps:
            C = A + (A - B) * fa/(fb - fa)
            fc = f(C)
            if fc * fb < 0:
                A = B
                fa = fb
            else:
                fa = fa/2
            B = C
            fb = fc
            
        return math.exp(A/2) 