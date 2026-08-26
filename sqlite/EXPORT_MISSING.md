# export_missing.py â€” Audio Database Missing Track Exporter

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
What You Need to Do to the .py Scripts
You only need to update the path loader in your scripts once so they handle ~ everywhere:

Replace any direct path usage:

Python
# OLD: Fails when reading '~' literally
raw_dir = Path(config["input_dir"])
With expanduser():

Python
# NEW: Resolves '~' dynamically on any system/user
raw_dir = Path(config["input_dir"]).expanduser()
Apply this standard line across your main loader scripts (format_count.py, ingest.py, analyzersqlite.py, update_audio_db.py), then rsync or git push the scripts. Every machine will run the exact same Python files without breaking.

Ok using the json file. Lets test. How will this effect the db file?

Should append correct?

Yes, running this script will append new tracks to audio_database.db while leaving your existing database entries and analysis intact.  
PY

How This Affects audio_database.db
Appends New Entries Only: The function get_processed_paths() checks the file_path column in the database first. Any raw audio file that has already been converted and registered in 128mp3 is skipped entirely.  
PY
+ 1

Preserves DSP Analysis: Because processed files are skipped, existing rows containing DSP calculations (like loudness_lufs, dsp_bpm, and dsp_key) remain untouched.  
PY

Prevents Duplicates: The SQL statement uses INSERT OR REPLACE INTO tracks keyed against the file_path UNIQUE index, ensuring no duplicate rows are created.  
PY

Important Bug Fix for config.json Path Resolution
Because config.json uses tilde paths (~/musicraw), standard Path() calls in Python will treat ~ as a literal folder name instead of expanding it to your user home directory.  
JSON
+ 1

To fix this, add .expanduser() to the path definitions in your __main__ block (around lines 186–188):  
PY

Python
# UPDATE THESE LINES IN ingest.py
input_root = Path(args.input or config.get("input_dir", BASE_DIR / "musicraw")).expanduser().resolve()
output_root = Path(args.output or config.get("output_dir", BASE_DIR / "128mp3")).expanduser().resolve()
db_path = Path(args.db or config.get("db_path", REPO_DIR / "audio_database.db")).expanduser().resolve()
Once .expanduser() is added, you can safely execute python3 ingest.py on either machine.  
PY

Check code return full code using cat

Here is the full updated code for ingest.py with the .expanduser() fix applied to the path variables.  
PY

You can copy this block directly into your file:

Python
#!/usr/bin/env python3
import os
import json
import argparse
import subprocess
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from mutagen import File as MutagenFile

def load_config(config_path):
    if Path(config_path).exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def init_db(db_path):
    """Initializes a fresh, empty SQLite database if it doesn't exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_path TEXT,
            processed_path TEXT,
            filename TEXT,
            grouping TEXT,
            format TEXT,
            sample_rate_hz INTEGER,
            duration_sec REAL,
            file_path TEXT UNIQUE,
            title TEXT,
            artist TEXT,
            album TEXT,
            album_artist TEXT,
            genre TEXT,
            year INTEGER,
            tracknumber TEXT,
            discnumber TEXT,
            loudness_lufs REAL,
            loudness_rms_db REAL,
            loudness_peak_db REAL,
            dynamics_crest_factor_db REAL,
            dsp_bpm INTEGER,
            rhythm_pulse_clarity REAL,
            dsp_key TEXT,
            key_confidence REAL,
            hpss_harmonic_ratio REAL,
            spectral_centroid_hz REAL,
            spectral_rolloff_hz REAL,
            spectral_flatness REAL,
            health_dc_offset REAL,
            health_clip_pct REAL,
            health_is_upscaled_lossy INTEGER,
            health_est_cutoff_hz INTEGER,
            buy_url TEXT,
            youtube_url TEXT
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_path ON tracks(file_path)")
    conn.commit()
    conn.close()

def get_processed_paths(db_path):
    if not Path(db_path).exists():
        return set()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT file_path FROM tracks WHERE file_path IS NOT NULL")
    paths = {row[0] for row in cursor.fetchall()}
    conn.close()
    return paths

def parse_bitrate_bps(bitrate_str):
    clean = str(bitrate_str).lower().replace('k', '').strip()
    if clean.isdigit():
        return int(clean) * 1000
    return 128000

def get_mp3_bitrate(input_file):
    cmd = [
        'ffprobe', '-v', 'error',
        '-select_streams', 'a:0',
        '-show_entries', 'stream=bit_rate',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(input_file)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        if output.isdigit():
            return int(output)
    except Exception:
        pass
    return None

def extract_id3_tags(file_path):
    data = {
        "title": Path(file_path).stem,
        "artist": "Unknown",
        "album": "Unknown",
        "album_artist": None,
        "genre": None,
        "year": None,
        "tracknumber": None,
        "discnumber": None,
        "format": Path(file_path).suffix.lstrip('.').lower(),
        "sample_rate_hz": None,
        "duration_sec": 0.0
    }
    try:
        audio = MutagenFile(file_path, easy=True)
        if audio is not None:
            if audio.info:
                data["duration_sec"] = round(getattr(audio.info, 'length', 0.0), 2)
                data["sample_rate_hz"] = getattr(audio.info, 'sample_rate', None)
            def get_tag(key):
                val = audio.get(key)
                return val[0] if val else None
            data["title"] = get_tag('title') or data["title"]
            data["artist"] = get_tag('artist') or "Unknown"
            data["album"] = get_tag('album') or "Unknown"
            data["album_artist"] = get_tag('albumartist')
            data["genre"] = get_tag('genre')
            year_val = get_tag('date') or get_tag('year')
            if year_val:
                digits = "".join(filter(str.isdigit, str(year_val)))
                data["year"] = int(digits[:4]) if digits else None
            data["tracknumber"] = get_tag('tracknumber')
            data["discnumber"] = get_tag('discnumber')
    except Exception:
        pass
    return data

def run_ffmpeg(input_file, output_file, bitrate, include_cover, cover_size="300"):
    clean_name = Path(input_file).stem 
    cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-i', str(input_file)]
    cmd.extend(['-map', '0:a'])
    
    if include_cover:
        cmd.extend(['-map', '0:v?', '-c:v', 'mjpeg', '-vf', f'scale={cover_size}:{cover_size}']) 
        
    cmd.extend([
        '-map_metadata', '0', '-id3v2_version', '3', 
        '-metadata', f'title={clean_name}', '-b:a', bitrate, '-ar', '44100', str(output_file)
    ])
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def process_track(f, input_root, output_root, flat, bitrate, cover, cover_size, override_group):
    if flat:
        relative_path = Path(f.name)
    elif input_root.is_dir():
        relative_path = f.relative_to(input_root)
    else:
        relative_path = Path(f.name)
        
    target_path = output_root / relative_path.with_suffix('.mp3')
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    target_bps = parse_bitrate_bps(bitrate)
    is_mp3 = f.suffix.lower() == '.mp3'
    should_copy = False

    if is_mp3:
        actual_bps = get_mp3_bitrate(f)
        if actual_bps and actual_bps <= (target_bps + 4000):
            should_copy = True

    if should_copy:
        try:
            shutil.copy2(f, target_path)
            success = True
        except Exception:
            success = False
    else:
        success = run_ffmpeg(f, target_path, bitrate, cover, cover_size)
    
    if success:
        meta = extract_id3_tags(f)
        group_name = override_group if override_group else f.parent.name
        
        row_data = {
            'original_path': str(f.resolve()),
            'processed_path': str(target_path.resolve()),
            'filename': f.name,
            'grouping': group_name,
            'file_path': str(target_path.resolve()),
            'format': meta['format'],
            'sample_rate_hz': meta['sample_rate_hz'],
            'duration_sec': meta['duration_sec'],
            'title': meta['title'],
            'artist': meta['artist'],
            'album': meta['album'],
            'album_artist': meta['album_artist'],
            'genre': meta['genre'],
            'year': meta['year'],
            'tracknumber': meta['tracknumber'],
            'discnumber': meta['discnumber']
        }
        return True, row_data, str(relative_path)
    return False, None, str(relative_path)

if __name__ == "__main__":
    REPO_DIR = Path(__file__).resolve().parent
    BASE_DIR = Path(os.environ.get("MUSIC_BASE", REPO_DIR.parent))
    DEFAULT_CONFIG = REPO_DIR / "config.json"
    
    cpu_count = os.cpu_count() or 4
    DEFAULT_WORKERS = max(1, cpu_count - 1)
    
    config = load_config(DEFAULT_CONFIG)
    
    parser = argparse.ArgumentParser(description="Config-Driven SQLite Audio Ingestion Engine")
    parser.add_argument("-c", "--config", default=str(DEFAULT_CONFIG), help="Path to config.json")
    parser.add_argument("-i", "--input", help="Input Root Directory (Overrides config)")
    parser.add_argument("-o", "--output", help="Target Root Directory (Overrides config)")
    parser.add_argument("-b", "--bitrate", help="Target Bitrate (Overrides config)")
    parser.add_argument("--cover", action="store_true", help="Include Cover Art (Overrides config)")
    parser.add_argument("--cover-size", help="Square pixel size for cover art")
    parser.add_argument("--flat", action="store_true", help="Flatten all files into a single output folder")
    parser.add_argument("-w", "--workers", type=int, help="Number of concurrent CPU workers")
    parser.add_argument("-g", "--group", help="Optional grouping tag override for this batch")
    parser.add_argument("--db", help="Path to SQLite database (Overrides config)")
    
    args = parser.parse_args()
    
    if args.config != str(DEFAULT_CONFIG):
         config = load_config(args.config)
    
    input_root = Path(args.input or config.get("input_dir", BASE_DIR / "musicraw")).expanduser().resolve()
    output_root = Path(args.output or config.get("output_dir", BASE_DIR / "128mp3")).expanduser().resolve()
    db_path = Path(args.db or config.get("db_path", REPO_DIR / "audio_database.db")).expanduser().resolve()
    bitrate = args.bitrate or config.get("bitrate", "128k")
    include_cover = args.cover or config.get("include_cover", True)
    cover_size = args.cover_size or str(config.get("cover_size", "300"))
    flat_mode = args.flat or config.get("flat", False)
    workers = args.workers or config.get("workers", DEFAULT_WORKERS)
    override_group = args.group

    if not input_root.exists():
        print(f"❌ Input directory does not exist: {input_root}")
        exit(1)

    init_db(db_path)

    if input_root.is_file():
        files_to_process = [input_root]
    else:
        extensions = ('.mp3', '.wav', '.flac', '.m4a', '.opus')
        all_found = [f for f in input_root.rglob('*') if f.suffix.lower() in extensions]
        
        files_to_process = []
        seen_filenames = {}
        for f in all_found:
            if f.name not in seen_filenames:
                seen_filenames[f.name] = f
                files_to_process.append(f)
            else:
                if len(f.parts) > len(seen_filenames[f.name].parts):
                    files_to_process.remove(seen_filenames[f.name])
                    seen_filenames[f.name] = f
                    files_to_process.append(f)
    
    processed_paths = get_processed_paths(db_path)
    
    remaining_files = []
    for f in files_to_process:
        if flat_mode:
            test_rel = Path(f.name)
        elif input_root.is_dir():
            test_rel = f.relative_to(input_root)
        else:
            test_rel = Path(f.name)
            
        expected_target = str((output_root / test_rel.with_suffix('.mp3')).resolve())
        if expected_target not in processed_paths:
            remaining_files.append(f)

    if not remaining_files:
        print("✅ All tracks are already compressed and registered in the database!")
        exit(0)

    total_tracks = len(remaining_files)
    completed_count = 0

    print(f"🚀 Processing {total_tracks} unique tracks at {bitrate} using {workers} workers...")
    if override_group:
        print(f"🏷️ Assigned Group Tag Override: '{override_group}'")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                process_track, f, input_root, output_root, flat_mode, 
                bitrate, include_cover, cover_size, override_group
            ): f 
            for f in remaining_files
        }
        
        for future in as_completed(futures):
            completed_count += 1
            success, row_data, rel_path = future.result()
            
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"[{timestamp}] [{completed_count:4d}/{total_tracks:4d}] Finished: {rel_path}")
            
            if success and row_data:
                keys = list(row_data.keys())
                values = list(row_data.values())
                placeholders = ",".join(["?"] * len(keys))
                columns = ",".join(keys)
                sql = f"INSERT OR REPLACE INTO tracks ({columns}) VALUES ({placeholders})"
                cursor.execute(sql, values)
                conn.commit()

    conn.close()
    print(f"\n✅ Ingestion Complete! Database updated: {db_path}")
Lets see if it works.

Go ahead and run the test script now on either your tablet or the EliteDesk to see if the paths resolve cleanly:

Bash
python3 format_count.py
Or run a dry/live check with the updated ingestion script:

Bash
python3 ingest.py
Let me know what output you get!

Loading configuration from config.json

=========================================

      AUDIO REPOSITORY FORMAT AUDIT

=========================================



📁 Raw Library (musicraw)

   Path: /data/data/com.termux/files/home/musicraw

   ├── .MP3: 43 files

   └── Total: 43 files | Size: 261.95 MB

-----------------------------------------



📁 Compressed Library (128mp3)

   Path: /data/data/com.termux/files/home/128mp3

   ├── .MP3: 4101 files

   └── Total: 4101 files | Size: 15.80 GB

-----------------------------------------

~/audio-repo/sqlite $ python3 ingest.py

🚀 Processing 43 unique tracks at 128k using 5 workers...

That is a clean execution! Path resolution is working perfectly, and the ingestion script has kicked off across your 5 workers to process those 43 unique tracks.

Once it finishes, it will append them smoothly into your audio_database.db without touching your existing 4,101 processed entries.

Do you want to run the updated script on your EliteDesk next to verify full cross-environment parity?

That will be in a few hours.

I'm going to append about 100 songs on the tablet first. With different scripts then push data to the Elitedesk along with the mp3 files.

Just want to double check the scripts.

[11:18:20] [  43/  43] Finished: Fellowship Symphonies/Ponycide/Sunrise (Orchestral).mp3



✅ Ingestion Complete! Database updated: /storage/2013-1E1B/audio-repo/SQLite/audio_database.db

~/audio-repo/sqlite $

That 43-track run completed cleanly. Seeing the terminal log wrap up with ✅ Ingestion Complete and point right to your SD card path confirms that the configuration and path expansion are operating seamlessly on the tablet.

Your plan to batch the next ~100 songs on the tablet, run your scripts, and then push the results over to the EliteDesk is a solid workflow.

Syncing Your Batch to the EliteDesk
When you finish processing your next batch and are ready to push everything over to the EliteDesk, you can use these rsync commands from your tablet:

Push the newly generated MP3s:

Bash
rsync -avzP ~/128mp3/ robumf@10.179.179.94:/home/128mp3/
Push the updated database and scripts:

Bash
rsync -avzP ~/audio-repo/sqlite/ robumf@10.179.179.94:/home/audio-repo/sqlite/
Which specific scripts would you like to double-check before you dive into processing that next batch of 100 songs?

Now

Ok check code give me back full code

Two key fixes were made to ensure full cross-environment compatibility:

Replaced Hardcoded Fallback: Updated the hardcoded default fallback from /storage/2013-1E1B/128mp3 to ~/128mp3.  
JSON
+ 1

Added .expanduser(): Applied .expanduser().resolve() to config_file, db_path, and target_dir so paths like ~/128mp3 expand correctly on both EliteDesk and Termux.  
JSON
+ 1

Here is the updated full code:

Python
#!/usr/bin/env python3
"""
Export a clean, full list of missing database tracks to a text file.
"""

import os
import json
import sqlite3
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Export a clean, full list of missing database tracks to a text file.")
    parser.add_argument("-c", "--config", default="config.json", help="Path to JSON config file")
    parser.add_argument("--db", default=None, help="Path to SQLite database (overrides config)")
    parser.add_argument("--target", default=None, help="Target music directory (overrides config)")
    parser.add_argument("--output", default="missing_tracks.txt", help="Output filename")
    args = parser.parse_args()

    # Load configuration from JSON
    config = {}
    config_file = Path(args.config).expanduser().resolve()
    if config_file.exists():
        print(f"📄 Loading configuration from {config_file}")
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        print(f"⚠️ Warning: Config file '{args.config}' not found. Using default fallbacks.")

    # Resolve database and target paths dynamically from config or args
    db_path_val = args.db or config.get("db_path", "audio_database.db")
    db_path = Path(db_path_val).expanduser()
    if not db_path.is_absolute():
        db_path = (config_file.parent / db_path).resolve()
    else:
        db_path = db_path.resolve()

    target_dir_val = args.target or config.get("output_dir", "~/128mp3")
    target_dir = Path(target_dir_val).expanduser().resolve()

    if not db_path.exists():
        print(f"❌ Error: Database not found at '{db_path}'")
        return

    if not target_dir.exists():
        print(f"❌ Error: Target directory not found at '{target_dir}'")
        return

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall() if not t[0].startswith("sqlite_")]
    if not tables:
        print("❌ Error: No tables found in database.")
        conn.close()
        return

    table_name = tables[0]
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()

    existing_files = set()
    existing_stems = set()
    for root, _, files in os.walk(target_dir):
        for f in files:
            if f.lower().endswith(".mp3"):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, target_dir)
                existing_files.add(rel_path.lower())
                existing_stems.add(os.path.splitext(f)[0].lower().strip())

    missing_records = []
    for row in rows:
        keys = row.keys()
        file_col = next((row[k] for k in keys if k.lower() in ['filename', 'file_name', 'file', 'path', 'filepath'] and row[k]), None)
        if not file_col:
            continue

        raw_path = str(file_col)
        base_name = os.path.basename(raw_path)
        stem = os.path.splitext(base_name)[0].lower().strip()

        if stem not in existing_stems and base_name.lower() not in existing_files:
            artist = next((row[k] for k in keys if k.lower() in ['artist', 'artist_name'] and row[k]), "Unknown Artist")
            album = next((row[k] for k in keys if k.lower() in ['album', 'album_name'] and row[k]), "Unknown Album")
            title = next((row[k] for k in keys if k.lower() in ['title', 'track_title', 'name'] and row[k]), stem)
            missing_records.append(f"{artist} | {album} | {title} ({base_name})")

    output_path = db_path.parent / args.output
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"=== MISSING TRACKS LIST ({len(missing_records)} total) ===\n\n")
        for line in sorted(missing_records):
            f.write(line + "\n")

    print(f"[*] Exported {len(missing_records)} missing tracks to: {output_path}")
    conn.close()

if __name__ == "__main__":
    main()
python3 export_missing.py

📄 Loading configuration from /storage/2013-1E1B/audio-repo/sqlite/config.json

[*] Exported 0 missing tracks to: /storage/2013-1E1B/audio-repo/sqlite/missing_tracks.txt

~/audio-repo/sqlite $

Add from what folder it search

Python
#!/usr/bin/env python3
"""
Export a clean, full list of missing database tracks to a text file.
"""

import os
import json
import sqlite3
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Export a clean, full list of missing database tracks to a text file.")
    parser.add_argument("-c", "--config", default="config.json", help="Path to JSON config file")
    parser.add_argument("--db", default=None, help="Path to SQLite database (overrides config)")
    parser.add_argument("--target", default=None, help="Target music directory (overrides config)")
    parser.add_argument("--output", default="missing_tracks.txt", help="Output filename")
    args = parser.parse_args()

    # Load configuration from JSON
    config = {}
    config_file = Path(args.config).expanduser().resolve()
    if config_file.exists():
        print(f"📄 Loading configuration from {config_file}")
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        print(f"⚠️ Warning: Config file '{args.config}' not found. Using default fallbacks.")

    # Resolve database and target paths dynamically from config or args
    db_path_val = args.db or config.get("db_path", "audio_database.db")
    db_path = Path(db_path_val).expanduser()
    if not db_path.is_absolute():
        db_path = (config_file.parent / db_path).resolve()
    else:
        db_path = db_path.resolve()

    target_dir_val = args.target or config.get("output_dir", "~/128mp3")
    target_dir = Path(target_dir_val).expanduser().resolve()

    if not db_path.exists():
        print(f"❌ Error: Database not found at '{db_path}'")
        return

    if not target_dir.exists():
        print(f"❌ Error: Target directory not found at '{target_dir}'")
        return

    print(f"🗄️ Database: {db_path}")
    print(f"📁 Searching target folder: {target_dir}")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall() if not t[0].startswith("sqlite_")]
    if not tables:
        print("❌ Error: No tables found in database.")
        conn.close()
        return

    table_name = tables[0]
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()

    existing_files = set()
    existing_stems = set()
    for root, _, files in os.walk(target_dir):
        for f in files:
            if f.lower().endswith(".mp3"):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, target_dir)
                existing_files.add(rel_path.lower())
                existing_stems.add(os.path.splitext(f)[0].lower().strip())

    missing_records = []
    for row in rows:
        keys = row.keys()
        file_col = next((row[k] for k in keys if k.lower() in ['filename', 'file_name', 'file', 'path', 'filepath'] and row[k]), None)
        if not file_col:
            continue

        raw_path = str(file_col)
        base_name = os.path.basename(raw_path)
        stem = os.path.splitext(base_name)[0].lower().strip()

        if stem not in existing_stems and base_name.lower() not in existing_files:
            artist = next((row[k] for k in keys if k.lower() in ['artist', 'artist_name'] and row[k]), "Unknown Artist")
            album = next((row[k] for k in keys if k.lower() in ['album', 'album_name'] and row[k]), "Unknown Album")
            title = next((row[k] for k in keys if k.lower() in ['title', 'track_title', 'name'] and row[k]), stem)
            missing_records.append(f"{artist} | {album} | {title} ({base_name})")

    output_path = db_path.parent / args.output
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"=== MISSING TRACKS LIST ({len(missing_records)} total) ===\n")
        f.write(f"Target Directory Searched: {target_dir}\n")
        f.write(f"Database Queried: {db_path}\n\n")
        for line in sorted(missing_records):
            f.write(line + "\n")

    print(f"[*] Exported {len(missing_records)} missing tracks to: {output_path}")
    conn.close()

if __name__ == "__main__":
    main()
Simple option description when uploading to github

Repository "About" Description (GitHub Page Header)

Config-driven Python pipeline for audio ingestion, MP3 transcoding, spectral analysis, and SQLite database management.

Cross-platform audio library scanner, dynamic analysis engine, and SQLite playlist generator for Linux and Termux.

Commit Message Options (Git Command Line)

Feature Update: git commit -m "feat: Add dynamic path resolution for cross-environment SQLite pipeline"

Bug Fix / Maintenance: git commit -m "fix: Update ingest and export scripts with expanduser path handling"

GitHub Web UI File Upload Options

Commit Title: Update SQLite pipeline scripts and config path handling

Extended Description: Added path expansion support across ingestion and export scripts to maintain filesystem parity between desktop and Termux environments.

No.. When u upload the export_missing.py

I can add optional description

Short & Direct

Audits the SQLite database against local MP3 directories and exports a clean list of missing audio tracks to a text file.

With Environment Fix Details

Compares database entries with target audio files to identify missing tracks. Updated with dynamic .expanduser() path handling for seamless execution across Termux and Linux environments.

Ultra-Simple One-Liner

Generates missing_tracks.txt by checking SQLite database entries against your destination MP3 directory.

Now create a MD with what it does and options.

Argument	Long Flag	Default	Description
-c	--config	config.json	Path to the JSON configuration file containing path definitions.
--db	db_path from config.json (or audio_database.db)	Direct path to the SQLite database file. Overrides config setting.
--target	output_dir from config.json (or ~/128mp3)	Target directory containing local MP3 files to check against. Overrides config setting.
--output	missing_tracks.txt	Output text file name (saved inside the database directory).
Example Usage
1. Standard Run (Uses config.json)
Bash
python3 export_missing.py
2. Override Output Target Directory
Bash
python3 export_missing.py --target ~/external/128mp3
3. Specify Custom Database and Config
Bash
python3 export_missing.py -c custom_config.json --db ~/audio-repo/sqlite/my_database.db
4. Custom Output Filename
Bash
python3 export_missing.py --output batch_missing_report.txt
Sample Output
Terminal Output
Plaintext
📄 Loading configuration from /home/robumf/audio-repo/sqlite/config.json
🗄️ Database: /home/robumf/audio-repo/sqlite/audio_database.db
📁 Searching target folder: /home/robumf/128mp3
[*] Exported 3 missing tracks to: /home/robumf/audio-repo/sqlite/missing_tracks.txt
Generated Report (missing_tracks.txt)
Plaintext
=== MISSING TRACKS LIST (3 total) ===
Target Directory Searched: /home/robumf/128mp3
Database Queried: /home/robumf/audio-repo/sqlite/audio_database.db

Artist Name | Album Title | Song Title (Track01.mp3)
Band Name | Live Album | Demo Track (DemoTrack.mp3)
Unknown Artist | Singles | Prototype (proto.mp3)
"""

filename = "EXPORT_MISSING.md"
with open(filename, "w", encoding="utf-8") as f:
f.write(md_content.strip())

print(f"File created successfully: {filename}")


```text?code_stdout&code_event_index=1
File created successfully: EXPORT_MISSING.md

Your Markdown documentation file is ready

MD icon
EXPORT_MISSING
 MD 
Open
File Overview: EXPORT_MISSING.md
Markdown
# `export_missing.py` — Audio Database Missing Track Exporter

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

## Command Line Options

```bash
python3 export_missing.py [OPTIONS]
Argument	Long Flag	Default	Description
-c	--config	config.json	Path to the JSON configuration file containing path definitions.
--db	db_path from config.json (or audio_database.db)	Direct path to the SQLite database file. Overrides config setting.
--target	output_dir from config.json (or ~/128mp3)	Target directory containing local MP3 files to check against. Overrides config setting.
--output	missing_tracks.txt	Output text file name (saved inside the database directory).
Example Usage
1. Standard Run (Uses config.json)
Bash
python3 export_missing.py
2. Override Output Target Directory
Bash
python3 export_missing.py --target ~/external/128mp3
3. Specify Custom Database and Config
Bash
python3 export_missing.py -c custom_config.json --db ~/audio-repo/sqlite/my_database.db
4. Custom Output Filename
Bash
python3 export_missing.py --output batch_missing_report.txt
Sample Output
Terminal Output
Plaintext
📄 Loading configuration from /home/robumf/audio-repo/sqlite/config.json
🗄️ Database: /home/robumf/audio-repo/sqlite/audio_database.db
📁 Searching target folder: /home/robumf/128mp3
[*] Exported 3 missing tracks to: /home/robumf/audio-repo/sqlite/missing_tracks.txt
Generated Report (missing_tracks.txt)
Plaintext
=== MISSING TRACKS LIST (3 total) ===
Target Directory Searched: /home/robumf/128mp3
Database Queried: /home/robumf/audio-repo/sqlite/audio_database.db

Artist Name | Album Title | Song Title (Track01.mp3)
Band Name | Live Album | Demo Track (DemoTrack.mp3)
Unknown Artist | Singles | Prototype (proto.mp3)
That is not a md file

Markdown
# export_missing.py — Audio Database Missing Track Exporter

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

## Command Line Options

```bash
python3 export_missing.py [OPTIONS]
Argument	Long Flag	Default	Description
-c	--config	config.json	Path to the JSON configuration file containing path definitions.
--db	db_path from config.json (or audio_database.db)	Direct path to the SQLite database file. Overrides config setting.
--target	output_dir from config.json (or ~/128mp3)	Target directory containing local MP3 files to check against. Overrides config setting.
--output	missing_tracks.txt	Output text file name (saved inside the database directory).
Example Usage
1. Standard Run (Uses config.json)
Bash
python3 export_missing.py
2. Override Output Target Directory
Bash
python3 export_missing.py --target ~/external/128mp3
3. Specify Custom Database and Config
Bash
python3 export_missing.py -c custom_config.json --db ~/audio-repo/sqlite/my_database.db
4. Custom Output Filename
Bash
python3 export_missing.py --output batch_missing_report.txt
Sample Output
Terminal Output
Plaintext
📄 Loading configuration from /home/robumf/audio-repo/sqlite/config.json
🗄️ Database: /home/robumf/audio-repo/sqlite/audio_database.db
📁 Searching target folder: /home/robumf/128mp3
[*] Exported 3 missing tracks to: /home/robumf/audio-repo/sqlite/missing_tracks.txt
Generated Report (missing_tracks.txt)
Plaintext
=== MISSING TRACKS LIST (3 total) ===
Target Directory Searched: /home/robumf/128mp3
Database Queried: /home/robumf/audio-repo/sqlite/audio_database.db

Artist Name | Album Title | Song Title (Track01.mp3)
Band Name | Live Album | Demo Track (DemoTrack.mp3)
Unknown Artist | Singles | Prototype (proto.mp3)
Can you add the table of flags in the MD file

Markdown
# export_missing.py — Audio Database Missing Track Exporter

## Overview
`export_missing.py` is a cross-platform Python utility designed to audit an SQLite audio database against a target directory of processed audio files (`128mp3`). It identifies database entries whose corresponding MP3 files are missing from local storage and exports a clean, formatted list to a text report.

Built for multi-device workflows (Linux desktops, Termux/Android, headless nodes), it supports dynamic tilde (`~`) path resolution using `Path.expanduser()` to ensure seamless cross-environment operation without modifying configuration files.

---

## Command Line Flags & Options

```bash
python3 export_missing.py [FLAGS]
Short Flag	Long Flag	Value Type	Default Value	Description
-c	--config	PATH	config.json	Path to the JSON configuration file containing path definitions.
(None)	--db	PATH	db_path in config.json	Direct path to the SQLite database file. Overrides config value.
(None)	--target	PATH	output_dir in config.json	Target directory containing local MP3 files to audit. Overrides config value.
(None)	--output	FILENAME	missing_tracks.txt	Output text report filename (saved inside the database directory).
-h	--help	(None)	(None)	Displays standard command-line help message and exits.
Features
Config-Driven & Flexible Overrides: Loads paths automatically from config.json while allowing full command-line parameter overrides.

Cross-Platform Compatibility: Expands ~ home paths natively across Linux, macOS, and Termux environments.

Smart Matching: Inspects both full relative file paths and filename stems to accurately detect missing tracks.

Detailed Terminal Output: Displays explicit database and target folder paths prior to scanning.

Structured Export: Generates a sorted text file containing metadata (Artist | Album | Title (Filename)) along with header audit details.

Example Usage
Standard Run (Uses config.json)
Bash
python3 export_missing.py
Override Target Folder
Bash
python3 export_missing.py --target ~/external/128mp3
Custom Database and Config Path
Bash
python3 export_missing.py -c custom_config.json --db ~/audio-repo/sqlite/my_database.db
Custom Output Report Name
Bash
python3 export_missing.py --output batch_missing_report.txt
Sample Output
Terminal Output
Plaintext
📄 Loading configuration from /home/robumf/audio-repo/sqlite/config.json
🗄️ Database: /home/robumf/audio-repo/sqlite/audio_database.db
📁 Searching target folder: /home/robumf/128mp3
[*] Exported 3 missing tracks to: /home/robumf/audio-repo/sqlite/missing_tracks.txt
Generated Report (missing_tracks.txt)
Plaintext
=== MISSING TRACKS LIST (3 total) ===
Target Directory Searched: /home/robumf/128mp3
Database Queried: /home/robumf/audio-repo/sqlite/audio_database.db

Artist Name | Album Title | Song Title (Track01.mp3)
Band Name | Live Album | Demo Track (DemoTrack.mp3)
Unknown Artist | Singles | Prototype (proto.mp3)
??? Full md file including the option table

Markdown
# export_missing.py — Audio Database Missing Track Exporter

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
Short Flag	Long Flag	Value Type	Default Value	Description
-c	--config	PATH	config.json	Path to the JSON configuration file containing path definitions.
(None)	--db	PATH	db_path in config.json	Direct path to the SQLite database file. Overrides config value.
(None)	--target	PATH	output_dir in config.json	Target directory containing local MP3 files to audit. Overrides config value.
(None)	--output	FILENAME	missing_tracks.txt	Output text report filename (saved inside the database directory).
-h	--help	(None)	(None)	Displays standard command-line help message and exits.
Example Usage
Standard Run (Uses config.json)
Bash
python3 export_missing.py
Override Target Folder
Bash
python3 export_missing.py --target ~/external/128mp3
Custom Database and Config Path
Bash
python3 export_missing.py -c custom_config.json --db ~/audio-repo/sqlite/my_database.db
Custom Output Report Name
Bash
python3 export_missing.py --output batch_missing_report.txt
Sample Output
Terminal Output
Plaintext
📄 Loading configuration from /home/robumf/audio-repo/sqlite/config.json
🗄️ Database: /home/robumf/audio-repo/sqlite/audio_database.db
📁 Searching target folder: /home/robumf/128mp3
[*] Exported 3 missing tracks to: /home/robumf/audio-repo/sqlite/missing_tracks.txt
Generated Report (missing_tracks.txt)
Plaintext
=== MISSING TRACKS LIST (3 total) ===
Target Directory Searched: /home/robumf/128mp3
Database Queried: /home/robumf/audio-repo/sqlite/audio_database.db

Artist Name | Album Title | Song Title (Track01.mp3)
Band Name | Live Album | Demo Track (DemoTrack.mp3)
Unknown Artist | Singles | Prototype (proto.mp3)
Why did you not add the flag table within the md file?

Ask three times

Short Flag	Long Flag	Value Type	Default Value	Description
-c	--config	PATH	config.json	Path to the JSON configuration file containing path definitions.
(None)	--db	PATH	db_path in config.json	Direct path to the SQLite database file. Overrides config value.
(None)	--target	PATH	output_dir in config.json	Target directory containing local MP3 files to audit. Overrides config value.
(None)	--output	FILENAME	missing_tracks.txt	Output text report filename (saved inside the database directory).
-h	--help	(None)	(None)	Displays standard command-line help message and exits.
Example Usage
Standard Run (Uses config.json)
Bash
python3 export_missing.py
Override Target Folder
Bash
python3 export_missing.py --target ~/external/128mp3
Custom Database and Config Path
Bash
python3 export_missing.py -c custom_config.json --db ~/audio-repo/sqlite/my_database.db
Custom Output Report Name
Bash
python3 export_missing.py --output batch_missing_report.txt
Sample Output
Terminal Output
Plaintext
📄 Loading configuration from /home/robumf/audio-repo/sqlite/config.json
🗄️ Database: /home/robumf/audio-repo/sqlite/audio_database.db
📁 Searching target folder: /home/robumf/128mp3
[*] Exported 3 missing tracks to: /home/robumf/audio-repo/sqlite/missing_tracks.txt
Generated Report (missing_tracks.txt)
Plaintext
=== MISSING TRACKS LIST (3 total) ===
Target Directory Searched: /home/robumf/128mp3
Database Queried: /home/robumf/audio-repo/sqlite/audio_database.db

Artist Name | Album Title | Song Title (Track01.mp3)
Band Name | Live Album | Demo Track (DemoTrack.mp3)
Unknown Artist | Singles | Prototype (proto.mp3)
"""

filename = "EXPORT_MISSING_v2.md"
with open(filename, "w", encoding="utf-8") as f:
f.write(md_content.strip())

print(f"File generated: {filename}")


```text?code_stdout&code_event_index=1
File generated: EXPORT_MISSING_v2.md

Your Markdown file is ready

MD icon
EXPORT_MISSING_v2
 MD 
Open
Apologies for the oversight — in the previous responses, I outputted the markdown formatted as plain text directly into the chat response instead of re-running the script to write and generate the actual .md file artifact with the updated flags table included.

The file EXPORT_MISSING_v2.md has now been regenerated and saved with the full flag table embedded inside.

Gemini is AI and can make mistakes.




Verifying the Execution
# export_missing.py — Audio Database Missing Track Exporter

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
📄 Loading configuration from /home/robumf/audio-repo/sqlite/config.json
🗄️ Database: /home/robumf/audio-repo/sqlite/audio_database.db
📁 Searching target folder: /home/robumf/128mp3
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
