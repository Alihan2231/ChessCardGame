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

    public Tile currentTile;
    private bool isMoving = false;

    public void MoveToPosition(Tile targetTile)
    {
        if (targetTile == null || !targetTile.isActive)
            return;

        // Önceki karenin referansını temizle
        if (currentTile != null)
            currentTile.currentBeast = null;

        // Yeni kareye yerleş
        currentTile = targetTile;
        currentTile.currentBeast = this;

        // Yumuşak hareket animasyonu
        StartCoroutine(SmoothMovement(targetTile.transform.position));
    }

    private System.Collections.IEnumerator SmoothMovement(Vector3 targetPosition)
    {
        isMoving = true;
        targetPosition.y = transform.position.y;
        float sqrRemainingDistance = (transform.position - targetPosition).sqrMagnitude;
        float moveSpeed = 5f;
        while (sqrRemainingDistance > float.Epsilon)
        {
            Vector3 newPosition = Vector3.MoveTowards(transform.position, targetPosition, moveSpeed * Time.deltaTime);
            transform.position = newPosition;
            sqrRemainingDistance = (transform.position - targetPosition).sqrMagnitude;
            yield return null;
        }
        transform.position = targetPosition;
        isMoving = false;
    }
}
