import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useGameState } from '../hooks/useGameState';
import { api } from '../services/api';

// Mock the API module
vi.mock('../services/api', () => ({
    api: {
        getGameState: vi.fn(),
        startNewGame: vi.fn(),
        setSearchDepth: vi.fn(),
        setEngineType: vi.fn(),
    }
}));

describe('useGameState Hook', () => {
    const mockGameState = {
        fen: 'initial-position',
        gameMode: 'human_vs_bot',
        status: 'active',
        whiteTime: 600,
        blackTime: 600,
        lastMove: null,
        isWhiteTurn: true,
    };

    beforeEach(() => {
        vi.clearAllMocks();
        // Reset default successful responses
        (api.getGameState as any).mockResolvedValue({ data: mockGameState });
        (api.startNewGame as any).mockResolvedValue({});
        (api.setSearchDepth as any).mockResolvedValue({});
        (api.setEngineType as any).mockResolvedValue({});
    });

    it('initializes with loading state and fetches game state', async () => {
        const { result } = renderHook(() => useGameState());

        expect(result.current.isLoading).toBe(true);
        expect(result.current.gameState).toBe(null);

        // Wait for initial fetch
        await act(async () => {
            await new Promise(resolve => setTimeout(resolve, 0));
        });

        expect(result.current.isLoading).toBe(false);
        expect(result.current.gameState).toEqual(mockGameState);
    });

    it('handles API errors correctly', async () => {
        const errorMessage = 'Failed to fetch game state';
        (api.getGameState as any).mockResolvedValue({ error: errorMessage });

        const onError = vi.fn();
        const { result } = renderHook(() => useGameState({ onError }));

        await act(async () => {
            await new Promise(resolve => setTimeout(resolve, 0));
        });

        expect(result.current.error).toBe(errorMessage);
        expect(onError).toHaveBeenCalledWith(errorMessage);
    });

    it('starts a new game successfully', async () => {
        const { result } = renderHook(() => useGameState());

        await act(async () => {
            await result.current.startNewGame('human_vs_bot', 3, 3);
        });

        expect(api.startNewGame).toHaveBeenCalledWith('human_vs_bot', 3, 3);
        expect(api.getGameState).toHaveBeenCalled();
    });

    it('updates search depth successfully', async () => {
        const { result } = renderHook(() => useGameState());

        await act(async () => {
            await result.current.updateSearchDepth(3, 4);
        });

        expect(api.setSearchDepth).toHaveBeenCalledWith(3, 4);
    });

    it('updates engine type successfully', async () => {
        const { result } = renderHook(() => useGameState());

        await act(async () => {
            await result.current.updateEngineType('stockfish', 'minimax');
        });

        expect(api.setEngineType).toHaveBeenCalledWith('stockfish', 'minimax');
    });

    it('cleans up interval on unmount', () => {
        vi.useFakeTimers();
        const { unmount } = renderHook(() => useGameState({ pollInterval: 1000 }));

        expect(setInterval).toHaveBeenCalledWith(expect.any(Function), 1000);

        unmount();

        expect(clearInterval).toHaveBeenCalled();
        vi.useRealTimers();
    });
}); 