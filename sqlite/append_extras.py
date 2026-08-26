#!/usr/bin/env python3
"""
Scan the target directory (128mp3) for extra/orphan MP3 files,
parse their metadata from folder structure, and append them to the database.
Default behavior is a dry run. Use --apply to write to the database.
"""

import os
import json
import sqlite3
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Find extra MP3 files and append them to the SQLite database.")
    parser.add_argument("-c", "--config", default="config.json", help="Path to JSON config file")
    parser.add_argument("--db", default=None, help="Path to SQLite database (overrides config)")
    parser.add_argument("--target", default=None, help="Target music directory (overrides config)")
    parser.add_argument("--apply", action="store_true", help="Actually insert records into the database (default is dry-run)")
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

    # Resolve paths dynamically
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

    if not args.apply:
        print("\n🛑 DRY RUN MODE: No changes will be written to the database. Use --apply to execute.")

    print(f"🗄️ Database: {db_path}")
    print(f"📁 Scanning target folder: {target_dir}\n")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get table name
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    table_row = cursor.fetchone()
    if not table_row:
        print("❌ Error: No tables found in database.")
        conn.close()
        return
    table_name = table_row[0]

    # Inspect table columns to build a dynamic insert query matching your schema
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = [col['name'] for col in cursor.fetchall()]

    # Get existing records from DB to check for duplicates
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()

    db_filepaths = set()
    db_stems = set()
    for row in rows:
        keys = row.keys()
        file_col = next((row[k] for k in keys if k.lower() in ['filename', 'file_name', 'file', 'path', 'filepath'] and row[k]), None)
        if file_col:
            p_str = str(file_col)
            db_filepaths.add(p_str.lower())
            db_stems.add(Path(p_str).stem.lower().strip())

    # Walk target directory for extra/orphan files
    added_count = 0
    for root, _, files in os.walk(target_dir):
        for f in files:
            if f.lower().endswith(".mp3"):
                full_path = Path(root) / f
                stem = full_path.stem.lower().strip()

                # If file is not in the database, parse and append it
                if str(full_path).lower() not in db_filepaths and stem not in db_stems:
                    parts = full_path.parts
                    try:
                        idx = parts.index(target_dir.name)
                        rel_parts = parts[idx+1:]
                    except ValueError:
                        rel_parts = parts[-2:]

                    # Parse metadata based on folder depth (using your structure logic)
                    if len(rel_parts) == 2:
                        artist = rel_parts[0]
                        album = "Unknown Album"
                        title = full_path.stem
                    elif len(rel_parts) >= 3:
                        artist = rel_parts[0]
                        album = rel_parts[1]
                        title = full_path.stem
                    else:
                        artist = "Unknown Artist"
                        album = "Unknown Album"
                        title = full_path.stem

                    # Construct dynamic insertion depending on available table columns
                    insert_data = {}
                    if 'artist' in columns: insert_data['artist'] = artist
                    if 'album' in columns: insert_data['album'] = album
                    if 'title' in columns: insert_data['title'] = title
                    
                    # Check common path column names
                    for path_col in ['file_path', 'filepath', 'filename', 'file_name', 'path']:
                        if path_col in columns:
                            insert_data[path_col] = str(full_path)
                            break

                    if insert_data:
                        added_count += 1
                        if args.apply:
                            print(f"➕ Inserting: {artist} - {title} ({full_path.name})")
                            cols_to_insert = list(insert_data.keys())
                            placeholders = ", ".join(["?"] * len(cols_to_insert))
                            cols_str = ", ".join(cols_to_insert)
                            sql = f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders})"
                            cursor.execute(sql, list(insert_data.values()))
                        else:
                            print(f"🔍 [DRY RUN] Would insert: {artist} - {title} ({full_path.name})")

    if args.apply:
        conn.commit()
        print(f"\n✅ Successfully appended {added_count} extra tracks to the database!")
    else:
        print(f"\n🛑 Dry run complete. {added_count} extra tracks found, but none were added.")
        print("Run with --apply to write these changes to the database.")

    conn.close()

if __name__ == "__main__":
    main()