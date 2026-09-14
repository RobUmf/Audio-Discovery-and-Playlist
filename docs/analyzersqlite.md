# analyzersqlite.py Documentation

## Overview
`analyzersqlite.py` is a high-performance, multi-processed Python script designed to extract advanced Digital Signal Processing (DSP) and audio health metrics from MP3 libraries and update a central SQLite database (`audio_database.db`). It is engineered for desktop environments (such as the EliteDesk) to handle heavy audio computations efficiently without memory bloat.

---

## Key Features
* **Smart Loading & Slicing**: Utilizes `PyDub` for full-track loudness analysis while slicing a targeted window from the middle of long tracks via `librosa` to conserve RAM.
* **Multi-Process Concurrency**: Automatically distributes workload across multiple CPU cores using `ProcessPoolExecutor`.
* **Memory Management**: Features explicit garbage collection (`gc.collect()`), tensor/array purging, and discrete batch chunking to ensure stability over large libraries.
* **Resumable State Tracking**: Automatically scans the database for already-indexed tracks and processes only remaining files.

---

## Extracted Metrics
The script computes and updates the following categories in the database:
* **Loudness & Dynamics**: LUFS, RMS dB, Peak dB, and Crest Factor.
* **Rhythm & Tempo**: Estimated BPM and Rhythm Pulse Clarity.
* **Harmonic Profile**: HPSS Harmonic Ratio (separating harmonic vs. percussive energy).
* **Spectral Characteristics**: Spectral Centroid (Hz), Spectral Rolloff (Hz), and Spectral Flatness.
* **Audio Health**: DC Offset and Clipping Percentage (`health_clip_pct`).

---

## Command-Line Arguments & Options

| Option / Flag | Description | Default Value |
| :--- | :--- | :--- |
| `-c`, `--config` | Path to the JSON configuration file. | `config.json` |
| `-d`, `--directory` | Target audio directory to scan (overrides configuration file). | Config value or `/storage/2013-1E1B/128mp3` |
| `--db` | Path to the SQLite database file (overrides configuration file). | `audio_database.db` |
| `-w`, `--workers` | Number of concurrent background worker processes. | Total CPU cores minus 1 |
| `--sr` | Target downsample sample rate in Hz to save RAM (`0` for native rate). | `22050` |
| `-b`, `--batch-size` | Number of files processed per batch before forcing a memory flush. | `50` |
| `-s`, `--sleep` | Pause duration in seconds between batches to let system resources cool down. | `2.0` |
| `--max-dur` | Maximum duration slice in seconds to analyze per track (centering on long tracks). | `120.0` |

---

## Usage Examples

### 1. Standard Execution (Using Defaults)
python analyzersqlite.py

Usage examples

python analyzersqlite.py --workers 4 --batch-size 25 --sleep 5.0 --max-dur 90.0

python analyzersqlite.py --batch-size 30 --sleep 3.0 --max-dur 90.0

python analyzersqlite.py -d /path/to/audio/files --db /path/to/custom_database.db
