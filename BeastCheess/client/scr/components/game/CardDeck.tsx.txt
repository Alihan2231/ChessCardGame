import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useCardStore } from "@/lib/stores/useCardStore";
import { useGameStore } from "@/lib/stores/useGameStore";
import { useAudio } from "@/lib/stores/useAudio";

const CardDeck = () => {
  const { drawCard, remainingCards } = useCardStore();
  const { phase, playerEnergy, isPlayerTurn } = useGameStore();
  const { playHit } = useAudio();
  
  // Tek seferde sadece 1 kart çekme sınırlaması ekleyelim
  const { turnNumber } = useGameStore();
  const [hasDrawnThisTurn, setHasDrawnThisTurn] = useState(false);
  
  // Turn değiştiğinde hasDrawnThisTurn'u sıfırla
  useEffect(() => {
    setHasDrawnThisTurn(false);
  }, [turnNumber]);
  
  const canDraw = isPlayerTurn() && 
                 phase === "playing" && 
                 remainingCards > 0 && 
                 playerEnergy > 0 &&
                 !hasDrawnThisTurn;
  
  const handleDrawCard = () => {
    if (canDraw) {
      drawCard();
      playHit();
      setHasDrawnThisTurn(true); // Kart çekildikten sonra bayrak ayarla
    }
  };
  
  // Calculate the number of visible "stacked" cards based on remaining cards
  const stackCount = Math.min(remainingCards, 5);
  
  return (
    <div className="mb-4">
      <p className="text-white text-sm mb-1">Deck: {remainingCards} cards</p>
      
      <div className="relative h-40 w-40 flex justify-center">
        {/* Create stacked cards effect */}
        {Array.from({ length: stackCount }).map((_, index) => (
          <motion.div
            key={index}
            className="absolute w-24 h-36 rounded-md bg-amber-800 border-2 border-amber-900 shadow-md"
            style={{ 
              backgroundImage: "url('/game-assets/card-back.svg')",
              backgroundSize: "cover",
              backgroundPosition: "center",
              zIndex: index,
              transformOrigin: "bottom center"
            }}
            initial={false}
            animate={{
              rotateZ: (index - 2) * 2,
              y: -index * 2
            }}
          />
        ))}
        
        {/* Draw card button - moved below the cards */}
        {remainingCards > 0 && (
          <motion.button
            className={`absolute top-36 left-1/2 transform -translate-x-1/2 px-3 py-1 rounded-md ${canDraw ? 'bg-green-600 text-white hover:bg-green-700' : 'bg-gray-600 text-gray-300 cursor-not-allowed'}`}
            whileHover={canDraw ? { scale: 1.05 } : {}}
            whileTap={canDraw ? { scale: 0.95 } : {}}
            onClick={handleDrawCard}
            disabled={!canDraw}
          >
            Draw (1 ⚡)
          </motion.button>
        )}
        
        {/* Empty deck indicator */}
        {remainingCards === 0 && (
          <div className="absolute top-4 left-0 w-full text-center text-red-500 font-bold transform rotate-12 border-2 border-red-500 bg-white bg-opacity-70 py-1">
            EMPTY
          </div>
        )}
      </div>
    </div>
  );
};

export default CardDeck;
