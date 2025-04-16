export type CardType = "attack" | "defense" | "special";

export interface Card {
  id: string;
  name: string;
  type: CardType;
  cost: number;
  description: string;
}

export const allCards: Card[] = [
  {
    id: "attack1",
    name: "Fierce Strike",
    type: "attack",
    cost: 2,
    description: "Deal 5 damage to a random enemy creature."
  },
  {
    id: "attack2",
    name: "Wild Roar",
    type: "attack",
    cost: 4,
    description: "Deal 3 damage to all enemy creatures."
  },
  {
    id: "attack3",
    name: "Sneak Attack",
    type: "attack",
    cost: 1,
    description: "Deal 3 damage to the weakest enemy creature."
  },
  {
    id: "attack4",
    name: "Venomous Bite",
    type: "attack",
    cost: 3,
    description: "Deal 6 damage to a single enemy creature."
  },
  {
    id: "defense1",
    name: "Healing Rain",
    type: "defense",
    cost: 3,
    description: "Restore 3 health to all your creatures."
  },
  {
    id: "defense2",
    name: "Lion's Pride",
    type: "defense",
    cost: 4,
    description: "Restore 10 health to your Lion."
  },
  {
    id: "defense3",
    name: "Natural Armor",
    type: "defense",
    cost: 2,
    description: "Your Bear gains 5 health."
  },
  {
    id: "defense4",
    name: "Swift Evasion",
    type: "defense",
    cost: 1,
    description: "Your Fox can move an extra space this turn."
  },
  {
    id: "special1",
    name: "Energy Surge",
    type: "special",
    cost: 2,
    description: "Gain 3 energy crystals."
  },
  {
    id: "special2",
    name: "Feral Rage",
    type: "special",
    cost: 3,
    description: "All your creatures deal 2 more damage this turn."
  },
  {
    id: "special3",
    name: "Forest Blessing",
    type: "special",
    cost: 2,
    description: "Heal all your creatures that are below half health."
  },
  {
    id: "special4",
    name: "Strategic Retreat",
    type: "special",
    cost: 3,
    description: "Move one of your creatures to any empty space on the board."
  }
];
