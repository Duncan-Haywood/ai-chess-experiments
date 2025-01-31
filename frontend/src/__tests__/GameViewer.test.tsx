import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import { GameViewer } from '../components/GameViewer';
import { GameState } from '../types/game';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useToast } from '../hooks/useToast';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch as any;

const mockGameState: GameState = {
    fen: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
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
    moveCount: 0,
    whiteEngine: 'minimax',
    blackEngine: 'minimax',
    turn: true  // White's turn
};

// Mock useToast hook
jest.mock('../hooks/useToast', () => ({
  useToast: jest.fn(),
}));

describe('GameViewer Component', () => {
    const mockOnReconnect = vi.fn();
    const mockToast = jest.fn();
    const mockCloseAll = jest.fn();

    beforeEach(() => {
        mockFetch.mockClear();
        mockOnReconnect.mockClear();
        vi.useFakeTimers();
        (useToast as jest.Mock).mockReturnValue(Object.assign(mockToast, {
          closeAll: mockCloseAll,
        }));
    });

    afterEach(() => {
        vi.useRealTimers();
        jest.clearAllMocks();
    });

    describe('Rendering and Basic Functionality', () => {
        it('renders loading skeleton when loading', () => {
            render(
                <ChakraProvider>
                    <GameViewer game={mockGameState} isLoading={true} soundEnabled={false} />
                </ChakraProvider>
            );

            expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();
        });

        it('displays player names and initial state correctly', () => {
            render(
                <ChakraProvider>
                    <GameViewer game={mockGameState} isLoading={false} soundEnabled={false} />
                </ChakraProvider>
            );

            expect(screen.getByText('Player')).toBeInTheDocument();
            expect(screen.getByText('Bot')).toBeInTheDocument();
            expect(screen.getByText('10:00')).toBeInTheDocument();
            expect(screen.getByText('ACTIVE')).toBeInTheDocument();
        });

        it('is accessible', async () => {
            const { container } = render(
                <ChakraProvider>
                    <GameViewer game={mockGameState} isLoading={false} soundEnabled={false} />
                </ChakraProvider>
            );

            // Check for ARIA labels
            expect(screen.getByRole('region')).toBeInTheDocument(); // Chessboard
            expect(container.querySelector('[aria-label="Game Status"]')).toBeInTheDocument();
            expect(container.querySelector('[aria-live="polite"]')).toBeInTheDocument();
        });
    });

    describe('Game Timer Behavior', () => {
        it('updates white player time during their turn', () => {
            const gameState = { ...mockGameState };
            render(
                <ChakraProvider>
                    <GameViewer game={gameState} isLoading={false} soundEnabled={false} />
                </ChakraProvider>
            );

            expect(screen.getByText('10:00')).toBeInTheDocument();
            vi.advanceTimersByTime(1000);
            expect(screen.getByText('9:59')).toBeInTheDocument();
        });

        it('shows red timer when time is low', () => {
            const lowTimeGame = { ...mockGameState, whiteTime: 25 };
            const { container } = render(
                <ChakraProvider>
                    <GameViewer game={lowTimeGame} isLoading={false} soundEnabled={false} />
                </ChakraProvider>
            );

            const timeElement = screen.getByText('0:25');
            expect(timeElement).toHaveStyle({ color: expect.stringContaining('red') });
        });

        it('stops timer when game is finished', () => {
            const finishedGame = { ...mockGameState, status: 'finished' as const };
            render(
                <ChakraProvider>
                    <GameViewer game={finishedGame} isLoading={false} soundEnabled={false} />
                </ChakraProvider>
            );

            const initialTime = screen.getByText('10:00');
            vi.advanceTimersByTime(5000);
            expect(screen.getByText('10:00')).toBe(initialTime);
        });
    });

    describe('Move Handling', () => {
        it('handles valid moves correctly', async () => {
            mockFetch.mockImplementationOnce(() => 
                Promise.resolve({ 
                    ok: true,
                    json: () => Promise.resolve({ success: true })
                })
            );

            const { container } = render(
                <ChakraProvider>
                    <GameViewer game={mockGameState} isLoading={false} soundEnabled={false} />
                </ChakraProvider>
            );

            const sourceSquare = container.querySelector('[data-square="e2"]');
            const targetSquare = container.querySelector('[data-square="e4"]');

            fireEvent.click(sourceSquare!);
            fireEvent.click(targetSquare!);

            await waitFor(() => {
                expect(mockFetch).toHaveBeenCalledWith(
                    expect.stringContaining('/move'),
                    expect.objectContaining({
                        method: 'POST',
                        body: expect.stringContaining('e2'),
                    })
                );
            });
        });

        it('handles invalid moves appropriately', async () => {
            mockFetch.mockImplementationOnce(() => 
                Promise.resolve({ 
                    ok: false,
                    status: 400,
                    json: () => Promise.resolve({ detail: 'Invalid move' })
                })
            );

            const { container } = render(
                <ChakraProvider>
                    <GameViewer game={mockGameState} isLoading={false} soundEnabled={false} />
                </ChakraProvider>
            );

            const sourceSquare = container.querySelector('[data-square="e2"]');
            const targetSquare = container.querySelector('[data-square="e6"]');

            fireEvent.click(sourceSquare!);
            fireEvent.click(targetSquare!);

            await waitFor(() => {
                expect(screen.getByText('Move Error')).toBeInTheDocument();
                expect(screen.getByText('Invalid move')).toBeInTheDocument();
            });
        });

        it('handles network errors with retry', async () => {
            mockFetch
                .mockImplementationOnce(() => Promise.reject(new Error('Network error')))
                .mockImplementationOnce(() => Promise.resolve({ ok: true }));

            const { container } = render(
                <ChakraProvider>
                    <GameViewer game={mockGameState} isLoading={false} soundEnabled={false} />
                </ChakraProvider>
            );

            const sourceSquare = container.querySelector('[data-square="e2"]');
            const targetSquare = container.querySelector('[data-square="e4"]');

            fireEvent.click(sourceSquare!);
            fireEvent.click(targetSquare!);

            await waitFor(() => {
                expect(mockFetch).toHaveBeenCalledTimes(2);
            });
        });
    });

    describe('Game State Transitions', () => {
        it('shows victory message for human player win', () => {
            const winningGame: GameState = {
                ...mockGameState,
                status: 'finished',
                result: '1-0',
                resultReason: 'Checkmate'
            };

            render(
                <ChakraProvider>
                    <GameViewer game={winningGame} isLoading={false} soundEnabled={false} />
                </ChakraProvider>
            );

            expect(screen.getByText('Victory!')).toBeInTheDocument();
            expect(screen.getByText('Checkmate')).toBeInTheDocument();
        });

        it('handles reconnection attempts', async () => {
            mockFetch
                .mockImplementationOnce(() => Promise.reject(new Error('Network error')))
                .mockImplementationOnce(() => Promise.resolve({ ok: true }));

            render(
                <ChakraProvider>
                    <GameViewer game={mockGameState} onReconnect={mockOnReconnect} isLoading={false} soundEnabled={false} />
                </ChakraProvider>
            );

            // Trigger a disconnection
            const { container } = render(
                <ChakraProvider>
                    <GameViewer game={mockGameState} isLoading={false} soundEnabled={false} />
                </ChakraProvider>
            );

            const sourceSquare = container.querySelector('[data-square="e2"]');
            const targetSquare = container.querySelector('[data-square="e4"]');

            fireEvent.click(sourceSquare!);
            fireEvent.click(targetSquare!);

            await waitFor(() => {
                expect(screen.getByText('RECONNECTING...')).toBeInTheDocument();
            });

            // Wait for reconnection attempt
            vi.advanceTimersByTime(2000);

            await waitFor(() => {
                expect(mockOnReconnect).toHaveBeenCalled();
            });
        });
    });

    describe('Advanced Move Handling', () => {
        it('handles pawn promotion correctly', async () => {
            const promotionPosition = {
                ...mockGameState,
                fen: 'rnbqkbnr/ppppppPp/8/8/8/8/PPPP1P1P/RNBQKBNR w KQkq - 0 1'
            };

            mockFetch.mockImplementationOnce(() => 
                Promise.resolve({ 
                    ok: true,
                    json: () => Promise.resolve({ success: true })
                })
            );

            const { container } = render(
                <ChakraProvider>
                    <GameViewer game={promotionPosition} isLoading={false} soundEnabled={false} />
                </ChakraProvider>
            );

            const sourceSquare = container.querySelector('[data-square="g7"]');
            const targetSquare = container.querySelector('[data-square="g8"]');

            fireEvent.click(sourceSquare!);
            fireEvent.click(targetSquare!);

            await waitFor(() => {
                expect(mockFetch).toHaveBeenCalledWith(
                    expect.stringContaining('/move'),
                    expect.objectContaining({
                        method: 'POST',
                        body: expect.stringContaining('"promotion":"q"')
                    })
                );
            });
        });

        it('handles maximum retry attempts correctly', async () => {
            mockFetch
                .mockImplementationOnce(() => Promise.reject(new Error('Network error')))
                .mockImplementationOnce(() => Promise.reject(new Error('Network error')))
                .mockImplementationOnce(() => Promise.reject(new Error('Network error')));

            const { container } = render(
                <ChakraProvider>
                    <GameViewer game={mockGameState} isLoading={false} soundEnabled={false} />
                </ChakraProvider>
            );

            const sourceSquare = container.querySelector('[data-square="e2"]');
            const targetSquare = container.querySelector('[data-square="e4"]');

            fireEvent.click(sourceSquare!);
            fireEvent.click(targetSquare!);

            await waitFor(() => {
                expect(mockFetch).toHaveBeenCalledTimes(3); // MAX_MOVE_RETRIES + 1
                expect(screen.getByText('Connection Lost')).toBeInTheDocument();
            });
        });

        it('prevents moves during opponent turn', () => {
            const blackTurnGame = {
                ...mockGameState,
                fen: 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1'
            };

            const { container } = render(
                <ChakraProvider>
                    <GameViewer game={blackTurnGame} isLoading={false} soundEnabled={false} />
                </ChakraProvider>
            );

            const sourceSquare = container.querySelector('[data-square="e7"]');
            fireEvent.click(sourceSquare!);

            expect(mockFetch).not.toHaveBeenCalled();
        });
    });

    describe('Toast Notification Behavior', () => {
        it('limits the number of active toasts', async () => {
            mockFetch.mockImplementation(() => 
                Promise.resolve({ 
                    ok: false,
                    status: 400,
                    json: () => Promise.resolve({ detail: 'Invalid move' })
                })
            );

            const { container } = render(
                <ChakraProvider>
                    <GameViewer game={mockGameState} isLoading={false} soundEnabled={false} />
                </ChakraProvider>
            );

            const sourceSquare = container.querySelector('[data-square="e2"]');
            const targetSquare = container.querySelector('[data-square="e6"]');

            // Trigger multiple invalid moves
            for (let i = 0; i < 6; i++) {
                fireEvent.click(sourceSquare!);
                fireEvent.click(targetSquare!);
                await waitFor(() => {
                    const toasts = document.querySelectorAll('[role="alert"]');
                    expect(toasts.length).toBeLessThanOrEqual(4); // MAX_TOASTS
                });
            }
        });
    });

    describe('Game Mode Transitions', () => {
        it('handles transition from human vs bot to bot vs bot', async () => {
            const gameState = { ...mockGameState };
            const { rerender } = render(
                <ChakraProvider>
                    <GameViewer game={gameState} />
                </ChakraProvider>
            );

            expect(screen.getByText('Human vs Bot')).toBeInTheDocument();

            const newGameState = {
                ...gameState,
                gameMode: 'bot_vs_bot' as const
            };

            rerender(
                <ChakraProvider>
                    <GameViewer game={newGameState} />
                </ChakraProvider>
            );

            expect(screen.getByText('Bot vs Bot')).toBeInTheDocument();
        });

        it('updates timer behavior when game mode changes', () => {
            const gameState = { ...mockGameState };
            const { rerender } = render(
                <ChakraProvider>
                    <GameViewer game={gameState} />
                </ChakraProvider>
            );

            vi.advanceTimersByTime(1000);
            expect(screen.getByText('9:59')).toBeInTheDocument();

            const botGame = {
                ...gameState,
                gameMode: 'bot_vs_bot' as const
            };

            rerender(
                <ChakraProvider>
                    <GameViewer game={botGame} />
                </ChakraProvider>
            );

            vi.advanceTimersByTime(1000);
            // In bot vs bot mode, both timers should update
            expect(screen.getAllByText('9:58')).toHaveLength(2);
        });
    });

    describe('Race Condition Handling', () => {
        it('handles rapid move attempts correctly', async () => {
            mockFetch.mockImplementation(() => 
                new Promise(resolve => setTimeout(() => resolve({ ok: true }), 100))
            );

            const { container } = render(
                <ChakraProvider>
                    <GameViewer game={mockGameState} />
                </ChakraProvider>
            );

            const sourceSquare = container.querySelector('[data-square="e2"]');
            const targetSquare = container.querySelector('[data-square="e4"]');

            // Attempt multiple rapid moves
            fireEvent.click(sourceSquare!);
            fireEvent.click(targetSquare!);
            fireEvent.click(sourceSquare!);
            fireEvent.click(targetSquare!);

            await waitFor(() => {
                expect(screen.getByText('PROCESSING...')).toBeInTheDocument();
            });

            // Only one move should be processed
            expect(mockFetch).toHaveBeenCalledTimes(1);
        });

        it('handles move attempts during reconnection', async () => {
            mockFetch
                .mockImplementationOnce(() => Promise.reject(new Error('Network error')))
                .mockImplementationOnce(() => Promise.resolve({ ok: true }));

            const { container } = render(
                <ChakraProvider>
                    <GameViewer game={mockGameState} />
                </ChakraProvider>
            );

            const sourceSquare = container.querySelector('[data-square="e2"]');
            const targetSquare = container.querySelector('[data-square="e4"]');

            // Trigger disconnection
            fireEvent.click(sourceSquare!);
            fireEvent.click(targetSquare!);

            await waitFor(() => {
                expect(screen.getByText('RECONNECTING...')).toBeInTheDocument();
            });

            // Attempt move during reconnection
            fireEvent.click(sourceSquare!);
            fireEvent.click(targetSquare!);

            // No additional move attempts should be made
            expect(mockFetch).toHaveBeenCalledTimes(2); // Initial attempt + reconnection check
        });
    });

    describe('Time-out Notification', () => {
        it('should show time-out notification only once when time runs out', () => {
            const gameState: GameState = {
                id: 'test',
                fen: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
                status: 'active',
                lastMove: null,
                moveCount: 0,
                whiteTime: 2,
                blackTime: 300,
                whiteName: 'Player',
                blackName: 'Bot',
                gameMode: 'human_vs_bot',
            };

            render(<GameViewer game={gameState} />);

            // Advance timer by 1 second
            act(() => {
                jest.advanceTimersByTime(1000);
            });

            // Time should be at 1 second
            expect(screen.getByText('0:01')).toBeInTheDocument();

            // Advance timer by 1 more second
            act(() => {
                jest.advanceTimersByTime(1000);
            });

            // Time should be at 0
            expect(screen.getByText('0:00')).toBeInTheDocument();

            // Toast should be called exactly once with time-out message
            expect(mockToast).toHaveBeenCalledTimes(1);
            expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({
                title: 'Time Out',
                description: 'You lost on time',
                status: 'error',
                duration: 5000,
                isClosable: true,
                key: 'time-out',
            }));

            // Advance timer more
            act(() => {
                jest.advanceTimersByTime(1000);
            });

            // Toast should still only have been called once
            expect(mockToast).toHaveBeenCalledTimes(1);
        });

        it('should auto-dismiss game end notification after duration', () => {
            const gameState: GameState = {
                id: 'test',
                fen: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
                status: 'finished',
                lastMove: 'e2e4',
                moveCount: 10,
                whiteTime: 0,
                blackTime: 300,
                whiteName: 'Player',
                blackName: 'Bot',
                gameMode: 'human_vs_bot',
                result: '0-1',
                resultReason: 'Time out',
            };

            render(<GameViewer game={gameState} />);

            // Toast should be called with game end message and 5s duration
            expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({
                title: 'Defeat',
                description: 'Time out',
                status: 'error',
                duration: 5000,
                isClosable: true,
                key: 'game-end',
            }));
        });
    });
}); 