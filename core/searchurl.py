#!/usr/init/env python3
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
DURATION_TOLERANCE = 0.033 # ~1 sec per 30 sec variance allowed

def log(msg):
    ts = datetime.now().strftime("%d  %H:%M:%S")
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
                
        if best_url:
            return track_id, query, best_url, f"{highest_conf:.1f}%"
        else:
            return track_id, query, None, "MISS"
        
    except subprocess.TimeoutExpired:
        return track_id, query, None, "TIMEOUT"
    except Exception as e:
        return track_id, query, None, f"ERROR"

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

    # Ensure url_acc column exists in the database
    try:
        cursor.execute("PRAGMA table_info(tracks);")
        columns = [col[1] for col in cursor.fetchall()]
        if 'url_acc' not in columns:
            cursor.execute("ALTER TABLE tracks ADD COLUMN url_acc TEXT;")
            conn.commit()
            log("🛠️ Added 'url_acc' column to 'tracks' table.")
    except sqlite3.Error as e:
        log(f"❌ Schema check error: {e}")
        conn.close()
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
            track_id, query, result_url, status_acc = future.result()
            
            # Always update database with the result url and the status/accuracy code
            cursor.execute("UPDATE tracks SET youtube_url = ?, url_acc = ? WHERE id = ?", (result_url, status_acc, track_id))
            conn.commit()
            
            if result_url:
                populated_count += 1
                log(f"[{completed_count}/{total_tracks}] ✅ Match [{status_acc}]: {query} -> {result_url}")
            else:
                log(f"[{completed_count}/{total_tracks}] ⚠️ Status [{status_acc}]: {query}")

    conn.close()
    log(f"✅ Processing complete! Populated {populated_count}/{total_tracks} tracks.")

if __name__ == '__main__':
    main()