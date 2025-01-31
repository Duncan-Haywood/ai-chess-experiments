import React, { useState, useEffect } from 'react';
import { ChakraProvider, Box, VStack, HStack, Button, useToast } from '@chakra-ui/react';
import { GameViewer } from './components/GameViewer';
import { EngineMonitor } from './components/EngineMonitor';
import { ErrorBoundary } from './components/ErrorBoundary';
import { PerformanceMonitor } from './components/PerformanceMonitor';
import { useGameState } from './hooks/useGameState';
import theme from './theme';
import { GameState, EngineMetrics, GameMode } from './types/game';

const API_URL = '/api';

export const App: React.FC = () => {
  const toast = useToast();
  const { gameState, error, isLoading, engineMetrics, startNewGame } = useGameState();

  useEffect(() => {
    if (error) {
      toast({
        title: 'Error',
        description: error,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  }, [error, toast]);

  const handleNewGame = async (mode: GameMode) => {
    try {
      // Use default depth of 3 for both players
      await startNewGame(mode, 3, 3);
      toast({
        title: 'New Game Started',
        status: 'success',
        duration: 2000,
        isClosable: true,
      });
    } catch (err) {
      toast({
        title: 'Failed to start new game',
        description: err instanceof Error ? err.message : 'Unknown error',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  // Convert engineMetrics to array if it's not already
  const metricsArray = Array.isArray(engineMetrics) ? engineMetrics : engineMetrics ? [engineMetrics] : [];

  return (
    <ChakraProvider theme={theme}>
      <ErrorBoundary>
        <Box p={4}>
          <VStack spacing={4} align="stretch">
            <HStack spacing={4} justify="center">
              <Button
                colorScheme="blue"
                size="lg"
                onClick={() => handleNewGame('human_vs_bot')}
                isLoading={isLoading}
              >
                Play vs Bot
              </Button>
              <Button
                colorScheme="green"
                size="lg"
                onClick={() => handleNewGame('bot_vs_bot')}
                isLoading={isLoading}
              >
                Watch Bots Play
              </Button>
            </HStack>
            {gameState && (
              <GameViewer
                game={gameState}
                isLoading={isLoading}
                soundEnabled={true}
              />
            )}
            <EngineMonitor
              engineName={gameState?.blackEngine || 'minimax'}
              metrics={metricsArray}
              isThinking={gameState?.status === 'active' && !gameState?.turn}
            />
            <PerformanceMonitor />
          </VStack>
        </Box>
      </ErrorBoundary>
    </ChakraProvider>
  );
};

export default App; 