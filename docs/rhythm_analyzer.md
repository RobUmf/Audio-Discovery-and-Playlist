# Rhythm, Groove, and Vibe Analyzer Documentation

`rhythm_analyzer.py` is a high-performance, multi-processed command-line utility designed to analyze rhythm, groove micro-timing, harmonic balance, and high-level musical vibes for audio libraries using `librosa` and `scipy`. Results are persisted directly into an SQLite database.

---

## Features

- **Parallel Processing**: Leverages Python's `ProcessPoolExecutor` to distribute CPU-bound DSP computations across multiple CPU cores (`cpu_count - 1` by default).
- **SciPy Compatibility Patch**: Automatically detects and patches missing `scipy.signal.hann` attributes in newer SciPy environments, ensuring smooth execution across various system configurations.
- **Groove & Triplet Analysis**: Analyzes onset micro-timing relative to the detected beat grid to distinguish between straight (4/4) rhythms and triplet/shuffle feels.
- **Harmonic-to-Percussive Separation (HPSS)**: Computes harmonic ratios using energy separation to quantify tonal versus percussive weight.
- **Rule-Based Vibe Classification**: Automatically categorizes tracks into descriptive vibes (e.g., *Ambient / Soundscape*, *High-Energy / Fast Electronic*, *Melodic / Mid-Tempo*, or *Dynamic / Rhythm-Driven*) based on BPM, spectral bandwidth, onset rate, and harmonic ratios.
- **Safe Batch Processing**: Chunks tracks into manageable batches with configurable sleep intervals to prevent memory exhaustion during large-scale library scans.

---

## Command-Line Options

| Option / Flag | Long Flag | Default | Description |
| :--- | :--- | :--- | :--- |
| `-c` | `--config` | `config.json` | Path to the JSON configuration file containing path mappings. |
| `--db` | `--db` | `audio_database.db` | File path to the SQLite target database. |
| `-w` | `--workers` | `cpu_count - 1` | Number of concurrent worker processes for parallel analysis. |
| `-b` | `--batch-size` | `50` | Number of tracks processed per batch block. |
| `-s` | `--sleep` | `1.0` | Pause duration in seconds between processing batches. |
| `-d` | `--directory` | `None` | Target audio library root directory (overrides configuration file). |

---

## Usage Examples

### 1. Run with Default Settings
Processes pending tracks using automatic multi-core worker allocation:

```bash
python rhythm_analyzer.py
```

### 2. Custom Worker Count and Batch Size
Limit concurrency to 4 workers with a smaller batch size of 20:

```bash
python rhythm_analyzer.py --workers 4 --batch-size 20 --sleep 0.5
```

### 3. Specify Custom Database and Directory
Point to an explicit database file and audio root directory:

```bash
python rhythm_analyzer.py --db /path/to/audio_database.db --directory /storage/2013-1E1B/128mp3
```