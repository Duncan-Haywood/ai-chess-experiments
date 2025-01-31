import { GameState, GameMode, EngineType, EngineMetrics } from '../types/game';
import { debounce } from '../utils/debounce';

const API_URL = '/api';
const RETRY_ATTEMPTS = 3;
const RETRY_DELAY = 1000;
const DEBOUNCE_DELAY = 300;

interface ApiResponse<T> {
    data?: T;
    error?: string;
}

class ApiError extends Error {
    constructor(public status: number, message: string) {
        super(message);
        this.name = 'ApiError';
    }
}

async function withRetry<T>(fn: () => Promise<T>, attempts: number = RETRY_ATTEMPTS): Promise<T> {
    try {
        return await fn();
    } catch (error) {
        if (attempts <= 1) throw error;
        await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
        return withRetry(fn, attempts - 1);
    }
}

export const api = {
    async checkHealth(): Promise<boolean> {
        try {
            const res = await withRetry(() => fetch(`${API_URL}/health`));
            return res.ok;
        } catch (error) {
            console.error('Health check failed:', error);
            return false;
        }
    },

    async getGameState(): Promise<ApiResponse<GameState>> {
        try {
            const res = await withRetry(() => fetch(`${API_URL}/game`));
            if (!res.ok) {
                throw new ApiError(res.status, `Failed to fetch game state: ${res.status} ${res.statusText}`);
            }
            const data = await res.json();
            return { data };
        } catch (error) {
            console.error('Error fetching game state:', error);
            return { 
                error: error instanceof ApiError ? error.message : 'Failed to fetch game state' 
            };
        }
    },

    async getEngineMetrics(): Promise<ApiResponse<EngineMetrics>> {
        try {
            const res = await withRetry(() => fetch(`${API_URL}/engine/metrics`));
            if (!res.ok) {
                throw new ApiError(res.status, `Failed to fetch engine metrics: ${res.status} ${res.statusText}`);
            }
            const data = await res.json();
            return { data };
        } catch (error) {
            console.error('Error fetching engine metrics:', error);
            return { 
                error: error instanceof ApiError ? error.message : 'Failed to fetch engine metrics' 
            };
        }
    },

    setSearchDepth: debounce(async (white?: number, black?: number): Promise<ApiResponse<void>> => {
        try {
            const res = await withRetry(() => 
                fetch(`${API_URL}/set_depth`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        white: white !== undefined ? white : null,
                        black: black !== undefined ? black : null
                    }),
                })
            );
            if (!res.ok) {
                throw new ApiError(res.status, 'Failed to update search depth');
            }
            return {};
        } catch (error) {
            console.error('Error updating search depth:', error);
            return { 
                error: error instanceof ApiError ? error.message : 'Failed to update search depth' 
            };
        }
    }, DEBOUNCE_DELAY),

    setEngineType: debounce(async (white?: EngineType, black?: EngineType): Promise<ApiResponse<void>> => {
        try {
            const res = await withRetry(() =>
                fetch(`${API_URL}/set_engine`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        white: white !== undefined ? white : null,
                        black: black !== undefined ? black : null
                    }),
                })
            );
            if (!res.ok) {
                throw new ApiError(res.status, 'Failed to update engine type');
            }
            return {};
        } catch (error) {
            console.error('Error updating engine type:', error);
            return { 
                error: error instanceof ApiError ? error.message : 'Failed to update engine type' 
            };
        }
    }, DEBOUNCE_DELAY),

    async startNewGame(mode: GameMode, whiteDepth: number, blackDepth: number): Promise<ApiResponse<void>> {
        try {
            const res = await withRetry(() =>
                fetch(
                    `${API_URL}/new_game?mode=${mode}&white_depth_param=${whiteDepth}&black_depth_param=${blackDepth}`,
                    { method: 'POST' }
                )
            );
            if (!res.ok) {
                throw new ApiError(res.status, 'Failed to start new game');
            }
            return {};
        } catch (error) {
            console.error('Error starting new game:', error);
            return { 
                error: error instanceof ApiError ? error.message : 'Failed to start new game' 
            };
        }
    }
}; 