import sqlite3
import math
import re
import os

def normalize_string(s):
    """Normalizes artist or title strings for smart deduplication."""
    if not s:
        return ""
    return re.sub(r'[^\w\s]', '', s).lower().strip()

def search_target_song(cursor, id_col, feature_cols):
    print("\n--- Find Seed Song ---")
    search_type = input("Search by [i] ID, [a] Author/Artist, [t] Title, or [q] Quit: ").strip().lower()
    
    if search_type == 'q':
        return None
        
    col_query = f"{id_col}, title, artist, album, file_path, youtube_url, {', '.join(feature_cols)}"
    
    if search_type == 'i':
        try:
            val = input("Enter song ID (or 'q' to quit): ").strip().lower()
            if val == 'q':
                return None
            target_id = int(val)
            cursor.execute(f"SELECT {col_query} FROM tracks WHERE {id_col} = ?;", (target_id,))
            row = cursor.fetchone()
            if row:
                return row
            else:
                print("⚠️ Song ID not found.")
        except ValueError:
            print("Invalid ID format.")
    elif search_type == 'a':
        query = input("Enter author/artist search term (or 'q' to quit): ").strip()
        if query.lower() == 'q':
            return None
        cursor.execute(f"SELECT {col_query} FROM tracks WHERE artist LIKE ?;", (f"%{query}%",))
        rows = cursor.fetchall()
        return select_from_results(rows)
    elif search_type == 't':
        query = input("Enter song title search term (or 'q' to quit): ").strip()
        if query.lower() == 'q':
            return None
        cursor.execute(f"SELECT {col_query} FROM tracks WHERE title LIKE ?;", (f"%{query}%",))
        rows = cursor.fetchall()
        return select_from_results(rows)
    else:
        print("Invalid option.")
    return None

def select_from_results(rows):
    if not rows:
        print("No tracks found matching that query.")
        return None
    
    print(f"\nFound {len(rows)} matching tracks:")
    print(f"{'Index':<6} | {'ID':<6} | {'Author - Song Title':<45} | {'Album'}")
    print("-" * 75)
    
    for idx, row in enumerate(rows[:20]):
        r_id, title, artist, album = row[0], row[1], row[2], row[3]
        print(f"{idx:<6} | {r_id:<6} | {f'{artist} - {title}':<45} | {album or 'N/A'}")
        
    choice_str = input("\nEnter Index number to pick, or 'q' to quit: ").strip().lower()
    if choice_str == 'q':
        return None
    try:
        choice = int(choice_str)
        if 0 <= choice < len(rows):
            return rows[choice]
    except ValueError:
        print("Invalid selection.")
    return None

def main():
    db_path = 'audio_database.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(tracks);")
    columns = [col[1] for col in cursor.fetchall()]
    id_col = 'id' if 'id' in columns else 'rowid'
    
    feature_cols = [
        'dsp_bpm', 'loudness_lufs', 'spectral_centroid_hz', 
        'spectral_rolloff_hz', 'rhythm_pulse_clarity', 
        'hpss_harmonic_ratio', 'duration_sec'
    ]
    active_features = [col for col in feature_cols if col in columns]
    
    # Initial seed selection
    target = search_target_song(cursor, id_col, active_features)
    if not target:
        print("Exiting session.")
        conn.close()
        return
        
    # Session state variables
    path_mode = None
    base_folder = ""
    current_m3u_filename = None
    used_track_ids = set()
    used_fingerprints = set()
    
    # Main interactive loop
    while True:
        target_id = target[0]
        target_title = target[1] or "Unknown Title"
        target_artist = target[2] or "Unknown Artist"
        target_album = target[3] or "Unknown Album"
        target_file = target[4] or "N/A"
        target_url = target[5] or "N/A"
        target_values = target[6:]
        target_fp = f"{normalize_string(target_artist)} - {normalize_string(target_title)}"
        
        print("\n" + "=" * 60)
        print("🎵 CURRENT SEED SONG")
        print("=" * 60)
        print(f"ID:           {target_id}")
        print(f"Author:       {target_artist}")
        print(f"Song:         {target_title}")
        print(f"Album:        {target_album}")
        print(f"File Path:    {target_file}")
        print(f"YouTube URL:  {target_url}")
        print("=" * 60)
        
        col_query = f"{id_col}, title, artist, album, file_path, youtube_url, {', '.join(active_features)}"
        url_condition = "youtube_url IS NOT NULL AND youtube_url != '' AND youtube_url != 'None'"
        
        cursor.execute(f"SELECT {col_query} FROM tracks WHERE {url_condition} AND {id_col} != {target_id};")
        candidates = cursor.fetchall()
        
        if not candidates:
            print("⚠️ No other mapped tracks found in the database to compare against.")
            break

        scored_tracks = []
        for cand in candidates:
            cand_id = cand[0]
            cand_title = cand[1] or ""
            cand_artist = cand[2] or ""
            fingerprint = f"{normalize_string(cand_artist)} - {normalize_string(cand_title)}"
            
            if cand_id in used_track_ids or fingerprint in used_fingerprints:
                continue
                
            cand_values = cand[6:]
            distance = 0.0
            valid_metrics = 0
            for t_val, c_val in zip(target_values, cand_values):
                if t_val is not None and c_val is not None:
                    distance += (float(t_val) - float(c_val)) ** 2
                    valid_metrics += 1
                    
            if valid_metrics > 0:
                score = math.sqrt(distance)
                scored_tracks.append((score, cand))
                
        scored_tracks.sort(key=lambda x: x[0])
        top_5 = scored_tracks[:5]
        
        if not top_5:
            print("⚠️ All close audio matches have already been included in this playlist session!")
            break
        
        print(f"\n✨ Top 5 New Closest Audio Matches (Strictly De-duplicated):")
        print(f"{'Index':<6} | {'Rank':<5} | {'ID':<6} | {'Author - Song Title':<35} | {'YouTube URL'}")
        print("-" * 85)
        
        fresh_matches = []
        for rank, (score, cand) in enumerate(top_5, 1):
            c_id = cand[0]
            fresh_matches.append(cand)
            print(f"[{len(fresh_matches)}]    | Match {rank} | {c_id:<6} | {f'{cand[2]} - {cand[1]}':<35} | {cand[5] or 'N/A'}")

        available_batch = [target] + fresh_matches

        # Prompt for Path configuration if not already set in session
        if not path_mode:
            print("\n--- M3U Playlist Export Options ---")
            print(" [a] Use absolute file paths")
            print(" [r] Make file paths relative to a specific folder root")
            print(" [q] Quit")
            path_mode = input("Select option [a/r/q]: ").strip().lower()
            
            if path_mode == 'q':
                break
            elif path_mode == 'r':
                print("\nFolder tree preview from sample track:")
                sample_path = available_batch[0][4]
                print(f"   Example: {sample_path}")
                base_folder = input("Enter base folder path (or 'q' to quit): ").strip()
                if base_folder.lower() == 'q':
                    break

        # Handle file creation vs append decision
        write_mode = "w"
        if current_m3u_filename and os.path.exists(current_m3u_filename):
            print(f"\nCurrent active playlist: {current_m3u_filename}")
            file_choice = input("Do you want to [c] Create new, [a] Append, or [q] Quit? [c/a/q]: ").strip().lower()
            if file_choice == 'q':
                break
            elif file_choice == 'a':
                write_mode = "a"
            else:
                safe_title = re.sub(r'[^\w\s-]', '', target_title).strip().replace(' ', '_')
                current_m3u_filename = f"like_{safe_title}.m3u"
        else:
            safe_title = re.sub(r'[^\w\s-]', '', target_title).strip().replace(' ', '_')
            current_m3u_filename = f"like_{safe_title}.m3u"

        # Check if seed was already written earlier
        is_seed_new = target_id not in used_track_ids and target_fp not in used_fingerprints

        # Mark tracking sets
        if is_seed_new:
            used_track_ids.add(target_id)
            used_fingerprints.add(target_fp)
            
        for cand in fresh_matches:
            c_id = cand[0]
            c_fp = f"{normalize_string(cand[2])} - {normalize_string(cand[1])}"
            used_track_ids.add(c_id)
            used_fingerprints.add(c_fp)

        # Write/Append to M3U file
        with open(current_m3u_filename, write_mode, encoding="utf-8") as f:
            if write_mode == "w":
                f.write("#EXTM3U\n")
            
            # Only write seed header/block info if this seed hasn't been logged yet
            if is_seed_new:
                f.write(f"\n# --- SEED SONG INFO (ID: {target_id}) ---\n")
                f.write(f"# Author: {target_artist} | Title: {target_title} | Album: {target_album}\n")
                f.write(f"# URL: {target_url}\n")
                f.write(f"# ---------------------------------------\n\n")
                
                # Write seed track itself only on its first appearance
                t_id, t_title, t_artist, t_album, t_file, t_url = target[0], target[1], target[2], target[3], target[4], target[5]
                output_path = t_file
                if path_mode == 'r' and base_folder and t_file and t_file != 'N/A':
                    try:
                        output_path = os.path.relpath(t_file, base_folder)
                    except ValueError:
                        output_path = t_file
                f.write(f"# ID: {t_id} | Album: {t_album} | URL: {t_url}\n")
                f.write(f"#EXTINF:-1,{t_artist} - {t_title}\n")
                f.write(f"{output_path}\n\n")
            
            # Write out the fresh matches
            for track in fresh_matches:
                t_id, t_title, t_artist, t_album, t_file, t_url = track[0], track[1], track[2], track[3], track[4], track[5]
                output_path = t_file
                if path_mode == 'r' and base_folder and t_file and t_file != 'N/A':
                    try:
                        output_path = os.path.relpath(t_file, base_folder)
                    except ValueError:
                        output_path = t_file
                
                f.write(f"# ID: {t_id} | Album: {t_album} | URL: {t_url}\n")
                f.write(f"#EXTINF:-1,{t_artist} - {t_title}\n")
                f.write(f"{output_path}\n\n")
                
        print(f"\n💾 Successfully updated playlist: {current_m3u_filename}!")

        # --- LOOP EXTENSION PROMPT ---
        cont = input("\nAdd more songs using one of these tracks as a new seed? ([y] Yes, [n] No / Quit): ").strip().lower()
        if cont != 'y':
            print("\n🎉 Playlist generation session complete!")
            break
            
        next_input = input(f"Enter Index number (0 to {len(available_batch)-1}) for new seed, or 'q' to quit: ").strip().lower()
        if next_input == 'q':
            print("\n🎉 Playlist generation session complete!")
            break
            
        try:
            next_idx = int(next_input)
            if 0 <= next_idx < len(available_batch):
                target = available_batch[next_idx]
                print(f"\n🔄 Switched new seed to: {target[2]} - {target[1]}")
            else:
                print("⚠️ Invalid index out of range. Ending session.")
                break
        except ValueError:
            print("⚠️ Invalid input format. Ending session.")
            break

    conn.close()

if __name__ == '__main__':
    main()