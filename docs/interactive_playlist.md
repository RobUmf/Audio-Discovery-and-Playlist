# Interactive Playlist Generator: Field Reference Guide

This document details all 12 filter fields available in `interactive_playlist.py`. Each entry explains what the Digital Signal Processing (DSP) metric measures, what low numbers find, and what high numbers find.

---

## 1. Tempo (`dsp_bpm`)
* **SQL Field:** `dsp_bpm`
* **Unit:** Beats Per Minute (BPM)
* **Description:** Measures the speed and cadence of the track.
* **Low Values (`< 90`, e.g., `60.0–85.0`):** Finds slow downtempo, chillout, ambient soundscapes, ballads, or relaxed beats.
* **High Values (`> 135`, e.g., `140.0–175.0`):** Finds fast drum & bass, high-energy house, hardcore, or frantic electronic tracks.

---

## 2. Spectral Centroid (`spectral_centroid_hz`)
* **SQL Field:** `spectral_centroid_hz`
* **Unit:** Hertz (Hz)
* **Description:** Measures the "center of mass" of the audio spectrum. Correlates directly with perceived brightness or darkness of timbre.
* **Low Values (`< 2000 Hz`, e.g., `1000.0–1800.0`):** Finds "brown," dark, warm, low-end heavy tracks with muffled highs and heavy bass focus.
* **High Values (`> 3800 Hz`, e.g., `4000.0–6500.0`):** Finds bright, crisp, treble-heavy tracks with prominent high synths, brass, or vocal presence.

---

## 3. Spectral Rolloff (`spectral_rolloff_hz`)
* **SQL Field:** `spectral_rolloff_hz`
* **Unit:** Hertz (Hz)
* **Description:** The frequency edge below which 85% of the total spectral energy is contained. Acts as a proxy for high-frequency attenuation.
* **Low Values (`< 4000 Hz`, e.g., `2500.0–3800.0`):** Finds low-pass filtered audio, deep atmospheric pads, and tracks lacking high-frequency noise/cymbals.
* **High Values (`> 8000 Hz`, e.g., `8500.0–12000.0`):** Finds full-spectrum, wide-open audio with active cymbals, crisp hi-hats, and sharp synths.

---

## 4. Harmonic Ratio (`hpss_harmonic_ratio`)
* **SQL Field:** `hpss_harmonic_ratio`
* **Unit:** Ratio (`0.0` to `1.0`)
* **Description:** Measures the ratio of sustained harmonic energy (melodies, chords) versus percussive/transient energy (drums, noise).
* **Low Values (`< 0.30`, e.g., `0.10–0.28`):** Finds drum solos, heavy percussive drops, rhythmic transients, clicks, or harsh noise-based tracks.
* **High Values (`> 0.60`, e.g., `0.65–0.90`):** Finds smooth synth pads, sustained vocal lines, orchestral strings, and fluid ambient textures.

---

## 5. Crest Factor (`dynamics_crest_factor_db`)
* **SQL Field:** `dynamics_crest_factor_db`
* **Unit:** Decibels (dB)
* **Description:** The peak-to-RMS ratio, measuring the dynamic punchiness vs. compression of the audio frame.
* **Low Values (`< 8.0 dB`, e.g., `4.0–7.5`):** Finds heavily compressed, brickwalled, squashed, or hyper-loud modern mixes.
* **High Values (`> 13.0 dB`, e.g., `14.0–18.5`):** Finds dynamic, uncompressed, punchy, or acoustic tracks with wide natural volume peaks.

---

## 6. Spectral Flatness (`spectral_flatness`)
* **SQL Field:** `spectral_flatness`
* **Unit:** Ratio (`0.0` to `1.0`)
* **Description:** Quantifies how much a sound resembles a pure tone versus white noise.
* **Low Values (`< 0.020`, e.g., `0.001–0.015`):** Finds clean tonal instruments, flute/synth solos, pure sine tones, and clear harmonic chords.
* **High Values (`> 0.050`, e.g., `0.060–0.180`):** Finds noisy textures, white noise risers, distortion, heavy cymbal crashes, or breathy soundscapes.

---

## 7. Complexity: Onset Rate (`onset_rate`)
* **SQL Field:** `onset_rate`
* **Unit:** Attacks per second
* **Description:** Counts the number of distinct note or beat events occurring per second (rhythmic density).
* **Low Values (`< 3.0`, e.g., `1.0–2.8`):** Finds sparse, slow-moving ambient compositions with drawn-out notes and low event density.
* **High Values (`> 6.5`, e.g., `7.0–12.0`):** Finds busy, highly complex compositions with rapid arpeggios, dense percussion, and fast note attacks.

---

## 8. Complexity: Rhythm Pulse Clarity (`rhythm_pulse_clarity`)
* **SQL Field:** `rhythm_pulse_clarity`
* **Unit:** Score (`0.0` to `1.0`)
* **Description:** Measures the strength, consistency, and predictability of the rhythmic beat pulse.
* **Low Values (`< 0.35`, e.g., `0.05–0.30`):** Finds beatless ambient, syncopated jazz rhythms, complex freeform percussion, or drone music.
* **High Values (`> 0.80`, e.g., `0.82–0.98`):** Finds driving, steady metronomic beats (e.g., 4-on-the-floor trance, house, or dance tracks).

---

## 9. Complexity: Spectral Contrast (`spectral_contrast`)
* **SQL Field:** `spectral_contrast`
* **Unit:** Decibels (dB)
* **Description:** Measures the average dB difference between spectral peaks (harmonics) and spectral valleys (background noise/space).
* **Low Values (`< 20.0 dB`, e.g., `12.0–18.5`):** Finds flat, simple timbres, washed-out audio, or single-layered drone textures.
* **High Values (`> 28.0 dB`, e.g., `29.0–36.0`):** Finds rich, multi-layered, highly detailed arrangements with distinct instrument separation across frequencies.

---

## 10. Musical Key (`dsp_key`)
* **SQL Field:** `dsp_key`
* **Unit:** Text string
* **Description:** Filters tracks by detected tonal key signature and scale mode.
* **Target 'Minor' (e.g., `Minor`, `F Minor`):** Finds cold, atmospheric, moody, dark, or introspective tracks.
* **Target 'Major' (e.g., `Major`, `C Major`):** Finds bright, happy, uplifting, or triumphant tracks.

---

## 11. Grouping / Album Collection (`grouping`)
* **SQL Field:** `grouping`
* **Unit:** Text string
* **Description:** Matches exact metadata tags for release collections, record labels, or community groupings.
* **Example:** Matching `Ponies at Dawn` isolates tracks specifically tagged under that collection.

---

## 12. Duration (`duration_sec`)
* **SQL Field:** `duration_sec`
* **Unit:** Seconds
* **Description:** Tracks total playback length in seconds.
* **Low Values (`< 120 sec`, e.g., `45.0–90.0`):** Finds short intros, interludes, skits, or quick transition tracks.
* **High Values (`> 360 sec`, e.g., `420.0–720.0`):** Finds extended club mixes, progressive suites, and long ambient journeys.
