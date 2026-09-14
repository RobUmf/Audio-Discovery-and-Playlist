# Count Utility (`count.py`)

A lightweight command-line audit and reporting tool for your local audio library and SQLite tracking database.

---

## Features

- **Directory Scanning**: Audits raw and compressed music libraries (`.mp3`, `.flac`, `.opus`, `.wav`, `.m4a`), breaking down file counts and storage size.
- **Database Metrics**: Connects to your SQLite database (`audio_database.db`) to pull record health metrics.
- **Config-Driven**: Automatically reads default paths from a local `config.json`, with terminal overrides.

---

## Command-Line Options

| Option / Flag | Long Flag | Default | Description |
| :--- | :--- | :--- | :--- |
| `-c` | `--config` | `config.json` | Path to custom JSON configuration file. |
| `-i` | `--input` | `/storage/2013-1E1B/musicraw` | Path to input music directory (Raw Library). |
| `-o` | `--output` | `/storage/2013-1E1B/128mp3` | Path to output compressed directory (`128mp3`). |
| `-d` | `--db` | `audio_database.db` | Path to the SQLite database file. |
| `-h` | `--help` | — | Show the help message and exit. |

---

## Usage Examples

**Run with default configuration:**
```bash
python3 count.py
