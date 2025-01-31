import os
import time
from typing import Optional, Iterator, Dict, Any, Literal
import berserk
import chess
from dotenv import load_dotenv

# Define enums that berserk uses
Color = Literal['white', 'black']
Variant = Literal['standard', 'chess960', 'crazyhouse', 'antichess', 'atomic', 
                 'horde', 'kingOfTheHill', 'racingKings', 'threeCheck']
ChallengeDeclineReason = Literal['generic', 'later', 'tooFast', 'tooSlow', 
                                'timeControl', 'rated', 'casual', 'standard',
                                'variant', 'noBot', 'onlyBot']

class LichessClient:
    def __init__(self):
        load_dotenv()
        self.api_token = os.getenv('LICHESS_API_TOKEN')
        if not self.api_token:
            raise ValueError("LICHESS_API_TOKEN not found in environment variables")
        
        self.session = berserk.TokenSession(self.api_token)
        self.client = berserk.Client(session=self.session)
        
    def get_account(self):
        """Get the account information."""
        return self.client.account.get()
    
    def make_move(self, game_id: str, move: chess.Move):
        """Make a move in a game.
        
        Args:
            game_id: The ID of the game
            move: The chess.Move object
        """
        return self.client.board.make_move(game_id, move.uci())
    
    def stream_incoming_events(self) -> Iterator[Dict[str, Any]]:
        """Stream incoming events (challenges, game starts, etc.)."""
        return self.client.board.stream_incoming_events()
    
    def stream_game_state(self, game_id: str) -> Iterator[Dict[str, Any]]:
        """Stream the state of a game."""
        return self.client.board.stream_game_state(game_id)
    
    def accept_challenge(self, challenge_id: str):
        """Accept an incoming challenge."""
        return self.client.challenges.accept(challenge_id)
    
    def decline_challenge(self, challenge_id: str, reason: ChallengeDeclineReason = 'generic'):
        """Decline an incoming challenge."""
        return self.client.challenges.decline(challenge_id, reason=reason)
    
    def create_challenge(self, username: Optional[str] = None, 
                        rated: bool = False,
                        clock_limit: int = 300,
                        clock_increment: int = 3,
                        color: Optional[Color] = None,
                        variant: Optional[Variant] = 'standard'):
        """Create a challenge to play with someone.
        
        Args:
            username: Optional username to challenge. If None, creates an open challenge
            rated: Whether the game should be rated
            clock_limit: Initial time in seconds
            clock_increment: Time increment per move in seconds
            color: 'white', 'black', or None for random
            variant: Game variant (e.g., 'standard', 'chess960', etc.)
        """
        if username:
            return self.client.challenges.create(
                username=username,
                rated=rated,
                clock_limit=clock_limit,
                clock_increment=clock_increment,
                color=color,
                variant=variant
            )
        else:
            return self.client.challenges.create_open(
                rated=rated,
                clock_limit=clock_limit,
                clock_increment=clock_increment
            )
    
    def abort_game(self, game_id: str):
        """Abort a game."""
        return self.client.board.abort_game(game_id)
    
    def resign_game(self, game_id: str):
        """Resign a game."""
        return self.client.board.resign_game(game_id) 