using UnityEngine;

public class BeastDeathHandler : MonoBehaviour
{
    private BeastStatsComponent statsComp;
    private Animator animator;
    private bool isDead = false;

    void Start()
    {
        statsComp = GetComponent<BeastStatsComponent>();
        animator = GetComponent<Animator>();
        if (statsComp != null)
            statsComp.onHealthChanged += OnHealthChanged;
    }

    void OnHealthChanged(int hp, int maxHp)
    {
        if (!isDead && hp <= 0)
        {
            isDead = true;
            if (animator != null)
                animator.SetTrigger("Die");
            // Ölüm animasyonu yoksa hemen yok et
            else
                Destroy(gameObject);
        }
    }

    // Animasyon eventinden çağrılır
    public void OnDeathAnimationEnd()
    {
        Destroy(gameObject);
    }
}
