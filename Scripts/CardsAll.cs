using UnityEngine;

public abstract class Card : ScriptableObject
{
    public string cardName;
    public string description;
    public abstract void Apply(BoardManager board, int playerID);
}

[CreateAssetMenu(menuName = "Cards/AreaHealCard")]
public class CardAreaHeal : Card
{
    public int healAmount = 2;
    public override void Apply(BoardManager board, int playerID)
    {
        var beasts = GameObject.FindObjectsOfType<Beast>();
        foreach (var beast in beasts)
        {
            if (beast.owner == playerID)
            {
                var buffSys = beast.GetComponent<BuffSystem>();
                if (buffSys == null)
                    buffSys = beast.gameObject.AddComponent<BuffSystem>();
                buffSys.AddBuff(new BuffData(BuffType.Heal, healAmount, 1, Color.green));
            }
        }
    }
}

[CreateAssetMenu(menuName = "Cards/BearRageCard")]
public class CardBearRage : Card
{
    public int powerBuff = 2;
    public int duration = 2;
    public Color rageColor = Color.red;
    public override void Apply(BoardManager board, int playerID)
    {
        var beasts = GameObject.FindObjectsOfType<BeastBear>();
        foreach (var bear in beasts)
        {
            if (bear.owner == playerID)
            {
                var buffSys = bear.GetComponent<BuffSystem>();
                if (buffSys == null)
                    buffSys = bear.gameObject.AddComponent<BuffSystem>();
                buffSys.AddBuff(new BuffData(BuffType.Power, powerBuff, duration, rageColor));
            }
        }
    }
}

[CreateAssetMenu(menuName = "Cards/AdvancedBuffCard")]
public class CardBuffAdvanced : Card
{
    public BuffType buffType = BuffType.Power;
    public int buffValue = 1;
    public int duration = 3;
    public Color buffColor = Color.cyan;
    public override void Apply(BoardManager board, int playerID)
    {
        var beasts = GameObject.FindObjectsOfType<Beast>();
        foreach (var beast in beasts)
        {
            if (beast.owner == playerID)
            {
                var buffSys = beast.GetComponent<BuffSystem>();
                if (buffSys == null)
                    buffSys = beast.gameObject.AddComponent<BuffSystem>();
                buffSys.AddBuff(new BuffData(buffType, buffValue, duration, buffColor));
            }
        }
    }
}

[CreateAssetMenu(menuName = "Cards/BuffBeastCard")]
public class CardBuffBeast : Card
{
    public int buffAmount = 1;
    public override void Apply(BoardManager board, int playerID)
    {
        var beasts = GameObject.FindObjectsOfType<Beast>();
        foreach (var beast in beasts)
        {
            if (beast.owner == playerID)
            {
                beast.gameObject.AddComponent<TempBuff>();
            }
        }
    }
}

[CreateAssetMenu(menuName = "Cards/DealDamageCard")]
public class CardDealDamage : Card
{
    public int damage = 2;
    public override void Apply(BoardManager board, int playerID)
    {
        var beasts = GameObject.FindObjectsOfType<Beast>();
        var enemyBeasts = new System.Collections.Generic.List<Beast>();
        foreach (var beast in beasts)
            if (beast.owner != playerID)
                enemyBeasts.Add(beast);
        if (enemyBeasts.Count == 0) return;
        var target = enemyBeasts[Random.Range(0, enemyBeasts.Count)];
        var stats = target.GetComponent<BeastStatsComponent>();
        if (stats != null)
            stats.TakeDamage(damage);
    }
}

[CreateAssetMenu(menuName = "Cards/ResurrectChooseCard")]
public class CardResurrectChoose : Card
{
    public override void Apply(BoardManager board, int playerID)
    {
        var graveyard = GraveyardManager.Instance;
        if (graveyard == null || graveyard.GetCount(playerID) == 0) return;
        var beastPrefab = graveyard.PeekFirstBeast(playerID);
        var activeCells = new System.Collections.Generic.List<Vector2Int>();
        for (int x = 0; x < board.width; x++)
            for (int y = 0; y < board.height; y++)
                if (board.IsTileEmpty(x, y) && board.IsCellActive(new Vector2Int(x, y)))
                    activeCells.Add(new Vector2Int(x, y));
        if (activeCells.Count == 0) return;
        var pos = activeCells[Random.Range(0, activeCells.Count)];
        GameObject beastObj = GameObject.Instantiate(beastPrefab, new Vector3(pos.x, 0.5f, pos.y), Quaternion.identity, board.transform);
        graveyard.RemoveBeast(playerID, beastPrefab);
    }
}

[CreateAssetMenu(menuName = "Cards/ReviveBeastCard")]
public class CardReviveBeast : Card
{
    public override void Apply(BoardManager board, int playerID)
    {
        var graveyard = GraveyardManager.Instance;
        if (graveyard == null || graveyard.GetCount(playerID) == 0) return;
        var beastPrefab = graveyard.GetRandomBeast(playerID);
        var activeCells = new System.Collections.Generic.List<Vector2Int>();
        for (int x = 0; x < board.width; x++)
            for (int y = 0; y < board.height; y++)
                if (board.IsTileEmpty(x, y) && board.IsCellActive(new Vector2Int(x, y)))
                    activeCells.Add(new Vector2Int(x, y));
        if (activeCells.Count == 0) return;
        var pos = activeCells[Random.Range(0, activeCells.Count)];
        GameObject beastObj = GameObject.Instantiate(beastPrefab, new Vector3(pos.x, 0.5f, pos.y), Quaternion.identity, board.transform);
    }
}

[CreateAssetMenu(menuName = "Cards/TeleportBeastCard")]
public class CardTeleportBeast : Card
{
    public override void Apply(BoardManager board, int playerID)
    {
        var beasts = GameObject.FindObjectsOfType<Beast>();
        var ownBeasts = new System.Collections.Generic.List<Beast>();
        foreach (var beast in beasts)
            if (beast.owner == playerID)
                ownBeasts.Add(beast);
        if (ownBeasts.Count == 0) return;
        var beastToTeleport = ownBeasts[Random.Range(0, ownBeasts.Count)];
        var activeCells = new System.Collections.Generic.List<Vector2Int>();
        for (int x = 0; x < board.width; x++)
            for (int y = 0; y < board.height; y++)
                if (board.IsCellActive(new Vector2Int(x, y)))
                    activeCells.Add(new Vector2Int(x, y));
        if (activeCells.Count == 0) return;
        var newPos = activeCells[Random.Range(0, activeCells.Count)];
        beastToTeleport.Move(newPos, board);
    }
}
