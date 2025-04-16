import { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { isTileOutOfBounds } from "@/lib/utils/boardUtils";

interface TileProps {
  x: number;
  y: number;
  color: 'light' | 'dark';
  children?: ReactNode;
  isSelected?: boolean;
  isValidMove?: boolean;
  shrinkLevel: number;
  onClick: () => void;
}

const Tile = ({ x, y, color, children, isSelected = false, isValidMove = false, shrinkLevel, onClick }: TileProps) => {
  // Check if this tile is outside the current playable area
  const isOutOfBounds = isTileOutOfBounds(x, y, shrinkLevel);
  
  return (
    <div
      className={cn(
        "relative flex items-center justify-center transition-all duration-300",
        color === 'light' ? 'bg-amber-200' : 'bg-amber-800',
        isSelected && 'ring-4 ring-blue-500 z-10',
        isValidMove && 'ring-2 ring-green-500 z-5',
        isOutOfBounds && 'bg-opacity-20 pointer-events-none'
      )}
      onClick={isOutOfBounds ? undefined : onClick}
      style={{
        aspectRatio: '1/1',
      }}
    >
      {/* Position coordinates (debug) */}
      <span className="absolute top-0 left-1 text-xs opacity-40">
        {String.fromCharCode(97 + x)}{8 - y}
      </span>
      
      {children}
      
      {/* Visual indicator for valid moves */}
      {isValidMove && !children && (
        <div className="absolute w-4 h-4 rounded-full bg-green-500 opacity-60 animate-pulse" />
      )}
      
      {/* Visual indicator for tiles outside play area */}
      {isOutOfBounds && (
        <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="transform rotate-45 w-full h-px bg-red-500" />
          <div className="transform -rotate-45 w-full h-px bg-red-500" />
        </div>
      )}
    </div>
  );
};

export default Tile;
