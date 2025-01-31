import React from 'react';
import {
  Box,
  Text,
  Heading,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  useColorModeValue,
} from '@chakra-ui/react';

interface EngineLevel {
  type: string;
  min: number;
  max: number;
  default: number;
  description: string;
  step?: number;
  validLevels?: number[];
}

interface EngineDescription {
  name: string;
  description: string;
  algorithm: string;
  strengths: string[];
  weaknesses: string[];
  complexity: string;
  history?: string;
  levels: EngineLevel;
}

const engineDescriptions: EngineDescription[] = [
  {
    name: 'Stockfish NNUE',
    description: 'A hybrid chess engine combining traditional alpha-beta search with a neural network for position evaluation.',
    algorithm: `Stockfish NNUE (Efficiently Updatable Neural Network) uses a sophisticated combination of techniques:
    
1. Alpha-Beta Search: A depth-first tree search algorithm that prunes branches that can't affect the final decision
2. Neural Network Evaluation: NNUE uses a specialized neural network architecture that can be efficiently updated incrementally as moves are made
3. Advanced Pruning: Null move pruning, late move reduction, and futility pruning to focus on promising variations
4. Sophisticated Move Ordering: Uses history heuristics, killer moves, and countermove heuristics to search better moves first`,
    strengths: [
      'Extremely strong positional and tactical play',
      'Efficient evaluation of positions',
      'Strong endgame play with tablebase support',
      'Balanced strategic understanding'
    ],
    weaknesses: [
      'High computational requirements',
      'Complex configuration needed for optimal performance'
    ],
    complexity: 'Very High',
    history: 'NNUE was first introduced by Yu Nasu for Shogi engines and was later adapted for chess by the Stockfish team.',
    levels: {
      type: 'depth',
      min: 1,
      max: 30,
      default: 20,
      step: 1,
      description: `Search depth in plies (half-moves). Higher values mean stronger but slower play:
      - 1-5: Very fast but weak play
      - 6-15: Good for casual games
      - 16-20: Strong play, good for serious games
      - 21-30: Very strong but slow analysis`
    }
  },
  {
    name: 'Maia',
    description: 'A neural network chess engine trained to play like humans at specific rating levels.',
    algorithm: `Maia uses a deep learning approach based on the Leela Chess Zero architecture:

1. Neural Network Architecture: Uses a deep residual network trained on millions of human games
2. Policy Network: Predicts probability distribution over moves that a human would play
3. Value Network: Evaluates positions based on human play patterns
4. Rating-Targeted Training: Separate models trained on games from specific rating bands (e.g., 1100, 1500, 1900)`,
    strengths: [
      'Human-like play style',
      'Consistent strength at specific rating levels',
      'Makes instructive mistakes similar to humans',
      'Good for training and learning'
    ],
    weaknesses: [
      'Not optimized for maximum playing strength',
      'Can make human-like blunders',
      'Limited to learned patterns'
    ],
    complexity: 'High',
    history: 'Developed by researchers at the University of Toronto, Cornell University, and Microsoft Research.',
    levels: {
      type: 'elo',
      min: 1100,
      max: 1900,
      default: 1500,
      validLevels: [1100, 1500, 1900],
      description: `ELO rating level that the engine plays at:
      - 1100: Plays like a beginner/novice player
      - 1500: Plays like an intermediate club player
      - 1900: Plays like a strong club player
      Each level represents a separate neural network model trained on games from players at that rating.`
    }
  },
  {
    name: 'Classical Engines',
    description: 'Traditional chess engines using hand-crafted evaluation functions and tree search.',
    algorithm: `Classical chess engines use several fundamental algorithms:

1. Minimax Search: A recursive algorithm that simulates both players making optimal moves
2. Alpha-Beta Pruning: An optimization that eliminates branches that won't affect the final decision
3. Position Evaluation: Uses material count, piece position, pawn structure, king safety, and other chess principles
4. Move Ordering: Examines promising moves first to improve pruning efficiency`,
    strengths: [
      'Transparent and understandable logic',
      'Consistent tactical strength',
      'Lower computational requirements',
      'Easy to modify and tune'
    ],
    weaknesses: [
      'Less sophisticated positional understanding',
      'Can be trapped in technical positions',
      'May miss subtle strategic concepts'
    ],
    complexity: 'Medium',
    history: 'The foundation of computer chess, dating back to Claude Shannon\'s seminal 1950 paper.',
    levels: {
      type: 'depth',
      min: 1,
      max: 20,
      default: 10,
      step: 1,
      description: `Search depth in plies (half-moves). Higher values mean stronger but slower play:
      - 1-3: Very fast tactical analysis
      - 4-8: Good for quick games
      - 9-12: Balanced strength/speed
      - 13-20: Deep tactical analysis
      Classical engines are typically faster than neural network based ones at the same depth.`
    }
  }
];

export const EngineInfo: React.FC = () => {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  return (
    <Box p={4}>
      <Heading size="lg" mb={4}>Chess Engine Algorithms</Heading>
      <Text mb={4}>
        Learn about the different algorithms and techniques used by our chess engines.
        Each engine represents a different approach to computer chess.
      </Text>
      
      <Accordion allowMultiple>
        {engineDescriptions.map((engine) => (
          <AccordionItem 
            key={engine.name}
            border="1px"
            borderColor={borderColor}
            borderRadius="md"
            mb={2}
          >
            <AccordionButton>
              <Box flex="1" textAlign="left">
                <Heading size="md">{engine.name}</Heading>
              </Box>
              <AccordionIcon />
            </AccordionButton>
            <AccordionPanel pb={4} bg={bgColor}>
              <Text fontWeight="bold" mb={2}>{engine.description}</Text>
              
              <Heading size="sm" mt={4} mb={2}>How it Works</Heading>
              <Text whiteSpace="pre-line">{engine.algorithm}</Text>
              
              {engine.levels && (
                <>
                  <Heading size="sm" mt={4} mb={2}>Strength Levels</Heading>
                  <Box mb={2}>
                    <Text fontWeight="bold" display="inline">Type: </Text>
                    <Text display="inline" textTransform="capitalize">{engine.levels.type}</Text>
                  </Box>
                  <Box mb={2}>
                    <Text fontWeight="bold" display="inline">Range: </Text>
                    <Text display="inline">
                      {engine.levels.validLevels 
                        ? engine.levels.validLevels.join(', ')
                        : `${engine.levels.min} to ${engine.levels.max}`}
                    </Text>
                  </Box>
                  <Text whiteSpace="pre-line">{engine.levels.description}</Text>
                </>
              )}
              
              <Heading size="sm" mt={4} mb={2}>Strengths</Heading>
              <ul>
                {engine.strengths.map((strength, idx) => (
                  <li key={idx}><Text>{strength}</Text></li>
                ))}
              </ul>
              
              <Heading size="sm" mt={4} mb={2}>Weaknesses</Heading>
              <ul>
                {engine.weaknesses.map((weakness, idx) => (
                  <li key={idx}><Text>{weakness}</Text></li>
                ))}
              </ul>
              
              <Box mt={4}>
                <Text fontWeight="bold" display="inline">Complexity: </Text>
                <Text display="inline">{engine.complexity}</Text>
              </Box>
              
              {engine.history && (
                <Box mt={4}>
                  <Text fontWeight="bold" mb={1}>Historical Note</Text>
                  <Text>{engine.history}</Text>
                </Box>
              )}
            </AccordionPanel>
          </AccordionItem>
        ))}
      </Accordion>
    </Box>
  );
}; 