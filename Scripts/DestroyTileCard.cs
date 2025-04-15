using UnityEngine;
using System.Collections.Generic;

[CreateAssetMenu(menuName = "Cards/DestroyTileCard")]
public class DestroyTileCard : Card
{
    public override void Apply(BoardManager board, int playerID)
    {
        // Rastgele bir aktif kareyi yok et
        var activeCells = new List<Vector2Int>();
        for (int x = 0; x < board.boardSize; x++)
            for (int y = 0; y < board.boardSize; y++)
                if (board.IsCellActive(new Vector2Int(x, y)))
                    activeCells.Add(new Vector2Int(x, y));
        if (activeCells.Count > 0)
        {
            var pos = activeCells[Random.Range(0, activeCells.Count)];
            board.tiles[pos.x, pos.y].SetActive(false);
        }
    }
}
