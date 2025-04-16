import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useGameStore } from "@/lib/stores/useGameStore";
import { useAudio } from "@/lib/stores/useAudio";
import { useBoardStore } from "@/lib/stores/useBoardStore";

const GameUI = () => {
  const { phase, currentTurn, turnNumber, playerEnergy, opponentEnergy, winner, resetGame } = useGameStore();
  const { resetBoard, shrinkLevel } = useBoardStore();
  const { toggleMute, isMuted } = useAudio();
  const [showRules, setShowRules] = useState(false);
  
  const handleResetGame = () => {
    resetGame();
    resetBoard();
  };
  
  return (
    <div className="text-white">
      {/* Game header */}
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-xl font-bold">BeastChess</h1>
        <div className="flex space-x-2">
          <button 
            onClick={toggleMute}
            className="w-8 h-8 flex items-center justify-center bg-gray-700 rounded-md hover:bg-gray-600"
          >
            {isMuted ? '🔇' : '🔊'}
          </button>
          <button
            onClick={() => setShowRules(!showRules)}
            className="w-8 h-8 flex items-center justify-center bg-gray-700 rounded-md hover:bg-gray-600"
          >
            ❓
          </button>
        </div>
      </div>
      
      {/* Game phase indicator */}
      <div className="mb-4 bg-gray-800 p-2 rounded-md">
        <p className="text-sm">Game Phase: 
          <span className="ml-1 font-bold">
            {phase === "menu" ? "Main Menu" : 
             phase === "playing" ? "In Progress" : 
             phase === "gameOver" ? "Game Over" : ""}
          </span>
        </p>
        <p className="text-sm">Turn: {turnNumber}</p>
        <p className="text-sm">Current Player: 
          <span className={`ml-1 font-bold ${currentTurn === "player" ? "text-blue-400" : "text-red-400"}`}>
            {currentTurn === "player" ? "You" : "Opponent"}
          </span>
        </p>
      </div>
      
      {/* Energy indicators */}
      <div className="grid grid-cols-2 gap-2 mb-4">
        <div className="bg-blue-900 p-2 rounded-md">
          <p className="text-xs">Your Energy</p>
          <div className="flex items-center">
            <span className="text-xl font-bold mr-1">{playerEnergy}</span>
            <span className="text-yellow-400">⚡</span>
          </div>
        </div>
        <div className="bg-red-900 p-2 rounded-md">
          <p className="text-xs">Opponent Energy</p>
          <div className="flex items-center">
            <span className="text-xl font-bold mr-1">{opponentEnergy}</span>
            <span className="text-yellow-400">⚡</span>
          </div>
        </div>
      </div>
      
      {/* Shrinking board indicator */}
      <div className="mb-4 bg-gray-800 p-2 rounded-md">
        <p className="text-sm">Board Shrink Level: {shrinkLevel}</p>
        <div className="w-full bg-gray-700 h-2 rounded-full mt-1">
          <motion.div 
            className="bg-amber-500 h-full rounded-full"
            initial={{ width: '0%' }}
            animate={{ width: `${(shrinkLevel / 3) * 100}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>
        <p className="text-xs mt-1 text-gray-400">Board shrinks every 5 turns</p>
      </div>
      
      {/* Game over screen */}
      {phase === "gameOver" && (
        <motion.div 
          className="mt-4 bg-gray-700 p-3 rounded-md text-center"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h2 className="text-xl font-bold mb-2">Game Over</h2>
          <p className="mb-3">{winner === "player" ? "You won!" : "Opponent won!"}</p>
          <button
            onClick={handleResetGame}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md transition-colors"
          >
            Play Again
          </button>
        </motion.div>
      )}
      
      {/* Rules modal */}
      <AnimatePresence>
        {showRules && (
          <motion.div
            className="fixed inset-0 bg-black bg-opacity-80 z-50 flex items-center justify-center p-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowRules(false)}
          >
            <motion.div 
              className="bg-gray-800 rounded-lg p-4 max-w-lg max-h-[80vh] overflow-y-auto"
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              onClick={e => e.stopPropagation()}
            >
              <h2 className="text-xl font-bold mb-4">How to Play BeastChess</h2>
              
              <div className="space-y-3 text-sm">
                <p>BeastChess combines chess-like movement with card mechanics and a shrinking board.</p>
                
                <h3 className="font-bold text-blue-400">Movement:</h3>
                <ul className="list-disc pl-5 space-y-1">
                  <li>Lion: Moves one square in any direction (like a king)</li>
                  <li>Eagle: Moves diagonally any number of squares (like a bishop)</li>
                  <li>Wolf: Moves horizontally or vertically any number of squares (like a rook)</li>
                  <li>Bear: Moves one square in any direction, but powerful in battle</li>
                  <li>Snake: Moves in an L-shape (like a knight)</li>
                  <li>Fox: Can move up to three squares in any direction</li>
                </ul>
                
                <h3 className="font-bold text-blue-400">Cards:</h3>
                <ul className="list-disc pl-5 space-y-1">
                  <li>Draw cards using energy (⚡)</li>
                  <li>Play cards to gain advantages, attack, defend, or use special abilities</li>
                  <li>Cards have different effects and costs</li>
                </ul>
                
                <h3 className="font-bold text-blue-400">Shrinking Board:</h3>
                <ul className="list-disc pl-5 space-y-1">
                  <li>Every 5 turns, the playable area of the board shrinks</li>
                  <li>Pieces caught outside the playable area take damage each turn</li>
                  <li>Plan your strategy accordingly as the space becomes limited</li>
                </ul>
                
                <h3 className="font-bold text-blue-400">Goal:</h3>
                <p>Defeat your opponent's Lion piece or force them into a position where they cannot make any legal moves.</p>
              </div>
              
              <button
                className="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md w-full"
                onClick={() => setShowRules(false)}
              >
                Close
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default GameUI;
