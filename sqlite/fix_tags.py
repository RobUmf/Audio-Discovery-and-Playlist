#!/usr/bin/env python3
"""
Update MP3 ID3 tags and SQLite database metadata based on folder structure.
Default behavior is a dry run. Use --apply to execute changes.
Intelligently skips files that are already correctly tagged.
"""

import os
import json
import sqlite3
import argparse
from pathlib import Path
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError

def main():
    parser = argparse.ArgumentParser(description="Update MP3 ID3 tags and SQLite DB from folder structure.")
    parser.add_argument("-c", "--config", default="config.json", help="Path to JSON config file")
    parser.add_argument("--db", default=None, help="Path to SQLite database (overrides config)")
    parser.add_argument("--target", default=None, help="Target music directory (overrides config)")
    parser.add_argument("--apply", action="store_true", help="Apply changes to MP3s and DB (default is dry-run)")
    args = parser.parse_args()

    # Load configuration
    config = {}
    config_file = Path(args.config).expanduser().resolve()
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

    # Resolve paths
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
        print("\n🛑 DRY RUN MODE: Checking for needed updates. No files or records will be modified.")

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    table_row = cursor.fetchone()
    table_name = table_row[0] if table_row else "tracks"

    total_scanned = 0
    already_good = 0
    changed_count = 0

    for root, _, files in os.walk(target_dir):
        for file in files:
            if file.lower().endswith(".mp3"):
                total_scanned += 1
                filepath = Path(root) / file
                
                try:
                    rel_path = filepath.relative_to(target_dir)
                    parts = rel_path.parts
                except ValueError:
                    parts = filepath.parts[-3:]

                # Derive target metadata from folder structure
                if len(parts) >= 3:
                    group = parts[0]
                    album = parts[1]
                elif len(parts) == 2:
                    group = parts[0]
                    album = parts[0]
                else:
                    group = "Unknown"
                    album = "Unknown"

                title = filepath.stem

                # 1. Check if ID3 needs update
                needs_id3_update = False
                try:
                    audio = EasyID3(str(filepath))
                    if audio.get("artist", [""])[0] != group: needs_id3_update = True
                    if audio.get("album", [""])[0] != album: needs_id3_update = True
                    if not audio.get("title"): needs_id3_update = True
                except ID3NoHeaderError:
                    needs_id3_update = True

                # 2. Check if DB needs update
                needs_db_update = False
                cursor.execute(f"SELECT artist FROM {table_name} WHERE title = ?", (title,))
                db_row = cursor.fetchone()
                if db_row and (db_row[0] in ['Unknown', None, '']):
                    needs_db_update = True

                # If perfectly fine, skip
                if not needs_id3_update and not needs_db_update:
                    already_good += 1
                    continue
                
                changed_count += 1

                if args.apply:
                    if needs_id3_update:
                        try:
                            audio = EasyID3(str(filepath))
                        except ID3NoHeaderError:
                            audio = EasyID3()
                            audio.save(str(filepath))
                            audio = EasyID3(str(filepath))
                        
                        audio["artist"] = group
                        audio["album"] = album
                        if not audio.get("title"):
                            audio["title"] = title
                        audio.save()

                    if needs_db_update:
                        sql = f"""
                            UPDATE {table_name} 
                            SET artist = ?, album = ?, grouping = ? 
                            WHERE title = ? AND (artist = 'Unknown' OR artist IS NULL)
                        """
                        cursor.execute(sql, (group, album, group, title))

                    print(f"✅ Updated: {title} (ID3 updated: {needs_id3_update}, DB updated: {needs_db_update})")
                else:
                    print(f"🔍 [DRY RUN] Would update: {file}")
                    print(f"      -> Needs ID3 Fix: {needs_id3_update} | Needs DB Fix: {needs_db_update}")

    if args.apply:
        conn.commit()
        print("\n=== RUN SUMMARY ===")
        print(f"Total files scanned : {total_scanned}")
        print(f"Already good (skipped): {already_good}")
        print(f"Tracks updated      : {changed_count}")
        print("===================")
    else:
        print("\n=== DRY RUN SUMMARY ===")
        print(f"Total files scanned : {total_scanned}")
        print(f"Already perfect     : {already_good}")
        print(f"Requires update     : {changed_count}")
        print("=======================")
        print("Run with --apply to execute these changes.")

    conn.close()

if __name__ == "__main__":
    main()