import React from 'react';
import { Chessboard } from 'react-chessboard';
import { Box, VStack, HStack, Text, Badge, useColorModeValue } from '@chakra-ui/react';
import { GameState } from '../types/game';
import { Square, Piece } from 'chess.js';

interface GameViewerProps {
    game: GameState;
}

const API_URL = '/api';  // Add back /api prefix for proxy to work

const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
};

export const GameViewer: React.FC<GameViewerProps> = ({ game }) => {
    const bgColor = useColorModeValue('white', 'gray.800');
    const textColor = useColorModeValue('gray.800', 'white');

    const onDrop = async (sourceSquare: Square, targetSquare: Square, piece: string) => {
        try {
            // Handle pawn promotion
            const isPawnPromotion = (piece.toUpperCase() === 'WP' && targetSquare[1] === '8') || 
                                  (piece.toUpperCase() === 'BP' && targetSquare[1] === '1');
            const promotion = isPawnPromotion ? 'q' : undefined; // Always promote to queen for simplicity

            const response = await fetch(`${API_URL}/move`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    from: sourceSquare,
                    to: targetSquare,
                    promotion
                }),
            });

            if (!response.ok) {
                const error = await response.json();
                console.error('Move error:', error);
                return false;
            }

            return true;
        } catch (error) {
            console.error('Error making move:', error);
            return false;
        }
    };

    // Convert last move to custom arrows format
    const customArrows = game.lastMove ? [
        [game.lastMove.slice(0, 2) as Square, game.lastMove.slice(2, 4) as Square]
    ] : [];

    return (
        <VStack spacing={4} bg={bgColor} p={4} borderRadius="lg" shadow="md">
            <HStack w="full" justify="space-between">
                <Box>
                    <Text fontWeight="bold">{game.whiteName}</Text>
                    <Text fontSize="lg">{formatTime(game.whiteTime)}</Text>
                </Box>
                <Badge colorScheme={game.status === 'active' ? 'green' : 'gray'}>
                    {game.status.toUpperCase()}
                </Badge>
                <Box textAlign="right">
                    <Text fontWeight="bold">{game.blackName}</Text>
                    <Text fontSize="lg">{formatTime(game.blackTime)}</Text>
                </Box>
            </HStack>

            <Box w="full" maxW="600px">
                <Chessboard 
                    position={game.fen}
                    boardWidth={600}
                    areArrowsAllowed
                    showBoardNotation
                    customArrows={customArrows}
                    onPieceDrop={onDrop}
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