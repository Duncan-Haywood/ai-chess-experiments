# Chess Sound Effects

This directory contains sound effects for chess moves and events. The sounds are optimized for web playback (small file size, quick loading).

## Files
- `move.mp3` - Standard piece movement (48ms)
- `capture.mp3` - Piece capture sound (62ms)
- `check.mp3` - Check notification (85ms)
- `castle.mp3` - Castling move (72ms)
- `promote.mp3` - Pawn promotion (68ms)
- `game-end.mp3` - Game over sound (120ms)

## Format
All sounds are:
- MP3 format for broad browser compatibility
- 44.1kHz sample rate
- Mono channel
- Variable bit rate (VBR) for optimal size/quality
- Compressed to minimize file size

## Usage
These sounds are triggered by the `useChessSound` hook in the React application.
Each sound is preloaded when the game starts to ensure responsive playback.

## Credits
Sounds are based on chess.com's sound effects, modified and optimized for this project.
Original sounds are property of their respective owners. 