#!/usr/bin/env python3
import os
import sys
import argparse
from datetime import datetime
import numpy as np
import pandas as pd
import librosa
from pydub import AudioSegment
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import warnings

# Suppress librosa/audioread warnings for clean terminal output
warnings.filterwarnings('ignore', module='librosa')

# --- HOTFIX FOR SCIPY/RESAMPY COMPATIBILITY ---
import scipy.signal
if not hasattr(scipy.signal, 'hann'):
    scipy.signal.hann = scipy.signal.windows.hann

def get_sample_db(audio, start_ms, duration_ms=20000):
    """Safely extracts a chunk of audio and returns its RMS dBFS value."""
    end_ms = start_ms + duration_ms
    if start_ms >= len(audio):
        return None
    if end_ms > len(audio):
        end_ms = len(audio)
    chunk = audio[start_ms:end_ms]
    return round(chunk.dBFS, 2) if len(chunk) > 0 else None

def analyze_track_assets(file_path):
    """
    Worker function: Extracts Intensity, Complexity, Dynamic Range, BPM, 
    Color, Aggressiveness, and Harmonic Purity independently for multiprocessing.
    """
    try:
        file_path_str = str(file_path)
        
        # --- 1. METADATA & FOLDER PARSING ---
        path_obj = Path(file_path)
        track_name = path_obj.stem
        album = path_obj.parent.name if path_obj.parent != path_obj else "Unknown"
        artist = path_obj.parent.parent.name if path_obj.parent.parent != path_obj.parent else "Unknown"

        # --- 2. INTENSITY ANALYSIS (Pydub) ---
        audio = AudioSegment.from_mp3(file_path_str)
        duration_sec = int(len(audio) / 1000)
        
        s1 = get_sample_db(audio, start_ms=20000)   # 0:20
        s2 = get_sample_db(audio, start_ms=60000)   # 1:00
        s3 = get_sample_db(audio, start_ms=120000) if duration_sec > 180 else None # 2:00
        
        valid_samples = [s for s in [s1, s2, s3] if s is not None]
        db_final = round(sum(valid_samples) / len(valid_samples), 2) if valid_samples else -99.0

        # --- 3. ADVANCED AUDIO ANALYSIS (Librosa) ---
        y, sr = librosa.load(file_path_str, sr=22050, mono=True)
        
        # A. Complexity & Dynamic Range Matrix
        rms = librosa.feature.rms(y=y)[0]
        rms_db = librosa.amplitude_to_db(rms, ref=np.max)
        loudness_variance = float(np.std(rms_db))
        
        peak = float(np.max(np.abs(y)))
        mean_rms = float(np.mean(rms))
        crest_factor = peak / mean_rms if mean_rms > 0 else 0
        complexity_score = round(loudness_variance * crest_factor, 2)
        dynamic_range_db = round(20 * np.log10(crest_factor), 2) if crest_factor > 0 else 0
        
        # B. Pacing (BPM)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm = round(float(np.atleast_1d(tempo)[0])) 
        
        # C. Color/Brightness Theory (Spectral Centroid)
        brightness_hz = int(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
        
        # D. Aggressiveness / Attack Sharpness (Onset Strength)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        attack_sharpness = round(float(np.mean(onset_env)), 2)
        
        # E. Harmonic Purity Matrix (HPSS Deconstruction)
        y_harmonic, y_percussive = librosa.effects.hpss(y)
        power_harmonic = float(np.sum(y_harmonic ** 2))
        power_percussive = float(np.sum(y_percussive ** 2))
        total_power = power_harmonic + power_percussive
        
        harmonic_purity = round((power_harmonic / total_power) * 100, 2) if total_power > 0 else 0.0
        
        row_data = {
            "Artist": artist, "Album": album, "Track Name": track_name,
            "Length_Sec": duration_sec, "Db_Final": db_final, "Sample1_dB": s1,
            "Sample2_dB": s2, "Sample3_dB": s3, "File_Path": file_path_str,
            "Complexity_Score": complexity_score, "Dynamic_Range": dynamic_range_db, 
            "BPM": bpm, "Brightness_Hz": brightness_hz, "Attack_Sharpness": attack_sharpness,
            "Harmonic_Purity": harmonic_purity
        }
        return True, row_data

    except Exception as e:
        return False, f"{Path(file_path).name} - Error: {e}"

def main():
    parser = argparse.ArgumentParser(description="Multi-Core Comprehensive Audio Matrix Indexer")
    parser.add_argument("-d", "--directory", default=".", help="Search directory root (e.g., ../128mp3)")
    parser.add_argument("--csv", default="intensity_database.csv", help="Database file path")
    
    cpu_count = os.cpu_count() or 4
    default_workers = max(1, cpu_count - 1)
    parser.add_argument("-w", "--workers", type=int, default=default_workers, help="Number of concurrent CPU workers")
    args = parser.parse_args()

    search_dir = Path(args.directory).resolve()
    database_file = Path(args.csv).resolve()

    print(f"Initializing Multi-Core Audio Matrix Indexer using {args.workers} workers...")
    
    headers = [
        "Artist", "Album", "Track Name", "Length_Sec", "Db_Final", 
        "Sample1_dB", "Sample2_dB", "Sample3_dB", "File_Path", 
        "Complexity_Score", "Dynamic_Range", "BPM", "Brightness_Hz", 
        "Attack_Sharpness", "Harmonic_Purity"
    ]
    
    # Load database or initialize fresh schema
    if database_file.exists():
        df = pd.read_csv(database_file)
        for col in headers:
            if col not in df.columns:
                df[col] = np.nan
    else:
        df = pd.DataFrame(columns=headers)

    # Discover target local MP3 assets recursively
    local_files = [f for f in search_dir.rglob('*.mp3') if not f.name.endswith('.m3u')]
    print(f"Found {len(local_files)} total files in target directory tree.")

    # Determine files needing processing (Resume logic)
    processed_paths = set()
    if not df.empty and 'File_Path' in df.columns:
        valid_rows = df.dropna(subset=['Harmonic_Purity', 'Attack_Sharpness'])
        processed_paths = set(valid_rows['File_Path'].astype(str))

    remaining_files = [f for f in local_files if str(f.resolve()) not in processed_paths]

    if remaining_files:
        print(f"🚀 Processing {len(remaining_files)} new tracks across {args.workers} cores...")
        database_file.parent.mkdir(parents=True, exist_ok=True)
        
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(analyze_track_assets, f): f for f in remaining_files}
            
            completed_count = 0
            for future in as_completed(futures):
                success, result = future.result()
                completed_count += 1
                
                if success:
                    # Clean out any old trace and append new row
                    df = df[df['File_Path'] != result['File_Path']]
                    df = pd.concat([df, pd.DataFrame([result])], ignore_index=True)
                    current_time = datetime.now().strftime("%H:%M:%S")
                    print(f"    [{current_time}] [{completed_count}/{len(remaining_files)}] Quantified: {result['Track Name'][:40]}")
                else:
                    current_time = datetime.now().strftime("%H:%M:%S")
                    print(f"    [{current_time}] [{completed_count}/{len(remaining_files)}] Failed: {result}")

                # Incremental flush to disk every 20 tracks
                if completed_count % 20 == 0:
                    df.to_csv(database_file, index=False)

        # Final database save
        df.to_csv(database_file, index=False)
        print(f"\n✅ Database Synchronization Complete.")
    else:
        print("\n✅ Database is fully up to date with all discovered tracks!")

    # --- PLAYLIST GENERATION MATRIX ENGINE ---
    print("\nCompiling Smart Multi-Matrix Playlists...")
    
    TIERS = {
        "1_Ambient_Chill.m3u":  {"min": -99.0, "max": -20.0},
        "2_Steady_Groove.m3u":  {"min": -20.0, "max": -15.0},
        "3_Mid_Energy.m3u":     {"min": -15.0, "max": -12.0},
        "4_High_Intensity.m3u": {"min": -12.0, "max": -9.0},
        "5_Absolute_Chaos.m3u": {"min": -9.0,  "max": 10.0}
    }

    # 1. Standard Volume Tier Compiler
    open_playlists = {}
    for name in TIERS.keys():
        open_playlists[name] = open(name, "w", encoding="utf-8")
        open_playlists[name].write("#EXTM3U\n")

    for _, row in df.iterrows():
        f_path = str(row['File_Path'])
        if os.path.exists(f_path):
            rel_path = os.path.relpath(f_path, search_dir)
            energy = row['Db_Final']

            if pd.notna(energy):
                for name, boundaries in TIERS.items():
                    if boundaries["min"] <= energy < boundaries["max"]:
                        open_playlists[name].write(f"{rel_path}\n")
                        break

    for f in open_playlists.values():
        f.close()

    # 2. Smart Matrix Selection Compiler
    def write_smart_playlist(filename, filtered_df):
        with open(filename, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for _, row in filtered_df.iterrows():
                f_path = str(row['File_Path'])
                if os.path.exists(f_path):
                    f.write(f"{os.path.relpath(f_path, search_dir)}\n")
        print(f"  -> Generated {filename} ({len(filtered_df)} tracks sorted)")

    valid_matrix_df = df.dropna(subset=['Complexity_Score', 'Attack_Sharpness', 'Brightness_Hz', 'Harmonic_Purity'])

    cinematic_df = valid_matrix_df[
        (valid_matrix_df['Db_Final'] >= -14.0) & 
        (valid_matrix_df['Db_Final'] <= -11.0) &
        (valid_matrix_df['Complexity_Score'] > 20)
    ].sort_values(by='Complexity_Score', ascending=False)
    
    flow_state_df = valid_matrix_df[
        (valid_matrix_df['Attack_Sharpness'] < 1.6) & 
        (valid_matrix_df['Complexity_Score'] > 22) & 
        (valid_matrix_df['Db_Final'] < -13.0)
    ].sort_values(by='Complexity_Score', ascending=False)

    aggressive_df = valid_matrix_df[
        (valid_matrix_df['Attack_Sharpness'] > 3.8) & 
        (valid_matrix_df['Dynamic_Range'] > 11.5)
    ].sort_values(by='Attack_Sharpness', ascending=False)

    deep_warm_df = valid_matrix_df[
        (valid_matrix_df['Brightness_Hz'] < 1600) & 
        (valid_matrix_df['Db_Final'] >= -18.0)
    ].sort_values(by='Brightness_Hz', ascending=True)

    melodic_df = valid_matrix_df[
        (valid_matrix_df['Harmonic_Purity'] > 72.0) &
        (valid_matrix_df['Attack_Sharpness'] < 2.2)
    ].sort_values(by='Harmonic_Purity', ascending=False)

    write_smart_playlist("Smart_Cinematic_Musicianship.m3u", cinematic_df)
    write_smart_playlist("Smart_Flow_State_Legato.m3u", flow_state_df)
    write_smart_playlist("Smart_Aggressive_Rhythmic.m3u", aggressive_df)
    write_smart_playlist("Smart_Late_Night_Warmth.m3u", deep_warm_df)
    write_smart_playlist("Smart_Pure_Melodic.m3u", melodic_df)
    
    print("\nAll architectural matrix configurations written successfully!")

if __name__ == "__main__":
    main()