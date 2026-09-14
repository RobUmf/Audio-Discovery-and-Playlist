# `fix_tags.py` ” Audio ID3 & Database Metadata Synchronizer

## Overview
`fix_tags.py` is a cross-platform Python utility that synchronizes local MP3 ID3 tags and SQLite database metadata according to folder structures (Artist/Album hierarchies). 

Designed with safety in mind, it operates in **dry-run mode by default** to audit changes, compare existing tags and database rows, and provide a clear statistical breakdown before requiring the explicit `--apply` flag to write modifications.

---

## Features
* **Dry-Run by Default:** Audits and previews all metadata and ID3 changes without modifying files or the database unless explicitly requested.
* **Smart Change Detection:** Intelligently compares current file ID3 tags and database records against folder structures, skipping files that are already pristine.
* **Config-Driven & Flexible Overrides:** Loads paths automatically from `config.json` while allowing command-line overrides for databases and target directories.
* **Cross-Platform Compatibility:** Fully supports tilde (`~`) home path expansion across Linux, macOS, and Termux environments.
* **Comprehensive Run Summary:** Provides clear metrics on total files scanned, already-perfect tracks, and pending updates.

---

## Command Line Flags & Options

python3 fix_tags.py [FLAGS]

| Short Flag | Long Flag | Value Type | Default Value | Description |
| :--- | :--- | :--- | :--- | :--- |
| `-c` | `--config` | `PATH` | `config.json` | Path to the JSON configuration file containing path definitions. |
| *(None)* | `--db` | `PATH` | `db_path` in `config.json` | Direct path to the SQLite database file. Overrides config value. |
| *(None)* | `--target` | `PATH` | `output_dir` in `config.json` | Target directory containing local MP3 files to scan. Overrides config value. |
| *(None)* | `--apply` | *(Flag)* | `False` (Dry run) | Commits changes to MP3 ID3 tags and SQLite database. Without this, runs in dry-run mode. |
| `-h` | `--help` | *(None)* | *(None)* | Displays standard command-line help message and exits. |

---

## Example Usage

### 1. Standard Run (Dry Run Preview & Audit)

python3 fix_tags.py

### 2. Live Run (Writes Updates to MP3 Tags & Database)
python3 fix_tags.py --apply

### 3. Custom Target Folder & Apply
python3 fix_tags.py --target ~/external/128mp3 --apply
