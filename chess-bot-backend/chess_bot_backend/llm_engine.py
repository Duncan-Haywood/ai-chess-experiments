"""
LLM Chess Engine Implementation

This module implements a chess engine that uses Large Language Models (LLMs) to generate moves.
It supports multiple LLM providers and models, including:
- OpenAI (GPT-4 variants)
- DeepSeek
- Google (Gemini variants)
- Anthropic (Claude variants)

The engine uses UCI (Universal Chess Interface) format for moves and FEN for board representation.

Key Features:
------------
- Multi-model support with easy model switching
- Automatic retry on API failures
- Move validation and extraction
- Asynchronous operation
- Comprehensive game state analysis

Usage Example:
-------------
```python
engine = LLMEngine()
board = chess.Board()
move, explanation = await engine.get_move(board, "claude-3-5-sonnet-latest")
board.push(move)
```

Implementation Notes:
-------------------
- Each model should be treated as a separate player for rating purposes
- Models use different temperatures/configurations for varied play styles
- Response parsing is handled by a dedicated Claude model for consistency
- Moves are validated against legal moves before being returned
"""

import chess
import chess.pgn
from tenacity import retry, stop_after_attempt, wait_fixed
from langchain_openai import ChatOpenAI
from langchain_deepseek import ChatDeepSeek
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain.chat_models.base import BaseChatModel
from typing import Dict, List, Tuple

class LLMEngine:
    """
    A chess engine that uses LLMs to generate moves.
    
    This class manages multiple LLM models and provides an interface for getting chess moves
    from them. It handles model initialization, move generation, validation, and parsing.
    """

    def __init__(self) -> None:
        """Initialize the LLM engine with supported models from various providers."""
        self.openai_models: list[str] = [
            "gpt-4o", 
            "chatgpt-4o-latest",
            "o1",
            "o3-mini"  
        ]
        self.deepseek_models: list[str] = [
            "deepseek-chat",
            "deepseek-reasoner"
        ]
        self.google_models: list[str] = [
            "gemini-2.0-flash",
            "gemini-2.0-pro-exp-02-05",
            "gemini-2.0-flash-thinking-exp-01-21"
        ]
        self.anthropic_models: list[str] = [
            "claude-3-5-sonnet-latest",
            "claude-3-5-haiku-latest",
            "claude-3-opus-latest"
        ]
        
        # Initialize model instances
        self.callable_models: Dict[str, BaseChatModel] = {}
        self._initialize_models()
        
    def _initialize_models(self) -> None:
        """Initialize all supported LLM models."""
        for model in self.openai_models:
            self.callable_models[model] = ChatOpenAI(model=model)
            
        for model in self.deepseek_models:
            self.callable_models[model] = ChatDeepSeek(model=model)
            
        for model in self.google_models:
            self.callable_models[model] = ChatGoogleGenerativeAI(model=model)
            
        for model in self.anthropic_models:
            self.callable_models[model] = ChatAnthropic(
                model_name=model, 
                timeout=60, 
                stop=None
            )

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(0.1))
    async def get_move(self, board: chess.Board, model_name: str) -> tuple[chess.Move, str]:
        """
        Get the best move from the LLM for the given board position.

        Args:
            board: Current chess.Board object representing the game state
            model_name: Name of the LLM model to use

        Returns:
            tuple containing:
                - chess.Move object representing the chosen move
                - str containing the model's explanation/reasoning

        Raises:
            ValueError: If the model generates an invalid or illegal move
            RuntimeError: If the model fails to generate a move after retries
        """
        # Get current board state
        board_fen = board.fen()
        legal_moves = board.legal_moves
        legal_moves_uci = ', '.join(move.uci() for move in legal_moves)
        
        # Get move history
        moves_history = []
        for move in board.move_stack:
            moves_history.append(move.uci())
        moves_str = ', '.join(moves_history) if moves_history else "Starting position"
        
        # Construct prompt for LLM
        prompt = (
            f"You are a chess engine analyzing a position. Current state:\n"
            f"1. Board (FEN): {board_fen}\n"
            f"2. Legal moves (UCI): {legal_moves_uci}\n"
            f"3. Move history: {moves_str}\n\n"
            f"Analyze the position and return the best move in UCI format (e.g. 'e2e4' or 'e7e8q').\n"
            f"Consider:\n"
            f"- Material balance\n"
            f"- Piece activity\n"
            f"- King safety\n"
            f"- Pawn structure\n"
            "Provide your chosen move with a brief explanation."
        )
        
        # Get model and generate move
        llm = self.callable_models[model_name]
        message = await llm.ainvoke(prompt)
        message_text = message.content
        assert isinstance(message_text, str)
        
        # Extract and validate move
        move = await self.extract_move_from_response(message_text, board)
        
        return move, message_text

    async def extract_move_from_response(self, response_text: str, board: chess.Board) -> chess.Move:
        """
        Extract and validate a UCI move from the model's response.

        Args:
            response_text: The full response from the LLM
            board: Current chess.Board object for move validation

        Returns:
            chess.Move object representing the extracted move

        Raises:
            ValueError: If no valid UCI move is found or the move is illegal
        """
        extraction_prompt = (
            f"Extract only the chess move in UCI format (e.g. 'e2e4' or 'e7e8q') from this response:\n"
            f"'''{response_text}'''\n"
            "Return only the move, nothing else. If no move is found, return 'NONE'."
        )
        
        llm = self.callable_models["claude-3-5-sonnet-latest"]
        message = await llm.ainvoke(extraction_prompt)
        message_text = message.content
        assert isinstance(message_text, str)
        
        # Validate extracted move
        move_text = message_text.strip().lower()
        if move_text == "none":
            raise ValueError(f"Could not find valid UCI move in response: {response_text}")
        
        try:
            move = chess.Move.from_uci(move_text)
        except ValueError:
            raise ValueError(f"Invalid UCI move format: {move_text}")
            
        if move not in board.legal_moves:
            raise ValueError(f"Illegal move: {move}")

        return move
