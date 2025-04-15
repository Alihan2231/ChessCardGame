using UnityEngine;

public class Beast : MonoBehaviour
{
    public Vector2Int position;
    public int owner; // 0 veya 1

    public void Init(Vector2Int pos, int ownerID)
    {
        position = pos;
        owner = ownerID;
    }

    // Hareket fonksiyonu örneği (detaylandırılabilir)
    public virtual bool CanMove(Vector2Int target, BoardManager board)
    {
        // Temel hareket kuralları burada olacak
        return board.IsCellActive(target);
    }

    public void Move(Vector2Int target, BoardManager board)
    {
        if (CanMove(target, board))
        {
            position = target;
            transform.position = new Vector3(target.x, 0.5f, target.y);
        }
    }
}
