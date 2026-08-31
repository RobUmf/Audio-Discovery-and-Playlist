import sqlite3
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

def search_youtube_and_populate(db_path="audio_database.db"):
    db_file = Path(db_path).expanduser()
    if not db_file.exists():
        print(f"❌ Database not found at '{db_file}'.")
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
        print(f"❌ Database query error: {e}")
        conn.close()
        return

    rows = cursor.fetchall()
    if not rows:
        print("No tracks found needing YouTube URLs.")
        conn.close()
        return

    print(f"\n--- Found {len(rows)} tracks to search on YouTube ---")

    for rowid, original_path, artist, album_artist in rows:
        path_obj = Path(original_path)
        filename_stem = path_obj.stem
        
        # Prefer 'artist', fallback to 'album_artist' if missing
        artist_to_use = (artist or album_artist or "").strip()
        
        # Deduplicate artist if already present in the filename
        if artist_to_use and artist_to_use.lower() not in filename_stem.lower():
            search_term = f"{artist_to_use} - {filename_stem}"
        else:
            search_term = filename_stem

        timestamp = datetime.now().strftime("[%H:%M:%S]")
        print(f"{timestamp} Searching: {search_term}...")

        # Search top 3 results, ignore deleted video errors, and suppress warning noise
        cmd = [
            "yt-dlp",
            "--print", "webpage_url",
            "--no-playlist",
            "--no-warnings",
            "--ignore-errors",
            f"ytsearch3:{search_term}"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            urls = [line.strip() for line in result.stdout.splitlines() if line.strip().startswith("http")]
            
            if urls:
                video_url = urls[0]  # Picks the first valid, accessible URL
                cursor.execute("UPDATE tracks SET youtube_url = ? WHERE rowid = ?", (video_url, rowid))
                conn.commit()
                print(f"  -> Added: {video_url}")
            else:
                print("  -> No match found.")
        except subprocess.TimeoutExpired:
            print("  -> Search timed out after 20s (skipping track).")
        except Exception as e:
            print(f"  -> Error executing search: {e}")

    conn.close()
    print("\n✅ Database population complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search YouTube using track paths/metadata and populate youtube_url")
    parser.add_argument("--db", default="audio_database.db", help="Path to SQLite database")
    args = parser.parse_args()
    
    search_youtube_and_populate(db_path=args.db)
