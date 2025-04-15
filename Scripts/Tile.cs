using UnityEngine;
using UnityEngine.Rendering.Universal; // Light2D için
using System.Collections;
using System.Collections.Generic;

/// <summary>
/// Balatro kalitesinde, tam profesyonel, modüler tile sistemi.
/// Asset pipeline, shader, animasyon ve efekt entegrasyonu ile.
/// </summary>
public enum TileVisualState
{
    Idle,           // Normal görünüm
    Highlight,      // Geçerli hamle
    Selected,       // Seçili tile
    Closing,        // Alan daralması/kapanma
    Closed,         // Pasif, oynanamaz tile
    Event,          // Zar/event efekti
    Buffed,         // Buff/debuff ikonu
    Danger,         // Tehlike animasyonu (alan daralacak)
}

public enum TileEffectType
{
    None, Lightning, Fire, Ice, Poison, Heal, Crack, Smoke, Custom
}

[RequireComponent(typeof(SpriteRenderer))]
[RequireComponent(typeof(AudioSource))]
[RequireComponent(typeof(Animator))]
public class Tile : MonoBehaviour
{
    [Header("Core")]
    public int x, y;
    public bool isActive = true;
    public TileVisualState visualState = TileVisualState.Idle;

    [Header("Sprites & Renderers")]
    public SpriteRenderer mainSprite;
    public SpriteRenderer outlineGlow;
    public SpriteRenderer overlaySprite;
    public SpriteRenderer vignetteOverlay;
    public SpriteRenderer crackSprite;

    [Header("Animator & Animation")]
    public Animator animator;
    public float pulseScale = 1.13f;
    public float pulseSpeed = 1.8f;
    public float shakeStrength = 0.08f;
    public float shakeDuration = 0.22f;

    [Header("Shader/Material")]
    public Material outlineMat;
    public Material dissolveMat;
    public Material vignetteMat;
    public Material grainMat;

    [Header("Light & Effects")]
    public Transform effectRoot;
    public Light2D pulseLight; // URP 2D Light
    public GameObject[] eventEffectPrefabs; // Lightning, fire, ice, etc.
    public GameObject closingEffectPrefab;
    public GameObject smokeEffectPrefab;
    public GameObject buffIconPrefab;
    public GameObject dangerEffectPrefab;

    [Header("Audio")]
    public AudioSource audioSource;
    public AudioClip highlightSfx, selectSfx, closeSfx, eventSfx, pulseSfx, dangerSfx;

    // --- STATE ---
    private Coroutine pulseRoutine, shakeRoutine, dissolveRoutine;
    private GameObject eventEffectInstance, closingEffectInstance, smokeEffectInstance, dangerEffectInstance;
    private List<GameObject> buffIcons = new List<GameObject>();

    private void Awake()
    {
        if (mainSprite == null) mainSprite = GetComponent<SpriteRenderer>();
        if (animator == null) animator = GetComponent<Animator>();
        if (audioSource == null) audioSource = GetComponent<AudioSource>();
        SetVisualState(TileVisualState.Idle, true);
    }

    public void SetCoords(int _x, int _y)
    {
        x = _x;
        y = _y;
    }

    // --- VISUAL STATE MANAGEMENT ---
    public void SetVisualState(TileVisualState state, bool instant = false)
    {
        visualState = state;
        switch (state)
        {
            case TileVisualState.Idle:
                SetIdleVisual(instant);
                break;
            case TileVisualState.Highlight:
                SetHighlightVisual(instant);
                break;
            case TileVisualState.Selected:
                SetSelectedVisual(instant);
                break;
            case TileVisualState.Closing:
                StartClosingSequence();
                break;
            case TileVisualState.Closed:
                SetClosedVisual(instant);
                break;
            case TileVisualState.Event:
                break;
            case TileVisualState.Buffed:
                ShowBuffIcon();
                break;
            case TileVisualState.Danger:
                ShowDangerEffect();
                break;
        }
    }

    // --- IDLE ---
    private void SetIdleVisual(bool instant)
    {
        mainSprite.color = Color.white;
        mainSprite.material = grainMat;
        if (outlineGlow != null) outlineGlow.enabled = false;
        if (overlaySprite != null) overlaySprite.enabled = false;
        if (vignetteOverlay != null) vignetteOverlay.enabled = false;
        if (crackSprite != null) crackSprite.enabled = false;
        if (pulseLight != null) pulseLight.intensity = 0;
        StopAllVisualCoroutines();
        transform.localScale = Vector3.one;
    }

    // --- HIGHLIGHT ---
    private void SetHighlightVisual(bool instant)
    {
        mainSprite.color = new Color(0.7f, 1f, 0.5f, 1f);
        mainSprite.material = outlineMat;
        if (outlineGlow != null) { outlineGlow.enabled = true; outlineGlow.color = Color.cyan; }
        if (overlaySprite != null) { overlaySprite.enabled = true; overlaySprite.color = new Color(1f, 1f, 1f, 0.6f); }
        if (vignetteOverlay != null) vignetteOverlay.enabled = false;
        if (crackSprite != null) crackSprite.enabled = false;
        if (pulseLight != null) pulseLight.intensity = 1f;
        PlaySfx(highlightSfx);
        StartPulse();
    }

    // --- SELECTED ---
    private void SetSelectedVisual(bool instant)
    {
        mainSprite.color = new Color(1f, 0.9f, 0.2f, 1f);
        mainSprite.material = outlineMat;
        if (outlineGlow != null) { outlineGlow.enabled = true; outlineGlow.color = Color.yellow; }
        if (overlaySprite != null) { overlaySprite.enabled = true; overlaySprite.color = new Color(1f, 1f, 0.7f, 0.7f); }
        if (vignetteOverlay != null) vignetteOverlay.enabled = false;
        if (crackSprite != null) crackSprite.enabled = false;
        if (pulseLight != null) pulseLight.intensity = 1.5f;
        PlaySfx(selectSfx);
        StartPulse();
    }

    // --- CLOSING (Alan Daralması) ---
    private void StartClosingSequence()
    {
        if (dissolveRoutine != null) StopCoroutine(dissolveRoutine);
        dissolveRoutine = StartCoroutine(ClosingSequence());
    }
    /// <summary>
    /// Kapanma animasyonu: shake, dissolve + overlay efekt, animasyon trigger
    /// </summary>
    private IEnumerator ClosingSequence()
    {
        mainSprite.material = outlineMat;
        mainSprite.color = Color.red;
        if (outlineGlow != null) { outlineGlow.enabled = true; outlineGlow.color = Color.red; }
        PlaySfx(dangerSfx);
        // Ekstra shake (daha punchy)
        yield return StartCoroutine(Shake(shakeDuration * 1.3f, shakeStrength * 1.2f));
        // Animator trigger (frame-based animasyon)
        if (animator != null) animator.SetTrigger("Closing");
        // Dissolve/fade out (shader ile noise, grain, renkli kenar efekti önerilir)
        mainSprite.material = dissolveMat;
        float t = 0;
        while (t < 1f)
        {
            t += Time.deltaTime / 0.7f;
            mainSprite.material.SetFloat("_DissolveAmount", t);
            yield return null;
        }
        mainSprite.enabled = false;
        if (outlineGlow != null) outlineGlow.enabled = false;
        if (overlaySprite != null) overlaySprite.enabled = false;
        if (vignetteOverlay != null) { vignetteOverlay.enabled = true; vignetteOverlay.material = vignetteMat; vignetteOverlay.color = new Color(0, 0, 0, 0.7f); }
        // Overlay ve particle efektler (VFX Graph/Particle önerilir)
        if (closingEffectPrefab != null && effectRoot != null)
            closingEffectInstance = Instantiate(closingEffectPrefab, effectRoot.position, Quaternion.identity, effectRoot);
        if (smokeEffectPrefab != null && effectRoot != null)
            smokeEffectInstance = Instantiate(smokeEffectPrefab, effectRoot.position, Quaternion.identity, effectRoot);
        PlaySfx(closeSfx);
        // Kamera shake (opsiyonel, Cinemachine veya custom ile)
        CameraShakeIfAvailable();
        yield return new WaitForSeconds(0.7f);
        SetVisualState(TileVisualState.Closed, true);
    }

    /// <summary>
    /// Event efektlerinde tile shake ve animasyon trigger
    /// </summary>
    public void PlayTileEffect(TileEffectType type)
    {
        if (eventEffectInstance != null) Destroy(eventEffectInstance);
        int idx = (int)type;
        if (eventEffectPrefabs != null && idx >= 0 && idx < eventEffectPrefabs.Length && eventEffectPrefabs[idx] != null)
        {
            eventEffectInstance = Instantiate(eventEffectPrefabs[idx], effectRoot.position, Quaternion.identity, effectRoot);
            PlaySfx(eventSfx);
            if (animator != null) animator.SetTrigger("Event");
            // Tile shake (daha kısa ve punchy)
            StartCoroutine(Shake(0.18f, 0.09f));
            // Kamera shake (opsiyonel)
            CameraShakeIfAvailable();
        }
    }

    /// <summary>
    /// Kamera shake için örnek fonksiyon (Cinemachine veya custom script ile entegre edilebilir)
    /// </summary>
    private void CameraShakeIfAvailable(float intensity = 0.15f, float duration = 0.18f)
    {
        var camShake = Camera.main?.GetComponent<CameraShake>();
        if (camShake != null)
            camShake.Shake(intensity, duration);
    }


    // --- CLOSED (Pasif) ---
    private void SetClosedVisual(bool instant)
    {
        mainSprite.enabled = false;
        if (outlineGlow != null) outlineGlow.enabled = false;
        if (overlaySprite != null) overlaySprite.enabled = false;
        if (vignetteOverlay != null) { vignetteOverlay.enabled = true; vignetteOverlay.material = vignetteMat; vignetteOverlay.color = new Color(0, 0, 0, 0.7f); }
        if (crackSprite != null) crackSprite.enabled = true;
        if (pulseLight != null) pulseLight.intensity = 0f;
        StopAllVisualCoroutines();
        transform.localScale = Vector3.one;
    }

    // --- EVENT (Zar/Çevresel Etki) ---
    public void PlayTileEffect(TileEffectType type)
    {
        if (eventEffectInstance != null) Destroy(eventEffectInstance);
        int idx = (int)type;
        if (eventEffectPrefabs != null && idx >= 0 && idx < eventEffectPrefabs.Length && eventEffectPrefabs[idx] != null)
        {
            eventEffectInstance = Instantiate(eventEffectPrefabs[idx], effectRoot.position, Quaternion.identity, effectRoot);
            PlaySfx(eventSfx);
            animator.SetTrigger("Event");
        }
    }

    // --- BUFF/DEBUFF ---
    public void ShowBuffIcon()
    {
        if (buffIconPrefab != null && effectRoot != null)
        {
            var icon = Instantiate(buffIconPrefab, effectRoot.position, Quaternion.identity, effectRoot);
            buffIcons.Add(icon);
        }
    }
    public void ClearBuffIcons()
    {
        foreach (var icon in buffIcons)
            Destroy(icon);
        buffIcons.Clear();
    }

    // --- DANGER (Alan daralacak) ---
    public void ShowDangerEffect()
    {
        if (dangerEffectPrefab != null && effectRoot != null)
        {
            if (dangerEffectInstance != null) Destroy(dangerEffectInstance);
            dangerEffectInstance = Instantiate(dangerEffectPrefab, effectRoot.position, Quaternion.identity, effectRoot);
            PlaySfx(dangerSfx);
        }
    }
    public void ClearDangerEffect()
    {
        if (dangerEffectInstance != null) Destroy(dangerEffectInstance);
    }

    // --- ANİMASYON YARDIMCILARI ---
    private void StartPulse()
    {
        if (pulseRoutine != null) StopCoroutine(pulseRoutine);
        pulseRoutine = StartCoroutine(PulseAnim());
    }
    /// <summary>
    /// Daha profesyonel, canlı ve yumuşak pulse & glow animasyonu (easing, renk, outline alpha animasyonu)
    /// </summary>
    private IEnumerator PulseAnim()
    {
        float baseScale = 1f;
        float t = 0;
        Color baseOutline = outlineGlow != null ? outlineGlow.color : Color.white;
        while (visualState == TileVisualState.Highlight || visualState == TileVisualState.Selected)
        {
            t += Time.deltaTime * pulseSpeed;
            // Easing ile yumuşak pulse
            float pulse = Mathf.SmoothStep(1f, pulseScale, (Mathf.Sin(t) + 1f) / 2f);
            transform.localScale = Vector3.one * pulse;

            // Outline glow animasyonu (alpha ve renk değişimi)
            if (outlineGlow != null)
            {
                Color c = baseOutline;
                c.a = Mathf.Lerp(0.5f, 1f, (Mathf.Sin(t * 1.3f) + 1f) / 2f);
                if (visualState == TileVisualState.Highlight)
                    c = Color.Lerp(Color.cyan, Color.white, (Mathf.Sin(t * 0.7f) + 1f) / 2f);
                if (visualState == TileVisualState.Selected)
                    c = Color.Lerp(Color.yellow, Color.white, (Mathf.Sin(t * 0.7f) + 1f) / 2f);
                outlineGlow.color = c;
            }
            // Pulse light animasyonu
            if (pulseLight != null)
                pulseLight.intensity = Mathf.Lerp(0.8f, 1.7f, (pulse - 1f) / (pulseScale - 1f));
            yield return null;
        }
        transform.localScale = Vector3.one;
        if (pulseLight != null) pulseLight.intensity = 0f;
        if (outlineGlow != null)
        {
            Color c = outlineGlow.color; c.a = 1f; outlineGlow.color = c;
        }
    }

    private IEnumerator Shake(float duration, float strength)
    {
        Vector3 orig = transform.position;
        float t = 0;
        while (t < duration)
        {
            t += Time.deltaTime;
            transform.position = orig + (Vector3)Random.insideUnitCircle * strength;
            yield return null;
        }
        transform.position = orig;
    }

    private void StopAllVisualCoroutines()
    {
        if (pulseRoutine != null) StopCoroutine(pulseRoutine);
        if (shakeRoutine != null) StopCoroutine(shakeRoutine);
        if (dissolveRoutine != null) StopCoroutine(dissolveRoutine);
    }

    // --- SES ---
    private void PlaySfx(AudioClip clip)
    {
        if (clip != null && audioSource != null)
            audioSource.PlayOneShot(clip);
    }
}

    [Header("Core")]
    public int x, y;
    public bool isActive = true;
    public TileVisualState visualState = TileVisualState.Idle;

    [Header("Sprites & Renderers")]
    public SpriteRenderer mainSprite;
    public SpriteRenderer outlineGlow;
    public SpriteRenderer overlaySprite;
    public SpriteRenderer vignetteOverlay;
    public SpriteRenderer crackSprite;

    [Header("Animator & Animation")]
    public Animator animator;
    public float pulseScale = 1.13f;
    public float pulseSpeed = 1.8f;
    public float shakeStrength = 0.08f;
    public float shakeDuration = 0.22f;

    [Header("Shader/Material")]
    public Material outlineMat;
    public Material dissolveMat;
    public Material vignetteMat;
    public Material grainMat;

    [Header("Light & Effects")]
    public Transform effectRoot;
    public Light2D pulseLight; // URP 2D Light
    public GameObject[] eventEffectPrefabs; // Lightning, fire, ice, etc.
    public GameObject closingEffectPrefab;
    public GameObject smokeEffectPrefab;
    public GameObject buffIconPrefab;
    public GameObject dangerEffectPrefab;

    [Header("Audio")]
    public AudioSource audioSource;
    public AudioClip highlightSfx, selectSfx, closeSfx, eventSfx, pulseSfx, dangerSfx;

    // --- STATE ---
    private Coroutine pulseRoutine, shakeRoutine, dissolveRoutine;
    private GameObject eventEffectInstance, closingEffectInstance, smokeEffectInstance, dangerEffectInstance;
    private List<GameObject> buffIcons = new List<GameObject>();

    private void Awake()
    {
        if (mainSprite == null) mainSprite = GetComponent<SpriteRenderer>();
        if (animator == null) animator = GetComponent<Animator>();
        if (audioSource == null) audioSource = GetComponent<AudioSource>();
        SetVisualState(TileVisualState.Idle, true);
    }

    public void SetCoords(int _x, int _y)
    {
        x = _x;
        y = _y;
    }

    public void SetActive(bool state, bool instant = false)
    {
        isActive = state;
        if (sr == null) sr = GetComponent<SpriteRenderer>();
        if (instant)
            sr.color = state ? activeColor : inactiveColor;
        else
            StartColorRoutine(state ? activeColor : inactiveColor);
        SetOutline(false);
        RemoveHighlight();
    }

    public void SetHighlight(bool state)
    {
        if (state)
        {
            StartColorRoutine(highlightColor);
            StartScaleRoutine(highlightScale);
            SpawnHighlightEffect();
            PlaySfx(highlightSfx);
        }
        else
        {
            StartColorRoutine(activeColor);
            StartScaleRoutine(1f);
            RemoveHighlight();
        }
    }

    public void SetSelected(bool state)
    {
        if (state)
        {
            StartColorRoutine(selectedColor);
            SetOutline(true);
            PlaySfx(selectSfx);
            SpawnSelectedEffect();
        }
        else
        {
            StartColorRoutine(activeColor);
            SetOutline(false);
            RemoveSelectedEffect();
        }
    }

    // --- PROFESYONEL: Tile Kapanma Animasyonu ve Efekti ---
    public void AnimateClosing()
    {
        StartCoroutine(ClosingSequence());
    }
    private System.Collections.IEnumerator ClosingSequence()
    {
        // 1. Kırmızıya geçiş
        StartColorRoutine(Color.red);
        // 2. Shake animasyonu
        yield return StartCoroutine(Shake(0.2f, 0.1f));
        // 3. Dissolve/fade out
        StartColorRoutine(inactiveColor);
        // 4. Efekt ve ses
        if (closingEffectPrefab != null && effectRoot != null)
            Instantiate(closingEffectPrefab, effectRoot.position, Quaternion.identity, effectRoot);
        PlaySfx(closeSfx);
        // 5. Tile devre dışı (gerekirse)
        yield return new WaitForSeconds(fadeDuration + 0.1f);
        SetActive(false, instant: true);
    }
    private System.Collections.IEnumerator Shake(float duration, float strength)
    {
        Vector3 orig = transform.position;
        float t = 0;
        while (t < duration)
        {
            t += Time.deltaTime;
            transform.position = orig + (Vector3)Random.insideUnitCircle * strength;
            yield return null;
        }
        transform.position = orig;
    }

    // --- PROFESYONEL: Event/Zar Efekti ---
    public void PlayTileEffect(TileEffectType type)
    {
        int idx = (int)type;
        if (eventEffectPrefabs != null && idx >= 0 && idx < eventEffectPrefabs.Length && eventEffectPrefabs[idx] != null)
        {
            if (effectRoot != null)
                Instantiate(eventEffectPrefabs[idx], effectRoot.position, Quaternion.identity, effectRoot);
            else
                Instantiate(eventEffectPrefabs[idx], transform.position, Quaternion.identity, transform);
            PlaySfx(eventSfx);
        }
    }

    // --- SEÇİLİ EFEKTİ (ör: halo, animasyonlu daire) ---
    public GameObject selectedEffectPrefab;
    private GameObject selectedEffectInstance;
    private void SpawnSelectedEffect()
    {
        if (selectedEffectPrefab != null && selectedEffectInstance == null)
            selectedEffectInstance = Instantiate(selectedEffectPrefab, transform.position, Quaternion.identity, transform);
    }
    private void RemoveSelectedEffect()
    {
        if (selectedEffectInstance != null)
        {
            Destroy(selectedEffectInstance);
            selectedEffectInstance = null;
        }
    }

    // --- SES ---
    private void PlaySfx(AudioClip clip)
    {
        if (clip != null && audioSource != null)
            audioSource.PlayOneShot(clip);
    }

    public void SetOutline(bool state)
    {
        if (outlineObject != null)
            outlineObject.SetActive(state);
    }

    private void SpawnHighlightEffect()
    {
        if (highlightEffectPrefab != null && highlightEffectInstance == null)
        {
            highlightEffectInstance = Instantiate(highlightEffectPrefab, transform.position, Quaternion.identity, transform);
        }
    }

    private void RemoveHighlight()
    {
        if (highlightEffectInstance != null)
        {
            Destroy(highlightEffectInstance);
            highlightEffectInstance = null;
        }
    }

    private void StartColorRoutine(Color target)
    {
        if (colorRoutine != null) StopCoroutine(colorRoutine);
        colorRoutine = StartCoroutine(FadeTo(target));
    }
    private System.Collections.IEnumerator FadeTo(Color target)
    {
        Color start = sr.color;
        float t = 0;
        while (t < 1f)
        {
            t += Time.deltaTime / fadeDuration;
            sr.color = Color.Lerp(start, target, t);
            yield return null;
        }
        sr.color = target;
    }

    private void StartScaleRoutine(float targetScale)
    {
        if (scaleRoutine != null) StopCoroutine(scaleRoutine);
        scaleRoutine = StartCoroutine(ScaleTo(targetScale));
    }
    private System.Collections.IEnumerator ScaleTo(float targetScale)
    {
        Vector3 start = transform.localScale;
        Vector3 end = Vector3.one * targetScale;
        float t = 0;
        while (t < 1f)
        {
            t += Time.deltaTime / fadeDuration;
            transform.localScale = Vector3.Lerp(start, end, t);
            yield return null;
        }
        transform.localScale = end;
        // Highlight pulse
        if (targetScale > 1f)
            StartCoroutine(PulseHighlight(targetScale));
    }
    private System.Collections.IEnumerator PulseHighlight(float baseScale)
    {
        while (true)
        {
            float s = baseScale + Mathf.Sin(Time.time * highlightPulseSpeed) * 0.08f;
            transform.localScale = Vector3.one * s;
            yield return null;
        }
    }
}
