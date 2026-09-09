Bash
cat << 'EOF' > count.md
# Count Utility (`count.py`)

A lightweight command-line audit and reporting tool for your local audio library and SQLite tracking database.

---

## Features

- **Directory Scanning**: Recursively audits your raw and compressed music libraries (`.mp3`, `.flac`, `.opus`, `.wav`, `.m4a`), breaking down file counts by format and calculating total storage size.
- **Database Metrics**: Connects to your SQLite database (`audio_database.db`) to instantly pull record health metrics (total entries, populated artists, groupings, cutoff frequencies, and YouTube URLs).
- **Config-Driven**: Automatically reads default paths from a local `config.json`, with quick overrides available straight from the terminal.

---

The script looks for a `config.json` file in the working directory by default

Argument,Long Flag,Description,Default Value
-c,--config,Path to custom JSON configuration file,config.json
-i,--input,Path to input music directory (Raw Library),/storage/2013-1E1B/musicraw
-o,--output,Path to output compressed directory (128mp3),/storage/2013-1E1B/128mp3
-d,--db,Path to the SQLite database file,audio_database.db
-h,--help,Show the help message and exit,—

python3 count.

python3 count.py -i /path/to/raw -o /path/to/compressed -d /path/to/database.db -c custom_config.json
