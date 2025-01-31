from utils.lichess_client import LichessClient
from engines.random_engine import RandomEngine
import chess
import time

def main():
    # Initialize the client and engine
    client = LichessClient()
    engine = RandomEngine()
    
    # Create an open challenge
    print("Creating challenge...")
    challenge = client.create_challenge()
    game_id = challenge['id']
    
    print(f"Waiting for opponent in game: {game_id}")
    print("Visit https://lichess.org/{game_id} to accept the challenge")
    
    # Stream the game state
    for state in client.get_game_stream(game_id):
        if state.get('type') == 'gameState':
            # Update our board with the last move if there was one
            moves = state.get('moves', '').split()
            if moves:
                last_move = chess.Move.from_uci(moves[-1])
                engine.update_board(last_move)
            
            # If it's our turn, make a move
            if state.get('status') == 'started' and len(moves) % 2 == 0:
                our_move = engine.get_move()
                client.make_move(game_id, our_move.uci())
                engine.update_board(our_move)
                print(f"Made move: {our_move.uci()}")
            
            # Check if game is over
            if state.get('status') != 'started':
                print(f"Game over! Status: {state.get('status')}")
                break
        
        time.sleep(1)  # Be nice to the Lichess API

if __name__ == "__main__":
    main() 