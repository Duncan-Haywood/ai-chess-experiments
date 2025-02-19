import chess
import os
import openai
import asyncio
from typing import Optional, Tuple
from .base_engine import BaseChessEngine


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
        prompt = (
            f"You are a chess engine. Given the board in FEN '{board_fen}' "
            f"with legal moves: {legal_moves_uci}, return the best move in UCI format only."
        )

        # Call the LLM using OpenAI's API in a thread
        response = await asyncio.to_thread(
            openai.ChatCompletion.create,
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a chess engine specialized in selecting the best move given a FEN and legal moves."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=10,
            n=1,
            temperature=0
        )

        # Extract the move string from the response
        move_str = response['choices'][0]['message']['content'].strip()

        try:
            move = chess.Move.from_uci(move_str)
        except Exception as e:
            raise RuntimeError(f"LLM returned an invalid move: {move_str}")

        # Return the move with a default evaluation score of 0.0
        return move, 0.0

    async def cleanup(self) -> None:
        """Cleanup resources for the LLM engine (none needed currently)."""
        pass 