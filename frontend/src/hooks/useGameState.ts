import { useState, useEffect, useCallback } from 'react';
import { GameState, GameMode, EngineType, EngineMetrics } from '../types/game';
import { api } from '../services/api';

interface UseGameStateReturn {
    gameState: GameState | null;
    isLoading: boolean;
    error: string | null;
    engineMetrics: EngineMetrics | null;
    startNewGame: (mode: GameMode, whiteDepth: number, blackDepth: number) => Promise<void>;
    updateSearchDepth: (white?: number, black?: number) => Promise<void>;
    updateEngineType: (white?: EngineType, black?: EngineType) => Promise<void>;
}

export function useGameState(): UseGameStateReturn {
    const [gameState, setGameState] = useState<GameState | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [engineMetrics, setEngineMetrics] = useState<EngineMetrics | null>(null);

    const handleError = useCallback((error: unknown) => {
        const errorMessage = error instanceof Error ? error.message : String(error);
        console.error('Error:', errorMessage);
        setError(errorMessage);
    }, []);

    const fetchGameState = useCallback(async () => {
        try {
            const response = await api.getGameState();
            if (response.error) {
                handleError(response.error);
            } else if (response.data) {
                setGameState(response.data);
                setError(null);
            }
        } catch (error) {
            handleError(error);
        } finally {
            setIsLoading(false);
        }
    }, [handleError]);

    useEffect(() => {
        fetchGameState();
        const interval = setInterval(fetchGameState, 1000);
        return () => clearInterval(interval);
    }, [fetchGameState]);

    const startNewGame = useCallback(async (mode: GameMode, whiteDepth: number, blackDepth: number) => {
        try {
            const response = await api.startNewGame(mode, whiteDepth, blackDepth);
            if (response.error) {
                handleError(response.error);
            } else {
                await fetchGameState();
            }
        } catch (error) {
            handleError(error);
        }
    }, [fetchGameState, handleError]);

    const updateSearchDepth = useCallback(async (white?: number, black?: number) => {
        try {
            const response = await api.setSearchDepth(white, black);
            if (response.error) {
                handleError(response.error);
            } else {
                await fetchGameState();
            }
        } catch (error) {
            handleError(error);
        }
    }, [fetchGameState, handleError]);

    const updateEngineType = useCallback(async (white?: EngineType, black?: EngineType) => {
        try {
            const response = await api.setEngineType(white, black);
            if (response.error) {
                handleError(response.error);
            } else {
                await fetchGameState();
            }
        } catch (error) {
            handleError(error);
        }
    }, [fetchGameState, handleError]);

    // Fetch engine metrics
    useEffect(() => {
        const fetchEngineMetrics = async () => {
            if (gameState?.status === 'active' && !gameState.turn) {
                try {
                    const response = await api.getEngineMetrics();
                    if (response.error) {
                        console.error('Error fetching engine metrics:', response.error);
                        setEngineMetrics(null);
                    } else if (response.data) {
                        setEngineMetrics(response.data);
                    }
                } catch (error) {
                    console.error('Error fetching engine metrics:', error);
                    setEngineMetrics(null);
                }
            } else {
                setEngineMetrics(null);
            }
        };

        fetchEngineMetrics();
        const interval = setInterval(fetchEngineMetrics, 500);
        return () => clearInterval(interval);
    }, [gameState?.status, gameState?.turn]);

    return {
        gameState,
        isLoading,
        error,
        engineMetrics,
        startNewGame,
        updateSearchDepth,
        updateEngineType,
    };
} 