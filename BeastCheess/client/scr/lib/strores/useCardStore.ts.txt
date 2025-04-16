import { create } from "zustand";
import { useGameStore } from "./useGameStore";
import { useBoardStore } from "./useBoardStore";
import { allCards, Card, CardType } from "@/lib/data/cards";

interface CardState {
  deck: Card[];
  playerHand: Card[];
  remainingCards: number;
  
  // Actions
  resetCards: () => void;
  drawCard: () => void;
  playCard: (cardId: string) => void;
  getRandomCardsForOpponent: (count: number) => Card[];
}

// Constants
const INITIAL_HAND_SIZE = 3;
const MAX_HAND_SIZE = 7;
const ENERGY_COST_TO_DRAW = 1;

export const useCardStore = create<CardState>((set, get) => ({
  deck: [],
  playerHand: [],
  remainingCards: 0,
  
  resetCards: () => {
    // Create a shuffled deck
    const shuffledDeck = [...allCards]
      .sort(() => Math.random() - 0.5)
      .map(card => ({
        ...card,
        id: `${card.id}-${Math.random().toString(36).substring(2, 9)}`
      }));
    
    // Draw initial hand
    const initialHand = shuffledDeck.slice(0, INITIAL_HAND_SIZE);
    const remainingDeck = shuffledDeck.slice(INITIAL_HAND_SIZE);
    
    set({
      deck: remainingDeck,
      playerHand: initialHand,
      remainingCards: remainingDeck.length
    });
  },
  
  drawCard: () => {
    const { deck, playerHand } = get();
    
    // Check if deck is empty
    if (deck.length === 0) return;
    
    // Check if hand is full
    if (playerHand.length >= MAX_HAND_SIZE) return;
    
    // Check if player has enough energy
    if (!useGameStore.getState().useEnergy(ENERGY_COST_TO_DRAW, "player")) return;
    
    // Draw the top card from the deck
    const [newCard, ...remainingDeck] = deck;
    
    set({
      deck: remainingDeck,
      playerHand: [...playerHand, newCard],
      remainingCards: remainingDeck.length
    });
  },
  
  playCard: (cardId: string) => {
    const { playerHand } = get();
    
    // Find the card in the player's hand
    const cardIndex = playerHand.findIndex(card => card.id === cardId);
    
    if (cardIndex === -1) return;
    
    const card = playerHand[cardIndex];
    
    // Check if player has enough energy to play the card
    if (!useGameStore.getState().useEnergy(card.cost, "player")) return;
    
    // Apply card effects
    applyCardEffect(card);
    
    // Remove card from hand
    const newHand = [...playerHand];
    newHand.splice(cardIndex, 1);
    
    set({
      playerHand: newHand
    });
  },
  
  getRandomCardsForOpponent: (count: number) => {
    // This function gets random cards for the AI opponent to play
    const availableCards = allCards.filter(card => {
      // Filter cards that make sense for AI to play
      if (card.type === "attack" || card.type === "special") return true;
      return card.cost <= 3; // Only include lower cost utility cards
    });
    
    // Select random cards
    const selectedCards: Card[] = [];
    for (let i = 0; i < count; i++) {
      const randomIndex = Math.floor(Math.random() * availableCards.length);
      selectedCards.push({
        ...availableCards[randomIndex],
        id: `ai-${availableCards[randomIndex].id}-${Math.random().toString(36).substring(2, 9)}`
      });
    }
    
    return selectedCards;
  }
}));

// Helper function to apply card effects when played
function applyCardEffect(card: Card) {
  const board = useBoardStore.getState().board;
  const boardStore = useBoardStore.getState();
  const gameStore = useGameStore.getState();
  
  // Kartın tipine göre etkiyi uygulayalım
  if (card.id.includes("attack")) {
    // Saldırı kartları rakip taşlara hasar verir
    
    // Rakip taşları bul
    const opponentPieces: { x: number, y: number }[] = [];
    for (let y = 0; y < 8; y++) {
      for (let x = 0; x < 8; x++) {
        if (board[y][x].piece && board[y][x].piece?.player === "opponent") {
          opponentPieces.push({ x, y });
        }
      }
    }
    
    if (opponentPieces.length > 0) {
      // Kartın numarasına göre farklı etkiler
      if (card.id.includes("attack1")) {
        // Tek bir taşa yüksek hasar
        const randomPiece = opponentPieces[Math.floor(Math.random() * opponentPieces.length)];
        boardStore.damagePiece(randomPiece.x, randomPiece.y, 8);
        console.log(`Attack card damaged opponent piece at (${randomPiece.x},${randomPiece.y}) for 8 damage`);
      } 
      else if (card.id.includes("attack2")) {
        // Tüm taşlara düşük hasar
        for (const piece of opponentPieces) {
          boardStore.damagePiece(piece.x, piece.y, 3);
        }
        console.log(`Attack card damaged all ${opponentPieces.length} opponent pieces for 3 damage`);
      }
      else if (card.id.includes("attack3")) {
        // İki farklı taşa orta seviye hasar
        if (opponentPieces.length >= 2) {
          // İki rastgele taş seç
          const shuffled = [...opponentPieces].sort(() => 0.5 - Math.random());
          const selected = shuffled.slice(0, 2);
          
          for (const piece of selected) {
            boardStore.damagePiece(piece.x, piece.y, 5);
          }
          console.log(`Attack card damaged 2 random opponent pieces for 5 damage each`);
        } else {
          // Tek taş varsa ona yüksek hasar
          boardStore.damagePiece(opponentPieces[0].x, opponentPieces[0].y, 8);
          console.log(`Attack card damaged single opponent piece for 8 damage`);
        }
      }
      else {
        // Varsayılan saldırı
        const randomPiece = opponentPieces[Math.floor(Math.random() * opponentPieces.length)];
        boardStore.damagePiece(randomPiece.x, randomPiece.y, 5);
        console.log(`Attack card damaged opponent piece at (${randomPiece.x},${randomPiece.y}) for 5 damage`);
      }
    }
  } 
  else if (card.id.includes("defense")) {
    // Savunma kartları kendi taşlarını iyileştirir
    
    // Kendi taşlarını bul
    const playerPieces: { x: number, y: number }[] = [];
    for (let y = 0; y < 8; y++) {
      for (let x = 0; x < 8; x++) {
        if (board[y][x].piece && board[y][x].piece?.player === "player") {
          playerPieces.push({ x, y });
        }
      }
    }
    
    if (playerPieces.length > 0) {
      // Kartın numarasına göre farklı etkiler
      if (card.id.includes("defense1")) {
        // Tüm taşları az iyileştir
        for (const piece of playerPieces) {
          boardStore.healPiece(piece.x, piece.y, 2);
        }
        console.log(`Defense card healed all ${playerPieces.length} player pieces for 2 health`);
      } 
      else if (card.id.includes("defense2")) {
        // Tek bir taşı çok iyileştir
        const randomPiece = playerPieces[Math.floor(Math.random() * playerPieces.length)];
        boardStore.healPiece(randomPiece.x, randomPiece.y, 8);
        console.log(`Defense card fully healed player piece at (${randomPiece.x},${randomPiece.y})`);
      }
      else if (card.id.includes("defense3")) {
        // İki farklı taşı orta seviye iyileştir
        if (playerPieces.length >= 2) {
          // İki rastgele taş seç
          const shuffled = [...playerPieces].sort(() => 0.5 - Math.random());
          const selected = shuffled.slice(0, 2);
          
          for (const piece of selected) {
            boardStore.healPiece(piece.x, piece.y, 5);
          }
          console.log(`Defense card healed 2 random player pieces for 5 health each`);
        } else {
          // Tek taş varsa onu tam iyileştir
          boardStore.healPiece(playerPieces[0].x, playerPieces[0].y, 10);
          console.log(`Defense card fully healed single player piece`);
        }
      }
      else {
        // Varsayılan savunma
        for (const piece of playerPieces) {
          boardStore.healPiece(piece.x, piece.y, 3);
        }
        console.log(`Defense card healed all player pieces for 3 health`);
      }
    }
  }
  else if (card.id.includes("special")) {
    // Özel kartlar farklı etkiler yapar
    
    if (card.id.includes("special1")) {
      // Enerji kazanma kartı
      gameStore.addEnergy(4, "player");
      console.log(`Special card granted 4 energy to player`);
    }
    else if (card.id.includes("special2")) {
      // Oyun alanını daraltmayı engelleme kartı
      // Bu sadece bir tur için geçerli olduğundan turnNumber + 5 yapıyoruz
      // Böylece sonraki alan daralmasını bir tur geciktirmiş oluyoruz
      gameStore.turnNumber -= 3;
      console.log(`Special card delayed board shrinking by 3 turns`);
    }
    else if (card.id.includes("special3")) {
      // Taşların hareket kabiliyetini artırma (simüle etmek için iyileştirme yapalım)
      const playerPieces: { x: number, y: number }[] = [];
      for (let y = 0; y < 8; y++) {
        for (let x = 0; x < 8; x++) {
          if (board[y][x].piece && board[y][x].piece.player === "player") {
            playerPieces.push({ x, y });
          }
        }
      }
      
      // Tüm taşların canını 1 arttır (hareket kabiliyeti artışını simüle etmek için)
      for (const piece of playerPieces) {
        boardStore.healPiece(piece.x, piece.y, 1);
      }
      console.log(`Special card increased movement ability of all player pieces`);
    }
    else {
      // Varsayılan özel kart etkisi: enerji kazanma
      gameStore.addEnergy(3, "player");
      console.log(`Special card granted 3 energy to player`);
    }
  }
  else {
    console.log("Card effect not implemented for card:", card.id);
  }
}
