using UnityEngine;

public class Beast : MonoBehaviour
{
    public Vector2Int position;
    public int owner;
    public virtual bool CanMove(Vector2Int target, BoardManager board)
    {
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

// Ayı
public class BeastBear : Beast
{
    public override bool CanMove(Vector2Int target, BoardManager board)
    {
        int dx = Mathf.Abs(target.x - position.x);
        int dy = Mathf.Abs(target.y - position.y);
        return ((dx == 1 && dy == 0) || (dx == 0 && dy == 1)) && board.IsCellActive(target);
    }
}

// Aslan
public class BeastLion : Beast
{
    public override bool CanMove(Vector2Int target, BoardManager board)
    {
        int dx = Mathf.Abs(target.x - position.x);
        int dy = Mathf.Abs(target.y - position.y);
        return ((dx == 2 && dy == 0) || (dx == 0 && dy == 2)) && board.IsCellActive(target);
    }
}

// Yılan
public class BeastSnake : Beast
{
    public override bool CanMove(Vector2Int target, BoardManager board)
    {
        int dx = Mathf.Abs(target.x - position.x);
        int dy = Mathf.Abs(target.y - position.y);
        return (dx == 1 && dy == 1) && board.IsCellActive(target);
    }
}

// Kartal
public class BeastEagle : Beast
{
    public override bool CanMove(Vector2Int target, BoardManager board)
    {
        int dx = target.x - position.x;
        int dy = target.y - position.y;
        if ((dx == 0 || dy == 0) && (dx != 0 || dy != 0))
        {
            int stepX = dx == 0 ? 0 : (dx > 0 ? 1 : -1);
            int stepY = dy == 0 ? 0 : (dy > 0 ? 1 : -1);
            int x = position.x + stepX;
            int y = position.y + stepY;
            while (x != target.x || y != target.y)
            {
                if (!board.IsCellActive(new Vector2Int(x, y)))
                    return false;
                x += stepX;
                y += stepY;
            }
            return board.IsCellActive(target);
        }
        return false;
    }
}

// Kurbağa
public class BeastFrog : Beast
{
    public override bool CanMove(Vector2Int target, BoardManager board)
    {
        int dx = Mathf.Abs(target.x - position.x);
        int dy = Mathf.Abs(target.y - position.y);
        return ((dx == 2 && dy == 0) || (dx == 0 && dy == 2) || (dx == 2 && dy == 2)) && board.IsCellActive(target);
    }
}

// Kurt
public class BeastWolf : Beast
{
    public override bool CanMove(Vector2Int target, BoardManager board)
    {
        int dx = Mathf.Abs(target.x - position.x);
        int dy = Mathf.Abs(target.y - position.y);
        return ((dx == 1 && dy == 1) || (dx == 1 && dy == 0) || (dx == 0 && dy == 1)) && board.IsCellActive(target);
    }
}

// Ejderha
public class BeastDragon : Beast
{
    public override bool CanMove(Vector2Int target, BoardManager board)
    {
        int dx = Mathf.Abs(target.x - position.x);
        int dy = Mathf.Abs(target.y - position.y);
        if ((dx == dy || dx == 0 || dy == 0) && (dx <= 3 && dy <= 3) && (dx != 0 || dy != 0))
        {
            int stepX = dx == 0 ? 0 : (target.x - position.x) / dx;
            int stepY = dy == 0 ? 0 : (target.y - position.y) / dy;
            int x = position.x + stepX;
            int y = position.y + stepY;
            while (x != target.x || y != target.y)
            {
                if (!board.IsCellActive(new Vector2Int(x, y)))
                    return false;
                x += stepX;
                y += stepY;
            }
            return board.IsCellActive(target);
        }
        return false;
    }
}
