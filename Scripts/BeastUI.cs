using UnityEngine;
using UnityEngine.UI;

public class BeastUI : MonoBehaviour
{
    public Slider healthBar;
    public Image portrait;
    public Text statsText;
    private BeastStatsComponent statsComp;

    void Start()
    {
        statsComp = GetComponent<BeastStatsComponent>();
        if (statsComp != null)
        {
            statsComp.onHealthChanged += UpdateHealthBar;
            UpdateHealthBar(statsComp.stats.currentHealth, statsComp.stats.maxHealth);
            UpdateStatsText();
        }
    }

    void UpdateHealthBar(int hp, int maxHp)
    {
        if (healthBar != null)
            healthBar.value = (float)hp / maxHp;
    }

    void UpdateStatsText()
    {
        if (statsText != null && statsComp != null)
        {
            statsText.text = $"POW: {statsComp.stats.basePower}  ARM: {statsComp.stats.armor}  SPD: {statsComp.stats.speed}";
        }
    }
}
