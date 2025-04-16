import { useGameStore } from "../stores/useGameStore";
import { useBoardStore, Piece } from "../stores/useBoardStore";
import { useCardStore } from "../stores/useCardStore";
import { getBoardBoundaries } from "../utils/boardUtils";

// Structure for a potential move
interface PotentialMove {
  fromX: number;
  fromY: number;
  toX: number;
  toY: number;
  piece: Piece;
  score: number;
}

// Track if the AI is currently taking its turn
let aiIsExecutingTurn = false;

// AI logic to execute a turn
export function runAI() {
  const gameState = useGameStore.getState();
  const boardState = useBoardStore.getState();
  const cardState = useCardStore.getState();
  
  // Only execute if it's the AI's turn and not already executing
  if (gameState.currentTurn !== "opponent" || gameState.phase !== "playing" || aiIsExecutingTurn) return;
  
  // Set flag to prevent multiple simultaneous AI turns
  aiIsExecutingTurn = true;
  
  console.log("AI is thinking...");
  
  // First, try to play a card
  tryPlayCard();
  
  // Then move a piece
  setTimeout(() => {
    const bestMove = findBestMove();
    
    if (bestMove) {
      console.log(`AI moving piece from (${bestMove.fromX},${bestMove.fromY}) to (${bestMove.toX},${bestMove.toY})`);
      console.log(`Move details: ${bestMove.piece.type} piece, score: ${bestMove.score}`);
      
      // Make a clone of the board
      const currentBoard = [...boardState.board];
      
      // Manually simulate move for validation before executing
      const fromTile = currentBoard[bestMove.fromY][bestMove.fromX];
      const toTile = currentBoard[bestMove.toY][bestMove.toX];
      
      // Validate one more time - should have AI piece at from position
      // and either empty or player piece at to position
      if (fromTile.piece && 
          fromTile.piece.player === "opponent" && 
          (!toTile.piece || toTile.piece.player === "player")) {
        
        // Execute the move
        const moveResult = boardState.movePiece(
          bestMove.fromX,
          bestMove.fromY,
          bestMove.toX,
          bestMove.toY,
          "opponent"
        );
        
        if (moveResult.success) {
          console.log("AI move successful!");
          // After a successful move, end the AI turn
          setTimeout(() => {
            gameState.nextTurn();
            // Reset the flag after turn is complete
            aiIsExecutingTurn = false;
          }, 500);
        } else {
          // If move failed (shouldn't happen with proper validation), just end turn
          console.error("AI move failed:", moveResult.message);
          gameState.nextTurn();
          // Reset the flag after turn is complete
          aiIsExecutingTurn = false;
        }
      } else {
        console.error("AI move validation failed - invalid source/target tiles");
        gameState.nextTurn();
        aiIsExecutingTurn = false;
      }
    } else {
      // No valid moves found, end turn
      console.log("AI couldn't find a valid move");
      gameState.nextTurn();
      // Reset the flag after turn is complete
      aiIsExecutingTurn = false;
    }
  }, 800); // Small delay for better player experience
}

// Try to play a card from AI's "hand"
function tryPlayCard() {
  const gameState = useGameStore.getState();
  
  // AI has a chance to play a card if it has energy
  if (gameState.opponentEnergy >= 2 && Math.random() > 0.3) {
    // Get some random cards as if the AI had a hand
    const cards = useCardStore.getState().getRandomCardsForOpponent(3);
    
    // Filter cards the AI can afford
    const playableCards = cards.filter(card => card.cost <= gameState.opponentEnergy);
    
    if (playableCards.length > 0) {
      // Choose a random card to play
      const randomCard = playableCards[Math.floor(Math.random() * playableCards.length)];
      
      // Use energy
      gameState.useEnergy(randomCard.cost, "opponent");
      
      console.log(`AI plays card: ${randomCard.name}`);
      
      // Apply AI card effects (simplified version of player card effects)
      applyAICardEffect(randomCard.id);
    }
  }
}

// Apply effects for AI cards
function applyAICardEffect(cardId: string) {
  const board = useBoardStore.getState().board;
  
  // Determine the type of effect based on the card ID
  if (cardId.includes("attack")) {
    // Attack card - find random player piece to damage
    const playerPieces: { x: number, y: number }[] = [];
    
    // Find all player pieces
    for (let y = 0; y < 8; y++) {
      for (let x = 0; x < 8; x++) {
        if (board[y][x].piece && board[y][x].piece?.player === "player") {
          playerPieces.push({ x, y });
        }
      }
    }
    
    // If there are player pieces, damage a random one
    if (playerPieces.length > 0) {
      const randomPiece = playerPieces[Math.floor(Math.random() * playerPieces.length)];
      useBoardStore.getState().damagePiece(randomPiece.x, randomPiece.y, 4);
    }
  } 
  else if (cardId.includes("defense")) {
    // Defense card - heal random AI piece
    const aiPieces: { x: number, y: number }[] = [];
    
    // Find all AI pieces
    for (let y = 0; y < 8; y++) {
      for (let x = 0; x < 8; x++) {
        if (board[y][x].piece && board[y][x].piece?.player === "opponent") {
          aiPieces.push({ x, y });
        }
      }
    }
    
    // If there are AI pieces, heal a random one
    if (aiPieces.length > 0) {
      const randomPiece = aiPieces[Math.floor(Math.random() * aiPieces.length)];
      useBoardStore.getState().healPiece(randomPiece.x, randomPiece.y, 5);
    }
  }
  else {
    // Special card - gain energy
    useGameStore.getState().addEnergy(2, "opponent");
  }
}

// Find the best move for the AI
function findBestMove(): PotentialMove | null {
  const boardStore = useBoardStore.getState();
  const board = boardStore.board;
  const shrinkLevel = boardStore.shrinkLevel;
  const boundaries = getBoardBoundaries(shrinkLevel);
  
  const potentialMoves: PotentialMove[] = [];
  
  console.log("AI is looking for valid moves...");
  
  // Go through each position on the board to find AI pieces
  for (let fromY = 0; fromY < 8; fromY++) {
    for (let fromX = 0; fromX < 8; fromX++) {
      const piece = board[fromY][fromX].piece;
      
      // Check if this is an AI piece
      if (piece && piece.player === "opponent") {
        console.log(`Found AI piece at (${fromX},${fromY}): ${piece.type}`);
        
        // Instead of using movePiece to check validity (which modifies state),
        // manually check valid moves for this piece type
        const validMoves = [];
        
        // Check surrounding squares for simple pieces (lion, bear)
        if (piece.type === "lion" || piece.type === "bear") {
          for (let dy = -1; dy <= 1; dy++) {
            for (let dx = -1; dx <= 1; dx++) {
              if (dx === 0 && dy === 0) continue; // Skip current position
              
              const toX = fromX + dx;
              const toY = fromY + dy;
              
              // Check if target is within board boundaries and is either empty or has an enemy piece
              if (toX >= 0 && toX < 8 && toY >= 0 && toY < 8) {
                const targetTile = board[toY][toX];
                if (!targetTile.piece || targetTile.piece.player === "player") {
                  validMoves.push({ toX, toY });
                }
              }
            }
          }
        }
        // Snake (knight) moves
        else if (piece.type === "snake") {
          const knightMoves = [
            { dx: 1, dy: 2 }, { dx: 2, dy: 1 },
            { dx: -1, dy: 2 }, { dx: -2, dy: 1 },
            { dx: 1, dy: -2 }, { dx: 2, dy: -1 },
            { dx: -1, dy: -2 }, { dx: -2, dy: -1 }
          ];
          
          for (const { dx, dy } of knightMoves) {
            const toX = fromX + dx;
            const toY = fromY + dy;
            
            if (toX >= 0 && toX < 8 && toY >= 0 && toY < 8) {
              const targetTile = board[toY][toX];
              if (!targetTile.piece || targetTile.piece.player === "player") {
                validMoves.push({ toX, toY });
              }
            }
          }
        }
        // Fox movement (up to 3 squares in straight or diagonal lines)
        else if (piece.type === "fox") {
          // 8 yön: dikey, yatay ve çapraz
          const directions = [
            [0, 1], [1, 1], [1, 0], [1, -1],  // Sağ, sağ-aşağı, aşağı, aşağı-sol
            [0, -1], [-1, -1], [-1, 0], [-1, 1]  // Sol, sol-yukarı, yukarı, yukarı-sağ
          ];
          
          for (const [dx, dy] of directions) {
            // Her yönde en fazla 3 kare
            for (let dist = 1; dist <= 3; dist++) {
              const toX = fromX + (dx * dist);
              const toY = fromY + (dy * dist);
              
              // Tahta sınırları içinde mi?
              if (toX >= 0 && toX < 8 && toY >= 0 && toY < 8) {
                const targetTile = board[toY][toX];
                
                // Hedef kare boş mu veya oyuncu taşı mı?
                if (!targetTile.piece || targetTile.piece.player === "player") {
                  // Yol temiz mi? Engel var mı?
                  let pathClear = true;
                  
                  // Aradaki tüm kareleri kontrol et
                  for (let i = 1; i < dist; i++) {
                    const checkX = fromX + (dx * i);
                    const checkY = fromY + (dy * i);
                    
                    if (board[checkY][checkX].piece) {
                      pathClear = false;
                      break;
                    }
                  }
                  
                  if (pathClear) {
                    validMoves.push({ toX, toY });
                  }
                }
                
                // Engel varsa daha ileri gitme
                if (targetTile.piece) {
                  break;
                }
              } else {
                // Tahta dışına çıkıldı, bu yönde ilerleme
                break;
              }
            }
          }
        }
        // Wolf (rook) and eagle (bishop) movements
        else if (piece.type === "wolf" || piece.type === "eagle") {
          const directions = piece.type === "wolf" 
            ? [[0, 1], [1, 0], [0, -1], [-1, 0]] // Rook directions
            : [[1, 1], [1, -1], [-1, 1], [-1, -1]]; // Bishop directions
          
          for (const [dx, dy] of directions) {
            for (let dist = 1; dist < 8; dist++) {
              const toX = fromX + (dx * dist);
              const toY = fromY + (dy * dist);
              
              // Check if within bounds
              if (toX >= 0 && toX < 8 && toY >= 0 && toY < 8) {
                const targetTile = board[toY][toX];
                
                if (!targetTile.piece) {
                  // Empty square, valid move
                  validMoves.push({ toX, toY });
                } else if (targetTile.piece.player === "player") {
                  // Enemy piece, can capture and stop
                  validMoves.push({ toX, toY });
                  break;
                } else {
                  // Friendly piece, blocked
                  break;
                }
              } else {
                // Out of bounds
                break;
              }
            }
          }
        }
        
        console.log(`Found ${validMoves.length} valid moves for piece at (${fromX},${fromY})`);
        
        // Create potential moves with scores
        for (const { toX, toY } of validMoves) {
          // Get the target piece (if any) to check if it's a capture
          const capturedPiece = board[toY][toX].piece?.player === "player" ? board[toY][toX].piece : null;
          
          // Calculate a score for this move
          const moveScore = evaluateMove(fromX, fromY, toX, toY, piece, capturedPiece);
          
          potentialMoves.push({
            fromX,
            fromY,
            toX,
            toY,
            piece,
            score: moveScore
          });
        }
      }
    }
  }
  
  // Sort moves by score (highest first)
  potentialMoves.sort((a, b) => b.score - a.score);
  
  console.log(`Found ${potentialMoves.length} potential moves for AI`);
  
  // Return the best move, or null if no valid moves
  return potentialMoves.length > 0 ? potentialMoves[0] : null;
}

// Evaluate how good a move is
function evaluateMove(
  fromX: number,
  fromY: number,
  toX: number,
  toY: number,
  piece: Piece,
  capturedPiece: Piece | null | undefined
): number {
  let score = 0;
  
  // Capturing a piece is good
  if (capturedPiece) {
    // Capturing pieces is good, especially valuable ones
    score += 100;
    
    // Extra points for capturing important pieces
    if (capturedPiece.type === "lion") {
      score += 1000; // Winning move
    } else if (capturedPiece.type === "bear" || capturedPiece.type === "eagle") {
      score += 50; // Strong pieces
    }
  }
  
  // Moving toward the center is generally good in chess
  const centerDistance = Math.abs(toX - 3.5) + Math.abs(toY - 3.5);
  score += (7 - centerDistance) * 2;
  
  // Moving pieces forward (toward player side) is good
  if (piece.type !== "lion") { // Lions should stay safe
    score += (7 - toY) * 3;
  }
  
  // Prioritize safe locations for the lion
  if (piece.type === "lion") {
    // Keep lion away from the edges
    if (toX >= 2 && toX <= 5 && toY >= 2 && toY <= 5) {
      score += 20;
    }
    
    // Avoid advancing lion too far
    if (toY > 3) {
      score -= (toY - 3) * 10;
    }
  }
  
  // Avoid moving into the "danger zone" if the board is shrinking
  const shrinkLevel = useBoardStore.getState().shrinkLevel;
  if (shrinkLevel > 0) {
    const boundaries = getBoardBoundaries(shrinkLevel);
    const { minX, minY, maxX, maxY } = boundaries;
    
    if (toX < minX || toX > maxX || toY < minY || toY > maxY) {
      score -= 60; // Big penalty for moving into the danger zone
    }
  }
  
  return score;
}
