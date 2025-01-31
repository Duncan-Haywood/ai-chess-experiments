import chess
import time
import os
from typing import Optional, Dict, Any, List
from ai_chess_experiments.utils.lichess_client import LichessClient
from ai_chess_experiments.utils.game_viewer import GameViewer
from ai_chess_experiments.utils.dashboard import Dashboard
from ai_chess_experiments.engines.base_engine import BaseChessEngine
import threading

class BotRunner:
    def __init__(self, engine: BaseChessEngine, client: Optional[LichessClient] = None):
        """Initialize the bot runner.
        
        Args:
            engine: The chess engine to use
            client: Optional LichessClient instance (creates new one if None)
        """
        self.engine = engine
        self.client = client or LichessClient()
        self.viewer = GameViewer()
        self.dashboard = Dashboard(port=8000)
        
        # Start dashboard in a separate thread
        self.dashboard_thread = threading.Thread(target=self.dashboard.run, daemon=True)
        self.dashboard_thread.start()
        
        # Time control preferences
        self.min_time = 30  # Minimum game time (30 seconds)
        self.max_time = 180  # Maximum game time (3 minutes)
        self.min_increment = 0  # Minimum increment
        self.max_increment = 2  # Maximum increment
        
        # Game seeking settings
        self.max_concurrent_games = 1  # Maximum number of games to play at once
        self.active_games: List[str] = []  # List of active game IDs
        self.last_seek_time = 0  # Last time we created a seek
        self.seek_interval = 30  # Minimum seconds between seeks
        self.max_rating_diff = 500  # Maximum rating difference to accept
        
        # Mode settings
        self.mode = os.environ.get('BOT_MODE', 'online')
        self.is_testing = self.mode == 'local'
        self.test_game_board = None if not self.is_testing else chess.Board()
    
    def should_accept_challenge(self, challenge: Dict[str, Any]) -> bool:
        """Determine whether to accept a challenge based on time control and current load."""
        if challenge['variant']['key'] != 'standard':
            return False
        
        # Accept all challenges in testing mode
        if self.is_testing:
            return True
        
        # Check if we're at max games
        if len(self.active_games) >= self.max_concurrent_games:
            return False
        
        # Check time control
        time_control = challenge.get('timeControl', {})
        initial_time = time_control.get('limit', 0)
        increment = time_control.get('increment', 0)
        
        # Check rating difference if available
        if 'rating' in challenge.get('challenger', {}):
            challenger_rating = challenge['challenger']['rating']
            bot_rating = self.client.get_account().get('rating', {}).get('classical', 1500)
            if abs(challenger_rating - bot_rating) > self.max_rating_diff:
                return False
        
        return (self.min_time <= initial_time <= self.max_time and 
                self.min_increment <= increment <= self.max_increment)
    
    def create_seek(self):
        """Create a new game seek if conditions are met."""
        if self.is_testing:
            return
            
        current_time = time.time()
        
        # Check if we can create a new seek
        if (len(self.active_games) < self.max_concurrent_games and 
            current_time - self.last_seek_time >= self.seek_interval):
            
            # Create a seek with random time control within our preferences
            initial_time = (self.min_time + self.max_time) // 2
            increment = (self.min_increment + self.max_increment) // 2
            
            try:
                self.client.create_seek(initial_time, increment)
                self.last_seek_time = current_time
                print(f"\nCreated new seek: {initial_time}+{increment}")
            except Exception as e:
                print(f"Error creating seek: {e}")
    
    def start_self_play_test(self):
        """Start a self-play test game."""
        self.is_testing = True
        self.test_game_board = chess.Board()
        print("\nStarting self-play test game...")
        self.handle_test_game()
    
    def handle_test_game(self):
        """Handle moves for a self-play test game."""
        while not self.test_game_board.is_game_over():
            # Display current position
            self.viewer.display_game(
                board=self.test_game_board,
                white_time=180,  # 3 minutes per side for testing
                black_time=180,
                last_move=self.test_game_board.peek().uci() if self.test_game_board.move_stack else None,
                white_name="Minimax (White)",
                black_name="Minimax (Black)"
            )
            
            # Calculate and make move
            try:
                move = self.engine.get_move()
                print(f"\nMaking move: {move.uci()}")
                self.test_game_board.push(move)
                time.sleep(0.5)  # Add delay to make it easier to follow
            except Exception as e:
                print(f"Error making move: {e}")
                break
        
        # Display final position
        self.viewer.display_game(
            board=self.test_game_board,
            white_time=180,
            black_time=180,
            last_move=self.test_game_board.peek().uci() if self.test_game_board.move_stack else None,
            white_name="Minimax (White)",
            black_name="Minimax (Black)"
        )
        
        print("\nGame Over!")
        print(f"Result: {self.test_game_board.result()}")
        print(f"Move count: {len(self.test_game_board.move_stack)}")
        
        self.is_testing = False
        self.test_game_board = None

    def handle_challenge(self, event):
        """Handle an incoming challenge."""
        challenge = event['challenge']
        challenger = challenge['challenger']['name']
        
        if self.should_accept_challenge(challenge):
            print(f"Accepting challenge from {challenger}")
            self.client.accept_challenge(challenge['id'])
        else:
            reason = 'generic'
            if len(self.active_games) >= self.max_concurrent_games:
                reason = 'later'
            elif 'timeControl' in challenge:
                reason = 'timeControl'
            print(f"Declining challenge from {challenger} ({reason})")
            self.client.decline_challenge(challenge['id'], reason=reason)
    
    def handle_game_end(self, game_id: str):
        """Handle game end cleanup."""
        if game_id in self.active_games:
            self.active_games.remove(game_id)
            self.dashboard.remove_game(game_id)
            print(f"\nGame {game_id} ended. Active games: {len(self.active_games)}")
    
    def calculate_move_time(self, remaining_time: float, increment: float, position: chess.Board) -> float:
        """Calculate how much time to spend on the move."""
        # Basic time management
        moves_left = 20  # Estimate remaining moves
        base_time = remaining_time / moves_left
        
        # Add increment but keep some buffer
        move_time = base_time + (increment * 0.8)
        
        # Adjust based on position
        if position.is_check():
            move_time *= 1.5  # Spend more time when in check
        elif len(list(position.legal_moves)) == 1:  # Convert to list to fix linter error
            move_time = 0.1  # Only one legal move
        
        # Never use more than 20% of remaining time
        max_time = remaining_time * 0.2
        move_time = min(move_time, max_time)
        
        # Ensure we don't go too low
        return max(0.1, min(move_time, remaining_time - 0.1))
    
    def handle_game_state(self, game_id: str, state: Dict[str, Any], board: chess.Board,
                         our_color: chess.Color, last_move: Optional[str] = None):
        """Handle a game state update."""
        # Update times
        white_time = state.get('wtime', 0) / 1000
        black_time = state.get('btime', 0) / 1000
        increment = state.get('winc' if our_color else 'binc', 0) / 1000
        
        # Update dashboard with game info
        self.dashboard.update_game(game_id, {
            'opponent': state.get('opponent', {}).get('username', 'Unknown'),
            'time_control': f"{white_time:.1f}s W / {black_time:.1f}s B",
            'last_move': last_move or '-',
            'status': 'Active'
        })
        
        # Display current position
        self.viewer.display_game(
            board=board,
            white_time=white_time,
            black_time=black_time,
            last_move=last_move,
            white_name="Bot" if our_color else "Opponent",
            black_name="Opponent" if our_color else "Bot"
        )
        
        # If it's our turn, calculate and make a move
        if len(board.move_stack) % 2 == (0 if our_color else 1):
            our_time = white_time if our_color else black_time
            move_time = self.calculate_move_time(our_time, increment, board)
            
            try:
                start_time = time.time()
                move = self.engine.get_move()
                actual_time = time.time() - start_time
                
                # Record move timing
                self.dashboard.record_move(actual_time)
                
                print(f"\nMaking move: {move.uci()} (time allocated: {move_time:.1f}s, actual: {actual_time:.1f}s)")
                self.client.make_move(game_id, move)
                return move.uci()
            except Exception as e:
                print(f"Error making move: {e}")
                self.client.resign_game(game_id)
                return None
        
        return last_move
    
    def handle_game_start(self, event):
        """Handle a game start event."""
        game_id = event['game']['id']
        our_color = event['game']['color'] == 'white'
        print(f"\nStarting game {game_id} as {'white' if our_color else 'black'}")
        
        # Track active game
        if game_id not in self.active_games:
            self.active_games.append(game_id)
        
        # Initialize a new board for the game
        board = chess.Board()
        last_move = None
        
        # Stream the game state and respond to moves
        try:
            for state in self.client.stream_game_state(game_id):
                if state.get('status') == 'started':
                    # Apply any new moves to our board
                    moves = state.get('moves', '').split()
                    while len(moves) > len(board.move_stack):
                        move = chess.Move.from_uci(moves[len(board.move_stack)])
                        board.push(move)
                        last_move = move.uci()
                    
                    # Handle the current state
                    last_move = self.handle_game_state(game_id, state, board, our_color, last_move)
                
                # Game ended
                if state.get('status') != 'started':
                    print(f"Game {game_id} ended. Status: {state.get('status')}")
                    self.handle_game_end(game_id)
                    break
        except Exception as e:
            print(f"Error in game {game_id}: {e}")
            self.handle_game_end(game_id)
    
    def run(self, test_mode: bool = False):
        """Main bot loop - handle events and play games."""
        if test_mode or self.mode == 'local':
            print("Starting bot in local mode...")
            self.start_self_play_test()
            return
            
        print("Starting bot in online mode...")
        account = self.client.get_account()
        print(f"Bot account: {account.get('username')}")
        print(f"Rating: {account.get('rating', {}).get('classical', 'Unrated')}")
        print("\nWaiting for games...")
        
        for event in self.client.stream_incoming_events():
            if event['type'] == 'challenge':
                self.handle_challenge(event)
            elif event['type'] == 'gameStart':
                self.handle_game_start(event)
            
            # Create seeks when idle
            self.create_seek()
            
            time.sleep(0.1)  # Be nice to the Lichess API

def main():
    """Run the bot with the minimax engine."""
    from ai_chess_experiments.engines.minimax_engine import MinimaxEngine
    import sys
    
    # Create engine with depth 3 (adjust based on your machine's performance)
    engine = MinimaxEngine(depth=3)
    runner = BotRunner(engine)
    
    # Check for test mode
    test_mode = '--test' in sys.argv
    
    try:
        runner.run(test_mode=test_mode)
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Bot stopped due to error: {e}")

if __name__ == "__main__":
    main() 