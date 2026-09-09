# Count Utility (`count.py`)

A lightweight command-line audit and reporting tool for your local audio library and SQLite tracking database.

---

## Features

- **Directory Scanning**: Recursively audits your raw and compressed music libraries (`.mp3`, `.flac`, `.opus`, `.wav`, `.m4a`), breaking down file counts by format and calculating total storage size.
- **Database Metrics**: Connects to your SQLite database (`audio_database.db`) to instantly pull record health metrics (total entries, populated artists, groupings, cutoff frequencies, and YouTube URLs).
- **Config-Driven**: Automatically reads default paths from a local `config.json`, with quick overrides available straight from the terminal.

---

## Configuration (`config.json`)

The script looks for a `config.json` file in the working directory by default. Example structure:

{
