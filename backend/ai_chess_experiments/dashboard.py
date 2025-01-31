import streamlit as st
import chess
import chess.svg
from dataclasses import dataclass
from typing import Dict, Optional
from datetime import datetime

@dataclass
class GameState:
    board: chess.Board
    white_player: str
    black_player: str
    last_move: Optional[str]
    start_time: datetime
    mode: str  # 'online' or 'local'

class ChessDashboard:
    def __init__(self):
        self.games: Dict[str, GameState] = {}
        
    def update_game(self, game_id: str, state: GameState):
        self.games[game_id] = state
        
    def remove_game(self, game_id: str):
        if game_id in self.games:
            del self.games[game_id]

def main():
    st.set_page_config(page_title="Chess Bot Dashboard", layout="wide")
    st.title("Chess Bot Dashboard")
    
    # Split into columns for online and local games
    online_col, local_col = st.columns(2)
    
    with online_col:
        st.header("Online Games")
        # Placeholder for online games
        st.info("No active online games")
        
    with local_col:
        st.header("Local Games")
        # Placeholder for local games
        st.info("No active local games")
        
    # Game requests section
    st.header("Game Requests")
    st.dataframe({
        "Time": [],
        "Challenger": [],
        "Time Control": [],
        "Status": []
    })
    
    # Refresh button
    if st.button("Refresh"):
        st.rerun()

if __name__ == "__main__":
    main() 