from pathlib import Path
from datetime import datetime
import json
import uuid
import chess
import pandas as pd
from typing import List, Optional, Dict

class GameRecorder:
    def __init__(self, data_dir: Path = Path("./data/matches")):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.current_batches = {}  # Dict to hold games for each pairing
        
    def get_pairing_key(self, model1: str, model2: str):
        return f"{min(model1, model2)}_vs_{max(model1, model2)}"

    def record_game(
        self,
        white_model: str,
        black_model: str,
        moves: List[chess.Move],
        result: str,
        llm_responses: List[str],
        final_position: Optional[chess.Board] = None
    ):
        """Record a game between two models.
        
        Args:
            white_model: Name of the model playing white
            black_model: Name of the model playing black
            moves: List of chess.Move objects
            result: Game result ("1-0", "0-1", or "1/2-1/2")
            llm_responses: List of LLM explanations for moves (if applicable)
            final_position: Final board position (optional)
        """
        pairing_key = self.get_pairing_key(white_model, black_model)
        
        # Convert moves to UCI format for storage
        moves_uci = [move.uci() for move in moves]
        
        # Reconstruct final position if not provided
        if final_position is None:
            final_position = chess.Board()
            for move in moves:
                final_position.push(move)
                
        game_data = {
            "game_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "white": white_model,
            "black": black_model,
            "result": result,
            "moves": moves_uci,
            "llm_responses": llm_responses,
            "final_fen": final_position.fen(),
            "total_moves": len(moves),
            "opening_eco": None,  # Could add ECO code detection
            "termination": self._get_termination_reason(final_position)
        }

        # Load or create pairing data
        if pairing_key not in self.current_batches:
            file_path = self.data_dir / f"{pairing_key}.json"
            if file_path.exists():
                with open(file_path) as f:
                    self.current_batches[pairing_key] = json.load(f)
            else:
                self.current_batches[pairing_key] = {
                    "pairing": pairing_key,
                    "last_updated": datetime.now().isoformat(),
                    "games": [],
                    "statistics": {
                        "total_games": 0,
                        f"{white_model}_wins_as_white": 0,
                        f"{black_model}_wins_as_black": 0,
                        "draws": 0,
                        "average_game_length": 0
                    }
                }

        # Update statistics
        stats = self.current_batches[pairing_key]["statistics"]
        stats["total_games"] += 1
        if result == "1-0":
            stats[f"{white_model}_wins_as_white"] += 1
        elif result == "0-1":
            stats[f"{black_model}_wins_as_black"] += 1
        else:
            stats["draws"] += 1
            
        # Update average game length
        total_games = stats["total_games"]
        old_avg = stats["average_game_length"]
        stats["average_game_length"] = (old_avg * (total_games - 1) + len(moves)) / total_games

        # Add the game
        self.current_batches[pairing_key]["games"].append(game_data)
        self.current_batches[pairing_key]["last_updated"] = datetime.now().isoformat()

        # Save after each game
        self.save_pairing(pairing_key)

    def _get_termination_reason(self, board: chess.Board) -> str:
        """Determine how the game ended."""
        if board.is_checkmate():
            return "checkmate"
        elif board.is_stalemate():
            return "stalemate"
        elif board.is_insufficient_material():
            return "insufficient_material"
        elif board.is_fifty_moves():
            return "fifty_moves"
        elif board.is_repetition():
            return "repetition"
        return "unknown"

    def save_pairing(self, pairing_key: str):
        file_path = self.data_dir / f"{pairing_key}.json"
        with open(file_path, 'w') as f:
            json.dump(self.current_batches[pairing_key], f, indent=2)

class GameAnalyzer:
    def __init__(self, data_dir: Path = Path("./data/matches")):
        self.data_dir = data_dir
        self._df = None  # Lazy load DataFrame

    @property
    def df(self) -> pd.DataFrame:
        """Lazy load all games into a DataFrame."""
        if self._df is None:
            games = []
            for file in self.data_dir.glob("*_vs_*.json"):
                with open(file) as f:
                    data = json.load(f)
                    for game in data["games"]:
                        game["pairing"] = data["pairing"]
                        games.append(game)
            self._df = pd.DataFrame(games)
        return self._df

    def get_model_performance(self, model_name: str) -> Dict:
        """Get performance stats for a model."""
        model_games = self.df[
            (self.df['white'] == model_name) | 
            (self.df['black'] == model_name)
        ]
        
        wins = len(model_games[
            ((model_games['white'] == model_name) & (model_games['result'] == '1-0')) |
            ((model_games['black'] == model_name) & (model_games['result'] == '0-1'))
        ])
        
        total_games = len(model_games)
        draws = len(model_games[model_games['result'] == '1/2-1/2'])
        losses = total_games - wins - draws
        
        return {
            'model': model_name,
            'total_games': total_games,
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'win_rate': wins / total_games if total_games > 0 else 0,
            'average_game_length': model_games['total_moves'].mean()
        }

    def get_opening_stats(self, model_name: Optional[str] = None) -> pd.DataFrame:
        """Analyze first moves."""
        df = self.df
        if model_name:
            df = df[(df['white'] == model_name) | (df['black'] == model_name)]
        
        openings = df.apply(lambda x: x['moves'][0], axis=1)
        return openings.value_counts().reset_index()

    def get_termination_stats(self) -> pd.DataFrame:
        """Analyze how games end."""
        return self.df['termination'].value_counts().reset_index()

    def get_model_pairings(self, model_name: Optional[str] = None) -> List[str]:
        """Get all pairings or pairings for specific model."""
        pairings = []
        for file in self.data_dir.glob("*_vs_*.json"):
            if model_name is None or model_name in file.stem:
                pairings.append(file.stem)
        return pairings 