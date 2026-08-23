
# Gap Finder Tool (`find_missing.py`)

`find_missing.py` is a repository diagnostic tool that recursively scans target music directories and compares them against SQLite database records to identify tracks that are missing from the file system[cite: 1, 3].

---

## 🚀 Key Features

* **Recursive Subfolder Scanning:** Deeply traverses target directories to check every nested MP3 file against database records[cite: 1, 3].
* **Flexible Matching:** Automatically matches files using both clean file stems and full base filenames to prevent false gaps[cite: 1, 3].
* **Report Exporting:** Features an `--export` flag to instantly dump the missing tracks list into a clean text report for review or batch recovery[cite: 1, 3].
* **Config or CLI Driven:** Reads default paths from `config.json`, but allows dynamic overrides via command-line arguments[cite: 1, 3].

---

## 📋 Requirements

* **Python 3.10+** (Recommended sweet spot for compatibility)
* Standard Python libraries only (`os`, `json`, `sqlite3`, `argparse`, `pathlib`)

---

## 🎛️ Command-Line Interface (CLI) Flags

The script accepts the following arguments. Omitted flags fall back to `config.json` defaults[cite: 1, 3]:

* `-c`, `--config` *(path)* : Path to JSON configuration file (Default: `config.json`)[cite: 1, 3].
* `--db` *(path)* : Path to SQLite database (overrides config)[cite: 1, 3].
* `--target` *(path)* : Target music directory to scan recursively (overrides config)[cite: 1, 3].
* `--export` *(path)* : Export the full missing tracks report to a specified text file[cite: 1, 3].

---

## 💡 Example Usage

**Standard Run (Relying on `config.json` defaults):**

python3 find_missing.py
python3 find_missing.py --target "/storage/2013-1E1B/test" --db "./test_audio.db" --export "missing_report.txt"

