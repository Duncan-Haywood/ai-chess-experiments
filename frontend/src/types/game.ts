export type GameMode = 'human_vs_bot' | 'bot_vs_bot';
export type GameStatus = 'active' | 'finished';
export type EngineType = 'minimax' | 'stockfish' | 'leela' | 'mcts';

export interface GameState {
    fen: string;
    lastMove: string | null;
    whiteTime: number;
    blackTime: number;
    whiteName: string;
    blackName: string;
    status: GameStatus;
    result?: '1-0' | '0-1' | '1/2-1/2';
    resultReason?: string;
    moveCount: number;
    gameMode: GameMode;
    whiteDepth?: number;
    blackDepth?: number;
    whiteEngine: EngineType;
    blackEngine: EngineType;
    avgMoveTime?: number;
    turn: boolean;  // true for white, false for black
}

export interface GameStats {
    rating: {
        bullet: number;
        blitz: number;
        rapid: number;
    };
    totalGames: number;
    username: string;
}

export interface EngineMetrics {
    nodes_searched: number;
    depth_reached: number;
    time_taken: number;
    memory_used: number;
    cpu_percent: number;
}

export interface EngineInfo {
    type: 'depth' | 'elo' | 'time';
    min: number;
    max: number;
    default: number;
    description: string;
    step?: number;
}

export interface EngineConfig {
    name: string;
    description: string;
    info: EngineInfo;
    supported_features: string[];
} 