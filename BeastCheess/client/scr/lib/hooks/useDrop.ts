import { useState, useRef, useEffect } from "react";

interface UseDropProps {
  onDrop?: (item: any) => void;
  accept?: string[];
}

export function useDrop({ onDrop, accept = [] }: UseDropProps = {}) {
  const [isOver, setIsOver] = useState(false);
  const dropTargetRef = useRef<HTMLElement | null>(null);

  const isAccepted = (type: string) => {
    return accept.length === 0 || accept.includes(type);
  };

  const handleDragEnter = (e: DragEvent) => {
    e.preventDefault();
    
    // Check if the dragged item is of an accepted type
    const itemType = e.dataTransfer?.types.find(type => isAccepted(type));
    if (!itemType) return;
    
    setIsOver(true);
  };

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    
    // Prevent default to allow drop
    if (isOver) {
      e.dataTransfer!.dropEffect = "move";
    }
  };

  const handleDragLeave = (e: DragEvent) => {
    // Only count as a leave if moving outside the target
    if (dropTargetRef.current && !dropTargetRef.current.contains(e.relatedTarget as Node)) {
      setIsOver(false);
    }
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    
    setIsOver(false);
    
    // Get the data that was transferred
    const itemType = e.dataTransfer?.types.find(type => isAccepted(type));
    if (!itemType) return;
    
    const data = e.dataTransfer?.getData(itemType);
    if (!data) return;
    
    // Call the onDrop callback with the data
    if (onDrop) {
      try {
        const parsedData = JSON.parse(data);
        onDrop(parsedData);
      } catch (err) {
        onDrop(data);
      }
    }
  };

  useEffect(() => {
    const element = dropTargetRef.current;
    if (!element) return;
    
    element.addEventListener("dragenter", handleDragEnter);
    element.addEventListener("dragover", handleDragOver);
    element.addEventListener("dragleave", handleDragLeave);
    element.addEventListener("drop", handleDrop);
    
    return () => {
      element.removeEventListener("dragenter", handleDragEnter);
      element.removeEventListener("dragover", handleDragOver);
      element.removeEventListener("dragleave", handleDragLeave);
      element.removeEventListener("drop", handleDrop);
    };
  }, [isOver, onDrop, accept]);

  return {
    isOver,
    dropTargetRef
  };
}
