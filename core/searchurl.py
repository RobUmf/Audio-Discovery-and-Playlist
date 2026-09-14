import sqlite3
import os
import json
import time
import argparse
import subprocess
import concurrent.futures
from datetime import datetime
from pathlib import Path

def print_ts(msg):
    """Print message with a clear timestamp prefix."""
    now = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{now} {msg}")

def perform_search(track_info, timeout_sec):
    rowid, search_term = track_info
    
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--print", "url",
        "--no-playlist",
        "--no-warnings",
        "--ignore-errors",
        f"ytsearch1:{search_term}"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
        urls = [line.strip() for line in result.stdout.splitlines() if line.strip().startswith("http")]
        
        if urls:
            return rowid, search_term, urls[0], None
        else:
            return rowid, search_term, None, "No match found"
    except subprocess.TimeoutExpired:
        return rowid, search_term, None, f"Timed out after {timeout_sec}s"
    except Exception as e:
        return rowid, search_term, None, str(e)

def search_youtube_and_populate(db_path, num_workers, timeout_sec=10):
    db_file = Path(db_path).expanduser().resolve()
    if not db_file.exists():
        print_ts(f"❌ Database not found at '{db_file}'.")
        return

    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT rowid, original_path, artist, album_artist 
            FROM tracks 
            WHERE youtube_url IS NULL OR youtube_url = 'None' OR youtube_url = ''
        """)
    except sqlite3.OperationalError as e:
        print_ts(f"❌ Database query error: {e}")
        conn.close()
        return

    rows = cursor.fetchall()
    total_remaining = len(rows)
    if total_remaining == 0:
        print_ts("🎉 No pending tracks needing YouTube URLs!")
        conn.close()
        return

    print_ts(f"🚀 Processing {total_remaining} tracks using {num_workers} parallel workers...")
    print_ts(f"⚙️ Settings: Workers={num_workers}, Timeout={timeout_sec}s, DB Path={db_file}")

    tasks = []
    for rowid, original_path, artist, album_artist in rows:
        path_obj = Path(original_path)
        filename_stem = path_obj.stem
        artist_to_use = (artist or album_artist or "").strip()
        
        if artist_to_use and artist_to_use.lower() not in filename_stem.lower():
            search_term = f"{artist_to_use} - {filename_stem}"
        else:
            search_term = filename_stem
            
        tasks.append((rowid, search_term))

    completed_count = 0
    matched_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = {
            executor.submit(perform_search, task, timeout_sec): task 
            for task in tasks
        }
        
        for future in concurrent.futures.as_completed(futures):
            completed_count += 1
            rowid, search_term, video_url, error_msg = future.result()
            
            if video_url:
                cursor.execute("UPDATE tracks SET youtube_url = ? WHERE rowid = ?", (video_url, rowid))
                conn.commit()
                matched_count += 1
                print_ts(f"[{completed_count}/{total_remaining}] ✅ Match: {search_term} -> {video_url}")
            else:
                print_ts(f"[{completed_count}/{total_remaining}] ⚠️ Miss: {search_term} ({error_msg})")

    conn.close()
    print_ts(f"✅ Processing complete! Populated {matched_count}/{total_remaining} tracks.")

def main():
    # Calculate default workers as CPU count - 1 (minimum 1)
    cpu_cores = os.cpu_count() or 2
    default_workers = max(1, cpu_cores - 1)

    parser = argparse.ArgumentParser(description="High-speed parallel YouTube URL search and SQLite population")
    parser.add_argument("-c", "--config", default="config.json", help="Path to JSON config file")
    parser.add_argument("--db", default="audio_database.db", help="SQLite database path")
    parser.add_argument("-w", "--workers", type=int, default=default_workers, help=f"Number of parallel worker threads (default: {default_workers} [CPU cores - 1])")
    parser.add_argument("-t", "--timeout", type=int, default=10, help="Search timeout in seconds per track (default: 10)")
    args = parser.parse_args()

    config = {}
    config_file = Path(args.config)
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)

    db_path_val = config.get("db_path", args.db)
    workers_val = config.get("workers", args.workers)
    timeout_val = config.get("timeout", args.timeout)

    search_youtube_and_populate(
        db_path=db_path_val,
        num_workers=workers_val,
        timeout_sec=timeout_val
    )

if __name__ == "__main__":
    main()
