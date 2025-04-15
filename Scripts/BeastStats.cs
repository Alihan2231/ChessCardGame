using UnityEngine;

[System.Serializable]
public class BeastStats {
    public int maxHealth = 5;
    public int currentHealth = 5;
    public int basePower = 1;
    public int baseRange = 1;
    public int armor = 0;
    public int speed = 1;
    public int critChance = 0;
    public int dodgeChance = 0;
    public int poison = 0;
    public int shield = 0;
    public int healPerTurn = 0;
}

public class BeastStatsComponent : MonoBehaviour
{
    public BeastStats stats = new BeastStats();
    public delegate void OnHealthChanged(int newHP, int maxHP);
    public event OnHealthChanged onHealthChanged;

    public void TakeDamage(int amount)
    {
        int dmg = Mathf.Max(0, amount - stats.armor - stats.shield);
        stats.currentHealth -= dmg;
        if (stats.currentHealth < 0) stats.currentHealth = 0;
        if (onHealthChanged != null) onHealthChanged(stats.currentHealth, stats.maxHealth);
    }

    public void Heal(int amount)
    {
        stats.currentHealth = Mathf.Min(stats.maxHealth, stats.currentHealth + amount);
        if (onHealthChanged != null) onHealthChanged(stats.currentHealth, stats.maxHealth);
    }

    public void ApplyPoison(int amount)
    {
        stats.poison += amount;
    }

    public void OnTurnPassed()
    {
        if (stats.poison > 0)
        {
            TakeDamage(stats.poison);
        }
        if (stats.healPerTurn > 0)
        {
            Heal(stats.healPerTurn);
        }
    }
}
