import sqlite3
import os
import json
import time
import argparse
import subprocess
import concurrent.futures
import difflib
from datetime import datetime
from pathlib import Path

def print_ts(msg):
    """Print message with a clear timestamp prefix."""
    now = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{now} {msg}")

def perform_search(track_info, timeout_sec, min_confidence):
    rowid, search_term = track_info
    
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--print", "%(url)s|%(title)s",
        "--no-playlist",
        "--no-warnings",
        "--ignore-errors",
        f"ytsearch1:{search_term}"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
        
        # Parse the custom output format "url|title"
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        
        if lines:
            parts = lines[0].split('|', 1)
            
            # If we successfully captured both URL and Title
            if len(parts) == 2:
                video_url, vid_title = parts
                
                # Calculate confidence score
                query_norm = search_term.lower()
                title_norm = vid_title.lower()
                confidence = difflib.SequenceMatcher(None, query_norm, title_norm).ratio() * 100
                
                if confidence >= min_confidence:
                    return rowid, search_term, video_url, None, confidence, vid_title
                else:
                    error_msg = f"Low confidence ({confidence:.1f}% < {min_confidence}%) - Found: '{vid_title}'"
                    return rowid, search_term, None, error_msg, confidence, vid_title
            
            # Fallback if yt-dlp didn't return a title
            elif len(parts) == 1 and parts[0].startswith("http"):
                video_url = parts[0]
                return rowid, search_term, video_url, None, 100.0, "Unknown Title"

        return rowid, search_term, None, "No match found", 0.0, ""
        
    except subprocess.TimeoutExpired:
        return rowid, search_term, None, f"Timed out after {timeout_sec}s", 0.0, ""
    except Exception as e:
        return rowid, search_term, None, str(e), 0.0, ""

def search_youtube_and_populate(db_path, num_workers, timeout_sec, min_confidence):
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
    print_ts(f"⚙️ Settings: Workers={num_workers}, Timeout={timeout_sec}s, Min Confidence={min_confidence}%, DB Path={db_file}")

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
            executor.submit(perform_search, task, timeout_sec, min_confidence): task 
            for task in tasks
        }
        
        for future in concurrent.futures.as_completed(futures):
            completed_count += 1
            rowid, search_term, video_url, error_msg, confidence, vid_title = future.result()
            
            if video_url:
                cursor.execute("UPDATE tracks SET youtube_url = ? WHERE rowid = ?", (video_url, rowid))
                conn.commit()
                matched_count += 1
                if vid_title != "Unknown Title":
                    print_ts(f"[{completed_count}/{total_remaining}] ✅ Match ({confidence:.1f}%): {search_term} -> {video_url}")
                else:
                    print_ts(f"[{completed_count}/{total_remaining}] ✅ Match: {search_term} -> {video_url}")
            else:
                print_ts(f"[{completed_count}/{total_remaining}] ⚠️ Miss: {search_term} ({error_msg})")

    conn.close()
    print_ts(f"✅ Processing complete! Populated {matched_count}/{total_remaining} tracks.")

def main():
    cpu_cores = os.cpu_count() or 2
    default_workers = max(1, cpu_cores - 1)

    parser = argparse.ArgumentParser(description="High-speed parallel YouTube URL search and SQLite population")
    parser.add_argument("-c", "--config", default="config.json", help="Path to JSON config file")
    parser.add_argument("--db", default="audio_database.db", help="SQLite database path")
    parser.add_argument("-w", "--workers", type=int, default=default_workers, help=f"Number of parallel worker threads (default: {default_workers})")
    parser.add_argument("-t", "--timeout", type=int, default=10, help="Search timeout in seconds per track (default: 10)")
    parser.add_argument("-m", "--min-confidence", type=float, default=0.0, help="Minimum title similarity confidence percentage (0-100) (default: 0.0)")
    args = parser.parse_args()

    config = {}
    config_file = Path(args.config)
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)

    db_path_val = config.get("db_path", args.db)
    workers_val = config.get("workers", args.workers)
    timeout_val = config.get("timeout", args.timeout)
    min_conf_val = config.get("min_confidence", args.min_confidence)

    search_youtube_and_populate(
        db_path=db_path_val,
        num_workers=workers_val,
        timeout_sec=timeout_val,
        min_confidence=min_conf_val
    )

if __name__ == "__main__":
    main()    except subprocess.TimeoutExpired:
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
