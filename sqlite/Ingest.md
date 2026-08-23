# Ingest Engine (`ingest.py`)

`ingest.py` is a high-performance, multithreaded audio ingestion pipeline. It serves as the front door to the repository by scanning raw audio files, compressing them into portable MP3s, embedding metadata tags, and registering them directly into a local SQLite database.

---

## 🚀 Key Features

* **Smart Deduplication:** If duplicate filenames are found in your source directory, the script automatically prioritizes the version nested deeper in subfolders (assuming it is the better-organized copy).
* **Config or CLI Driven:** Define standard paths in `config.json`, or dynamically override any setting directly from the command line.
* **Intelligent Compression:** Uses `ffprobe` to bypass re-encoding if an incoming file is already an MP3 at or below the target bitrate threshold. Otherwise, `ffmpeg` transcodes lossless or high-bitrate files down to target.
* **Flat Output Option:** Can recursively scan deeply nested music folders but output all converted MP3s into a single, flat destination folder without retaining the original subfolder structure.
* **Automatic Database Provisioning:** Automatically creates `audio_database.db` and the core `tracks` table if they do not exist.
* **Rich Metadata Extraction:** Reads ID3 tags via `mutagen` to capture title, artist, album, genre, year, track number, disc number, duration, and sample rate during ingestion.

---

## 📋 Requirements

* **Python 3.10+** (Recommended sweet spot for compatibility)
* `ffmpeg` and `ffprobe` installed on system path
* Python packages: `mutagen`

---

## 🎛️ Command-Line Interface (CLI) Flags

The script accepts the following arguments. If an argument is not provided, the script falls back to `config.json`. If `config.json` lacks the key, hardcoded defaults take over.

* `-c`, `--config` *(path)* : Path to JSON configuration file (Default: `config.json`).
* `-i`, `--input` *(path)* : Input root directory containing raw audio files.
* `-o`, `--output` *(path)* : Output root directory for processed MP3s.
* `-b`, `--bitrate` *(string)* : Target audio encoding bitrate (Default: `"128k"`).
  * Available choices: `128k`, `192k`, `256k`, `320k`
* `--cover` *(flag)* : Include and embed album cover art (Scales embedded video/images).
* `--cover-size` *(string)* : Square pixel dimension for scaled cover art (Default: `"300"`).
* `--flat` *(flag)* : Flatten all processed files directly into the root output folder without subdirectories.
* `-w`, `--workers` *(int)* : Number of concurrent CPU workers. Defaults to max available cores minus one.
* `-g`, `--group` *(string)* : Custom grouping name override for this batch. Bypasses the default parent folder name assignment.

---

## ⚙️ Configuration File (`config.json`)

You can define baseline settings in `config.json` to avoid typing flags every time:

```json
{
  "input_dir": "./musicraw",
  "output_dir": "./128mp3",
  "db_path": "./audio_database.db",
  "bitrate": "128k",
  "include_cover": true,
  "cover_size": "300",
  "flat": false,
  "workers": 4
}
