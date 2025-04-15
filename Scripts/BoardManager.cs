using UnityEngine;
using System.Collections;
using System.Collections.Generic;

/// <summary>
/// BoardManager: Stratejik ve animasyonlu alan daralması, event/buff yönetimi ve gelişmiş board kontrolü sağlar.
/// </summary>
public enum ShrinkPattern
{
    OuterRing, // Klasik dış katman
    Corners,   // Sadece köşeler
    Spiral,    // Spiral şeklinde
    Random     // Rastgele tile'lar
}

/// <summary>
/// BoardManager: Stratejik ve animasyonlu alan daralması, event/buff yönetimi ve gelişmiş board kontrolü sağlar.
/// </summary>
public enum ShrinkPattern
{
    OuterRing, // Klasik dış katman
    Corners,   // Sadece köşeler
    Spiral,    // Spiral şeklinde
    Random     // Rastgele tile'lar
}

public class BoardManager : MonoBehaviour
{
    public int width = 8;
    public int height = 8;
    public GameObject tilePrefab;
    public GameObject piecePrefab;
    private GameObject[,] tiles;
    private List<GameObject> activeTiles = new List<GameObject>();
    [Header("Enemy Prefabs (çeşitli düşmanlar için)")]
    public List<GameObject> enemyPrefabs;
    [Header("Düşman Zorluk Katsayısı")]
    public float enemyDifficulty = 1f; // LevelData'dan alınır, AI veya stat çarpanı olarak kullanılır
    [Header("Effect Prefabs (sis, yıldırım, bataklık, vs.)")]
    public List<GameObject> effectPrefabs;

    [Header("Alan Daralması Ayarları")]
    public ShrinkPattern shrinkPattern = ShrinkPattern.OuterRing;
    public int shrinkLayer = 0; // Spiral için

    /// <summary>
    /// Kapanacak tile'ları daralma desenine göre belirler.
    /// </summary>
    public List<Tile> GetTilesToShrink()
    {
        List<Tile> closingTiles = new List<Tile>();
        switch (shrinkPattern)
        {
            case ShrinkPattern.OuterRing:
                for (int x = 0; x < width; x++)
                {
                    if (tiles[x, 0] != null) closingTiles.Add(tiles[x, 0].GetComponent<Tile>());
                    if (tiles[x, height - 1] != null) closingTiles.Add(tiles[x, height - 1].GetComponent<Tile>());
                }
                for (int y = 1; y < height - 1; y++)
                {
                    if (tiles[0, y] != null) closingTiles.Add(tiles[0, y].GetComponent<Tile>());
                    if (tiles[width - 1, y] != null) closingTiles.Add(tiles[width - 1, y].GetComponent<Tile>());
                }
                break;
            case ShrinkPattern.Corners:
                closingTiles.Add(tiles[0, 0].GetComponent<Tile>());
                closingTiles.Add(tiles[0, height - 1].GetComponent<Tile>());
                closingTiles.Add(tiles[width - 1, 0].GetComponent<Tile>());
                closingTiles.Add(tiles[width - 1, height - 1].GetComponent<Tile>());
                break;
            case ShrinkPattern.Spiral:
                int layer = shrinkLayer;
                for (int x = layer; x < width - layer; x++)
                {
                    if (tiles[x, layer] != null) closingTiles.Add(tiles[x, layer].GetComponent<Tile>());
                    if (tiles[x, height - layer - 1] != null) closingTiles.Add(tiles[x, height - layer - 1].GetComponent<Tile>());
                }
                for (int y = layer + 1; y < height - layer - 1; y++)
                {
                    if (tiles[layer, y] != null) closingTiles.Add(tiles[layer, y].GetComponent<Tile>());
                    if (tiles[width - layer - 1, y] != null) closingTiles.Add(tiles[width - layer - 1, y].GetComponent<Tile>());
                }
                break;
            case ShrinkPattern.Random:
                List<Tile> allActive = GetAllActiveTiles();
                int n = Mathf.Min(6, allActive.Count);
                for (int i = 0; i < n; i++)
                {
                    var t = allActive[Random.Range(0, allActive.Count)];
                    closingTiles.Add(t);
                    allActive.Remove(t);
                }
                break;
        }
        return closingTiles;
    }

    /// <summary>
    /// Alan daralmasını başlatır, animasyon ve buff/event tetikler.
    /// </summary>
    public void TriggerShrink()
    {
        FeedbackManager.Instance?.ShowMessage("Alan Daralıyor!", FeedbackManager.Instance?.areaShrinkClip);
        List<Tile> closingTiles = GetTilesToShrink();
        AnimateClosingWave(closingTiles);
        // Kapanacak tile'ların üstündeki taşlara buff/debuff veya event uygula
        foreach (var tile in closingTiles)
        {
            Piece p = GetPieceAt(tile.x, tile.y);
            if (p != null)
            {
                // Örnek: Taşa debuff uygula veya event tetikle
                p.ApplyDebuff(DebuffType.Stun, 1);
                // veya tile.PlayTileEffect(TileEffectType.Lightning);
            }
        }
        // Board'un aktif alanını güncelle (kapanan tile'ları devre dışı bırak)
        foreach (var tile in closingTiles)
            tile.isActive = false;
    }

    [Header("Alan Daralması Ayarları")]
    public ShrinkPattern shrinkPattern = ShrinkPattern.OuterRing;
    public int shrinkLayer = 0; // Spiral için

    void Start()
    {
        GenerateBoard();
        SpawnPieces();
        shrinkCounter = shrinkEveryXMoves;
        if (GameManager.Instance != null)
            GameManager.Instance.UpdateShrinkCounter(shrinkCounter);
    }

    // --- DALGA DALGA ALAN DARALMASI ve EVENT ENTEGRASYONU ---
    /// <summary>
    /// Alan daralmasında dış katmandaki tile'ları sırayla (dalga gibi) önce danger efektiyle uyarır, sonra dalga dalga kapatır.
    /// </summary>
    public void AnimateClosingWave(List<Tile> closingTiles, float dangerWaveDelay = 0.06f, float closeWaveDelay = 0.08f)
    {
        StartCoroutine(DangerAndCloseWave(closingTiles, dangerWaveDelay, closeWaveDelay));
    }
    private IEnumerator DangerAndCloseWave(List<Tile> closingTiles, float dangerWaveDelay, float closeWaveDelay)
    {
        // 1. Danger alarm dalgası
        foreach (var tile in closingTiles)
        {
            tile.SetVisualState(TileVisualState.Danger);
            yield return new WaitForSeconds(dangerWaveDelay);
        }
        yield return new WaitForSeconds(0.6f);
        // 2. Dalga dalga kapanma
        foreach (var tile in closingTiles)
        {
            tile.SetVisualState(TileVisualState.Closing);
            yield return new WaitForSeconds(closeWaveDelay);
        }
    }

    /// <summary>
    /// Zar/event ile toplu tile efektleri (ör: yıldırım dalgası)
    /// </summary>
    public void AnimateEventWave(List<Tile> targetTiles, TileEffectType effectType, float waveDelay = 0.07f)
    {
        StartCoroutine(EventWave(targetTiles, effectType, waveDelay));
    }
    private IEnumerator EventWave(List<Tile> targetTiles, TileEffectType effectType, float waveDelay)
    {
        foreach (var tile in targetTiles)
        {
            tile.PlayTileEffect(effectType);
            yield return new WaitForSeconds(waveDelay);
        }
    }


    // --- Satranç yardımcı fonksiyonları ---
    public bool IsTileEmpty(int x, int y)
    {
        if (!IsInBounds(x, y)) return false;
        return GetPieceAt(x, y) == null && tiles[x, y] != null && tiles[x, y].activeSelf;
    }

    public bool IsEnemyAt(int x, int y, bool isWhite)
    {
        if (!IsInBounds(x, y)) return false;
        Piece p = GetPieceAt(x, y);
        return p != null && p.isWhite != isWhite;
    }

    public Piece GetPieceAt(int x, int y)
    {
        foreach (Piece p in FindObjectsOfType<Piece>())
        {
            if (p.x == x && p.y == y)
                return p;
        }
        return null;
    }

    public Vector3 GetTilePosition(int x, int y)
    {
        if (!IsInBounds(x, y)) return Vector3.zero;
        return tiles[x, y].transform.position;
    }

    public bool IsInBounds(int x, int y)
    {
        return x >= 0 && x < width && y >= 0 && y < height && tiles[x, y] != null && tiles[x, y].activeSelf;
    }

    // Doğrusal (kale, fil, vezir) hareketler için
    public List<Vector2Int> GetLinearMoves(int x, int y, bool isWhite, bool straight, bool diagonal)
    {
        List<Vector2Int> moves = new List<Vector2Int>();
        int[] dx = { 1, -1, 0, 0, 1, 1, -1, -1 };
        int[] dy = { 0, 0, 1, -1, 1, -1, 1, -1 };
        for (int dir = 0; dir < 8; dir++)
        {
            if ((dir < 4 && straight) || (dir >= 4 && diagonal))
            {
                int nx = x + dx[dir];
                int ny = y + dy[dir];
                while (IsInBounds(nx, ny))
                {
                    Piece p = GetPieceAt(nx, ny);
                    if (p == null)
                        moves.Add(new Vector2Int(nx, ny));
                    else
                    {
                        if (p.isWhite != isWhite)
                            moves.Add(new Vector2Int(nx, ny));
                        break;
                    }
                    nx += dx[dir];
                    ny += dy[dir];
                }
            }
        }
        return moves;
    }

    // Şah hareketleri
    public List<Vector2Int> GetKingMoves(int x, int y, bool isWhite)
    {
        List<Vector2Int> moves = new List<Vector2Int>();
        int[] dx = { 1, 1, 1, 0, 0, -1, -1, -1 };
        int[] dy = { 1, 0, -1, 1, -1, 1, 0, -1 };
        for (int i = 0; i < 8; i++)
        {
            int nx = x + dx[i];
            int ny = y + dy[i];
            if (IsInBounds(nx, ny))
            {
                Piece p = GetPieceAt(nx, ny);
                if (p == null || p.isWhite != isWhite)
                    moves.Add(new Vector2Int(nx, ny));
            }
        }
        return moves;
    }

    // At hareketleri
    public List<Vector2Int> GetKnightMoves(int x, int y, bool isWhite)
    {
        List<Vector2Int> moves = new List<Vector2Int>();
        int[] dx = { 1, 2, 2, 1, -1, -2, -2, -1 };
        int[] dy = { 2, 1, -1, -2, -2, -1, 1, 2 };
        for (int i = 0; i < 8; i++)
        {
            int nx = x + dx[i];
            int ny = y + dy[i];
            if (IsInBounds(nx, ny))
            {
                Piece p = GetPieceAt(nx, ny);
                if (p == null || p.isWhite != isWhite)
                    moves.Add(new Vector2Int(nx, ny));
            }
        }
        return moves;
    }

    // Hareket sonrası event (ör: zar atma, alan daralması, yetenek tetikleme)
    [Header("Alan Daralması Ayarları")]
    public int shrinkEveryXMoves = 3;
    private int shrinkCounter;

    public void OnPieceMoved(Piece piece)
    {
        // Her hamlede sayaç azaltılır, sıfırlanırsa alan daralır
        shrinkCounter--;
        GameManager.Instance.UpdateShrinkCounter(shrinkCounter);
        if (shrinkCounter <= 0)
        {
            ShrinkArea();
            shrinkCounter = shrinkEveryXMoves;
            GameManager.Instance.UpdateShrinkCounter(shrinkCounter, true); // true: animasyon/uyarı göster
        }
        Debug.Log($"Taş hareket etti: {piece.characterName} ({piece.x},{piece.y})");
    }

    void Start()
    {
        GenerateBoard();
        SpawnPieces();
        shrinkCounter = shrinkEveryXMoves;
        if (GameManager.Instance != null)
            GameManager.Instance.UpdateShrinkCounter(shrinkCounter);
    }

    // --- Taş seçimi ve highlight altyapısı ---
    public Piece selectedPiece;
    public List<GameObject> highlightTiles = new List<GameObject>();
    public GameObject highlightPrefab;

    [Header("Yetenek UI")]
    public UnityEngine.UI.Text abilityNameText;
    public UnityEngine.UI.Text abilityDescText;
    public UnityEngine.UI.Text abilityCooldownText;
    public UnityEngine.UI.Button abilityButton;

    public void SelectPiece(Piece piece)
    {
        selectedPiece = piece;
        ClearHighlights();
        List<Vector2Int> moves = piece.GetValidMoves();
        foreach (var move in moves)
        {
            if (IsInBounds(move.x, move.y))
            {
                GameObject highlight = Instantiate(highlightPrefab, tiles[move.x, move.y].transform.position, Quaternion.identity);
                highlightTiles.Add(highlight);
            }
        }
        UpdateAbilityUI(piece);
    }

    public void UpdateAbilityUI(Piece piece)
    {
        if (abilityNameText != null) abilityNameText.text = piece.abilityName;
        if (abilityDescText != null) abilityDescText.text = piece.abilityDescription;
        if (abilityCooldownText != null)
        {
            if (piece.CanUseAbility())
                abilityCooldownText.text = "Hazır";
            else
                abilityCooldownText.text = $"Bekleme: {piece.abilityCooldownTimer:F1}s";
        }
        if (abilityButton != null)
        {
            abilityButton.interactable = piece.CanUseAbility();
            abilityButton.onClick.RemoveAllListeners();
            abilityButton.onClick.AddListener(() => piece.UseAbility());
        }
    }

    public void ClearHighlights()
    {
        foreach (var obj in highlightTiles)
            Destroy(obj);
        highlightTiles.Clear();
    }

    void Update()
    {
        // Hotkey ile yetenek kullanımı (Q tuşu)
        if (selectedPiece != null && Input.GetKeyDown(KeyCode.Q))
        {
            selectedPiece.UseAbility();
        }
    }

    void GenerateBoard()
    {
        tiles = new GameObject[width, height];
        for (int x = 0; x < width; x++)
        {
            for (int y = 0; y < height; y++)
            {
                Vector3 pos = new Vector3(x + y * 0.5f, y * 0.866f, 0); // izometrik görünüm için
                GameObject tile = Instantiate(tilePrefab, pos, Quaternion.identity, transform);
                tile.name = $"Tile_{x}_{y}";
                tiles[x, y] = tile;
                Tile tileScript = tile.GetComponent<Tile>();
                if (tileScript != null)
                {
                    tileScript.SetCoords(x, y);
                    tileScript.SetActive(true, instant: true);
                }
            }
        }
    }

    void SpawnPieces()
    {
        // Satranç dizilimine uygun şekilde taşları yerleştir
        // 1. sıra (arka sıra)
        PieceType[] backRow = new PieceType[] {
            PieceType.Rook, PieceType.Knight, PieceType.Bishop, PieceType.Queen, PieceType.King, PieceType.Bishop, PieceType.Knight, PieceType.Rook
        };
        for (int x = 0; x < width; x++)
        {
            // Arka sıra
            Vector3 posBack = tiles[x, 0].transform.position;
            GameObject pieceBack = Instantiate(piecePrefab, posBack, Quaternion.identity);
            Piece pieceScriptBack = pieceBack.GetComponent<Piece>();
            pieceScriptBack.SetPosition(x, 0);
            pieceScriptBack.SetPiece(backRow[x]);

            // Piyonlar
            Vector3 posPawn = tiles[x, 1].transform.position;
            GameObject piecePawn = Instantiate(piecePrefab, posPawn, Quaternion.identity);
            Piece pieceScriptPawn = piecePawn.GetComponent<Piece>();
            pieceScriptPawn.SetPosition(x, 1);
            pieceScriptPawn.SetPiece(PieceType.Pawn);
        }
    }

    // Zar sonucu: Alan daraltma
    public void ShrinkArea()
    {
        // En dış katmanı devre dışı bırak ve üstündeki taşları yok et, fade animasyonu ile
        int min = 0;
        int maxX = width - 1;
        int maxY = height - 1;
        bool shrinked = false;
        for (int x = 0; x < width; x++)
        {
            for (int y = 0; y < height; y++)
            {
                if (x == min || x == maxX || y == min || y == maxY)
                {
                    if (tiles[x, y] != null && tiles[x, y].activeSelf)
                    {
                        // O tile'ın üstünde taş varsa yok et
                        Collider2D[] hits = Physics2D.OverlapCircleAll(tiles[x, y].transform.position, 0.1f);
                        foreach (var hit in hits)
                        {
                            Piece piece = hit.GetComponent<Piece>();
                            if (piece != null)
                            {
                                // Yok edilme efekti tetiklenebilir
                                Destroy(piece.gameObject);
                            }
                        }
                        Tile tileScript = tiles[x, y].GetComponent<Tile>();
                        if (tileScript != null)
                            tileScript.SetActive(false, instant: false); // fade animasyonu
                        else
                            tiles[x, y].SetActive(false);
                        shrinked = true;
                    }
                }
            }
        }
        Debug.Log(shrinked ? "Alan daraldı: Dış katman fade ile yok oldu ve taşlar yok edildi." : "Alan daraltılamadı, zaten daraltılmış.");
    }

    // Zar sonucu: Yeni düşman ekle
    public void SpawnEnemy()
    {
        // Düşman spawn edildiğinde AIController varsa enemyDifficulty ile başlatılır
    }

    /// <summary>
    /// Tüm düşman taşlarının AI turunu başlatır.
    /// </summary>
    public void PlayAllEnemyTurns()
    {
        // Boss AI da oynasın
        foreach (var boss in FindObjectsOfType<BossPiece>())
        {
            if (boss.isBossAlive)
            {
                var bossAI = boss.GetComponent<BossAIController>();
                if (bossAI != null)
                    bossAI.DoAITurn();
            }
        }
        foreach (var enemy in FindObjectsOfType<Piece>())
        {
            if (!enemy.isWhite && enemy.isAlive && !(enemy is BossPiece))
            {
                var ai = enemy.GetComponent<AIController>();
                if (ai != null)
                    ai.DoAITurn();
            }
        }
    }
        // Rastgele aktif bir tile ve rastgele düşman prefab seç
        List<Vector2Int> availableTiles = new List<Vector2Int>();
        for (int x = 0; x < width; x++)
        {
            for (int y = 0; y < height; y++)
            {
                if (tiles[x, y] != null && tiles[x, y].activeSelf)
                    availableTiles.Add(new Vector2Int(x, y));
            }
        }
        if (availableTiles.Count > 0 && enemyPrefabs != null && enemyPrefabs.Count > 0)
        {
            Vector2Int pos = availableTiles[Random.Range(0, availableTiles.Count)];
            GameObject prefab = enemyPrefabs[Random.Range(0, enemyPrefabs.Count)];
            Instantiate(prefab, tiles[pos.x, pos.y].transform.position, Quaternion.identity);
            Debug.Log($"Yeni düşman spawnlandı: ({pos.x}, {pos.y})");
        }
        else
        {
            Debug.Log("Düşman spawnlanacak uygun tile yok veya enemyPrefabs atanmadı.");
        }
    }

    // Zar sonucu: Efekt ekle (sis, yıldırım, vs.)
    public void SpawnEffect()
    {
        // Rastgele aktif bir tile ve rastgele efekt prefab seç
        List<Vector2Int> availableTiles = new List<Vector2Int>();
        for (int x = 0; x < width; x++)
        {
            for (int y = 0; y < height; y++)
            {
                if (tiles[x, y] != null && tiles[x, y].activeSelf)
                    availableTiles.Add(new Vector2Int(x, y));
            }
        }
        if (availableTiles.Count > 0 && effectPrefabs != null && effectPrefabs.Count > 0)
        {
            Vector2Int pos = availableTiles[Random.Range(0, availableTiles.Count)];
            GameObject prefab = effectPrefabs[Random.Range(0, effectPrefabs.Count)];
            Instantiate(prefab, tiles[pos.x, pos.y].transform.position, Quaternion.identity);
            Debug.Log($"Efekt oluştu: ({pos.x}, {pos.y})");
        }
        else
        {
            Debug.Log("Efekt spawnlanacak uygun tile yok veya effectPrefabs atanmadı.");
        }
    }
}
