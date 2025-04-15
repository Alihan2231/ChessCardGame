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

    public void PlayCard(Card card, Beast targetBeast = null)
    {
        if (card == null)
        {
            Debug.LogError("Oynamak için geçerli bir kart seçilmedi!");
            return;
        }

        Debug.Log($"Playing card: {card.cardName}");

        // Kart tipi kontrolü
        switch (card.cardType)
        {
            case CardType.Attack:
                if (targetBeast == null)
                {
                    Debug.LogWarning("Saldırı kartı için hedef seçilmedi!");
                    return;
                }
                ApplyDamageCard(card, targetBeast);
                break;
            case CardType.DestroyTile:
                Tile targetTile = BoardManager.Instance.selectedTile;
                if (targetTile == null)
                {
                    Debug.LogWarning("Kare yok etme kartı için hedef seçilmedi!");
                    return;
                }
                DestroyTileCard destroyCard = card as DestroyTileCard;
                if (destroyCard != null)
                {
                    destroyCard.DestroyTile(targetTile);
                }
                break;
            // Diğer kart tipleri...
        }

        // Kartı elden çıkar
        RemoveCardFromHand(card);
        // Mezarlığa ekle
        GraveyardManager.Instance.AddCardToGraveyard(card);
        // UI'ı güncelle
        UpdateCardUI();
    }

    private void ApplyDamageCard(Card card, Beast targetBeast)
    {
        if (targetBeast == null) return;
        int damageAmount = card.value;
        targetBeast.TakeDamage(damageAmount);
        StartCoroutine(ShowDamageEffect(targetBeast.transform.position, damageAmount));
    }

    private System.Collections.IEnumerator ShowDamageEffect(Vector3 position, int damage)
    {
        GameObject damageText = new GameObject("DamageText");
        damageText.transform.position = position + Vector3.up;
        TextMesh textMesh = damageText.AddComponent<TextMesh>();
        textMesh.text = $"-{damage}";
        textMesh.color = Color.red;
        textMesh.fontSize = 20;
        float duration = 1.0f;
        float elapsed = 0f;
        while (elapsed < duration)
        {
            damageText.transform.position += Vector3.up * Time.deltaTime;
            elapsed += Time.deltaTime;
            yield return null;
        }
        Destroy(damageText);
    }
}
