using System.Collections.Generic;
using UnityEngine;

public class CardManager : MonoBehaviour
{
    public List<Card> deck;
    public List<Card> hand;
    public int handSize = 3;

    void Start()
    {
        DrawHand();
    }

    public void DrawHand()
    {
        hand.Clear();
        for (int i = 0; i < handSize; i++)
        {
            if (deck.Count > 0)
            {
                Card c = deck[Random.Range(0, deck.Count)];
                hand.Add(c);
            }
        }
    }

    public void PlayCard(int index, BoardManager board, int playerID)
    {
        if (index >= 0 && index < hand.Count)
        {
            hand[index].Apply(board, playerID);
            hand.RemoveAt(index);
        }
    }
}
