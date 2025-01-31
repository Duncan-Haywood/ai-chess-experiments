import chess
import random
import math
import time
from typing import Dict, List, Optional, Tuple, Union
from .base_engine import BaseChessEngine
from .heuristics import evaluate_position

class MCTSNode:
    """Node in the Monte Carlo Tree Search."""
    
    def __init__(self, board: chess.Board, parent: Optional['MCTSNode'] = None, move: Optional[chess.Move] = None):
        self.board = board.copy()
        self.parent = parent
        self.move = move
        self.children: List['MCTSNode'] = []
        self.wins: float = 0.0
        self.visits: int = 0
        self.untried_moves = list(board.legal_moves)
        random.shuffle(self.untried_moves)

    def ucb1(self, exploration: float = 1.414) -> float:
        """Calculate the UCB1 value for this node."""
        if self.visits == 0 or not self.parent:
            return float('inf')
        return (self.wins / self.visits) + exploration * math.sqrt(math.log(self.parent.visits) / self.visits)

    def expand(self) -> Optional['MCTSNode']:
        """Expand this node by adding a child node."""
        if not self.untried_moves:
            return None
        move = self.untried_moves.pop()
        self.board.push(move)
        child = MCTSNode(self.board, self, move)
        self.board.pop()
        self.children.append(child)
        return child

    def is_terminal(self) -> bool:
        """Check if this node represents a terminal game state."""
        return self.board.is_game_over()

    def rollout(self) -> float:
        """Perform a random playout from this node."""
        board = self.board.copy()
        
        while not board.is_game_over():
            moves = list(board.legal_moves)
            if not moves:
                break
            move = random.choice(moves)
            board.push(move)
        
        # Use the evaluation function for the result
        return evaluate_position(board)

    def backpropagate(self, result: float) -> None:
        """Backpropagate the result up the tree."""
        self.visits += 1
        # Convert evaluation score to win probability
        win_prob = 1.0 / (1.0 + math.exp(-result / 100.0))  # Sigmoid function
        self.wins += win_prob
        
        if self.parent:
            # Negate the result for the parent (opponent's perspective)
            self.parent.backpropagate(-result)

class MCTSEngine(BaseChessEngine):
    """Chess engine using Monte Carlo Tree Search."""
    
    def __init__(self, simulation_time: float = 1.0):
        """Initialize the MCTS engine.
        
        Args:
            simulation_time: Time in seconds to run simulations
        """
        super().__init__()
        self.simulation_time = simulation_time
        self.root: Optional[MCTSNode] = None
    
    def get_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Get the best move using MCTS."""
        if board.is_game_over():
            return None
            
        # Initialize root node
        self.root = MCTSNode(board)
        
        # Run simulations
        end_time = time.time() + self.simulation_time
        while time.time() < end_time:
            if not self.root:
                break
                
            node = self.root
            
            # Selection
            while node.untried_moves == [] and node.children != []:
                node = max(node.children, key=lambda n: n.ucb1())
            
            # Expansion
            if node.untried_moves != []:
                child_node = node.expand()
                if child_node:
                    node = child_node
            
            # Simulation
            result = node.rollout()
            
            # Backpropagation
            node.backpropagate(result)
        
        # Choose best move
        if not self.root or not self.root.children:
            return None
            
        best_child = max(self.root.children, key=lambda n: n.visits)
        return best_child.move
    
    def cleanup(self) -> None:
        """Clean up resources."""
        self.root = None 