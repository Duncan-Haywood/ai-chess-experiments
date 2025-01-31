import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Create logs directory if it doesn't exist
log_dir = Path(__file__).parent.parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_dir / f"chess_bot_{datetime.now().strftime('%Y%m%d')}.log")
    ]
)

logger = logging.getLogger("chess_bot")

class GameLogger:
    """Structured logging for chess game events."""
    
    @staticmethod
    def log_game_event(
        event_type: str,
        details: Dict[str, Any],
        error: Optional[Exception] = None,
        level: str = "INFO"
    ) -> None:
        """Log a game event with structured data."""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details
        }
        
        if error:
            log_data["error"] = {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc()
            }
        
        log_method = getattr(logger, level.lower())
        log_method(f"Game Event: {log_data}")

    @staticmethod
    def log_engine_error(engine_type: str, error: Exception, context: Dict[str, Any]) -> None:
        """Log chess engine specific errors."""
        GameLogger.log_game_event(
            event_type="engine_error",
            details={
                "engine_type": engine_type,
                "context": context
            },
            error=error,
            level="ERROR"
        )

    @staticmethod
    def log_game_state(
        game_id: str,
        fen: str,
        last_move: Optional[str],
        status: str,
        additional_info: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log current game state."""
        details = {
            "game_id": game_id,
            "fen": fen,
            "last_move": last_move,
            "status": status
        }
        if additional_info:
            details.update(additional_info)
            
        GameLogger.log_game_event(
            event_type="game_state",
            details=details
        )

    @staticmethod
    def log_move_attempt(
        game_id: str,
        move: str,
        player: str,
        is_valid: bool,
        error: Optional[Exception] = None
    ) -> None:
        """Log move attempts, including validation failures."""
        GameLogger.log_game_event(
            event_type="move_attempt",
            details={
                "game_id": game_id,
                "move": move,
                "player": player,
                "is_valid": is_valid
            },
            error=error,
            level="ERROR" if error else "INFO"
        )

def get_logger() -> logging.Logger:
    """Get the configured logger instance."""
    return logger 