import { useMemo } from "react";
import { PieceType, PieceData } from "@/lib/data/pieces";
import { motion } from "framer-motion";

interface PieceProps {
  piece: {
    type: PieceType;
    player: "player" | "opponent";
    hasMoved?: boolean;
    health: number;
    maxHealth: number;
  };
  isSelected?: boolean;
}

const Piece = ({ piece, isSelected = false }: PieceProps) => {
  // Get piece data which includes the SVG and properties
  const pieceData = useMemo(() => {
    const piecesData: Record<PieceType, PieceData> = {
      lion: {
        svg: (
          <svg viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
            <path d="M12,3C7.03,3 3,7.03 3,12s4.03,9 9,9s9-4.03 9-9S16.97,3 12,3M12,11.5c-0.83,0-1.5-0.67-1.5-1.5s0.67-1.5 1.5-1.5s1.5,0.67 1.5,1.5S12.83,11.5 12,11.5M12,7.5c-1.66,0-3,1.34-3,3s1.34,3 3,3s3-1.34 3-3S13.66,7.5 12,7.5z"/>
            <path d="M16,14c0,0.55-0.45,1-1,1s-1-0.45-1-1s0.45-1 1-1S16,13.45 16,14z"/>
            <path d="M8,14c0,0.55-0.45,1-1,1s-1-0.45-1-1s0.45-1 1-1S8,13.45 8,14z"/>
            <path d="M12,14c0,0.55-0.45,1-1,1s-1-0.45-1-1s0.45-1 1-1S12,13.45 12,14z"/>
            <path d="M18,14c0,0.55-0.45,1-1,1s-1-0.45-1-1s0.45-1 1-1S18,13.45 18,14z"/>
            <path d="M10,16c0,0.55-0.45,1-1,1s-1-0.45-1-1s0.45-1 1-1S10,15.45 10,16z"/>
            <path d="M14,16c0,0.55-0.45,1-1,1s-1-0.45-1-1s0.45-1 1-1S14,15.45 14,16z"/>
            <path d="M12,18c0,0.55-0.45,1-1,1s-1-0.45-1-1s0.45-1 1-1S12,17.45 12,18z"/>
          </svg>
        ),
        name: "Lion",
        description: "The king of beasts. Can move one square in any direction."
      },
      eagle: {
        svg: (
          <svg viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
            <path d="M22,15h-3v-3h-3v-2l-6,1l-4,-6l-2,6l-3,2v2h2v3h-2v3h7c0,1.66 1.34,3 3,3s3,-1.34 3,-3h7v-3h-2v-3h-2z"/>
            <path d="M15,15v3h-6v-3l-2,-4l6,-1l-2,-2l5,2v5h-1z"/>
          </svg>
        ),
        name: "Eagle",
        description: "Can fly across the board diagonally like a bishop."
      },
      wolf: {
        svg: (
          <svg viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
            <path d="M16,8c0,-2.21 -1.79,-4 -4,-4S8,5.79 8,8c0,2.21 1.79,4 4,4S16,10.21 16,8z"/>
            <path d="M19,12c0,-3.3 -2.7,-6 -6,-6s-6,2.7 -6,6s2.7,6 6,6S19,15.3 19,12z"/>
            <path d="M20,12c0,0.46 -0.05,0.91 -0.14,1.34l-3.68,-2.37l-1.74,0.89l-1.74,-1.5l-1.74,1.5l-2.28,-1.25l-1.57,1.01c-0.11,-0.42 -0.17,-0.86 -0.17,-1.31c0,-2.76 2.24,-5 5,-5S20,9.24 20,12z"/>
            <path d="M16,16c-1.98,0 -3.77,-0.96 -4.9,-2.43l-1.1,0.76l1.56,1.08l-0.89,1.32l-2.67,-1.85l-0.06,0.14c1.27,1.79 3.37,2.97 5.76,2.97c3.87,0 7,-3.13 7,-7c0,-0.2 -0.01,-0.39 -0.03,-0.58l-1.94,0.63l-0.42,-1.95c-2.12,0.69 -3.44,2.73 -3.31,4.91z"/>
            <path d="M5.23,9.35c0.42,-1.53 1.4,-2.83 2.71,-3.63l-0.56,-1.91l-3.13,0.92c0.25,1.62 0.84,3.11 1.69,4.36l-0.71,0.26z"/>
          </svg>
        ),
        name: "Wolf",
        description: "Moves horizontally and vertically like a rook."
      },
      bear: {
        svg: (
          <svg viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
            <path d="M12,2C9.24,2 7,4.24 7,7c0,1.1 0.36,2.1 0.97,2.91C7.37,10.88 7,11.92 7,13c0,3.31 2.69,6 6,6c3.31,0 6,-2.69 6,-6c0,-1.08 -0.37,-2.12 -0.97,-3.09C18.64,9.1 19,8.1 19,7C19,4.24 16.76,2 14,2H12z"/>
            <path d="M8,7c0,1.1 0.9,2 2,2s2,-0.9 2,-2s-0.9,-2 -2,-2S8,5.9 8,7z"/>
            <path d="M16,7c0,1.1 0.9,2 2,2s2,-0.9 2,-2s-0.9,-2 -2,-2S16,5.9 16,7z"/>
            <path d="M9,11v1h4v-1H9z"/>
            <path d="M15,10v1h2v1h-2v1h3v-3H15z"/>
            <path d="M9,15c0,1.66 1.34,3 3,3s3,-1.34 3,-3c0,-1.42 -1,-2.61 -2.33,-2.92C13.42,11.74 13.75,11 14,10h-4c0.35,1 0.58,1.74 1.33,2.08C10,12.39 9,13.58 9,15z"/>
          </svg>
        ),
        name: "Bear",
        description: "Powerful but slow. Moves one square in any direction."
      },
      snake: {
        svg: (
          <svg viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
            <path d="M19.57,9.76C19.57,9.76 17.76,12.47 16.15,12.45C14.53,12.42 14.38,11.09 14.38,11.09C14.38,11.09 13.8,7.86 9.81,7.84C5.82,7.83 5.25,10.28 5.25,10.28C5.25,10.28 4.57,13.05 2,12.32L2.67,13.5C2.67,13.5 4.37,14.5 5.21,13.19C5.21,13.19 5.77,11.25 8.82,11.26C11.88,11.27 11.88,14.09 11.88,14.09C11.88,14.09 12.31,18.95 17.57,18.41C18.13,18.34 18.66,18.07 19.08,17.67L19.1,17.64C19.11,17.63 19.12,17.6 19.13,17.59L20.91,15.37L19.57,9.76z"/>
          </svg>
        ),
        name: "Snake",
        description: "Slithers through the board. Can move in an L-shape like a knight."
      },
      fox: {
        svg: (
          <svg viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
            <path d="M12,3C7.69,3 4.1,4.96 2,8c0.07,0.36 0.32,0.73 0.68,1h7.49c-0.23,-0.3 -0.37,-0.66 -0.37,-1.06c0,-0.96 0.78,-1.75 1.74,-1.75c0.96,0 1.74,0.79 1.74,1.75c0,0.4 -0.14,0.76 -0.37,1.06h7.49c0.36,-0.27 0.61,-0.64 0.68,-1C19.9,4.96 16.31,3 12,3z"/>
            <path d="M20.12,9H3.88c-0.16,0.64 -0.27,1.31 -0.27,2c0,4.41 3.59,8 8,8s8,-3.59 8,-8C19.61,10.31 19.5,9.64 20.12,9z"/>
            <path d="M12,11c-1.66,0 -3,1.34 -3,3s1.34,3 3,3s3,-1.34 3,-3S13.66,11 12,11z"/>
            <path d="M8,11.5c0,0.83 -0.67,1.5 -1.5,1.5S5,12.33 5,11.5S5.67,10 6.5,10S8,10.67 8,11.5z"/>
            <path d="M19,11.5c0,0.83 -0.67,1.5 -1.5,1.5S16,12.33 16,11.5s0.67,-1.5 1.5,-1.5S19,10.67 19,11.5z"/>
          </svg>
        ),
        name: "Fox",
        description: "Cunning and quick. Can move three squares in any direction."
      }
    };
    
    return piecesData[piece.type];
  }, [piece.type]);

  // Calculate health bar percentage
  const healthPercentage = (piece.health / piece.maxHealth) * 100;
  
  // Determine health bar color based on percentage
  const healthBarColor = 
    healthPercentage > 70 ? 'bg-green-500' : 
    healthPercentage > 30 ? 'bg-yellow-500' : 
    'bg-red-500';

  return (
    <motion.div 
      className={`w-4/5 h-4/5 relative flex flex-col items-center justify-center 
        ${piece.player === "player" ? "text-blue-500" : "text-red-500"}
        ${isSelected ? "scale-110" : ""}
      `}
      initial={{ scale: 0 }}
      animate={{ 
        scale: isSelected ? 1.1 : 1,
        y: isSelected ? -5 : 0
      }}
      transition={{ 
        type: "spring",
        stiffness: 300,
        damping: 15
      }}
    >
      {/* The piece icon */}
      <div className="w-full h-full">
        {pieceData.svg}
      </div>
      
      {/* Health bar */}
      <div className="absolute bottom-0 w-full h-1 bg-gray-700 rounded-full overflow-hidden">
        <div 
          className={`h-full ${healthBarColor} transition-all duration-300`}
          style={{ width: `${healthPercentage}%` }}
        />
      </div>
    </motion.div>
  );
};

export default Piece;
