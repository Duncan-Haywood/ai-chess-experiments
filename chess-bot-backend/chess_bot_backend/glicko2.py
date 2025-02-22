"""
Glicko-2 Rating System for LLM Chess Engines

This module implements the Glicko-2 rating system, specifically adapted for rating LLM chess engines.
The system tracks three key metrics for each engine:

Core Metrics:
------------
1. Rating (μ):
   - Represents the engine's playing strength
   - Default: 1500 (standard starting rating)
   - Higher values indicate stronger play

2. Rating Deviation (RD/φ):
   - Represents uncertainty in the rating
   - Default: 500 (maximum uncertainty for new engines)
   - Decreases with more games played
   - Increases during periods of inactivity

3. Volatility (σ):
   - Represents consistency of performance
   - Default: 0.06 (standard starting volatility)
   - Lower values indicate more consistent play
   - Higher values suggest erratic performance

LLM Engine Integration:
----------------------
For rating LLM chess engines, special considerations should be made:

1. Rating Initialization:
   - New LLM engines should start with default ratings (1500)
   - When using different model versions/temperatures, treat each as a separate player
   - Example: "gpt-4-t0.7" and "gpt-4-t0.3" should have separate ratings

2. Game Results:
   - Wins/losses should be clear and deterministic (checkmate, resignation, timeout)
   - For draws, ensure they're legitimate (stalemate, repetition, insufficient material)
   - Avoid counting aborted or incomplete games

3. Rating Periods:
   - Group games into rating periods (e.g., daily or weekly updates)
   - Update all ratings simultaneously at the end of each period
   - This ensures rating changes are based on consistent opponent ratings

4. Performance Analysis:
   - Track rating changes across model versions
   - Monitor RD (rating deviation) to ensure sufficient games
   - Use volatility (σ) to identify inconsistent performance

Usage Example:
-------------
```python
# Initialize rating system
rating_system = RatingSystem()

# Add different LLM configurations as players
rating_system.add_player("gpt4-t0.7")
rating_system.add_player("gpt4-t0.3")
rating_system.add_player("claude-t0.5")

# Record game results
rating_system.record_game("gpt4-t0.7", "claude-t0.5", score=1.0)  # GPT-4 wins
rating_system.record_game("gpt4-t0.3", "claude-t0.5", score=0.5)  # Draw

# Update all ratings at end of rating period
rating_system.update_ratings()

# Analyze performance
gpt4_rating = rating_system.get_rating("gpt4-t0.7")
print(f"Rating: {gpt4_rating.rating:.1f} ± {2*gpt4_rating.rd:.1f}")
```

Implementation Details:
---------------------
1. Rating Scale:
   - Uses standard Glicko-2 scale (μ=1500, φ=350, σ=0.06)
   - Rating differences of 100 points ≈ 64% expected score
   - Rating differences of 200 points ≈ 76% expected score

2. Update Process:
   - Step 1: Calculate variance (v) from game outcomes
   - Step 2: Calculate improvement/delta (δ)
   - Step 3: Update volatility (σ') using iterative algorithm
   - Step 4: Update rating deviation (φ') based on new volatility
   - Step 5: Update rating (μ') using game outcomes

3. System Constants:
   - τ (tau): Controls volatility change (default: 0.5)
   - Convergence tolerance: 0.000001 for volatility calculation
   - Maximum RD: 500 (caps uncertainty growth)

Storage Recommendations:
----------------------
1. In-Memory Testing:
   - Use RatingSystem class for quick testing
   - Suitable for development and simulation

2. Production Database:
   - Store GlickoRating objects in database
   - Use Glicko2 calculator directly with DB storage
   - Track additional metadata:
     * Model version
     * Temperature settings
     * Game duration
     * Opening played
     * Termination reason

3. Performance Tracking:
   - Log rating changes over time
   - Monitor RD convergence
   - Track volatility trends
   - Store game results for analysis

Reference: http://www.glicko.net/glicko/glicko2.pdf
"""

import math
from typing import NamedTuple
from dataclasses import dataclass

# System constants
DEFAULT_RATING = 1500.0
DEFAULT_RD = 500.0
DEFAULT_VOLATILITY = 0.06
DEFAULT_TAU = 0.5
CONVERGENCE_TOLERANCE = 0.000001

# Mathematical constants
PI_SQUARED = math.pi ** 2
SCALE_FACTOR = 400.0  # Used in E function for logistic curve scaling

@dataclass
class GlickoRating:
    rating: float  # μ (mu) - Player's rating
    rd: float     # φ (phi) - Rating deviation
    vol: float    # σ (sigma) - Volatility

    @classmethod
    def default(cls) -> 'GlickoRating':
        """Create a default rating for a new player."""
        return cls(
            rating=DEFAULT_RATING,
            rd=DEFAULT_RD,
            vol=DEFAULT_VOLATILITY
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
        """
        Scale factor g(φ) for rating deviation.
        
        Formula: g(φ) = 1 / sqrt(1 + 3φ²/π²)
        """
        return 1.0 / math.sqrt(1 + (3 * rd**2) / PI_SQUARED)
        
    def _E(self, rating: float, opp_r: float, opp_rd: float) -> float:
        """
        Expected score E(μ,μj,φj) against an opponent.
        
        Formula: E = 1 / (1 + exp(-g(φ)(μ-μj)/400))
        
        Args:
            rating: Player's rating (μ)
            opp_r: Opponent's rating (μj)
            opp_rd: Opponent's rating deviation (φj)
        """
        g_phi = self._g(opp_rd)
        rating_diff = rating - opp_r
        return 1.0 / (1 + math.exp(-g_phi * rating_diff / SCALE_FACTOR))
        
    def _v_inv(self, rating: float, results: list[GameResult]) -> float:
        """
        Compute inverse of estimated variance v⁻¹ of rating based on game outcomes.
        
        Formula: v⁻¹ = Σ[g(φj)² * E(μ,μj,φj) * (1 - E(μ,μj,φj))]
        """
        variance_sum = 0.0
        for opp_r, opp_rd, _ in results:
            E = self._E(rating, opp_r, opp_rd)
            g_phi = self._g(opp_rd)
            variance_sum += (g_phi**2) * E * (1 - E)
        return variance_sum
        
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
                rd=min(math.sqrt(rating.rd**2 + rating.vol**2), 500.0),
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
            rd=min(rd_new, 500.0),  # cap RD at 500
            vol=vol_new
        )
        
    def _update_volatility(self, rating: GlickoRating, v: float, delta: float) -> float:
        """
        Update volatility using iterative algorithm.
        
        This implements the iteration algorithm from step 5.1 of Glickman's paper.
        Uses the Illinois algorithm, a variant of the regula falsi method.
        
        Args:
            rating: Current rating object
            v: Variance of rating
            delta: Rating change factor
            
        Returns:
            New volatility value σ'
        """
        a = math.log(rating.vol**2)  # α = ln(σ²)
        
        def f(x: float) -> float:
            """
            The function to find the zero of.
            
            Formula: f(x) = (e^x * (δ² - φ² - v - e^x))/(2(φ² + v + e^x)²) - (x - α)/τ²
            """
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
        while abs(B - A) > CONVERGENCE_TOLERANCE:
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