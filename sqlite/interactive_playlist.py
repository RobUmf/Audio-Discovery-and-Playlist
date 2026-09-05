import sqlite3
from pathlib import Path
from datetime import datetime

def main():
    db_path = 'audio_database.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get total database size for the M3U remark
    cursor.execute("SELECT COUNT(*) FROM tracks")
    total_db_records = cursor.fetchone()[0]
    
    print("=" * 60)
    print("🎵 Ultimate DSP Playlist Generator (Includes Complexity)")
    print("Press [Enter] on any prompt to skip that filter.")
    print("=" * 60)
    
    filters = []
    params = []
    
    # 1. BPM (Tempo)
    print("\n[1/12] BPM (Tempo)")
    min_bpm = input("   -> Min BPM (skip): ").strip()
    max_bpm = input("   -> Max BPM (skip): ").strip()
    if min_bpm: filters.append("dsp_bpm >= ?"); params.append(float(min_bpm))
    if max_bpm: filters.append("dsp_bpm <= ?"); params.append(float(max_bpm))
        
    # 2. Spectral Centroid
    print("\n[2/12] Spectral Centroid (Brightness/Timbre)")
    min_cent = input("   -> Min Centroid Hz (skip): ").strip()
    max_cent = input("   -> Max Centroid Hz (skip): ").strip()
    if min_cent: filters.append("spectral_centroid_hz >= ?"); params.append(float(min_cent))
    if max_cent: filters.append("spectral_centroid_hz <= ?"); params.append(float(max_cent))

    # 3. Spectral Rolloff
    print("\n[3/12] Spectral Rolloff (High-Frequency Cutoff)")
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
