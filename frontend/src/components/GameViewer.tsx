import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Chessboard } from 'react-chessboard';
import { Box, VStack, HStack, Text, Badge, useColorModeValue, Skeleton } from '@chakra-ui/react';
import { GameState } from '../types/game';
import { Square, Chess, Move } from 'chess.js';
import { Arrow as ChessboardArrow } from 'react-chessboard/dist/chessboard/types';
import { useChessSound } from '../hooks/useChessSound';
import { useSettings } from '../contexts/SettingsContext';
import { useToast } from '../hooks/useToast';
import logger from '../utils/logger';

interface GameViewerProps {
    game: GameState;
    onReconnect?: () => void;
    isLoading?: boolean;
    soundEnabled?: boolean;  // New prop to control sound
}

const API_URL = '/api';
const RETRY_DELAY = 2000; // 2 seconds between retries
const REQUEST_TIMEOUT = 5000; // 5 seconds timeout for requests
const MAX_MOVE_RETRIES = 2; // Maximum number of times to retry a move
const MAX_TOASTS = 4;  // Maximum number of toasts to show at once

const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
};

// Utility function to add timeout to fetch
const fetchWithTimeout = async (url: string, options: RequestInit = {}, timeout = REQUEST_TIMEOUT) => {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        clearTimeout(id);
        return response;
    } catch (error) {
        clearTimeout(id);
        throw error;
    }
};

// Custom toast function that limits the number of toasts
const useCustomToast = () => {
    const toast = useToast();
    return (props: any) => {
        // Close oldest toast if we're at the limit
        const toasts = document.querySelectorAll('[role="alert"]');
        if (toasts.length >= MAX_TOASTS) {
            toast.closeAll();
        }
        return toast(props);
    };
};

export const GameViewer: React.FC<GameViewerProps> = ({ 
    game, 
    onReconnect, 
    isLoading = false,
    soundEnabled = true  // Default to true for backward compatibility
}) => {
    const bgColor = useColorModeValue('white', 'gray.800');
    const textColor = useColorModeValue('gray.800', 'white');
    const [whiteTimeLeft, setWhiteTimeLeft] = useState(game.whiteTime);
    const [blackTimeLeft, setBlackTimeLeft] = useState(game.blackTime);
    const [isReconnecting, setIsReconnecting] = useState(false);
    const [moveInProgress, setMoveInProgress] = useState(false);
    const [selectedSquare, setSelectedSquare] = useState<Square | null>(null);
    const toast = useToast();
    const { settings } = useSettings();
    const { playMoveSound } = useChessSound(settings.soundEnabled && soundEnabled);
    const [gameState, setGameState] = useState(() => {
        const chess = new Chess();
        chess.load(game.fen);
        return chess;
    });
    const gameEndRef = useRef<boolean>(false);

    // Update local time state when game state changes
    useEffect(() => {
        setWhiteTimeLeft(game.whiteTime);
        setBlackTimeLeft(game.blackTime);
    }, [game.whiteTime, game.blackTime]);

    // Show game result notification when game ends
    useEffect(() => {
        if (game.status === 'finished' && game.result && !gameEndRef.current) {
            gameEndRef.current = true;
            const isHumanGame = game.gameMode === 'human_vs_bot';
            const humanIsWhite = isHumanGame;
            const humanWon = (humanIsWhite && game.result === '1-0') || (!humanIsWhite && game.result === '0-1');
            
            // Close any existing toasts
            toast.closeAll();
            
            if (isHumanGame) {
                toast({
                    title: humanWon ? 'Victory!' : 'Defeat',
                    description: game.resultReason || (humanWon ? 'You won the game!' : 'You lost the game'),
                    status: humanWon ? 'success' : 'error',
                    duration: 5000,
                    isClosable: true,
                    key: 'game-end',
                });
            } else {
                toast({
                    title: 'Game Over',
                    description: game.resultReason || `${game.result === '1-0' ? 'White' : 'Black'} won the game`,
                    status: 'info',
                    duration: 5000,
                    isClosable: true,
                    key: 'game-end',
                });
            }
            logger.info('Game ended', {
                result: game.result,
                reason: game.resultReason,
                mode: game.gameMode,
            });
        }
    }, [game.status, game.result, game.gameMode, game.resultReason, toast]);

    // Reset game end ref when starting a new game
    useEffect(() => {
        if (game.status === 'active') {
            gameEndRef.current = false;
            // Clear any lingering game end toasts
            toast.closeAll();
        }
    }, [game.status, toast]);

    // Health check function
    const checkServerHealth = useCallback(async () => {
        try {
            const response = await fetchWithTimeout(`${API_URL}/health`);
            if (response.ok) {
                if (isReconnecting) {
                    setIsReconnecting(false);
                    onReconnect?.();
                    toast({
                        title: 'Reconnected',
                        description: 'Connection to server restored',
                        status: 'success',
                        duration: 3000,
                        isClosable: true,
                    });
                }
                return true;
            }
            return false;
        } catch (error) {
            return false;
        }
    }, [isReconnecting, onReconnect, toast]);

    // Reconnection logic
    useEffect(() => {
        let reconnectInterval: NodeJS.Timeout | null = null;

        const handleReconnection = async () => {
            if (isReconnecting) {
                const isHealthy = await checkServerHealth();
                if (!isHealthy) {
                    reconnectInterval = setTimeout(handleReconnection, RETRY_DELAY);
                }
            }
        };

        if (isReconnecting) {
            handleReconnection();
        }

        return () => {
            if (reconnectInterval) {
                clearTimeout(reconnectInterval);
            }
        };
    }, [isReconnecting, checkServerHealth]);

    // Live clock update with time-out handling
    useEffect(() => {
        if (game.status !== 'active' || moveInProgress) return;

        const interval = setInterval(() => {
            if (game.status === 'active' && !moveInProgress) {
                if (game.gameMode === 'human_vs_bot') {
                    if (game.fen.includes(' w ')) {
                        setWhiteTimeLeft(prev => {
                            const newTime = Math.max(0, prev - 1);
                            // Only show time-out notification if time just ran out
                            if (prev > 0 && newTime === 0 && !gameEndRef.current) {
                                gameEndRef.current = true;
                                toast({
                                    title: 'Time Out',
                                    description: 'You lost on time',
                                    status: 'error',
                                    duration: 5000,
                                    isClosable: true,
                                    key: 'time-out',
                                });
                            }
                            return newTime;
                        });
                    }
                } else {
                    if (game.fen.includes(' w ')) {
                        setWhiteTimeLeft(prev => {
                            const newTime = Math.max(0, prev - 1);
                            if (prev > 0 && newTime === 0 && !gameEndRef.current) {
                                gameEndRef.current = true;
                                toast({
                                    title: 'Time Out',
                                    description: 'White lost on time',
                                    status: 'info',
                                    duration: 5000,
                                    isClosable: true,
                                    key: 'time-out',
                                });
                            }
                            return newTime;
                        });
                    } else {
                        setBlackTimeLeft(prev => {
                            const newTime = Math.max(0, prev - 1);
                            if (prev > 0 && newTime === 0 && !gameEndRef.current) {
                                gameEndRef.current = true;
                                toast({
                                    title: 'Time Out',
                                    description: 'Black lost on time',
                                    status: 'info',
                                    duration: 5000,
                                    isClosable: true,
                                    key: 'time-out',
                                });
                            }
                            return newTime;
                        });
                    }
                }
            }
        }, 1000);

        return () => clearInterval(interval);
    }, [game.status, game.fen, game.gameMode, moveInProgress, toast]);

    // Fetch game state with better error handling
    const fetchGameState = useCallback(async () => {
        try {
            logger.info('Fetching game state');
            const response = await fetchWithTimeout(`${API_URL}/game`);
            
            if (!response.ok) {
                const errorText = await response.text();
                let errorDetail;
                try {
                    errorDetail = JSON.parse(errorText).detail;
                } catch {
                    errorDetail = errorText;
                }
                
                logger.error('Game state fetch failed', {
                    status: response.status,
                    statusText: response.statusText,
                    error: errorDetail,
                    url: `${API_URL}/game`
                });

                toast({
                    title: 'Failed to fetch game state',
                    description: `Server error: ${response.status} - ${errorDetail || response.statusText}`,
                    status: 'error',
                    duration: 5000,
                    isClosable: true,
                    key: 'fetch-error'
                });

                // If backend is down, trigger reconnection
                if (response.status >= 500) {
                    setIsReconnecting(true);
                }
                return;
            }

            const data = await response.json();
            logger.debug('Game state received', data);
            
            // Update local game state
            const chess = new Chess();
            chess.load(data.fen);
            setGameState(chess);

            // Update game state from server
            setWhiteTimeLeft(data.whiteTime);
            setBlackTimeLeft(data.blackTime);

        } catch (error) {
            logger.error('Error fetching game state', {
                error: error instanceof Error ? error.message : String(error),
                stack: error instanceof Error ? error.stack : undefined
            });

            toast({
                title: 'Connection Error',
                description: error instanceof Error ? error.message : 'Failed to connect to server',
                status: 'error',
                duration: 5000,
                isClosable: true,
                key: 'connection-error'
            });

            setIsReconnecting(true);
        }
    }, [toast]);

    // Poll game state
    useEffect(() => {
        if (isReconnecting || !game.status) return;

        fetchGameState();
        const interval = setInterval(fetchGameState, 1000);
        return () => clearInterval(interval);
    }, [fetchGameState, isReconnecting, game.status]);

    const handleMove = useCallback((move: Move) => {
        try {
            const newPosition = new Chess();
            newPosition.load(game.fen);
            const result = newPosition.move(move);
            
            if (result) {
                playMoveSound(
                    move,
                    newPosition.isCheck(),
                    newPosition.isGameOver()
                );
                setGameState(newPosition);
            }
        } catch (error) {
            logger.error('Invalid move:', error);
            toast({
                title: 'Invalid Move',
                description: 'That move is not allowed',
                status: 'error',
                duration: 2000,
                key: 'invalid-move',
            });
        }
    }, [game, playMoveSound, toast]);

    const makeMove = async (
        sourceSquare: Square, 
        targetSquare: Square,
        retryCount = 0
    ): Promise<boolean> => {
        try {
            setMoveInProgress(true);
            logger.info('Making move', { 
                sourceSquare, 
                targetSquare,
                gameMode: game.gameMode,
                isWhiteTurn: game.fen.includes(' w '),
                moveCount: game.moveCount
            });

            // Show loading state for bot moves
            if (game.gameMode === 'human_vs_bot') {
                toast({
                    title: 'Processing move...',
                    status: 'info',
                    duration: null,
                    isClosable: false,
                    key: 'move-processing'
                });
            }

            const response = await fetchWithTimeout(
                `${API_URL}/move`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        from: sourceSquare,
                        to: targetSquare,
                        promotion: 'q',
                        white_depth: game.whiteDepth,
                        black_depth: game.blackDepth
                    }),
                }
            );

            if (!response.ok) {
                const errorText = await response.text();
                let errorDetail;
                try {
                    errorDetail = JSON.parse(errorText).detail;
                } catch {
                    errorDetail = errorText;
                }

                logger.error('Move failed', {
                    status: response.status,
                    statusText: response.statusText,
                    error: errorDetail,
                    move: { sourceSquare, targetSquare }
                });

                if (response.status === 503 || response.status === 502) {
                    if (retryCount < MAX_MOVE_RETRIES) {
                        logger.warn('Move failed, retrying...', { retryCount });
                        await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
                        return makeMove(sourceSquare, targetSquare, retryCount + 1);
                    }
                    setIsReconnecting(true);
                    toast({
                        title: 'Server Disconnected',
                        description: 'Server is not responding. Attempting to reconnect...',
                        status: 'warning',
                        duration: null,
                        isClosable: false,
                        key: 'server-disconnect'
                    });
                } else {
                    toast({
                        title: 'Move Error',
                        description: errorDetail || 'Failed to make move',
                        status: 'error',
                        duration: 3000,
                        isClosable: true,
                        key: 'move-error'
                    });
                }
                return false;
            }

            // Update game state after successful move
            const newGameState = await response.json();
            logger.debug('Move response', newGameState);

            if (newGameState.fen) {
                const chess = new Chess();
                chess.load(newGameState.fen);
                setGameState(chess);
                
                // Update times
                if (newGameState.whiteTime) setWhiteTimeLeft(newGameState.whiteTime);
                if (newGameState.blackTime) setBlackTimeLeft(newGameState.blackTime);
            }

            // Close any processing toasts
            toast.close('move-processing');
            return true;

        } catch (error) {
            logger.error('Move error', {
                error: error instanceof Error ? error.message : String(error),
                stack: error instanceof Error ? error.stack : undefined,
                move: { sourceSquare, targetSquare }
            });

            if (error instanceof Error && error.name === 'AbortError') {
                toast({
                    title: 'Move Timeout',
                    description: 'The server took too long to respond. Please try again.',
                    status: 'error',
                    duration: 3000,
                    isClosable: true,
                    key: 'move-timeout'
                });
            } else if (retryCount < MAX_MOVE_RETRIES) {
                logger.warn('Move failed, retrying...', { error, retryCount });
                await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
                return makeMove(sourceSquare, targetSquare, retryCount + 1);
            } else {
                setIsReconnecting(true);
                toast({
                    title: 'Connection Lost',
                    description: 'Cannot reach the server. Attempting to reconnect...',
                    status: 'warning',
                    duration: null,
                    isClosable: false,
                    key: 'connection-lost'
                });
            }
            return false;
        } finally {
            setMoveInProgress(false);
            setSelectedSquare(null);
            toast.close('move-processing');
        }
    };

    const onSquareClick = (square: Square) => {
        // If it's not the player's turn or the game is not active, do nothing
        if (game.status !== 'active' || 
            (game.gameMode === 'human_vs_bot' && !game.fen.includes(' w '))) {
            return;
        }

        if (selectedSquare === null) {
            setSelectedSquare(square);
        } else {
            if (square !== selectedSquare) {
                makeMove(selectedSquare, square);
            }
            setSelectedSquare(null);
        }
    };

    const customArrows: ChessboardArrow[] = game.lastMove ? [
        [game.lastMove.slice(0, 2) as Square, game.lastMove.slice(2, 4) as Square]
    ] : [];

    // Calculate which squares should be highlighted
    const customSquareStyles = {
        ...(selectedSquare ? {
            [selectedSquare]: {
                background: 'rgba(255, 255, 0, 0.4)',
                borderRadius: '50%'
            }
        } : {}),
        ...(game.lastMove ? {
            [game.lastMove.slice(0, 2)]: { background: 'rgba(255, 255, 0, 0.2)' },
            [game.lastMove.slice(2, 4)]: { background: 'rgba(255, 255, 0, 0.2)' }
        } : {})
    };

    if (isLoading) {
        return (
            <VStack spacing={4} align="stretch" data-testid="loading-skeleton">
                <Skeleton height="400px" />
                <HStack justify="space-between">
                    <Skeleton height="20px" width="100px" />
                    <Skeleton height="20px" width="100px" />
                </HStack>
            </VStack>
        );
    }

    return (
        <VStack spacing={4} bg={bgColor} p={4} borderRadius="lg" shadow="md">
            <HStack w="full" justify="space-between">
                <Box>
                    <Text fontWeight="bold">{game.whiteName}</Text>
                    <Text 
                        fontSize="lg" 
                        color={
                            game.status === 'finished' && game.result === '0-1' ? 'red.500' :
                            whiteTimeLeft < 30 ? 'red.500' : 
                            undefined
                        }
                    >
                        {formatTime(whiteTimeLeft)}
                    </Text>
                </Box>
                <Badge colorScheme={
                    moveInProgress ? 'blue' :
                    isReconnecting ? 'yellow' : 
                    game.status === 'active' ? 'green' : 
                    'gray'
                }>
                    {moveInProgress ? 'PROCESSING...' :
                     isReconnecting ? 'RECONNECTING...' : 
                     game.status === 'finished' ? (game.resultReason || game.status.toUpperCase()) :
                     game.status.toUpperCase()}
                </Badge>
                <Box textAlign="right">
                    <Text fontWeight="bold">{game.blackName}</Text>
                    <Text 
                        fontSize="lg" 
                        color={
                            game.status === 'finished' && game.result === '1-0' ? 'red.500' :
                            blackTimeLeft < 30 ? 'red.500' : 
                            undefined
                        }
                    >
                        {formatTime(blackTimeLeft)}
                    </Text>
                </Box>
            </HStack>

            <Box w="full" maxW="600px" opacity={isReconnecting || moveInProgress ? 0.7 : 1}>
                <Chessboard 
                    position={game.fen}
                    boardWidth={600}
                    areArrowsAllowed
                    showBoardNotation
                    customArrows={customArrows}
                    onSquareClick={onSquareClick}
                    customSquareStyles={customSquareStyles}
                />
            </Box>

            <HStack w="full" justify="space-between" color={textColor}>
                <Text>Last Move: {game.lastMove || '-'}</Text>
                <Text>Move Count: {game.moveCount}</Text>
                {game.result && <Text>Result: {game.result}</Text>}
            </HStack>
        </VStack>
    );
}; 