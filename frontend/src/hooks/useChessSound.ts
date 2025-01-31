import { useEffect, useCallback, useRef } from 'react';
import { Move } from 'chess.js';

interface ChessSounds {
  move: HTMLAudioElement;
  capture: HTMLAudioElement;
  check: HTMLAudioElement;
  castle: HTMLAudioElement;
  gameEnd: HTMLAudioElement;
}

export const useChessSound = (enabled: boolean = true) => {
  const sounds = useRef<ChessSounds>({
    move: new Audio('/sounds/move.mp3'),
    capture: new Audio('/sounds/capture.mp3'),
    check: new Audio('/sounds/check.mp3'),
    castle: new Audio('/sounds/castle.mp3'),
    gameEnd: new Audio('/sounds/game-end.mp3'),
  });

  useEffect(() => {
    // Preload sounds
    Object.values(sounds.current).forEach(audio => {
      audio.load();
    });

    return () => {
      // Cleanup
      Object.values(sounds.current).forEach(audio => {
        audio.pause();
        audio.currentTime = 0;
      });
    };
  }, []);

  const playMoveSound = useCallback((
    move: Move,
    isCheck: boolean,
    isGameOver: boolean
  ) => {
    if (!enabled) return;

    const sound = sounds.current;

    if (isGameOver) {
      sound.gameEnd.play();
    } else if (isCheck) {
      sound.check.play();
    } else if (move.captured) {
      sound.capture.play();
    } else if (move.flags.includes('k') || move.flags.includes('q')) {
      sound.castle.play();
    } else {
      sound.move.play();
    }
  }, [enabled]);

  return { playMoveSound };
}; 