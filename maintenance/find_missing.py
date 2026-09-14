#!/usr/bin/env python3
"""
Recursive Audio Archive Gap Finder
Recursively walks target subfolders from config.json and checks against database records.
"""

import os
import json
import sqlite3
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Find database records missing from target directory subfolders recursively.")
    parser.add_argument("-c", "--config", default="config.json", help="Path to JSON config file")
    parser.add_argument("--db", default=None, help="Path to SQLite database (overrides config)")
    parser.add_argument("--target", default=None, help="Target music directory (overrides config)")
    parser.add_argument("--export", default=None, help="Path to export missing tracks report to a text file")
    args = parser.parse_args()

    # Load configuration from JSON
    config = {}
    config_file = Path(args.config)
    if config_file.exists():
        print(f"📄 Loading configuration from {config_file}")
        with open(config_file, 'r') as f:
            config = json.load(f)
    else:
        print(f"⚠️ Warning: Config file '{args.config}' not found. Using default fallbacks.")

    # Resolve database and target paths dynamically from config or args
    db_path_val = args.db or config.get("db_path", "audio_database.db")
    db_path = Path(db_path_val)
    if not db_path.is_absolute():
        db_path = Path.cwd() / db_path

    target_dir_val = args.target or config.get("output_dir", "/storage/2013-1E1B/128mp3")
    target_dir = Path(target_dir_val)

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

    # Step 1: Recursively scan target directory for all MP3 files across subfolders
    existing_files = set()
    existing_stems = set()
    for root, _, files in os.walk(target_dir):
        for f in files:
            if f.lower().endswith(".mp3"):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, target_dir)
                existing_files.add(rel_path.lower())
                existing_stems.add(os.path.splitext(f)[0].lower().strip())

    print(f"[*] Scanned target directory ({target_dir}): {len(existing_files)} MP3 files found across all subfolders.")
    print(f"[*] Total records in database ({db_path.name}): {len(rows)}\n")

    missing_records = []

    for row in rows:
        keys = row.keys()
        file_col = next((row[k] for k in keys if k.lower() in ['filename', 'file_name', 'file', 'path', 'filepath'] and row[k]), None)
        
        if not file_col:
            continue

        raw_path = str(file_col)
        base_name = os.path.basename(raw_path)
        stem = os.path.splitext(base_name)[0].lower().strip()
        
        # Check if this file stem or filename exists anywhere in the target folder tree
        if stem not in existing_stems and base_name.lower() not in existing_files:
            artist = next((row[k] for k in keys if k.lower() in ['artist', 'artist_name'] and row[k]), "Unknown Artist")
            album = next((row[k] for k in keys if k.lower() in ['album', 'album_name'] and row[k]), "Unknown Album")
            title = next((row[k] for k in keys if k.lower() in ['title', 'track_title', 'name'] and row[k]), stem)
            
            missing_records.append({
                "artist": str(artist),
                "album": str(album),
                "title": str(title),
                "file": base_name
            })

    print("=== RECURSIVE GAP ANALYSIS ===")
    print(f"Database tracks missing in target subfolders: {len(missing_records)}\n")

    if missing_records:
        print("--- Missing Tracks ---")
        for item in missing_records[:40]:  # Display up to the first 40
            print(f"  [Missing] {item['artist']} - {item['album']} -> {item['title']} ({item['file']})")
        if len(missing_records) > 40:
            print(f"  ... and {len(missing_records) - 40} more tracks.")
        
        # Handle file export if requested
        if args.export:
            export_path = Path(args.export)
            if not export_path.is_absolute():
                export_path = Path.cwd() / export_path
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write("=== RECURSIVE GAP ANALYSIS REPORT ===\n")
                f.write(f"Total Missing Tracks: {len(missing_records)}\n\n")
                for item in missing_records:
                    f.write(f"{item['artist']} - {item['album']} -> {item['title']} ({item['file']})\n")
            print(f"\n📄 Successfully exported missing records report to: {export_path}")
    else:
        print("  (None! Every database record has a matching MP3 file nested in the subfolders.)")

    conn.close()

if __name__ == "__main__":
    main()