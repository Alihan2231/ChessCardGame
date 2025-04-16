export type PieceType = "lion" | "eagle" | "wolf" | "bear" | "snake" | "fox";

export interface PieceData {
  svg: JSX.Element;
  name: string;
  description: string;
}

// Note: SVG content is included in the Piece component
