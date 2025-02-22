from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class GameResult(enum.Enum):
    WHITE_WIN = "1-0"
    BLACK_WIN = "0-1"
    DRAW = "1/2-1/2"

class Game(Base):
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True)
    white_model = Column(String, nullable=False)
    black_model = Column(String, nullable=False)
    pgn = Column(String, nullable=False)
    result = Column(Enum(GameResult), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    num_moves = Column(Integer, nullable=False)
    termination_reason = Column(String)

class Rating(Base):
    __tablename__ = "ratings"
    
    id = Column(Integer, primary_key=True)
    model_name = Column(String, nullable=False)
    rating = Column(Float, nullable=False, default=1500)
    rd = Column(Float, nullable=False, default=350)  # Rating deviation
    vol = Column(Float, nullable=False, default=0.06)  # Volatility
    num_games = Column(Integer, nullable=False, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)

class GameMove(Base):
    __tablename__ = "game_moves"
    
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    move_number = Column(Integer, nullable=False)
    move_uci = Column(String, nullable=False)
    fen_after = Column(String, nullable=False)
    time_taken = Column(Float)  # Time in seconds the model took to make the move
    llm_move_message = Column(Text, nullable=False)  # Full response from LLM for move generation
    llm_extraction_message = Column(Text, nullable=False)  # Full response from LLM for move extraction
    model_used = Column(String, nullable=False)  # Which model made this move 