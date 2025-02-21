import chess
import os
import openai
import asyncio
from typing import Optional, Tuple
from .base_engine import BaseChessEngine

openai_models = [
    "gpt-4o",
    "chatgpt-4o-latest",
    "o1",
    "o3-mini"  
]
deepseek_models = [
    "deepseek-chat",
    "deepseek-reasoner"
]
google_models = [
    "gemini-2.0-flash",
    "gemini-2.0-pro-exp-02-05",
    "gemini-2.0-flash-thinking-exp-01-21"
]
anthropic_models = [
    "claude-3-5-sonnet-latest",
    "claude-3-5-haiku-latest",
    "claude-3-opus-latest"
]



class LLMEngine(BaseChessEngine):
    """
    Chess engine that uses an LLM (e.g., OpenAI's GPT-3.5-turbo) to select a move.

    It sends the board position in FEN format along with the legal moves to the LLM and expects
    a response with the best move in UCI notation. The evaluation score is returned as 0.0.
    """

    def __init__(self, level: Optional[int] = None):
        super().__init__(level)
        # Optionally, ensure the OpenAI API key is set in the environment
        if not openai.api_key:
            openai.api_key = os.getenv('OPENAI_API_KEY')

    async def get_move(self, board: chess.Board) -> Tuple[chess.Move, float]:
        """
        Get the best move from the LLM for the given board position.

        :param board: Current chess.Board state
        :return: Tuple of (chess.Move, evaluation score as float)
        """
        # Prepare prompt with board state and legal moves
        board_fen = board.fen()
        legal_moves = list(board.legal_moves)
        legal_moves_uci = ', '.join(move.uci() for move in legal_moves)
        game_pgn = str(board.game())  # Get game history in PGN format
        
        # Construct prompt for LLM
        prompt = (
            f"You are a chess engine. Given the board in FEN '{board_fen}' "
            f"with legal moves: {legal_moves_uci}. "
            f"Game history (PGN): {game_pgn}. "
            f"Return the best move in UCI format."
        )

        # Helper function to extract and validate move
        async def extract_move_from_response(response_text: str, legal_moves_uci: str) -> str:
            extraction_prompt = (
                f"You are a chess move extractor. Extract only the UCI format move from the final decision of the message.Extract only the chess move in UCI format (e.g. 'e2e4' or 'e7e8q') from this response: '{response_text}'. "
                "Return only the move, nothing else. If no valid UCI move is found, return 'INVALID'."
            )
            
            # Get move extraction from LLM
            extraction_response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": extraction_prompt}
                ],
                max_tokens=10,
                temperature=0
            )
            
            extracted_move = extraction_response['choices'][0]['message']['content'].strip().lower()
            
            # Validate extracted move
            if extracted_move == "invalid":
                raise ValueError(f"Could not find valid UCI move in response: {response_text}")
                
            try:
                chess.Move.from_uci(extracted_move)
            except ValueError:
                raise ValueError(f"Extracted move '{extracted_move}' is not a valid UCI move.")
                
            legal_moves_list = [m.strip() for m in legal_moves_uci.split(',')]
            if extracted_move not in legal_moves_list:
                raise ValueError(f"Extracted move '{extracted_move}' is not in legal moves: {legal_moves_uci}")
                
            return extracted_move

        # Using Python's built-in functools for retry decorator
        from functools import wraps
        import random