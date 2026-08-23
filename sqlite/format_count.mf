
# Format Audit Tool (`format_count.py`)

`format_count.py` is a repository auditing tool that recursively scans target directories for supported audio formats, breaks down file counts by extension, computes total storage sizes with human-readable units, and integrates with the repository's hierarchical configuration system.

---

## 🚀 Key Features

* **Recursive Scanning:** Deeply traverses folder trees to discover all supported audio formats (`.mp3`, `.flac`, `.opus`, `.wav`, `.m4a`).
* **Format Breakdown & Sizing:** Tallies counts per extension and aggregates total directory size using clean, human-readable units (KB, MB, GB, TB).
* **Config or CLI Driven:** Reads default baseline paths from `config.json`, but allows instant dynamic overriding via command-line flags.

---

## 📋 Requirements

* **Python 3.10+** (Recommended sweet spot for compatibility)
* Standard Python libraries only (`json`, `argparse`, `pathlib`, `collections`)

---

## 🎛️ Command-Line Interface (CLI) Flags

The script accepts the following arguments. If path flags are omitted, the script falls back to `config.json`, then to default paths.

* `-c`, `--config` *(path)* : Path to JSON configuration file (Default: `config.json`).
* `-i`, `--input` *(path)* : Input music directory (overrides config).
* `-o`, `--output` *(path)* : Output compressed directory (overrides config).

---

## ⚙️ Configuration File (`config.json`)

The script looks for default paths defined in your `config.json`:

```json
{
  "input_dir": "/storage/2013-1E1B/musicraw",
  "output_dir": "/storage/2013-1E1B/128mp3",
  "db_path": "./audio_database.db",
  "bitrate": "128k",
  "include_cover": true,
  "cover_size": "300",
  "flat": false,
  "workers": 4
}
