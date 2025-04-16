import { create } from "zustand";
import { useCardStore } from "./useCardStore";
import { useBoardStore } from "./useBoardStore";

export type GamePhase = "menu" | "playing" | "gameOver";
export type PlayerType = "player" | "opponent";

interface GameState {
  phase: GamePhase;
  currentTurn: PlayerType;
  turnNumber: number;
  playerEnergy: number;
  opponentEnergy: number;
  winner: PlayerType | null;
}

interface GameActions {
  startGame: () => void;
  resetGame: () => void;
  nextTurn: () => void;
  setWinner: (winner: PlayerType) => void;
  useEnergy: (amount: number, player: PlayerType) => boolean;
  addEnergy: (amount: number, player: PlayerType) => void;
  isPlayerTurn: () => boolean;
}

const MAX_ENERGY = 10;
const BASE_ENERGY_PER_TURN = 3;

export const useGameStore = create<GameState & GameActions>((set, get) => ({
  // Initial state
  phase: "menu",
  currentTurn: "player",
  turnNumber: 1,
  playerEnergy: MAX_ENERGY,
  opponentEnergy: MAX_ENERGY,
  winner: null,
  
  // Actions
  startGame: () => {
    set({
      phase: "playing",
      currentTurn: "player",
      turnNumber: 1,
      playerEnergy: MAX_ENERGY,
      opponentEnergy: MAX_ENERGY,
      winner: null
    });
    
    // Reset other stores
    useCardStore.getState().resetCards();
    useBoardStore.getState().resetBoard();
  },
  
  resetGame: () => {
    set({
      phase: "menu",
      currentTurn: "player",
      turnNumber: 1,
      playerEnergy: MAX_ENERGY,
      opponentEnergy: MAX_ENERGY,
      winner: null
    });
  },
  
  nextTurn: () => {
    const currentState = get();
    
    // If game is over, don't change turns
    if (currentState.phase === "gameOver") return;
    
    const nextTurn = currentState.currentTurn === "player" ? "opponent" : "player";
    const newTurnNumber = nextTurn === "player" ? currentState.turnNumber + 1 : currentState.turnNumber;
    
    // Add energy for the new player's turn
    const newPlayerEnergy = nextTurn === "player" 
      ? Math.min(currentState.playerEnergy + BASE_ENERGY_PER_TURN, MAX_ENERGY)
      : currentState.playerEnergy;
      
    const newOpponentEnergy = nextTurn === "opponent"
      ? Math.min(currentState.opponentEnergy + BASE_ENERGY_PER_TURN, MAX_ENERGY) 
      : currentState.opponentEnergy;
    
    set({
      currentTurn: nextTurn,
      turnNumber: newTurnNumber,
      playerEnergy: newPlayerEnergy,
      opponentEnergy: newOpponentEnergy
    });
    
    // Check if we need to shrink the board
    if (newTurnNumber > 1 && newTurnNumber % 5 === 0) {
      useBoardStore.getState().shrinkBoard();
    }
    
    // Apply damage to pieces outside the play area
    useBoardStore.getState().damageOutOfBoundsPieces();
    
    // Check for win conditions after applying damages
    const checkResult = useBoardStore.getState().checkWinCondition();
    if (checkResult.gameOver) {
      set({
        phase: "gameOver",
        winner: checkResult.winner
      });
    }
  },
  
  setWinner: (winner) => {
    set({
      phase: "gameOver",
      winner
    });
  },
  
  useEnergy: (amount, player) => {
    const { playerEnergy, opponentEnergy } = get();
    
    if (player === "player" && playerEnergy >= amount) {
      set({ playerEnergy: playerEnergy - amount });
      return true;
    } else if (player === "opponent" && opponentEnergy >= amount) {
      set({ opponentEnergy: opponentEnergy - amount });
      return true;
    }
    
    return false;
  },
  
  addEnergy: (amount, player) => {
    const { playerEnergy, opponentEnergy } = get();
    
    if (player === "player") {
      set({ playerEnergy: Math.min(playerEnergy + amount, MAX_ENERGY) });
    } else {
      set({ opponentEnergy: Math.min(opponentEnergy + amount, MAX_ENERGY) });
    }
  },
  
  isPlayerTurn: () => {
    return get().currentTurn === "player";
  }
}));
