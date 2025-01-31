import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import App from '../App';
import theme from '../theme';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch as any;

// Mock responses
const mockGameState = {
    fen: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
    gameMode: 'human_vs_bot',
    status: 'active',
    whiteTime: 600,
    blackTime: 600,
    lastMove: null,
    possibleMoves: {},
    isWhiteTurn: true,
};

const mockHealthyResponse = { ok: true, status: 200 };
const mockUnhealthyResponse = { ok: false, status: 500 };

describe('App Component', () => {
    beforeEach(() => {
        mockFetch.mockClear();
        // Mock successful health check and game state fetch by default
        mockFetch
            .mockImplementationOnce(() => Promise.resolve(mockHealthyResponse))
            .mockImplementationOnce(() => Promise.resolve({
                ok: true,
                json: () => Promise.resolve(mockGameState)
            }));
    });

    it('renders without crashing', async () => {
        render(
            <ChakraProvider theme={theme}>
                <App />
            </ChakraProvider>
        );
        
        expect(screen.getByText('Chess Bot Arena')).toBeDefined();
        expect(screen.getByRole('button', { name: /new game/i })).toBeDefined();
    });

    it('shows error message when backend is down', async () => {
        mockFetch.mockImplementationOnce(() => Promise.resolve(mockUnhealthyResponse));

        render(
            <ChakraProvider theme={theme}>
                <App />
            </ChakraProvider>
        );

        await waitFor(() => {
            expect(screen.getByText(/backend connection lost/i)).toBeDefined();
        });
    });

    it('shows game board when game state is loaded', async () => {
        render(
            <ChakraProvider theme={theme}>
                <App />
            </ChakraProvider>
        );

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith('/api/game');
        });
    });

    it('opens new game modal when new game button is clicked', async () => {
        render(
            <ChakraProvider theme={theme}>
                <App />
            </ChakraProvider>
        );

        const newGameButton = screen.getByRole('button', { name: /new game/i });
        fireEvent.click(newGameButton);

        expect(screen.getByText('Select Game Mode')).toBeDefined();
        expect(screen.getByText('Play Against Bot')).toBeDefined();
        expect(screen.getByText('Watch Bots Play')).toBeDefined();
    });

    it('handles theme toggle correctly', async () => {
        render(
            <ChakraProvider theme={theme}>
                <App />
            </ChakraProvider>
        );

        const themeToggle = screen.getByRole('button', { name: /toggle/i });
        expect(themeToggle).toBeDefined();

        fireEvent.click(themeToggle);
        // Theme should change - we can verify this by checking the color mode class on the body
        expect(document.body.classList.contains('chakra-ui-dark')).toBe(true);

        fireEvent.click(themeToggle);
        expect(document.body.classList.contains('chakra-ui-light')).toBe(true);
    });

    // Add more tests as needed...
}); 