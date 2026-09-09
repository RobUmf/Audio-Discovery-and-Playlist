# DeleteRecord (`deleterecord.py`)

## Overview
`deleterecord.py` is an interactive command-line maintenance tool designed for querying, inspecting, and selectively removing records from your SQLite audio database (`audio_database.db`). It includes built-in safety features to safeguard your data before any modifications are made.

## Features
* **Optional Timestamped Backups**: On startup, the script prompts you to create a secure backup copy of your database (e.g., `audio_database_backup_YYYYMMDD_HHMMSS.db`) before any actions can take place.
* **Expanded Search Capabilities**: Query records using an exact numeric database ID, or partial text matches across song titles, artists, album artists, albums, and file paths.
* **Detailed Vertical View**: Displays all tracked metadata fields (such as DSP metrics, health statistics, and paths) cleanly line-by-line.
* **Interactive Management**: Prompt-driven workflow per record letting you choose whether to delete it (`d`), skip it (`s`), or quit the session (`q`).

## Usage
Run the script from your terminal:

python3 deleterecord.py
