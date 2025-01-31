import React from 'react';
import { Grid, GridItem, useBreakpointValue } from '@chakra-ui/react';
import { GameViewer } from './GameViewer';
import { GameState } from '../types/game';

interface MultiGameViewerProps {
  games: GameState[];
  onReconnect?: (gameId: string) => void;
}

export const MultiGameViewer: React.FC<MultiGameViewerProps> = ({ games, onReconnect }) => {
  const columns = useBreakpointValue({ base: 1, lg: 2 });
  
  return (
    <Grid
      templateColumns={`repeat(${columns}, 1fr)`}
      gap={4}
      w="100%"
      maxW="1400px"
      mx="auto"
      px={4}
    >
      {games.map((game) => (
        <GridItem key={game.id}>
          <GameViewer
            game={game}
            onReconnect={() => onReconnect?.(game.id)}
            soundEnabled={false}
          />
        </GridItem>
      ))}
    </Grid>
  );
}; 