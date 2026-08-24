# analyzersqlite.py Documentation

## Overview
`analyzersqlite.py` is a high-performance, multi-processed Python script designed to extract advanced Digital Signal Processing (DSP) and audio health metrics from MP3 libraries and update a central SQLite database (`audio_database.db`)[cite: 2]. It is engineered for desktop environments (such as the EliteDesk) to handle heavy audio computations efficiently without memory bloat[cite: 2].

---

## Key Features
* **Smart Loading & Slicing**: Utilizes `PyDub` for full-track loudness analysis while slicing a targeted window from the middle of long tracks via `librosa` to conserve RAM[cite: 2].
* **Multi-Process Concurrency**: Automatically distributes workload across multiple CPU cores using `ProcessPoolExecutor`[cite: 2].
* **Memory Management**: Features explicit garbage collection (`gc.collect()`), tensor/array purging, and discrete batch chunking to ensure stability over large libraries[cite: 2].
* **Resumable State Tracking**: Automatically scans the database for already-indexed tracks and processes only remaining files[cite: 2].

---

## Extracted Metrics
The script computes and updates the following categories in the database:
* **Loudness & Dynamics**: LUFS, RMS dB, Peak dB, and Crest Factor[cite: 2].
* **Rhythm & Tempo**: Estimated BPM and Rhythm Pulse Clarity[cite: 2].
* **Harmonic Profile**: HPSS Harmonic Ratio (separating harmonic vs. percussive energy)[cite: 2].
* **Spectral Characteristics**: Spectral Centroid (Hz), Spectral Rolloff (Hz), and Spectral Flatness[cite: 2].
* **Audio Health**: DC Offset and Clipping Percentage (`health_clip_pct`)[cite: 2].

---

## Command-Line Arguments & Options

| Option / Flag | Description | Default Value |
| :--- | :--- | :--- |
| `-c`, `--config` | Path to the JSON configuration file[cite: 2]. | `config.json`[cite: 2] |
| `-d`, `--directory` | Target audio directory to scan (overrides configuration file)[cite: 2]. | Config value or `/storage/2013-1E1B/128mp3`[cite: 2] |
| `--db` | Path to the SQLite database file (overrides configuration file)[cite: 2]. | `audio_database.db`[cite: 2] |
| `-w`, `--workers` | Number of concurrent background worker processes[cite: 2]. | Total CPU cores minus 1[cite: 2] |
| `--sr` | Target downsample sample rate in Hz to save RAM (`0` for native rate)[cite: 2]. | `22050`[cite: 2] |
| `-b`, `--batch-size` | Number of files processed per batch before forcing a memory flush[cite: 2]. | `50`[cite: 2] |
| `-s`, `--sleep` | Pause duration in seconds between batches to let system resources cool down[cite: 2]. | `2.0`[cite: 2] |
| `--max-dur` | Maximum duration slice in seconds to analyze per track (centering on long tracks)[cite: 2]. | `120.0`[cite: 2] |

---

## Usage Examples

### 1. Standard Execution (Using Defaults)

python analyzersqlite.py

python analyzersqlite.py --batch-size 30 --sleep 3.0 --max-dur 90.0
