# Advanced Audio Analyzer Documentation

`advanced_analyzer.py` is a robust command-line utility designed for batch processing audio libraries using `librosa` DSP algorithms. It extracts music information retrieval (MIR) features, estimates musical keys, detects upscaled lossy files, and stores everything into an SQLite database.

---

## Features

- **Pitch & Harmony Analysis**: Implements the Krumhansl-Schmuckler key determination algorithm using chroma feature vectors to estimate musical keys and confidence scores.
- **Upscale & Quality Health Checks**: Analyzes high-frequency spectrum cutoffs to flag potentially upscaled lossy audio files.
- **Transients & Attack Profiling**: Calculates onset detection rates and average envelope intensity.
- **Timbre & Instrumentation Profiling**: Extracts spectral contrast and a 13-coefficient Mel-frequency cepstral coefficients (MFCC) profile array stored as JSON.
- **Safe Batch Processing**: Chunks large libraries into manageable batches with configurable sleep intervals to prevent memory spikes and resource exhaustion.
- **Timestamped Logging**: Comprehensive status output via structured timestamps.

---

## Command-Line Options

| Option / Flag | Long Flag | Default | Description |
| :--- | :--- | :--- | :--- |
| `-c` | `--config` | `config.json` | Path to the JSON configuration file containing path mappings. |
| `--db` | `--db` | `/home/audio-repo/sqlite/audio_database.db` | File path to the SQLite target database. |
| `-b` | `--batch-size` | `50` | Number of tracks to process before pausing / clearing worker cache. |
| `-s` | `--sleep` | `2.0` | Pause duration in seconds between processing batches. |
| `-d` | `--directory` | `None` | Target audio library root directory (overrides configuration file). |

---

## Usage Examples

### 1. Run with Default Settings
Processes unindexed tracks using default paths and a batch size of 50:

python advanced_analyzer.py

### 2. Custom Batch Size and Sleep Interval
Process tracks in smaller chunks of 10 with a 1-second cooldown:

python advanced_analyzer.py --batch-size 10 --sleep 1.0

### 3. Specify Custom Database and Library Path
Override default paths for custom environments:

python advanced_analyzer.py --db /path/to/audio_database.db --directory /path/to/128mp3
