using UnityEngine;
using UnityEngine.UI;
using System.Collections.Generic;

public class GraveyardUI : MonoBehaviour
{
    public GameObject panel;
    public Transform contentRoot;
    public GameObject beastButtonPrefab;
    private int currentPlayerID;
    private System.Action<GameObject> onBeastSelected;

    public void Show(int playerID, System.Action<GameObject> onSelect)
    {
        currentPlayerID = playerID;
        onBeastSelected = onSelect;
        panel.SetActive(true);
        ClearContent();
        var graveyard = GraveyardManager.Instance.GetGraveyardList(playerID);
        foreach (var beast in graveyard)
        {
            var btnObj = Instantiate(beastButtonPrefab, contentRoot);
            var btn = btnObj.GetComponent<Button>();
            btn.onClick.AddListener(() => SelectBeast(beast));
            var txt = btnObj.GetComponentInChildren<Text>();
            if (txt != null) txt.text = beast.name;
        }
    }

    private void SelectBeast(GameObject beast)
    {
        panel.SetActive(false);
        onBeastSelected?.Invoke(beast);
    }

    private void ClearContent()
    {
        foreach (Transform child in contentRoot)
            Destroy(child.gameObject);
    }

    public void Hide()
    {
        panel.SetActive(false);
    }
}
