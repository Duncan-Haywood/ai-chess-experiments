import { describe, it, expect, beforeEach, vi } from 'vitest';
import { GameState } from '../types/game';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch as any;

describe('API Interactions', () => {
    beforeEach(() => {
        mockFetch.mockClear();
    });

    describe('Health Check', () => {
        it('handles successful health check', async () => {
            mockFetch.mockResolvedValueOnce({ ok: true, status: 200 });
            const response = await fetch('/api/health');
            expect(response.ok).toBe(true);
            expect(response.status).toBe(200);
        });

        it('handles failed health check', async () => {
            mockFetch.mockResolvedValueOnce({ ok: false, status: 500 });
            const response = await fetch('/api/health');
            expect(response.ok).toBe(false);
            expect(response.status).toBe(500);
        });

        it('handles network errors', async () => {
            mockFetch.mockRejectedValueOnce(new Error('Network error'));
            await expect(fetch('/api/health')).rejects.toThrow('Network error');
        });
    });

    describe('Game State Management', () => {
        const mockGameState: GameState = {
            fen: 'initial-position',
            gameMode: 'human_vs_bot',
            status: 'active',
            whiteTime: 600,
            blackTime: 600,
            lastMove: null,
            isWhiteTurn: true,
            whiteName: 'Player',
            blackName: 'Bot',
            whiteDepth: 3,
            blackDepth: 3,
            moveCount: 0
        };

        it('fetches game state successfully', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: () => Promise.resolve(mockGameState)
            });

            const response = await fetch('/api/game');
            const data = await response.json();
            expect(data).toEqual(mockGameState);
        });

        it('handles game state fetch errors', async () => {
            mockFetch.mockResolvedValueOnce({
                ok: false,
                status: 404,
                statusText: 'Not Found'
            });

            const response = await fetch('/api/game');
            expect(response.ok).toBe(false);
            expect(response.status).toBe(404);
        });
    });

    describe('Engine Configuration', () => {
        it('updates search depth successfully', async () => {
            mockFetch.mockResolvedValueOnce({ ok: true });
            
            const response = await fetch('/api/set_depth', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ white: 3, black: 4 })
            });

            expect(response.ok).toBe(true);
            expect(mockFetch).toHaveBeenCalledWith('/api/set_depth', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ white: 3, black: 4 })
            });
        });

        it('handles depth update errors', async () => {
            mockFetch.mockResolvedValueOnce({ 
                ok: false, 
                status: 400,
                statusText: 'Bad Request'
            });
            
            const response = await fetch('/api/set_depth', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ white: -1, black: 100 })
            });

            expect(response.ok).toBe(false);
            expect(response.status).toBe(400);
        });
    });
}); 