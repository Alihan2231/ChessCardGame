import { useMemo } from "react";
import { motion } from "framer-motion";
import { useBoardStore } from "@/lib/stores/useBoardStore";
import { getBoardBoundaries } from "@/lib/utils/boardUtils";

const ShrinkingArea = () => {
  const { shrinkLevel } = useBoardStore();
  
  // Calculate the boundaries based on current shrink level
  const { minX, minY, maxX, maxY } = useMemo(() => 
    getBoardBoundaries(shrinkLevel), 
    [shrinkLevel]
  );
  
  // No need to visualize if board isn't shrunk yet
  if (shrinkLevel === 0) return null;
  
  return (
    <div className="absolute inset-0 pointer-events-none">
      {/* Top out-of-bounds area */}
      <motion.div
        className="absolute left-0 right-0 bg-red-500 bg-opacity-20 border-b border-red-500"
        style={{
          top: 0,
          bottom: `${(7 - maxY) * 12.5}%`,
        }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      />
      
      {/* Bottom out-of-bounds area */}
      <motion.div
        className="absolute left-0 right-0 bg-red-500 bg-opacity-20 border-t border-red-500"
        style={{
          top: `${(minY) * 12.5}%`,
          bottom: 0,
        }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      />
      
      {/* Left out-of-bounds area */}
      <motion.div
        className="absolute top-0 bottom-0 bg-red-500 bg-opacity-20 border-r border-red-500"
        style={{
          left: 0,
          right: `${(7 - maxX) * 12.5}%`,
        }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      />
      
      {/* Right out-of-bounds area */}
      <motion.div
        className="absolute top-0 bottom-0 bg-red-500 bg-opacity-20 border-l border-red-500"
        style={{
          left: `${(minX) * 12.5}%`,
          right: 0,
        }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      />
      
      {/* Danger warning text */}
      <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-red-500 font-bold text-xl whitespace-nowrap">
        ⚠️ DANGER ZONE ⚠️
      </div>
    </div>
  );
};

export default ShrinkingArea;
