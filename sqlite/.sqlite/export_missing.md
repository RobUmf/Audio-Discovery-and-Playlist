# export_missing.py” Audio Database Missing Track Exporter

## Overview
`export_missing.py` is a cross-platform Python utility designed to audit an SQLite audio database against a target directory of processed audio files (`128mp3`). It identifies database entries whose corresponding MP3 files are missing from local storage and exports a clean, formatted list to a text report.

Built for multi-device workflows (Linux desktops, Termux/Android, headless nodes), it supports dynamic tilde (`~`) path resolution using `Path.expanduser()` to ensure seamless cross-environment operation without modifying configuration files.

---

## Features
* **Config-Driven & Flexible Overrides:** Loads paths automatically from `config.json` while allowing full command-line parameter overrides.
* **Cross-Platform Compatibility:** Expands `~` home paths natively across Linux, macOS, and Termux environments.
* **Smart Matching:** Inspects both full relative file paths and filename stems to accurately detect missing tracks.
* **Detailed Terminal Output:** Displays explicit database and target folder paths prior to scanning.
* **Structured Export:** Generates a sorted text file containing metadata (`Artist | Album | Title (Filename)`) along with header audit details.

---

## Command Line Flags & Options

```bash
python3 export_missing.py [FLAGS]
```

| Short Flag | Long Flag | Value Type | Default Value | Description |
| :--- | :--- | :--- | :--- | :--- |
| `-c` | `--config` | `PATH` | `config.json` | Path to the JSON configuration file containing path definitions. |
| *(None)* | `--db` | `PATH` | `db_path` in `config.json` | Direct path to the SQLite database file. Overrides config value. |
| *(None)* | `--target` | `PATH` | `output_dir` in `config.json` | Target directory containing local MP3 files to audit. Overrides config value. |
| *(None)* | `--output` | `FILENAME` | `missing_tracks.txt` | Output text report filename (saved inside the database directory). |
| `-h` | `--help` | *(None)* | *(None)* | Displays standard command-line help message and exits. |

---

## Example Usage

### Standard Run (Uses `config.json`)
```bash
python3 export_missing.py
```

### Override Target Folder
```bash
python3 export_missing.py --target ~/external/128mp3
```

### Custom Database and Config Path
```bash
python3 export_missing.py -c custom_config.json --db ~/audio-repo/sqlite/my_database.db
```

### Custom Output Report Name
```bash
python3 export_missing.py --output batch_missing_report.txt
```

---

## Sample Output

### Terminal Output
```text
ðŸ“„ Loading configuration from /home/robumf/audio-repo/sqlite/config.json
ðŸ—„ï¸ Database: /home/robumf/audio-repo/sqlite/audio_database.db
ðŸ“ Searching target folder: /home/robumf/128mp3
[*] Exported 3 missing tracks to: /home/robumf/audio-repo/sqlite/missing_tracks.txt
```

### Generated Report (`missing_tracks.txt`)
```text
=== MISSING TRACKS LIST (3 total) ===
Target Directory Searched: /home/robumf/128mp3
Database Queried: /home/robumf/audio-repo/sqlite/audio_database.db

Artist Name | Album Title | Song Title (Track01.mp3)
Band Name | Live Album | Demo Track (DemoTrack.mp3)
Unknown Artist | Singles | Prototype (proto.mp3)
```
