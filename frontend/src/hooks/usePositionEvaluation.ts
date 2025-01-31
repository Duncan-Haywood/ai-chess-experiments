import { useState, useEffect } from 'react';
import { Chess } from 'chess.js';

interface UsePositionEvaluationProps {
  fen: string;           // Current position in FEN notation
  depth?: number;        // Analysis depth (default: 15)
  onError?: (err: any) => void;
}

interface UsePositionEvaluationResult {
  evaluation: number;    // Evaluation in pawns (positive for white advantage)
  isAnalyzing: boolean;  // Whether analysis is in progress
  error: Error | null;   // Any error that occurred
}

export const usePositionEvaluation = ({
  fen,
  depth = 15,
  onError
}: UsePositionEvaluationProps): UsePositionEvaluationResult => {
  const [evaluation, setEvaluation] = useState<number>(0);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const analyzePosition = async () => {
      setIsAnalyzing(true);
      setError(null);

      try {
        // Validate FEN first
        const chess = new Chess(fen);
        if (chess.isGameOver()) {
          // Handle game over states
          if (chess.isCheckmate()) {
            setEvaluation(chess.turn() === 'w' ? -100 : 100);
          } else {
            setEvaluation(0); // Draw
          }
          return;
        }

        // Request evaluation from backend
        const response = await fetch('/api/analyze', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            fen,
            depth,
            engine: 'stockfish-nnue'  // Always use Stockfish NNUE for consistent evals
          }),
        });

        if (!response.ok) {
          throw new Error('Failed to analyze position');
        }

        const data = await response.json();
        setEvaluation(data.evaluation);
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Unknown error');
        setError(error);
        onError?.(error);
      } finally {
        setIsAnalyzing(false);
      }
    };

    // Don't analyze if FEN is invalid
    if (!fen) {
      setError(new Error('Invalid FEN'));
      return;
    }

    analyzePosition();
  }, [fen, depth, onError]);

  return { evaluation, isAnalyzing, error };
}; 