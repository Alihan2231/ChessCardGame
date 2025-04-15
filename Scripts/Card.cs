using UnityEngine;

public abstract class Card : ScriptableObject
{
    public string cardName;
    public string description;

    // Kartın oyuna etkisi
    public abstract void Apply(BoardManager board, int playerID);
}
