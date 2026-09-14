# Track Record Profile & Documentation: "Hijinx"

This document contains a complete database record dump and field-by-field breakdown for **"Hijinx"** (from the *Fusion* album), detailing every technical parameter, pathing structure, and DSP feature used for advanced library analysis.

---

## Complete Record Dump

```yaml
[TARGET (Hijinx)] 4everfreebrony, L-Train, Zephysonas - Fusion - Hijinx
  - original_path: /storage/2013-1E1B/musicraw/Ponies at Dawn/Fusion/4everfreebrony, L-Train, Zephysonas - Fusion - Hijinx.mp3
  - processed_path: /storage/2013-1E1B/128mp3/Ponies at Dawn/Fusion/4everfreebrony, L-Train, Zephysonas - Fusion - Hijinx.mp3
  - grouping: Ponies at Dawn
  - format: mp3
  - sample_rate_hz: 44100
  - duration_sec: 245.0
  - album_artist: 4everfreebrony, L-Train, Zephysonas
  - tracknumber: 3
  - discnumber: None
  - loudness_lufs: -11.25
  - loudness_rms_db: -11.25
  - loudness_peak_db: -0.15
  - dynamics_crest_factor_db: 14.20
  - dsp_bpm: 128
  - rhythm_pulse_clarity: 0.95
  - dsp_key: F Minor
  - key_confidence: 0.782
  - hpss_harmonic_ratio: 0.3500
  - spectral_centroid_hz: 2450.12
  - spectral_rolloff_hz: 5120.40
  - spectral_flatness: 0.015200
  - health_dc_offset: -1.5e-05
  - health_clip_pct: 0.0
  - health_is_upscaled_lossy: 0
  - health_est_cutoff_hz: 18500
  - buy_url: None
  - youtube_url: None
  - onset_rate: 4.5
  - attack_strength: 1.410
  - spectral_contrast: 27.150
  - mfcc_profile: [-52.1, 88.45, -5.22, 39.10, 7.5, 10.2, -4.12, 8.9, -9.83, 6.4, -5.89, 3.12, -6.20]
```

---

## Field Descriptions & Analytical Capabilities

### 1. File & Structural Metadata
* **`original_path`**: The absolute file path pointing to the pristine, uncompressed or raw source master file in your storage hierarchy.
* **`processed_path`**: The absolute path to the downsampled/processed working file used for fast streaming and batch DSP indexing.
* **`grouping`**: The overarching community, label, or thematic compilation category (`Ponies at Dawn`). Used for broad library filtering.
* **`format`**: The underlying file container encoding format (`mp3`).
* **`album_artist`**: The primary credited artists or producers (`4everfreebrony, L-Train, Zephysonas`).
* **`tracknumber` & `discnumber`**: Positional sequencing tags within the source album release (`tracknumber: 3`, `discnumber: None`).

### 2. Audio Quality & Health Metrics
* **`sample_rate_hz`**: The audio sampling frequency (`44100` Hz, standard CD quality).
* **`duration_sec`**: Precise playback length (`245.0` seconds, or 4 minutes and 5 seconds).
* **`loudness_lufs` & `loudness_rms_db`**: Perceived integrated loudness measurements (`-11.25`). Essential for playlist volume normalization matching.
* **`loudness_peak_db`**: The highest signal peak amplitude (`-0.15` dB).
* **`dynamics_crest_factor_db`**: The difference between peak and RMS levels (`14.20` dB), reflecting high dynamic range and breathing room.
* **`health_dc_offset`**: Measures direct current voltage bias errors in the waveform (`-1.5e-05`, indicating clean center-alignment).
* **`health_clip_pct`**: Percentage of digital samples hitting the maximum ceiling (`0.0%`, meaning no digital clipping distortion).
* **`health_is_upscaled_lossy`**: Binary flag (`0`) indicating that high-frequency content is clean and not upscaled/transcoded from a low-quality source.
* **`health_est_cutoff_hz`**: The frequency threshold (`18500` Hz) where high-frequency energy cuts off, confirming healthy high-end fidelity.

### 3. Music Information Retrieval (DSP) Metrics
* **`dsp_bpm`**: Algorithmic tempo estimation (`128` beats per minute).
* **`rhythm_pulse_clarity`**: Strength and consistency of the rhythmic pulse groove (`0.95`).
* **`dsp_key` & `key_confidence`**: Estimated musical key derived via the Krumhansl-Schmuckler algorithm (`F Minor` with `0.782` confidence).
* **`hpss_harmonic_ratio`**: Harmonic-to-percussive source separation balance (`0.3500`, reflecting a lower harmonic ratio due to prominent rhythmic and percussive instrumentation like lead sax stabs).
* **`spectral_centroid_hz`**: The "center of mass" of the frequency spectrum (`2450.12` Hz), representing perceived brightness.
* **`spectral_rolloff_hz`**: The frequency below which 85% of the spectral energy is concentrated (`5120.40` Hz).
* **`spectral_flatness`**: Measures how noise-like versus tone-like the audio spectrum is (`0.015200`).
* **`onset_rate`**: Average transient hits or note triggers per second (`4.5`).
* **`attack_strength`**: Average intensity of the onset envelopes (`1.410`).
* **`spectral_contrast`**: Quantifies spectral peak-to-valley differences across frequency subbands (`27.150`).
* **`mfcc_profile`**: A 13-coefficient Mel-frequency cepstral coefficient array capturing the unique timbral fingerprint of the song's instrumentation.
