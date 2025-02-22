"""
SQLAlchemy Models for LLM Chess Engine Rating System

This module implements the database schema for tracking chess games between LLM engines
and their Glicko2 ratings. The schema consists of three main tables:

Database Schema:
---------------
1. games
   - Stores complete chess games between two LLM models
   - Links to individual moves through game_moves table
   - Tracks game outcomes and metadata

2. game_moves
   - Stores each individual move in every game
   - Links back to parent game
   - Contains full LLM analysis and responses

3. ratings
   - Tracks Glicko2 ratings for each LLM model
   - Updated after each rating period
   - Stores rating uncertainty and volatility

Key Relationships:
----------------
Game (1) <----> (Many) GameMove
- Each Game has multiple GameMoves
- Each GameMove belongs to exactly one Game
- Cascade deletion: moves are deleted with their game

Rating (1) <----> (Many) Games
- Each Rating corresponds to one LLM model
- Models can participate in multiple games
- Rating updated based on game results

Data Storage Details:
-------------------
1. Move Information:
   - UCI format moves (e.g., 'e2e4', 'e7e8q')
   - FEN position after each move
   - Complete LLM responses and analysis
   - Timing information

2. Game Metadata:
   - Participating models (white/black)
   - Complete PGN record
   - Game result and termination reason
   - Timestamp and move count

3. Rating Data:
   - Current rating (μ)
   - Rating deviation (RD/φ)
   - Volatility (σ)
   - Game count and last update time

Performance Considerations:
-------------------------
- Indexed fields for common queries
- Appropriate field size constraints
- Efficient relationship mappings
- Cascade delete behaviors
"""

import enum
from typing import Optional, List, Any
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.schema import Index

class Base(DeclarativeBase):
    pass

class GameResult(str, enum.Enum):
    """
    Possible results of a chess game.
    
    Values correspond to standard PGN result notation:
    - "1-0": White wins
    - "0-1": Black wins
    - "1/2-1/2": Draw
    """
    WHITE_WIN = "1-0"
    BLACK_WIN = "0-1"
    DRAW = "1/2-1/2"

class Game(Base):
    """
    A chess game between two LLM models.
    
    Core Data:
    ---------
    - white_model: Name/version of white-playing LLM
    - black_model: Name/version of black-playing LLM
    - pgn: Complete game record in PGN format
    - result: Game outcome (1-0, 0-1, or 1/2-1/2)
    - num_moves: Total number of moves played
    
    Metadata:
    --------
    - timestamp: When the game was played
    - termination_reason: How the game ended (checkmate, timeout, etc.)
    
    Relationships:
    ------------
    - moves: List[GameMove] - All moves in the game, ordered by move_number
    """
    __tablename__ = "games"
    
    # Core fields
    id: Mapped[int] = mapped_column(primary_key=True)
    white_model: Mapped[str] = mapped_column(String(100), nullable=False)
    black_model: Mapped[str] = mapped_column(String(100), nullable=False)
    pgn: Mapped[str] = mapped_column(Text, nullable=False)
    result: Mapped[GameResult] = mapped_column(Enum(GameResult), nullable=False)
    num_moves: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Metadata
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    termination_reason: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Relationships
    moves: Mapped[List["GameMove"]] = relationship(
        "GameMove",
        back_populates="game",
        cascade="all, delete-orphan",
        order_by="GameMove.move_number"
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index('ix_games_white_model', 'white_model'),
        Index('ix_games_black_model', 'black_model'),
        Index('ix_games_timestamp', 'timestamp'),
    )

class Rating(Base):
    """
    Glicko2 rating for an LLM chess engine.
    
    Core Rating Values:
    ----------------
    - rating (μ): Base rating, default 1500
    - rd (φ): Rating deviation, default 350
    - vol (σ): Rating volatility, default 0.06
    
    Statistics:
    ----------
    - num_games: Total games played
    - last_updated: Timestamp of last rating update
    
    Notes:
    -----
    - Each model version should have its own rating
    - RD increases during inactivity
    - Volatility reflects rating stability
    """
    __tablename__ = "ratings"
    
    # Identification
    id: Mapped[int] = mapped_column(primary_key=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    
    # Glicko2 rating components
    rating: Mapped[float] = mapped_column(Float, nullable=False, default=1500.0)
    rd: Mapped[float] = mapped_column(Float, nullable=False, default=350.0)
    vol: Mapped[float] = mapped_column(Float, nullable=False, default=0.06)
    
    # Statistics
    num_games: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Index for quick lookups
    __table_args__ = (
        Index('ix_ratings_model_name', 'model_name', unique=True),
    )

class GameMove(Base):
    """
    A single move in a chess game with LLM analysis.
    
    Move Information:
    ---------------
    - move_number: Position in game (1-based)
    - move_uci: Move in UCI format (e.g., 'e2e4')
    - fen_after: Board position after move
    - time_taken: Seconds taken to generate move
    
    LLM Analysis:
    -----------
    - llm_move_message: Complete response for move generation
    - llm_extraction_message: Response from move extraction
    - model_used: Which LLM made this move
    
    Relationships:
    ------------
    - game: Parent Game object
    - game_id: Foreign key to games table
    """
    __tablename__ = "game_moves"
    
    # Primary key and foreign key
    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    
    # Move details
    move_number: Mapped[int] = mapped_column(Integer, nullable=False)
    move_uci: Mapped[str] = mapped_column(String(10), nullable=False)
    fen_after: Mapped[str] = mapped_column(String(100), nullable=False)
    time_taken: Mapped[Optional[float]] = mapped_column(Float)
    
    # LLM analysis
    llm_move_message: Mapped[str] = mapped_column(Text, nullable=False)
    llm_extraction_message: Mapped[str] = mapped_column(Text, nullable=False)
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Relationship back to game
    game: Mapped["Game"] = relationship("Game", back_populates="moves")
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('ix_game_moves_game_id_move_number', 'game_id', 'move_number', unique=True),
        Index('ix_game_moves_model_used', 'model_used'),
    ) 