export interface BotAlgorithm {
    id: string;
    name: string;
    description: string;
    characteristics: string[];
    difficultyLevel: 'Beginner' | 'Intermediate' | 'Advanced';
    recommendedDepth: {
        min: number;
        max: number;
        default: number;
    };
}

export const AVAILABLE_BOTS: BotAlgorithm[] = [
    {
        id: 'minimax',
        name: 'Minimax Bot',
        description: 'A chess engine using minimax search with alpha-beta pruning and sophisticated evaluation features.',
        characteristics: [
            'Material counting with piece-square tables',
            'Mobility evaluation',
            'King safety analysis',
            'Pawn structure evaluation',
            'Center control',
            'Development bonuses'
        ],
        difficultyLevel: 'Intermediate',
        recommendedDepth: {
            min: 2,
            max: 5,
            default: 3
        }
    },
    {
        id: 'leela',
        name: 'Leela Chess Zero',
        description: 'A neural network based chess engine using deep learning techniques.',
        characteristics: [
            'Neural network evaluation',
            'Monte Carlo Tree Search',
            'Pattern recognition',
            'Positional understanding',
            'Strategic planning',
            'Endgame knowledge'
        ],
        difficultyLevel: 'Advanced',
        recommendedDepth: {
            min: 1,
            max: 40,
            default: 20
        }
    }
]; 