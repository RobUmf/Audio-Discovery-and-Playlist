#!/usr/bin/env python3
import sqlite3
import concurrent.futures
import subprocess
import json
import difflib
import argparse
import os
from datetime import datetime

# --- Configuration Settings ---
DB_PATH = "/storage/2013-1E1B/audio-repo/sqlite/audio_database.db"
DURATION_TOLERANCE = 0.10  # 10% duration variance allowed

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def is_duration_match(local_sec, yt_sec, tolerance):
    if not local_sec or not yt_sec:
        return True
    
    try:
        local_sec = float(local_sec)
        yt_sec = float(yt_sec)
    except (ValueError, TypeError):
        return True
    
    diff = abs(local_sec - yt_sec)
    max_allowed = local_sec * tolerance
    return diff <= max_allowed

def process_track(track, timeout, min_confidence):
    track_id, artist, title, duration_sec = track
    query = f"{artist} - {title}"
    
    cmd = [
        "yt-dlp",
        f"ytsearch3:{query}",
        "--dump-json",
        "--default-search", "ytsearch",
        "--no-playlist",
        "--no-warnings",
        "--quiet"
    ]
    
    best_url = None
    highest_conf = -1
    
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        
        for line in proc.stdout.splitlines():
            if not line.strip():
                continue
                
            try:
                data = json.loads(line)
                yt_title = data.get("title", "")
                yt_url = data.get("webpage_url", "")
                yt_duration = data.get("duration", 0)
                
                if not is_duration_match(duration_sec, yt_duration, DURATION_TOLERANCE):
                    continue
                    
                seq = difflib.SequenceMatcher(None, query.lower(), yt_title.lower())
                conf = seq.ratio() * 100
                
                if conf >= min_confidence and conf > highest_conf:
                    highest_conf = conf
                    best_url = yt_url
                    
            except json.JSONDecodeError:
                continue
                
        return track_id, query, best_url
        
    except subprocess.TimeoutExpired:
        return track_id, query, "TIMEOUT"
    except Exception as e:
        return track_id, query, f"ERROR: {str(e)}"

def main():
    default_workers = max(1, (os.cpu_count() or 4) - 1)
    parser = argparse.ArgumentParser(description="Search and map YouTube URLs to local audio tracks.")
    parser.add_argument("-t", "--timeout", type=int, default=10, help="Subprocess timeout in seconds")
    parser.add_argument("-w", "--workers", type=int, default=default_workers, help="Number of parallel workers")
    parser.add_argument("-m", "--min-confidence", type=float, default=100.0, help="Minimum confidence percentage")
    args = parser.parse_args()

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
    except sqlite3.Error as e:
        log(f"❌ Database error: {e}")
        return

    try:
        cursor.execute("SELECT id, artist, title, duration_sec FROM tracks WHERE youtube_url IS NULL")
        tracks = cursor.fetchall()
    except sqlite3.Error as e:
        log(f"❌ Query error: {e}")
        conn.close()
        return

    total_tracks = len(tracks)
    
    if total_tracks == 0:
        log("✅ Processing complete! No empty YouTube URLs found.")
        conn.close()
        return
        
    log(f"🚀 Processing {total_tracks} tracks using {args.workers} parallel workers...")
    log(f"⚙️ Settings: Workers={args.workers}, Timeout={args.timeout}s, Min Confidence={args.min_confidence}%, DB Path={DB_PATH}")
    
    populated_count = 0
    completed_count = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_track, track, args.timeout, args.min_confidence): track for track in tracks}
        
        for future in concurrent.futures.as_completed(futures):
            completed_count += 1
            track_id, query, result = future.result()
            
            if result and result.startswith("http"):
                cursor.execute("UPDATE tracks SET youtube_url = ? WHERE id = ?", (result, track_id))
                conn.commit()
                populated_count += 1
                log(f"[{completed_count}/{total_tracks}] ✅ Match: {query} -> {result}")
            else:
                # If result is None, TIMEOUT, or ERROR
                reason = result if result else "No valid match found"
                log(f"[{completed_count}/{total_tracks}] ⚠️ Miss: {query} ({reason})")

    conn.close()
    log(f"✅ Processing complete! Populated {populated_count}/{total_tracks} tracks.")

if __name__ == '__main__':
    main()
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
