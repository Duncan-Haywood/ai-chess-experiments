import React, { useState, useEffect } from 'react';
import { ChakraProvider, Box, VStack, useToast } from '@chakra-ui/react';
import { GameViewer } from './components/GameViewer';
import { EngineMonitor } from './components/EngineMonitor';
import { ErrorBoundary } from './components/ErrorBoundary';
import { PerformanceMonitor } from './components/PerformanceMonitor';
import { useGameState } from './hooks/useGameState';
import theme from './theme';
import { GameState, EngineMetrics } from './types/game';

export const App: React.FC = () => {
  const toast = useToast();
  const { gameState, error, isLoading, engineMetrics } = useGameState();

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

  // Convert engineMetrics to array if it's not already
  const metricsArray = Array.isArray(engineMetrics) ? engineMetrics : engineMetrics ? [engineMetrics] : [];

  return (
    <ChakraProvider theme={theme}>
      <ErrorBoundary>
        <Box p={4}>
          <VStack spacing={4} align="stretch">
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