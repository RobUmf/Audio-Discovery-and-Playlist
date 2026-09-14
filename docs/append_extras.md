# `append_extras.py` — Audio Database Orphan Appender

## Overview
`append_extras.py` is a cross-platform Python utility designed to audit local MP3 storage (`128mp3`) against an SQLite audio database, detect orphan/extra files, parse their metadata (`Artist`, `Album`, `Title`) directly from their folder structure, and append them into the database.

Built with safety in mind, it operates in **dry-run mode by default** to preview changes before requiring the explicit `--apply` flag to commit updates. It also fully supports cross-platform tilde (`~`) path resolution using `config.json`.

---

## Features
* **Dry-Run by Default:** Prevents accidental database modification by previewing all operations unless explicitly overridden.
* **Config-Driven & Flexible Overrides:** Loads paths automatically from `config.json` while allowing command-line parameter overrides.
* **Smart Folder-Structure Parsing:** Automatically extracts artist and album names based on relative directory depth.
* **Dynamic Schema Inspection:** Automatically adapts to database table columns using `PRAGMA table_info`.
* **Cross-Platform Compatibility:** Expands home paths (`~`) natively across Linux, macOS, and Termux environments.

---

## Command Line Flags & Options

```bash
python3 append_extras.py [FLAGS]
```

| Short Flag | Long Flag | Value Type | Default Value | Description |
| :--- | :--- | :--- | :--- | :--- |
| `-c` | `--config` | `PATH` | `config.json` | Path to the JSON configuration file containing path definitions. |
| *(None)* | `--db` | `PATH` | `db_path` in `config.json` | Direct path to the SQLite database file. Overrides config value. |
| *(None)* | `--target` | `PATH` | `output_dir` in `config.json` | Target directory containing local MP3 files to scan. Overrides config value. |
| *(None)* | `--apply` | *(Flag)* | `False` (Dry run) | Commits records to the database. Without this, script runs in dry-run mode. |
| `-h` | `--help` | *(None)* | *(None)* | Displays standard command-line help message and exits. |

---

## Example Usage

### 1. Standard Run (Dry Run Preview)
```bash
python3 append_extras.py
```

### 2. Live Run (Writes to Database)
```bash
python3 append_extras.py --apply
```

### 3. Override Target Folder
```bash
python3 append_extras.py --target ~/external/128mp3 --apply
```

### 4. Custom Config and Database
```bash
python3 append_extras.py -c custom_config.json --db my_db.db --apply
```

---

## Sample Output

### Dry-Run Terminal Output
```text
📄 Loading configuration from /storage/2013-1E1B/audio-repo/SQLite/config.json

🛑 DRY RUN MODE: No changes will be written to the database. Use --apply to execute.
🗄️ Database: /storage/2013-1E1B/audio-repo/SQLite/audio_database.db
📁 Scanning target folder: /storage/2013-1E1B/128mp3

🔍 [DRY RUN] Would insert: Elias Frost - They are the Night (Elias Frost - They are the Night.mp3)
🛑 Dry run complete. 1 extra track found, but none were added.
Run with --apply to write these changes to the database.
```

### Live Apply Terminal Output
```text
📄 Loading configuration from /storage/2013-1E1B/audio-repo/SQLite/config.json
🗄️ Database: /storage/2013-1E1B/audio-repo/SQLite/audio_database.db
📁 Scanning target folder: /storage/2013-1E1B/128mp3

➕ Inserting: Elias Frost - They are the Night (Elias Frost - They are the Night.mp3)
✅ Successfully appended 1 extra tracks to the database!
```
