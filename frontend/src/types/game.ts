export interface GameState {
    fen: string;
    lastMove?: string;
    whiteTime: number;
    blackTime: number;
    whiteName: string;
    blackName: string;
    status: 'active' | 'finished';
    result?: string;
    moveCount: number;
    gameMode: 'human_vs_bot' | 'bot_vs_bot';
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

export type GameMode = 'human_vs_bot' | 'bot_vs_bot'; 