import sqlite3
import json
import math
import os

DB_PATH = "audio_database.db"
# Change 'tracks' to match your actual SQLite table name if different
TABLE_NAME = "tracks" 

def prompt_float(prompt_text):
    val = input(prompt_text).strip()
    if not val:
        return None
    try:
        return float(val)
    except ValueError:
        print("   [!] Invalid number, skipping...")
        return None

def prompt_str(prompt_text):
    val = input(prompt_text).strip()
    return val if val else None

def main():
    print("=" * 60)
    print("🎵 Ultimate DSP Playlist Generator (SQLite + MFCC Average)")
    print("Press [Enter] on any prompt to skip that filter.")
    print("=" * 60)

    conditions = ["1=1"]
    params = []

    # 1. BPM
    print("\n[1/12] BPM (Tempo)")
    min_bpm = prompt_float("   -> Min BPM (skip): ")
    if min_bpm is not None:
        conditions.append("dsp_bpm >= ?"); params.append(min_bpm)
    max_bpm = prompt_float("   -> Max BPM (skip): ")
    if max_bpm is not None:
        conditions.append("dsp_bpm <= ?"); params.append(max_bpm)

    # 2. Spectral Centroid
    print("\n[2/12] Spectral Centroid (Brightness/Timbre)")
    min_cent = prompt_float("   -> Min Centroid Hz (skip): ")
    if min_cent is not None:
        conditions.append("spectral_centroid_hz >= ?"); params.append(min_cent)
    max_cent = prompt_float("   -> Max Centroid Hz (skip): ")
    if max_cent is not None:
        conditions.append("spectral_centroid_hz <= ?"); params.append(max_cent)

    # 3. Spectral Rolloff
    print("\n[3/12] Spectral Rolloff (High-Frequency Cutoff)")
    min_roll = prompt_float("   -> Min Rolloff Hz (skip): ")
    if min_roll is not None:
        conditions.append("spectral_rolloff_hz >= ?"); params.append(min_roll)
    max_roll = prompt_float("   -> Max Rolloff Hz (skip): ")
    if max_roll is not None:
        conditions.append("spectral_rolloff_hz <= ?"); params.append(max_roll)

    # 4. Harmonic Ratio
    print("\n[4/12] Harmonic Ratio (Smoothness vs Percussiveness)")
    min_harm = prompt_float("   -> Min Harmonic Ratio [0.0 - 1.0] (skip): ")
    if min_harm is not None:
        conditions.append("hpss_harmonic_ratio >= ?"); params.append(min_harm)
    max_harm = prompt_float("   -> Max Harmonic Ratio [0.0 - 1.0] (skip): ")
    if max_harm is not None:
        conditions.append("hpss_harmonic_ratio <= ?"); params.append(max_harm)

    # 5. Crest Factor
    print("\n[5/12] Crest Factor (Dynamic Punchiness)")
    min_crest = prompt_float("   -> Min Crest Factor dB (skip): ")
    if min_crest is not None:
        conditions.append("dynamics_crest_factor_db >= ?"); params.append(min_crest)
    max_crest = prompt_float("   -> Max Crest Factor dB (skip): ")
    if max_crest is not None:
        conditions.append("dynamics_crest_factor_db <= ?"); params.append(max_crest)

    # 6. Spectral Flatness
    print("\n[6/12] Spectral Flatness (Tone vs Noise)")
    min_flat = prompt_float("   -> Min Flatness (skip): ")
    if min_flat is not None:
        conditions.append("spectral_flatness >= ?"); params.append(min_flat)
    max_flat = prompt_float("   -> Max Flatness (skip): ")
    if max_flat is not None:
        conditions.append("spectral_flatness <= ?"); params.append(max_flat)

    # 7. Onset Rate
    print("\n[7/12] Complexity: Onset Rate (Rhythmic Busyness)")
    min_onset = prompt_float("   -> Min Onset Rate (skip): ")
    if min_onset is not None:
        conditions.append("onset_rate >= ?"); params.append(min_onset)
    max_onset = prompt_float("   -> Max Onset Rate (skip): ")
    if max_onset is not None:
        conditions.append("onset_rate <= ?"); params.append(max_onset)

    # 8. Rhythm Pulse Clarity
    print("\n[8/12] Complexity: Rhythm Pulse Clarity")
    min_pulse = prompt_float("   -> Min Pulse Clarity [0.0 - 1.0] (skip): ")
    if min_pulse is not None:
        conditions.append("rhythm_pulse_clarity >= ?"); params.append(min_pulse)
    max_pulse = prompt_float("   -> Max Pulse Clarity [0.0 - 1.0] (skip): ")
    if max_pulse is not None:
        conditions.append("rhythm_pulse_clarity <= ?"); params.append(max_pulse)

    # 9. Spectral Contrast
    print("\n[9/12] Complexity: Spectral Contrast")
    min_contrast = prompt_float("   -> Min Contrast (skip): ")
    if min_contrast is not None:
        conditions.append("spectral_contrast >= ?"); params.append(min_contrast)
    max_contrast = prompt_float("   -> Max Contrast (skip): ")
    if max_contrast is not None:
        conditions.append("spectral_contrast <= ?"); params.append(max_contrast)

    # 10. Musical Key
    print("\n[10/12] Musical Key")
    key_val = prompt_str("   -> Key contains (e.g., 'Minor') (skip): ")
    if key_val is not None:
        conditions.append("dsp_key LIKE ?"); params.append(f"%{key_val}%")

    # 11. Grouping
    print("\n[11/12] Grouping / Album Collection")
    group_val = prompt_str("   -> Grouping contains (skip): ")
    if group_val is not None:
        conditions.append("grouping LIKE ?"); params.append(f"%{group_val}%")

    # 12. Duration
    print("\n[12/12] Duration")
    min_dur = prompt_float("   -> Min Duration sec (skip): ")
    if min_dur is not None:
        conditions.append("duration_sec >= ?"); params.append(min_dur)
    max_dur = prompt_float("   -> Max Duration sec (skip): ")
    if max_dur is not None:
        conditions.append("duration_sec <= ?"); params.append(max_dur)

    # Sorting
    print("\n" + "=" * 60)
    print("🔄 Sorting Configuration")
    sort_field = prompt_str("   -> Sort by field [default: dsp_bpm]: ") or "dsp_bpm"
    sort_order = prompt_str("   -> Sort order (ASC / DESC) [default: ASC]: ") or "ASC"
    
    query = f"SELECT * FROM {TABLE_NAME} WHERE " + " AND ".join(conditions)
    query += f" ORDER BY {sort_field} {sort_order}"

    # Execute SQLite Query
    if not os.path.exists(DB_PATH):
        print(f"\n❌ Error: Database not found at '{DB_PATH}'")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Returns dict-like rows
        cursor = conn.cursor()
        cursor.execute(query, params)
        all_matched_tracks = cursor.fetchall()
        total_matched = len(all_matched_tracks)
    except sqlite3.Error as e:
        print(f"\n❌ SQLite Error: {e}")
        return
    finally:
        if 'conn' in locals():
            conn.close()

    print("\n" + "=" * 60)
    print("📊 Quantity Bounds & MFCC Averaging")
    print(f"   (Matching tracks found: {total_matched})")
    
    if total_matched == 0:
        print("\n❌ No tracks matched your criteria.")
        return

    use_mfcc_avg = prompt_str("   -> Filter final selection by proximity to Average MFCC Vibe? (y/N): ")
    use_mfcc = use_mfcc_avg and use_mfcc_avg.lower() == 'y'
    
    max_qty_input = prompt_str("   -> Maximum quantity of songs (skip for all): ")
    max_qty = int(max_qty_input) if max_qty_input and max_qty_input.isdigit() else total_matched

    # MFCC Sonic Centroid Logic
    if use_mfcc:
        valid_candidates = []
        mfcc_matrix = []

        for row in all_matched_tracks:
            mfcc_raw = row['mfcc_profile']
            if mfcc_raw:
                try:
                    vec = json.loads(mfcc_raw)
                    if len(vec) == 13:
                        mfcc_matrix.append(vec)
                        valid_candidates.append((row, vec))
                except (json.JSONDecodeError, TypeError, ValueError):
                    continue

        if mfcc_matrix:
            num_items = len(mfcc_matrix)
            mean_mfcc = [sum(v[i] for v in mfcc_matrix) / num_items for i in range(13)]
            
            scored_candidates = []
            for row, vec in valid_candidates:
                dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(vec, mean_mfcc)))
                scored_candidates.append((dist, row))
                
            # Sort by shortest distance to the average 13D vector
            scored_candidates.sort(key=lambda x: x[0])
            all_matched_tracks = [item[1] for item in scored_candidates]
            print(f"   🎯 Re-ranked {len(all_matched_tracks)} tracks by proximity to average sonic profile.")
        else:
            print("   ⚠️ No valid MFCC data found in matching tracks. Using standard SQL sort.")

    # Apply Quantity Truncation
    final_tracks = all_matched_tracks[:max_qty]
    
    # Export to M3U
    m3u_filename = prompt_str("\n   -> Output filename [default: playlist.m3u]: ") or "playlist.m3u"
    
    try:
        with open(m3u_filename, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            for row in final_tracks:
                dur = int(row['duration_sec']) if row['duration_sec'] else 0
                artist = row['album_artist'] or "Unknown Artist"
                # Fallback to original_path if processed_path is NULL
                file_path = row['processed_path'] or row['original_path'] 
                title = os.path.basename(file_path) if file_path else "Unknown Title"
                
                f.write(f"#EXTINF:{dur},{artist} - {title}\n")
                f.write(f"{file_path}\n")
        print(f"\n✅ Playlist successfully saved with {len(final_tracks)} tracks to: {m3u_filename}")
    except IOError as e:
        print(f"\n❌ Failed to write M3U file: {e}")

if __name__ == "__main__":
    main()    print("\n[3/12] Spectral Rolloff (High-Frequency Cutoff)")
    min_roll = input("   -> Min Rolloff Hz (skip): ").strip()
    max_roll = input("   -> Max Rolloff Hz (skip): ").strip()
    if min_roll: filters.append("spectral_rolloff_hz >= ?"); params.append(float(min_roll))
    if max_roll: filters.append("spectral_rolloff_hz <= ?"); params.append(float(max_roll))

    # 4. Harmonic Ratio
    print("\n[4/12] Harmonic Ratio (Smoothness vs Percussiveness)")
    min_harm = input("   -> Min Harmonic Ratio [0.0 - 1.0] (skip): ").strip()
    max_harm = input("   -> Max Harmonic Ratio [0.0 - 1.0] (skip): ").strip()
    if min_harm: filters.append("hpss_harmonic_ratio >= ?"); params.append(float(min_harm))
    if max_harm: filters.append("hpss_harmonic_ratio <= ?"); params.append(float(max_harm))
    
    # 5. Crest Factor (Dynamic Range)
    print("\n[5/12] Crest Factor (Dynamic Punchiness)")
    print("   Desc: High = natural/punchy dynamics (e.g., >12), Low = heavily compressed/loud (e.g., <8).")
    min_crest = input("   -> Min Crest Factor dB (skip): ").strip()
    max_crest = input("   -> Max Crest Factor dB (skip): ").strip()
    if min_crest: filters.append("dynamics_crest_factor_db >= ?"); params.append(float(min_crest))
    if max_crest: filters.append("dynamics_crest_factor_db <= ?"); params.append(float(max_crest))

    # 6. Spectral Flatness
    print("\n[6/12] Spectral Flatness (Tone vs Noise)")
    print("   Desc: Low = pure tones/synths (e.g., <0.02), High = noisy/cymbals (e.g., >0.05).")
    min_flat = input("   -> Min Flatness (skip): ").strip()
    max_flat = input("   -> Max Flatness (skip): ").strip()
    if min_flat: filters.append("spectral_flatness >= ?"); params.append(float(min_flat))
    if max_flat: filters.append("spectral_flatness <= ?"); params.append(float(max_flat))

    # 7. Complexity: Onset Rate
    print("\n[7/12] Complexity: Onset Rate (Rhythmic Busyness)")
    print("   Desc: Number of note attacks per second. High = busy/fast/complex (e.g., >6.0), Low = sparse/ambient (e.g., <3.0).")
    min_onset = input("   -> Min Onset Rate (skip): ").strip()
    max_onset = input("   -> Max Onset Rate (skip): ").strip()
    if min_onset: filters.append("onset_rate >= ?"); params.append(float(min_onset))
    if max_onset: filters.append("onset_rate <= ?"); params.append(float(max_onset))

    # 8. Complexity: Rhythm Pulse Clarity
    print("\n[8/12] Complexity: Rhythm Pulse Clarity")
    print("   Desc: Low = complex/syncopated/ambient (e.g., <0.3). High = steady 4/4 dance beat (e.g., >0.8).")
    min_pulse = input("   -> Min Pulse Clarity [0.0 - 1.0] (skip): ").strip()
    max_pulse = input("   -> Max Pulse Clarity [0.0 - 1.0] (skip): ").strip()
    if min_pulse: filters.append("rhythm_pulse_clarity >= ?"); params.append(float(min_pulse))
    if max_pulse: filters.append("rhythm_pulse_clarity <= ?"); params.append(float(max_pulse))

    # 9. Complexity: Spectral Contrast
    print("\n[9/12] Complexity: Spectral Contrast")
    print("   Desc: High = complex multi-layered timbres with deep peaks/valleys (e.g., >25). Low = flatter/simpler.")
    min_contrast = input("   -> Min Contrast (skip): ").strip()
    max_contrast = input("   -> Max Contrast (skip): ").strip()
    if min_contrast: filters.append("spectral_contrast >= ?"); params.append(float(min_contrast))
    if max_contrast: filters.append("spectral_contrast <= ?"); params.append(float(max_contrast))

    # 10. Musical Key
    print("\n[10/12] Musical Key")
    key_query = input("   -> Key contains (e.g., 'Minor') (skip): ").strip()
    if key_query: filters.append("dsp_key LIKE ?"); params.append(f"%{key_query}%")

    # 11. Grouping
    print("\n[11/12] Grouping / Album Collection")
    group_query = input("   -> Grouping contains (skip): ").strip()
    if group_query: filters.append("grouping LIKE ?"); params.append(f"%{group_query}%")

    # 12. Duration
    print("\n[12/12] Duration")
    min_dur = input("   -> Min Duration sec (skip): ").strip()
    max_dur = input("   -> Max Duration sec (skip): ").strip()
    if min_dur: filters.append("duration_sec >= ?"); params.append(float(min_dur))
    if max_dur: filters.append("duration_sec <= ?"); params.append(float(max_dur))

    # Build SQL Query
    query = "SELECT processed_path, duration_sec, album_artist, tracknumber FROM tracks WHERE processed_path IS NOT NULL"
    if filters:
        query += " AND " + " AND ".join(filters)

    # Sorting options
    print("\n" + "=" * 60)
    print("🔄 Sorting Configuration")
    sort_field = input("   -> Sort by field [default: dsp_bpm]: ").strip() or "dsp_bpm"
    sort_order = input("   -> Sort order (ASC / DESC) [default: ASC]: ").strip().upper()
    if sort_order not in ("ASC", "DESC"): sort_order = "ASC"
    query += f" ORDER BY {sort_field} {sort_order}"

    cursor.execute(query, params)
    all_matched_tracks = cursor.fetchall()
    total_matched = len(all_matched_tracks)
    
    # Quantity Bounds Configuration
    print("\n" + "=" * 60)
    print("📊 Quantity Bounds Configuration")
    print(f"   (Matching tracks found: {total_matched})")
    
    min_qty_val = input("   -> Minimum quantity required (skip for none): ").strip()
    if min_qty_val and total_matched < int(min_qty_val):
        print(f"\n⚠️ Warning: Found {total_matched} tracks, fewer than minimum {min_qty_val}.")
            
    max_qty_val = input("   -> Maximum quantity of songs (skip for all): ").strip()
    if max_qty_val:
        tracks = all_matched_tracks[:int(max_qty_val)]
    else:
        tracks = all_matched_tracks

    if not tracks:
        print("\n❌ No tracks matched your criteria.")
        conn.close()
        return

    # Relative path configuration
    print("\n" + "=" * 60)
    print("📂 File Path Configuration")
    top_folder = input("   -> Enter top folder for relative paths [default: Ponies at Dawn]: ").strip() or "Ponies at Dawn"
    output_filename = input("   -> Enter output filename [default: custom_playlist.m3u]: ").strip() or "custom_playlist.m3u"
    conn.close()

    playlist_path = Path(output_filename)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(playlist_path, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        # Write Database Records and Options into M3U remarks
        f.write(f"#REMARK: Generated on {timestamp}\n")
        f.write(f"#REMARK: Total records in database: {total_db_records}\n")
        f.write(f"#REMARK: Tracks matching DSP filters: {total_matched}\n")
        f.write(f"#REMARK: Playlist track count applied: {len(tracks)}\n")
        f.write(f"#REMARK: Sorted by: {sort_field} {sort_order}\n")
        
        count = 0
        for row in tracks:
            processed_path, duration, artist, _ = row
            p = Path(processed_path)
            parts = p.parts
            
            if top_folder in parts:
                idx = parts.index(top_folder)
                rel_path = Path(*parts[idx+1:])
            else:
                rel_path = p.name
                
            dur = int(duration) if duration else -1
            art = artist if artist else "Unknown Artist"
            filename = p.stem
            
            f.write(f"#EXTINF:{dur},{art} - {filename}\n")
            f.write(f"{str(rel_path)}\n")
            count += 1
            
    print(f"\n✅ Generated '{playlist_path.resolve()}' with {count} tracks!")

if __name__ == "__main__":
    main()
