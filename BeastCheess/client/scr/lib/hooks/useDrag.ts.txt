import { useState, useEffect, useRef } from "react";

interface UseDragProps {
  onDragStart?: () => void;
  onDragEnd?: (dropped: boolean) => void;
}

export function useDrag({ onDragStart, onDragEnd }: UseDragProps = {}) {
  const [isDragging, setIsDragging] = useState(false);
  const dragElementRef = useRef<HTMLElement | null>(null);
  const startPositionRef = useRef({ x: 0, y: 0 });
  const currentPositionRef = useRef({ x: 0, y: 0 });

  const handleMouseDown = (e: MouseEvent) => {
    if (!dragElementRef.current) return;
    
    setIsDragging(true);
    startPositionRef.current = { x: e.clientX, y: e.clientY };
    currentPositionRef.current = { x: e.clientX, y: e.clientY };
    
    if (onDragStart) onDragStart();
    
    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging || !dragElementRef.current) return;
    
    currentPositionRef.current = { x: e.clientX, y: e.clientY };
    
    const deltaX = currentPositionRef.current.x - startPositionRef.current.x;
    const deltaY = currentPositionRef.current.y - startPositionRef.current.y;
    
    dragElementRef.current.style.transform = `translate(${deltaX}px, ${deltaY}px)`;
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    
    if (onDragEnd) {
      // Determine if this was dropped on a valid target
      // This would need to be coordinated with the drop targets
      onDragEnd(false);
    }
    
    document.removeEventListener("mousemove", handleMouseMove);
    document.removeEventListener("mouseup", handleMouseUp);
    
    if (dragElementRef.current) {
      dragElementRef.current.style.transform = "";
    }
  };

  const dragHandleProps = {
    onMouseDown: (e: React.MouseEvent) => handleMouseDown(e.nativeEvent),
    style: { cursor: isDragging ? "grabbing" : "grab" }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, []);

  return {
    isDragging,
    dragElementRef,
    dragHandleProps
  };
}
