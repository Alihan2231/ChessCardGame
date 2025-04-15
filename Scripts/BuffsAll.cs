using UnityEngine;
using System.Collections.Generic;

public enum BuffType { Power, Range, Shield, Poison, Heal, Custom }

public class BuffData {
    public BuffType type;
    public int value;
    public int duration;
    public Color color;
    public BuffData(BuffType type, int value, int duration, Color color)
    {
        this.type = type;
        this.value = value;
        this.duration = duration;
        this.color = color;
    }
}

public class BuffSystem : MonoBehaviour
{
    private List<BuffData> activeBuffs = new List<BuffData>();
    private Beast beast;
    private Renderer rend;

    void Awake()
    {
        beast = GetComponent<Beast>();
        rend = GetComponent<Renderer>();
    }

    public void AddBuff(BuffData buff)
    {
        activeBuffs.Add(buff);
        UpdateVisuals();
    }

    public void OnTurnPassed()
    {
        for (int i = activeBuffs.Count - 1; i >= 0; i--)
        {
            activeBuffs[i].duration--;
            if (activeBuffs[i].duration <= 0)
                activeBuffs.RemoveAt(i);
        }
        UpdateVisuals();
    }

    public int GetBuffValue(BuffType type)
    {
        int sum = 0;
        foreach (var buff in activeBuffs)
            if (buff.type == type)
                sum += buff.value;
        return sum;
    }

    private void UpdateVisuals()
    {
        if (activeBuffs.Count > 0)
        {
            Color c = Color.white;
            foreach (var b in activeBuffs) c += b.color;
            c /= (activeBuffs.Count + 1);
            rend.material.color = c;
        }
        else
        {
            rend.material.color = Color.white;
        }
    }
}

public class TempBuff : MonoBehaviour
{
    public int duration = 3;
    private int turnsLeft;

    void Start()
    {
        turnsLeft = duration;
        GetComponent<Renderer>().material.color = Color.yellow;
    }

    public void OnTurnPassed()
    {
        turnsLeft--;
        if (turnsLeft <= 0)
        {
            GetComponent<Renderer>().material.color = Color.white;
            Destroy(this);
        }
    }
}
