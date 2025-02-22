"""
Tournament Runner for LLM Chess Engines

This module implements a tournament system for running chess games between LLM models.
It handles:
- Game scheduling and execution
- Rating updates
- Data persistence
- Error recovery
"""

import asyncio
import chess
import chess.pgn
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Sequence

from sqlalchemy.orm import Session
from sqlalchemy import select, create_engine

from .models import Game, GameMove, Rating, GameResult
from .llm_chess_engine import LLMEngine
from .data_manager import DataManager
from .glicko2_ratings import GlickoRating, Glicko2, GameResult as GlickoGameResult

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chess_tournament.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TournamentConfig:
    """Configuration for tournament settings."""
    def __init__(
        self,
        model1: str = "o3-mini",
        model2: str = "gpt-4o",
        num_games: int = 10,
        data_dir: str = "chess_data",
        export_after_game: bool = True,
        db_url: str = "postgresql://localhost/chess_bot"
    ):
        self.model1 = model1
        self.model2 = model2
        self.num_games = num_games
        self.data_dir = data_dir
        self.export_after_game = export_after_game
        self.db_url = db_url

class ChessTournament:
    """
    Manages chess tournaments between LLM models.
    
    Features:
    --------
    - Automatic game scheduling
    - Rating updates after games
    - Data persistence
    - Error recovery
    - Detailed logging
    """
    
    def __init__(self, config: TournamentConfig, session: Session):
        """
        Initialize tournament manager.
        
        Args:
            config: Tournament configuration
            session: SQLAlchemy session
        """
        self.config = config
        self.session = session
        self.engine = LLMEngine()
        self.data_manager = DataManager(config.data_dir)
        
        # Validate models
        if not self._validate_models():
            raise ValueError(f"Invalid models: {config.model1}, {config.model2}")
            
        # Initialize or load ratings
        self._init_ratings()
        
    def _validate_models(self) -> bool:
        """Check if configured models are available in LLM engine."""
        all_models = (
            self.engine.openai_models +
            self.engine.deepseek_models +
            self.engine.google_models +
            self.engine.anthropic_models
        )
        return self.config.model1 in all_models and self.config.model2 in all_models
        
    def _init_ratings(self) -> None:
        """Initialize or load ratings for both models."""
        for model in [self.config.model1, self.config.model2]:
            rating = self.session.execute(
                select(Rating).filter_by(model_name=model)
            ).scalar_one_or_none()
            
            if rating is None:
                rating = Rating(model_name=model)
                self.session.add(rating)
                
        self.session.commit()
        
    async def run_initial_test(self, num_games: Optional[int] = None) -> Sequence[Game]:
        """
        Run initial test games between the two models.
        
        Args:
            num_games: Override default number of games
            
        Returns:
            List of completed Game objects
        """
        n = num_games or self.config.num_games
        completed_game_ids = []
        
        try:
            for i in range(n):
                # Alternate colors
                if i % 2 == 0:
                    white, black = self.config.model1, self.config.model2
                else:
                    white, black = self.config.model2, self.config.model1
                    
                logger.info(f"Starting game {i+1}/{n}: {white} (White) vs {black} (Black)")
                
                try:
                    game = await self._play_game(white, black)
                    completed_game_ids.append(game.id)
                    
                    # Update ratings after each game
                    self._update_ratings(game)
                    
                    # Export if configured
                    if self.config.export_after_game:
                        self.data_manager.export_game_data(
                            self.config.db_url,
                            [game.id]
                        )
                        
                except Exception as e:
                    logger.error(f"Error in game {i+1}: {str(e)}")
                    continue
                    
        finally:
            # Always export session at end
            if completed_game_ids:
                self.data_manager.export_game_data(
                    self.config.db_url,
                    completed_game_ids
                )
                
        return self.data_manager.get_completed_games(self.session)
    
    async def _play_game(self, white_model: str, black_model: str) -> Game:
        """Play a single game between two models."""
        board = chess.Board()
        moves: List[GameMove] = []
        game_start = datetime.utcnow()
        
        # Create game record
        game = Game(
            white_model=white_model,
            black_model=black_model,
            pgn="",  # Will be updated at end
            result=GameResult.DRAW,  # Default until game ends
            num_moves=0,
            timestamp=game_start
        )
        self.session.add(game)
        self.session.flush()  # Get game.id
        
        try:
            while not board.is_game_over():
                is_white = board.turn
                current_model = white_model if is_white else black_model
                
                # Get move from model
                move_start = datetime.utcnow()
                try:
                    chess_move, analysis = await self.engine.get_move(board, current_model)
                except Exception as e:
                    logger.error(f"Error getting move: {str(e)}")
                    game.termination_reason = f"Error: {str(e)}"
                    break
                    
                time_taken = (datetime.utcnow() - move_start).total_seconds()
                
                # Apply move
                board.push(chess_move)
                
                # Record move
                move = GameMove(
                    game_id=game.id,
                    move_number=len(moves) + 1,
                    move_uci=chess_move.uci(),
                    fen_after=board.fen(),
                    time_taken=time_taken,
                    llm_move_message=analysis,
                    llm_extraction_message="",  # Already extracted
                    model_used=current_model
                )
                moves.append(move)
                
            # Game ended, update final state
            game.moves = moves
            game.num_moves = len(moves)
            game.pgn = str(chess.pgn.Game.from_board(board))
            
            # Set result
            if board.is_checkmate():
                game.result = GameResult.WHITE_WIN if not board.turn else GameResult.BLACK_WIN
                game.termination_reason = "Checkmate"
            elif board.is_stalemate():
                game.termination_reason = "Stalemate"
            elif board.is_insufficient_material():
                game.termination_reason = "Insufficient material"
            elif board.is_fifty_moves():
                game.termination_reason = "Fifty-move rule"
            elif board.is_repetition():
                game.termination_reason = "Threefold repetition"
            
            self.session.commit()
            return game
            
        except Exception as e:
            self.session.rollback()
            raise
            
    def _update_ratings(self, game: Game) -> None:
        """Update Glicko2 ratings after a game."""
        # Get current ratings
        white_rating = self.session.execute(
            select(Rating).filter_by(model_name=game.white_model)
        ).scalar_one()
        black_rating = self.session.execute(
            select(Rating).filter_by(model_name=game.black_model)
        ).scalar_one()
        
        # Convert to Glicko ratings
        white_glicko = GlickoRating(
            rating=white_rating.rating,
            rd=white_rating.rd,
            vol=white_rating.vol
        )
        black_glicko = GlickoRating(
            rating=black_rating.rating,
            rd=black_rating.rd,
            vol=black_rating.vol
        )
        
        # Create match result
        if game.result == GameResult.WHITE_WIN:
            score = 1.0
        elif game.result == GameResult.BLACK_WIN:
            score = 0.0
        else:
            score = 0.5
            
        # Create Glicko2 calculator
        glicko2 = Glicko2()
        
        # Update white's rating
        white_result = [GlickoGameResult(
            opponent_rating=black_glicko.rating,
            opponent_rd=black_glicko.rd,
            score=score
        )]
        new_white = glicko2.update_rating(white_glicko, white_result)
        
        # Update black's rating
        black_result = [GlickoGameResult(
            opponent_rating=white_glicko.rating,
            opponent_rd=white_glicko.rd,
            score=1.0 - score
        )]
        new_black = glicko2.update_rating(black_glicko, black_result)
        
        # Save updated ratings
        white_rating.rating = new_white.rating
        white_rating.rd = new_white.rd
        white_rating.vol = new_white.vol
        white_rating.num_games += 1
        white_rating.last_updated = datetime.utcnow()
        
        black_rating.rating = new_black.rating
        black_rating.rd = new_black.rd
        black_rating.vol = new_black.vol
        black_rating.num_games += 1
        black_rating.last_updated = datetime.utcnow()
        
        self.session.commit() 