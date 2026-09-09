#!/usr/bin/env python3
import json
import argparse
from pathlib import Path
from collections import Counter
import sqlite3

def format_size(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def analyze_folder(folder_path):
    p = Path(folder_path)
    if not p.exists():
        print(f"❌ Path does not exist: {p}")
        return None, 0, 0
    
    extensions = ('.mp3', '.flac', '.opus', '.wav', '.m4a')
    found_files = [f for f in p.rglob('*') if f.suffix.lower() in extensions]
    
    counts = Counter(f.suffix.lower() for f in found_files)
    total_size = sum(f.stat().st_size for f in found_files if f.is_file())
    return counts, len(found_files), total_size

def analyze_database(db_path):
    p = Path(db_path)
    if not p.exists():
        print(f"⚠️ Database not found at: {p}")
        return None
    
    try:
        conn = sqlite3.connect(p)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) AS total_records,
                SUM(CASE WHEN album_artist IS NOT NULL AND album_artist != '' THEN 1 ELSE 0 END) AS total_with_artist,
                SUM(CASE WHEN grouping IS NOT NULL AND grouping != '' THEN 1 ELSE 0 END) AS total_with_grouping,
                SUM(CASE WHEN health_est_cutoff_hz IS NOT NULL THEN 1 ELSE 0 END) AS total_with_cutoff_hz,
                SUM(CASE WHEN youtube_url IS NOT NULL AND youtube_url != '' AND youtube_url != 'None' THEN 1 ELSE 0 END) AS total_with_youtube_url
            FROM tracks;
        """)
        row = cursor.fetchone()
        conn.close()
        return {
            "total_records": row[0],
            "total_with_artist": row[1],
            "total_with_grouping": row[2],
            "total_with_cutoff_hz": row[3],
            "total_with_youtube_url": row[4]
        }
    except Exception as e:
        print(f"❌ Error querying database: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audio Repository and Database Audit Tool")
    parser.add_argument("-c", "--config", default="config.json", help="Path to JSON config file")
    parser.add_argument("-i", "--input", help="Input music directory (overrides config)")
    parser.add_argument("-o", "--output", help="Output compressed directory (overrides config)")
    parser.add_argument("-d", "--db", help="Path to SQLite database")
    args = parser.parse_args()

    config = {}
    config_file = Path(args.config)
    if config_file.exists():
        print(f"📄 Loading configuration from {config_file}")
        with open(config_file, 'r') as f:
            config = json.load(f)
    else:
        print(f"⚠️ Warning: Config file '{args.config}' not found. Using default paths.")

    input_dir = Path(args.input or config.get("input_dir", '/storage/2013-1E1B/musicraw')).expanduser()
    output_dir = Path(args.output or config.get("output_dir", '/storage/2013-1E1B/128mp3')).expanduser()
    db_path = Path(args.db or config.get("db_path", 'audio_database.db')).expanduser()

    folders = {
        "Raw Library (musicraw)": input_dir,
        "Compressed Library (128mp3)": output_dir
    }

    print("=========================================")
    print("      AUDIO REPOSITORY & DB AUDIT        ")
    print("=========================================")

    for name, path in folders.items():
        print(f"\n📁 {name}")
        print(f"   Path: {path}")
        counts, total_count, total_size = analyze_folder(path)
        
        if counts is not None:
            if total_count == 0:
                print("   (Folder is empty)")
            else:
                for ext, count in counts.most_common():
                    print(f"   ├── {ext.upper()}: {count} files")
                print(f"   └── Total: {total_count} files | Size: {format_size(total_size)}")
        print("-" * 41)

    print(f"\n🗄️ Database Analytics")
    print(f"   Path: {db_path}")
    db_stats = analyze_database(db_path)
    if db_stats:
        print(f"   ├── Total Records:           {db_stats['total_records']:,}")
        print(f"   ├── Total with Artist:       {db_stats['total_with_artist']:,}")
        print(f"   ├── Total with Grouping:     {db_stats['total_with_grouping']:,}")
        print(f"   ├── Total with Cutoff (Hz):  {db_stats['total_with_cutoff_hz']:,}")
        print(f"   └── Total with YouTube URL:  {db_stats['total_with_youtube_url']:,}")
    print("=========================================")