import { useEffect, useState } from 'react';
import { ChakraProvider, Container, Button, VStack, HStack, useToast, Text } from '@chakra-ui/react';
import { GameViewer } from './components/GameViewer';
import { GameState } from './types/game';
import theme from './theme';

const API_URL = '/api';  // Add back /api prefix for proxy to work
const POLL_INTERVAL = 250; // Poll every 250ms

console.log('App.tsx loaded, API_URL:', API_URL);

function App() {
    const [gameState, setGameState] = useState<GameState | null>(null);
    const [isHealthy, setIsHealthy] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const toast = useToast();

    // Check backend health
    useEffect(() => {
        const checkHealth = async () => {
            try {
                console.log('Checking health...');
                const res = await fetch(`${API_URL}/health`);
                const wasHealthy = isHealthy;
                const isNowHealthy = res.ok;
                setIsHealthy(isNowHealthy);
                console.log('Health check result:', isNowHealthy, 'Status:', res.status);
                
                // Show toast when health status changes
                if (wasHealthy && !isNowHealthy) {
                    toast({
                        title: "Backend is down",
                        status: "error",
                        duration: null,
                        isClosable: true,
                    });
                } else if (!wasHealthy && isNowHealthy) {
                    toast({
                        title: "Backend is back up",
                        status: "success",
                        duration: 3000,
                        isClosable: true,
                    });
                }
            } catch (err) {
                console.error('Health check error:', err);
                setIsHealthy(false);
                setError(err instanceof Error ? err.message : 'Unknown error');
            }
        };

        // Check health every 5 seconds
        checkHealth();
        const interval = setInterval(checkHealth, 5000);
        return () => clearInterval(interval);
    }, [isHealthy, toast]);

    // Fetch game state frequently
    useEffect(() => {
        const fetchGameState = async () => {
            try {
                console.log('Fetching game state from:', `${API_URL}/game`);
                const res = await fetch(`${API_URL}/game`);
                if (!res.ok) {
                    console.error('Game state fetch failed:', res.status, res.statusText, 'URL:', `${API_URL}/game`);
                    throw new Error(`Failed to fetch game state: ${res.status} ${res.statusText}`);
                }
                const data = await res.json();
                console.log('Game state received:', JSON.stringify(data, null, 2));
                setGameState(data);
                setError(null);
            } catch (err) {
                console.error('Error fetching game state:', err);
                setError(err instanceof Error ? err.message : 'Unknown error');
            }
        };

        // Initial fetch
        fetchGameState();

        // Poll frequently
        const interval = setInterval(fetchGameState, POLL_INTERVAL);
        return () => clearInterval(interval);
    }, []);

    const startNewGame = async (mode: 'human_vs_bot' | 'bot_vs_bot') => {
        try {
            console.log('Starting new game in mode:', mode);
            const res = await fetch(`${API_URL}/new_game?mode=${mode}`, { method: 'POST' });
            if (!res.ok) throw new Error('Failed to start new game');
            console.log('New game started successfully');
            // Fetch game state immediately after starting new game
            const gameRes = await fetch(`${API_URL}/game`);
            if (!gameRes.ok) throw new Error('Failed to fetch new game state');
            const data = await gameRes.json();
            console.log('New game state:', JSON.stringify(data, null, 2));
            setGameState(data);
            setError(null);
        } catch (err) {
            console.error('Error starting new game:', err);
            setError(err instanceof Error ? err.message : 'Unknown error');
            toast({
                title: "Failed to start new game",
                status: "error",
                duration: 3000,
                isClosable: true,
            });
        }
    };

    console.log('Rendering App, gameState:', JSON.stringify(gameState, null, 2), 'isHealthy:', isHealthy);

    return (
        <ChakraProvider theme={theme}>
            <Container>
                <VStack spacing={4} align="center" justify="center" minH="100vh">
                    <HStack spacing={4}>
                        <Button 
                            onClick={() => startNewGame('human_vs_bot')}
                            colorScheme={isHealthy ? "blue" : "gray"}
                            isDisabled={!isHealthy}
                            size="lg"
                        >
                            Play vs Bot
                        </Button>
                        <Button 
                            onClick={() => startNewGame('bot_vs_bot')}
                            colorScheme={isHealthy ? "green" : "gray"}
                            isDisabled={!isHealthy}
                            size="lg"
                        >
                            Watch Bots Play
                        </Button>
                    </HStack>
                    {error && (
                        <Text color="red.500" fontSize="lg">
                            Error: {error}
                        </Text>
                    )}
                    {gameState ? (
                        <GameViewer game={gameState} />
                    ) : (
                        <Text fontSize="lg">Loading game state...</Text>
                    )}
                </VStack>
            </Container>
        </ChakraProvider>
    );
}

export default App; 