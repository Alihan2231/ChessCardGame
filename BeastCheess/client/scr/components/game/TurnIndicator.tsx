import { motion, AnimatePresence } from "framer-motion";
import { useGameStore } from "@/lib/stores/useGameStore";

const TurnIndicator = () => {
  const { currentTurn } = useGameStore();
  
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={currentTurn}
        className={`absolute top-0 left-0 right-0 py-2 text-center text-white font-bold text-xl
          ${currentTurn === "player" ? "bg-blue-600" : "bg-red-600"}`}
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: -50, opacity: 0 }}
        transition={{ type: "spring", stiffness: 300, damping: 25 }}
      >
        {currentTurn === "player" ? "Your Turn" : "Opponent's Turn"}
      </motion.div>
    </AnimatePresence>
  );
};

export default TurnIndicator;
