import { create } from "zustand";
import { PieceType } from "@/lib/data/pieces";
import { isTileOutOfBounds, getBoardBoundaries } from "@/lib/utils/boardUtils";
import { useGameStore } from "./useGameStore";

// Type definitions
export interface Piece {
  type: PieceType;
  player: "player" | "opponent";
  hasMoved?: boolean;
  health: number;
  maxHealth: number;
}

export interface Tile {
  piece: Piece | null;
}

export interface SelectedTile {
  x: number;
  y: number;
}

export interface MoveResult {
  success: boolean;
  message?: string;
  capturedPiece?: Piece | null;
}

export interface WinConditionResult {
  gameOver: boolean;
  winner: "player" | "opponent" | null;
}

interface BoardState {
  board: Tile[][];
  shrinkLevel: number;
  selectedTile: SelectedTile | null;
  
  // Actions
  initializeBoard: () => void;
  resetBoard: () => void;
  selectTile: (x: number, y: number) => void;
  clearSelection: () => void;
  movePiece: (fromX: number, fromY: number, toX: number, toY: number, currentPlayer: "player" | "opponent") => MoveResult;
  shrinkBoard: () => void;
  damageOutOfBoundsPieces: () => void;
  damagePiece: (x: number, y: number, amount: number) => void;
  healPiece: (x: number, y: number, amount: number) => void;
  checkWinCondition: () => WinConditionResult;
}

// Initial piece health values
const PIECE_HEALTH: Record<PieceType, number> = {
  lion: 20,
  eagle: 12,
  wolf: 15,
  bear: 25,
  snake: 10,
  fox: 8
};

export const useBoardStore = create<BoardState>((set, get) => ({
  // Initial empty board
  board: Array(8).fill(null).map(() => Array(8).fill(null).map(() => ({ piece: null }))),
  shrinkLevel: 0,
  selectedTile: null,
  
  // Actions
  initializeBoard: () => {
    // Create a new 8x8 board
    const newBoard: Tile[][] = Array(8)
      .fill(null)
      .map(() => Array(8).fill(null).map(() => ({ piece: null })));
    
    // Set up player pieces (bottom of board)
    newBoard[7][0].piece = { type: "wolf", player: "player", health: PIECE_HEALTH.wolf, maxHealth: PIECE_HEALTH.wolf };
    newBoard[7][1].piece = { type: "snake", player: "player", health: PIECE_HEALTH.snake, maxHealth: PIECE_HEALTH.snake };
    newBoard[7][2].piece = { type: "bear", player: "player", health: PIECE_HEALTH.bear, maxHealth: PIECE_HEALTH.bear };
    newBoard[7][3].piece = { type: "lion", player: "player", health: PIECE_HEALTH.lion, maxHealth: PIECE_HEALTH.lion };
    newBoard[7][4].piece = { type: "fox", player: "player", health: PIECE_HEALTH.fox, maxHealth: PIECE_HEALTH.fox };
    newBoard[7][5].piece = { type: "bear", player: "player", health: PIECE_HEALTH.bear, maxHealth: PIECE_HEALTH.bear };
    newBoard[7][6].piece = { type: "snake", player: "player", health: PIECE_HEALTH.snake, maxHealth: PIECE_HEALTH.snake };
    newBoard[7][7].piece = { type: "wolf", player: "player", health: PIECE_HEALTH.wolf, maxHealth: PIECE_HEALTH.wolf };
    
    newBoard[6][0].piece = { type: "fox", player: "player", health: PIECE_HEALTH.fox, maxHealth: PIECE_HEALTH.fox };
    newBoard[6][1].piece = { type: "fox", player: "player", health: PIECE_HEALTH.fox, maxHealth: PIECE_HEALTH.fox };
    newBoard[6][2].piece = { type: "fox", player: "player", health: PIECE_HEALTH.fox, maxHealth: PIECE_HEALTH.fox };
    newBoard[6][3].piece = { type: "eagle", player: "player", health: PIECE_HEALTH.eagle, maxHealth: PIECE_HEALTH.eagle };
    newBoard[6][4].piece = { type: "eagle", player: "player", health: PIECE_HEALTH.eagle, maxHealth: PIECE_HEALTH.eagle };
    newBoard[6][5].piece = { type: "fox", player: "player", health: PIECE_HEALTH.fox, maxHealth: PIECE_HEALTH.fox };
    newBoard[6][6].piece = { type: "fox", player: "player", health: PIECE_HEALTH.fox, maxHealth: PIECE_HEALTH.fox };
    newBoard[6][7].piece = { type: "fox", player: "player", health: PIECE_HEALTH.fox, maxHealth: PIECE_HEALTH.fox };
    
    // Set up opponent pieces (top of board)
    newBoard[0][0].piece = { type: "wolf", player: "opponent", health: PIECE_HEALTH.wolf, maxHealth: PIECE_HEALTH.wolf };
    newBoard[0][1].piece = { type: "snake", player: "opponent", health: PIECE_HEALTH.snake, maxHealth: PIECE_HEALTH.snake };
    newBoard[0][2].piece = { type: "bear", player: "opponent", health: PIECE_HEALTH.bear, maxHealth: PIECE_HEALTH.bear };
    newBoard[0][3].piece = { type: "fox", player: "opponent", health: PIECE_HEALTH.fox, maxHealth: PIECE_HEALTH.fox };
    newBoard[0][4].piece = { type: "lion", player: "opponent", health: PIECE_HEALTH.lion, maxHealth: PIECE_HEALTH.lion };
    newBoard[0][5].piece = { type: "bear", player: "opponent", health: PIECE_HEALTH.bear, maxHealth: PIECE_HEALTH.bear };
    newBoard[0][6].piece = { type: "snake", player: "opponent", health: PIECE_HEALTH.snake, maxHealth: PIECE_HEALTH.snake };
    newBoard[0][7].piece = { type: "wolf", player: "opponent", health: PIECE_HEALTH.wolf, maxHealth: PIECE_HEALTH.wolf };
    
    newBoard[1][0].piece = { type: "fox", player: "opponent", health: PIECE_HEALTH.fox, maxHealth: PIECE_HEALTH.fox };
    newBoard[1][1].piece = { type: "fox", player: "opponent", health: PIECE_HEALTH.fox, maxHealth: PIECE_HEALTH.fox };
    newBoard[1][2].piece = { type: "fox", player: "opponent", health: PIECE_HEALTH.fox, maxHealth: PIECE_HEALTH.fox };
    newBoard[1][3].piece = { type: "eagle", player: "opponent", health: PIECE_HEALTH.eagle, maxHealth: PIECE_HEALTH.eagle };
    newBoard[1][4].piece = { type: "eagle", player: "opponent", health: PIECE_HEALTH.eagle, maxHealth: PIECE_HEALTH.eagle };
    newBoard[1][5].piece = { type: "fox", player: "opponent", health: PIECE_HEALTH.fox, maxHealth: PIECE_HEALTH.fox };
    newBoard[1][6].piece = { type: "fox", player: "opponent", health: PIECE_HEALTH.fox, maxHealth: PIECE_HEALTH.fox };
    newBoard[1][7].piece = { type: "fox", player: "opponent", health: PIECE_HEALTH.fox, maxHealth: PIECE_HEALTH.fox };
    
    set({ 
      board: newBoard,
      shrinkLevel: 0,
      selectedTile: null 
    });
  },
  
  resetBoard: () => {
    set({
      shrinkLevel: 0,
      selectedTile: null
    });
    get().initializeBoard();
  },
  
  selectTile: (x, y) => {
    set({ selectedTile: { x, y } });
  },
  
  clearSelection: () => {
    set({ selectedTile: null });
  },
  
  movePiece: (fromX, fromY, toX, toY, currentPlayer) => {
    const { board, shrinkLevel } = get();
    
    // Check if coordinates are valid
    if (
      fromX < 0 || fromX >= 8 || fromY < 0 || fromY >= 8 ||
      toX < 0 || toX >= 8 || toY < 0 || toY >= 8
    ) {
      return { success: false, message: "Invalid coordinates" };
    }
    
    // Check if destination is outside playable area
    if (isTileOutOfBounds(toX, toY, shrinkLevel)) {
      return { success: false, message: "Destination is outside the playable area" };
    }
    
    const sourceTile = board[fromY][fromX];
    const targetTile = board[toY][toX];
    
    // Check if source has a piece and it belongs to the current player
    if (!sourceTile.piece || sourceTile.piece.player !== currentPlayer) {
      return { success: false, message: "No valid piece to move" };
    }
    
    // Check if the target is occupied by the same player's piece
    if (targetTile.piece && targetTile.piece.player === currentPlayer) {
      return { success: false, message: "Cannot move to a space occupied by your own piece" };
    }
    
    // Check movement validity based on piece type
    const piece = sourceTile.piece;
    const isValidMove = isValidMoveForPiece(piece.type, fromX, fromY, toX, toY, board);
    
    if (!isValidMove) {
      return { success: false, message: "Invalid move for this piece type" };
    }
    
    // Save the captured piece (if any) for return value
    const capturedPiece = targetTile.piece;
    
    // Create a new board with the piece moved
    const newBoard = [...board];
    newBoard[toY][toX] = { piece: { ...piece, hasMoved: true } };
    newBoard[fromY][fromX] = { piece: null };
    
    // Check if it was the lion that was captured and set winner accordingly
    if (capturedPiece && capturedPiece.type === "lion") {
      // Use timeout to let the board update first
      setTimeout(() => {
        useGameStore.getState().setWinner(currentPlayer);
      }, 500);
    }
    
    set({ board: newBoard });
    
    return { 
      success: true, 
      capturedPiece
    };
  },
  
  shrinkBoard: () => {
    const { shrinkLevel } = get();
    
    // Max shrink level is 4 (daha yavaş daralma için)
    if (shrinkLevel < 4) {
      set({ shrinkLevel: shrinkLevel + 1 });
    }
  },
  
  damageOutOfBoundsPieces: () => {
    const { board, shrinkLevel } = get();
    
    // If board hasn't shrunk yet, no damage to apply
    if (shrinkLevel === 0) return;
    
    const boundaries = getBoardBoundaries(shrinkLevel);
    
    // Check each tile on the board
    for (let y = 0; y < 8; y++) {
      for (let x = 0; x < 8; x++) {
        // If the tile is outside boundaries and has a piece, damage it
        if (isTileOutOfBounds(x, y, shrinkLevel) && board[y][x].piece) {
          get().damagePiece(x, y, 5); // Apply 5 damage per turn outside boundaries
        }
      }
    }
  },
  
  damagePiece: (x, y, amount) => {
    const { board } = get();
    const piece = board[y][x].piece;
    
    if (!piece) return;
    
    // Create a new board to update the piece's health
    const newBoard = [...board];
    const newHealth = Math.max(0, piece.health - amount);
    
    newBoard[y][x] = {
      piece: {
        ...piece,
        health: newHealth
      }
    };
    
    // If the piece is dead, remove it
    if (newHealth <= 0) {
      newBoard[y][x] = { piece: null };
      
      // If it was a lion, set the winner
      if (piece.type === "lion") {
        setTimeout(() => {
          useGameStore.getState().setWinner(piece.player === "player" ? "opponent" : "player");
        }, 500);
      }
    }
    
    set({ board: newBoard });
  },
  
  healPiece: (x, y, amount) => {
    const { board } = get();
    const piece = board[y][x].piece;
    
    if (!piece) return;
    
    // Create a new board to update the piece's health
    const newBoard = [...board];
    const newHealth = Math.min(piece.maxHealth, piece.health + amount);
    
    newBoard[y][x] = {
      piece: {
        ...piece,
        health: newHealth
      }
    };
    
    set({ board: newBoard });
  },
  
  checkWinCondition: () => {
    const { board } = get();
    
    let hasPlayerLion = false;
    let hasOpponentLion = false;
    
    // Check if lions still exist
    for (let y = 0; y < 8; y++) {
      for (let x = 0; x < 8; x++) {
        const piece = board[y][x].piece;
        if (piece && piece.type === "lion") {
          if (piece.player === "player") {
            hasPlayerLion = true;
          } else {
            hasOpponentLion = true;
          }
        }
      }
    }
    
    // If a player lost their lion, the other player wins
    if (!hasPlayerLion) {
      return {
        gameOver: true,
        winner: "opponent"
      };
    }
    
    if (!hasOpponentLion) {
      return {
        gameOver: true,
        winner: "player"
      };
    }
    
    // Game continues
    return {
      gameOver: false,
      winner: null
    };
  }
}));

// Helper function to check if a move is valid for the given piece type
function isValidMoveForPiece(
  pieceType: PieceType,
  fromX: number,
  fromY: number,
  toX: number,
  toY: number,
  board: Tile[][]
): boolean {
  // Calculate movement deltas
  const dx = toX - fromX;
  const dy = toY - fromY;
  const absDx = Math.abs(dx);
  const absDy = Math.abs(dy);
  
  switch (pieceType) {
    case "lion":
      // Lion moves one square in any direction (like a king)
      return absDx <= 1 && absDy <= 1 && (absDx > 0 || absDy > 0);
      
    case "eagle":
      // Eagle moves diagonally any number of squares (like a bishop)
      if (absDx !== absDy || absDx === 0) return false;
      
      // Check for pieces in the path
      const dirX = dx > 0 ? 1 : -1;
      const dirY = dy > 0 ? 1 : -1;
      
      for (let i = 1; i < absDx; i++) {
        const checkX = fromX + (dirX * i);
        const checkY = fromY + (dirY * i);
        
        if (board[checkY][checkX].piece) return false;
      }
      
      return true;
      
    case "wolf":
      // Wolf moves horizontally or vertically any number of squares (like a rook)
      if ((absDx > 0 && absDy > 0) || (absDx === 0 && absDy === 0)) return false;
      
      // Check for pieces in the path
      const horizontal = absDx > 0;
      const dir = horizontal ? (dx > 0 ? 1 : -1) : (dy > 0 ? 1 : -1);
      const distance = horizontal ? absDx : absDy;
      
      for (let i = 1; i < distance; i++) {
        const checkX = fromX + (horizontal ? dir * i : 0);
        const checkY = fromY + (horizontal ? 0 : dir * i);
        
        if (board[checkY][checkX].piece) return false;
      }
      
      return true;
      
    case "bear":
      // Bear moves one square in any direction (like a king)
      return absDx <= 1 && absDy <= 1 && (absDx > 0 || absDy > 0);
      
    case "snake":
      // Snake moves in an L-shape (like a knight)
      return (absDx === 1 && absDy === 2) || (absDx === 2 && absDy === 1);
      
    case "fox":
      // Fox can move up to three squares in any direction (horizontally, vertically, or diagonally)
      // Check total movement is not more than 3 squares
      const totalMovement = Math.max(absDx, absDy);
      if (totalMovement > 3) return false;
      
      // For diagonal movement, dx and dy should be equal
      if (absDx > 0 && absDy > 0 && absDx !== absDy) return false;
      
      // Check for pieces in the path
      if (absDx === absDy) {
        // Diagonal
        const dirX = dx > 0 ? 1 : -1;
        const dirY = dy > 0 ? 1 : -1;
        
        for (let i = 1; i < absDx; i++) {
          const checkX = fromX + (dirX * i);
          const checkY = fromY + (dirY * i);
          
          if (board[checkY][checkX].piece) return false;
        }
      } else if (absDx === 0) {
        // Vertical
        const dirY = dy > 0 ? 1 : -1;
        
        for (let i = 1; i < absDy; i++) {
          const checkY = fromY + (dirY * i);
          
          if (board[checkY][fromX].piece) return false;
        }
      } else if (absDy === 0) {
        // Horizontal
        const dirX = dx > 0 ? 1 : -1;
        
        for (let i = 1; i < absDx; i++) {
          const checkX = fromX + (dirX * i);
          
          if (board[fromY][checkX].piece) return false;
        }
      }
      
      return true;
      
    default:
      return false;
  }
}
