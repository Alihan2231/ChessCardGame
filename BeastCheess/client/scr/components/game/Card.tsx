import { useState } from "react";
import { motion } from "framer-motion";
import { Card as CardType } from "@/lib/data/cards";
import { useCardStore } from "@/lib/stores/useCardStore";
import { useGameStore } from "@/lib/stores/useGameStore";
import { cn } from "@/lib/utils";
import { useAudio } from "@/lib/stores/useAudio";

interface CardProps {
  card: CardType;
  index: number;
  isInHand?: boolean;
}

const Card = ({ card, index, isInHand = true }: CardProps) => {
  const [isHovered, setIsHovered] = useState(false);
  const { playCard } = useCardStore();
  const { phase, isPlayerTurn } = useGameStore();
  const { playSuccess } = useAudio();
  
  const canPlay = isPlayerTurn() && phase === "playing" && isInHand;
  
  const handlePlayCard = () => {
    if (canPlay) {
      playSuccess();
      playCard(card.id);
    }
  };
  
  // Define card appearance variants
  const cardVariants = {
    normal: { 
      y: 0,
      rotateZ: 0,
      scale: 1
    },
    hovered: { 
      y: -30,
      rotateZ: 0,
      scale: 1.05,
      zIndex: 10
    }
  };
  
  // Define staggered appearance for hand cards
  const handPositionVariants = {
    initial: { 
      x: -300, 
      rotateZ: -90,
      opacity: 0
    },
    animate: { 
      x: 0, 
      rotateZ: (index - 2) * 5, // Slight fan effect
      opacity: 1,
      transition: {
        delay: index * 0.1,
        type: "spring",
        stiffness: 300,
        damping: 25
      }
    }
  };

  return (
    <motion.div
      className={cn(
        "relative w-32 h-44 rounded-lg shadow-lg cursor-pointer transform transition-transform",
        !canPlay && "opacity-70 cursor-not-allowed",
        isInHand && "absolute"
      )}
      style={{
        left: isInHand ? `${index * 40}px` : 0, // Increased spacing between cards
        backgroundImage: "url('/textures/wood.jpg')",
        backgroundSize: "cover",
        transformOrigin: "bottom center",
      }}
      variants={isInHand ? handPositionVariants : undefined}
      initial={isInHand ? "initial" : { scale: 0 }}
      animate={isInHand ? "animate" : { scale: 1 }}
      whileHover={canPlay ? "hovered" : undefined}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      onClick={handlePlayCard}
    >
      {/* Card border */}
      <div className="absolute inset-1 bg-amber-100 rounded-md flex flex-col p-1">
        {/* Card header */}
        <div className={`rounded-t-md p-1 font-bold text-center text-white ${card.type === 'attack' ? 'bg-red-600' : card.type === 'defense' ? 'bg-blue-600' : 'bg-purple-600'}`}>
          {card.name}
        </div>
        
        {/* Card image area */}
        <div className="flex-1 flex items-center justify-center bg-gray-200 my-1 rounded-md overflow-hidden">
          <div className="text-3xl">
            {card.type === 'attack' ? '⚔️' : card.type === 'defense' ? '🛡️' : '✨'}
          </div>
        </div>
        
        {/* Card description */}
        <div className="bg-amber-50 rounded-md p-1 text-xs h-16 overflow-hidden">
          {card.description}
        </div>
        
        {/* Card cost/value */}
        <div className="absolute top-1 right-1 bg-yellow-500 text-white w-6 h-6 rounded-full flex items-center justify-center font-bold">
          {card.cost}
        </div>
      </div>
      
      {/* Show hover tooltip with expanded details for small screens */}
      {isHovered && (
        <motion.div 
          className="absolute -top-24 left-0 bg-black bg-opacity-80 p-2 rounded text-white text-xs z-20 w-48 pointer-events-none"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <p className="font-bold">{card.name}</p>
          <p>{card.description}</p>
        </motion.div>
      )}
    </motion.div>
  );
};

export default Card;
