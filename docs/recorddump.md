# FindRecord (`findrecord.py`)

## Overview
`findrecord.py` is an interactive command-line tool designed for querying and managing records inside your SQLite audio database (`audio_database.db`). Unlike the read-only dump tool, this script allows you to search, inspect vertical field details, and selectively delete database entries.

## Features
* **Flexible Search**: Query records using an exact numeric database ID, or partial text matches across song titles, artists, album artists, and file paths[cite: 2].
* **Detailed Vertical View**: Displays all tracked metadata fields (such as DSP metrics, health statistics, and paths) cleanly line-by-line[cite: 2].
* **Interactive Management**: Prompt-driven workflow letting you choose whether to skip a record, delete it from the database, or quit the session[cite: 2].

## Usage
Run the script from your terminal:

python3 findrecord.py
