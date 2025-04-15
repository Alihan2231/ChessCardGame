using UnityEngine;
using System.Collections.Generic;

public class GraveyardManager : MonoBehaviour
{
    public static GraveyardManager Instance;
    private Dictionary<int, List<GameObject>> graveyard = new Dictionary<int, List<GameObject>>();
    public IReadOnlyList<GameObject> GetGraveyardList(int owner)
    {
        if (!graveyard.ContainsKey(owner))
            graveyard[owner] = new List<GameObject>();
        return graveyard[owner].AsReadOnly();
    }

    void Awake()
    {
        if (Instance == null) Instance = this;
        else Destroy(gameObject);
        graveyard[0] = new List<GameObject>();
        graveyard[1] = new List<GameObject>();
    }

    public void AddToGraveyard(GameObject beast, int owner)
    {
        if (!graveyard.ContainsKey(owner))
            graveyard[owner] = new List<GameObject>();
        graveyard[owner].Add(beast);
    }

    public GameObject GetRandomBeast(int owner)
    {
        if (!graveyard.ContainsKey(owner) || graveyard[owner].Count == 0) return null;
        var list = graveyard[owner];
        int idx = Random.Range(0, list.Count);
        var prefab = list[idx];
        list.RemoveAt(idx);
        return prefab;
    }

    // UI ile seçim için: ilk taşı döndür (veya index ile seçilebilir)
    public GameObject PeekFirstBeast(int owner)
    {
        if (!graveyard.ContainsKey(owner) || graveyard[owner].Count == 0) return null;
        return graveyard[owner][0];
    }

    public void RemoveBeast(int owner, GameObject beast)
    {
        if (!graveyard.ContainsKey(owner)) return;
        graveyard[owner].Remove(beast);
    }

    public int GetCount(int owner) => graveyard[owner].Count;
}
