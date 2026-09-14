# Track Metadata & Analysis Profile: "Hijinx"

This document provides a comprehensive breakdown of the track analysis fields stored in the SQLite database, using **"Hijinx"** (from the *Fusion* album by Ponies at Dawn) as a practical reference example. It outlines field descriptions, analytical capabilities, and how to combine them for specific playback goals.

---

## Full Record Breakdown: "Hijinx"

### 1. `grouping` : Ponies at Dawn
* **Field Description**: The overarching community, label, or thematic compilation category the track belongs to.
* **What it can determine**: Filters your library by specific fandom music hubs or album series collections.

### 2. `album_artist` : 4everfreebrony, L-Train, Zephysonas
* **Field Description**: The primary artists, producers, or collaborative creators credited for the track.
* **What it can determine**: Identifies specific creators or collaborative groups when browsing multi-artist community albums.

### 3. `duration_sec` : 245.0 (4:05)
* **Field Description**: The exact length of the audio track measured in seconds.
* **What it can determine**: Allows you to filter tracks by length (e.g., separating extended mixes or short interludes from standard radio-length songs).

### 4. `dsp_bpm` : 128
* **Field Description**: The algorithmic beats-per-minute tempo estimation derived from rhythmic analysis.
* **What it can determine**: Essential for identifying tempo. If you want a **"fast beat"**, you can query tracks where `dsp_bpm > 130` or sort by highest tempo.

### 5. `loudness_lufs` : -11.25
* **Field Description**: Integrated perceived loudness measured in LUFS (Loudness Units relative to Full Scale).
* **What it can determine**: Measures how loud a track sounds to the human ear. Useful for normalization matching across playlists.

### 6. `dynamics_crest_factor_db` : 14.20
* **Field Description**: The ratio (in decibels) between the peak signal level and the root-mean-square (RMS) average level. 
* **What it can determine**: This is your **high dynamic range** indicator. A higher crest factor means the track has wide breathing room between its quietest and loudest moments (less crushed/over-compressed mastering), which is great for audiophile listening.

### 7. `hpss_harmonic_ratio` : 0.35 (Low/Instrumental-leaning relative to heavy percussive elements)
* **Field Description**: The Harmonic-Percussive Source Separation ratio, indicating the balance between sustained melodic tones (vocals, synths, pads) versus transient-heavy elements (drums, rhythm guitar, heavy brass/sax stabs like the lead sax in *Hijinx*).
* **What it can determine**: Helps isolate rhythmic or percussion-driven tracks. Lower harmonic ratios combined with specific spectral features can help filter out vocal-heavy ballad structures in favor of energetic instrumentals.

### 8. `onset_rate` : 4.5
* **Field Description**: The average frequency of musical onsets (transients or distinct note/hit triggers) per second.
* **What it can determine**: Measures how busy or rhythmically active a song is. A high onset rate means rapid notes, fast drum fills, or frequent musical changes.

---

## Example Query Scenario: Finding "Fast Beat, No Vocals, High Dynamic Range"

To write a database query or filter to find tracks matching target criteria using these fields, use the following SQL structure:

```sql
SELECT file_path, dsp_bpm, dynamics_crest_factor_db, hpss_harmonic_ratio 
FROM tracks 
WHERE dsp_bpm >= 135                 -- Fast beat
  AND dynamics_crest_factor_db > 12.0 -- High dynamic range (wide breathing room)
  AND hpss_harmonic_ratio < 0.5      -- Percussive/instrumental-heavy bias
ORDER BY dsp_bpm DESC;
```
