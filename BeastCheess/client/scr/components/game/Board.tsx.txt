import { useEffect, useState } from "react";
import { useBoardStore } from "@/lib/stores/useBoardStore";
import { useGameStore } from "@/lib/stores/useGameStore";
import Tile from "./Tile";
import Piece from "./Piece";
import ShrinkingArea from "./ShrinkingArea";
import { useAudio } from "@/lib/stores/useAudio";
import { runAI } from "@/lib/ai/basicAI";
import { getValidMovesForPiece } from "@/lib/utils/gameLogic";

const Board = () => {
  const { board, shrinkLevel, initializeBoard, selectedTile, selectTile, clearSelection, movePiece } = useBoardStore();
  const { phase, currentTurn, nextTurn, isPlayerTurn } = useGameStore();
  const { playHit } = useAudio();
  
  // State to store valid moves for the selected piece
  const [validMoves, setValidMoves] = useState<{x: number, y: number}[]>([]);

  // Initialize the board on first render
  useEffect(() => {
    initializeBoard();
  }, [initializeBoard]);

  // Run AI on opponent's turn
  useEffect(() => {
    // Only run AI when it's not player's turn and game is in progress
    if (!isPlayerTurn() && phase === "playing") {
      const aiTimeout = setTimeout(() => {
        runAI();
      }, 1000); // Delay AI move for a more natural feel
      
      return () => clearTimeout(aiTimeout);
    }
  }, [currentTurn, phase, isPlayerTurn]);
  
  // Update valid moves when a piece is selected
  useEffect(() => {
    if (selectedTile) {
      const { x, y } = selectedTile;
      const selectedPiece = board[y][x].piece;
      
      if (selectedPiece) {
        // Get all valid moves for the selected piece
        const moves = getValidMovesForPiece(
          selectedPiece.type,
          x,
          y,
          board,
          selectedPiece.player
        );
        setValidMoves(moves);
      }
    } else {
      // Clear valid moves when no piece is selected
      setValidMoves([]);
    }
  }, [selectedTile, board]);

  const handleTileClick = (x: number, y: number) => {
    // Only allow interaction when it's player's turn
    if (!isPlayerTurn() || phase !== "playing") return;
    
    const tile = board[y][x];
    
    // If no tile is selected and the clicked tile has a piece of the current player's color
    if (!selectedTile && tile.piece && tile.piece.player === currentTurn) {
      selectTile(x, y);
    } 
    // If a tile with a piece is already selected
    else if (selectedTile) {
      // If clicking on the same tile, deselect it
      if (selectedTile.x === x && selectedTile.y === y) {
        clearSelection();
      } 
      // If clicking on a different tile, try to move the piece
      else {
        const sourceX = selectedTile.x;
        const sourceY = selectedTile.y;
        const targetX = x;
        const targetY = y;
        
        // Check if move is valid and perform it
        const moveResult = movePiece(sourceX, sourceY, targetX, targetY, currentTurn);
        
        if (moveResult.success) {
          playHit(); // Play sound for successful move
          clearSelection();
          
          // After a successful move, check game conditions and then proceed to next turn
          setTimeout(() => {
            nextTurn();
          }, 500);
        } else {
          // Invalid move - just clear selection
          clearSelection();
        }
      }
    }
  };

  return (
    <div className="relative">
      <div 
        className="grid grid-cols-8 gap-0 border-4 border-amber-800"
        style={{
          width: 'min(80vh, 95vw)',
          height: 'min(80vh, 95vw)',
        }}
      >
        {board.map((row, y) => 
          row.map((tile, x) => (
            <Tile
              key={`${x}-${y}`}
              x={x}
              y={y}
              color={(x + y) % 2 === 0 ? 'light' : 'dark'}
              shrinkLevel={shrinkLevel}
              isSelected={selectedTile?.x === x && selectedTile?.y === y}
              isValidMove={validMoves.some(move => move.x === x && move.y === y)}
              onClick={() => handleTileClick(x, y)}
            >
              {tile.piece && (
                <Piece 
                  piece={tile.piece} 
                  isSelected={selectedTile?.x === x && selectedTile?.y === y}
                />
              )}
            </Tile>
          ))
        )}
      </div>
      
      <ShrinkingArea />
    </div>
  );
};

export default Board;
