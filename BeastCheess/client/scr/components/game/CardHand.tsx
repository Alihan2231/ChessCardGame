import { useCardStore } from "@/lib/stores/useCardStore";
import Card from "./Card";
import { motion } from "framer-motion";

const CardHand = () => {
  const { playerHand } = useCardStore();
  
  return (
    <div className="relative h-48">
      <p className="text-white text-sm mb-1">Your Hand: {playerHand.length} cards</p>
      
      <div className="relative h-44">
        {/* Container for the cards with perspective */}
        <div 
          className="relative h-full"
          style={{ perspective: '1000px', width: `${Math.max(300, playerHand.length * 45)}px` }}
        >
          {/* If hand is empty, show placeholder */}
          {playerHand.length === 0 && (
            <motion.div
              className="absolute bottom-0 w-32 h-44 rounded-lg border-2 border-dashed border-gray-400 flex items-center justify-center text-gray-400"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              No Cards
            </motion.div>
          )}
          
          {/* Display cards in hand */}
          {playerHand.map((card, index) => (
            <Card 
              key={card.id}
              card={card}
              index={index}
              isInHand={true}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default CardHand;
