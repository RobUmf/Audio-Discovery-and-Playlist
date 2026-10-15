#!/usr/bin/env python3
import sqlite3
import os
import json
import warnings
import numpy as np
import scipy.signal
import time
import argparse
from datetime import datetime
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

# Compatibility patch for newer SciPy versions removing scipy.signal.hann
if not hasattr(scipy.signal, 'hann'):
    try:
        from scipy.signal.windows import hann
        scipy.signal.hann = hann
    except ImportError:
        scipy.signal.hann = np.hanning

import librosa

# Suppress warnings for clean console output
warnings.filterwarnings('ignore', category=UserWarning)

def print_ts(msg):
    now = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{now} {msg}")

def setup_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    new_columns = {
        "spectral_bandwidth_hz": "REAL",
        "harmonic_ratio": "REAL",
        "triplet_score": "REAL",
        "rhythm_grid_type": "TEXT",
        "audio_vibe": "TEXT"
    }
    for col, dtype in new_columns.items():
        try:
            cursor.execute(f"ALTER TABLE tracks ADD COLUMN {col} {dtype}")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    return conn

def calculate_triplet_score(y, sr, beats):
    """
    Estimates whether a track leans toward a straight (4/4) or triplet/shuffle groove
    by analyzing onset micro-timing relative to the detected beat grid.
    """
    if len(beats) < 4:
        return 0.0, "Straight (4/4)"
    
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, units='frames')
    
    if len(onset_frames) == 0:
        return 0.0, "Straight (4/4)"

    onset_times = librosa.frames_to_time(onset_frames, sr=sr)
    beat_times = librosa.frames_to_time(beats, sr=sr)
    
    triplet_hits = 0
    total_hits = 0
    
    for i in range(len(beat_times) - 1):
        b_start = beat_times[i]
        b_end = beat_times[i+1]
        interval = b_end - b_start
        if interval <= 0:
            continue
            
        sub_onsets = [t for t in onset_times if b_start <= t < b_end]
        for t in sub_onsets:
            total_hits += 1
            rel_pos = (t - b_start) / interval
            
            dist_triplet = min(abs(rel_pos - 0.33), abs(rel_pos - 0.67))
            dist_straight = min(abs(rel_pos - 0.25), abs(rel_pos - 0.5), abs(rel_pos - 0.75))
            
            if dist_triplet < dist_straight:
                triplet_hits += 1
                
    if total_hits == 0:
        return 0.0, "Straight (4/4)"
        
    triplet_score = round(triplet_hits / total_hits, 2)
    grid_type = "Triplet / Shuffle" if triplet_score > 0.38 else "Straight (4/4)"
    return triplet_score, grid_type

def classify_vibe(bpm, harmonic_ratio, onset_rate, spectral_bandwidth):
    """Rule-based heuristic for audio vibe classification."""
    if harmonic_ratio > 0.82 and bpm < 95:
        return "Ambient / Soundscape"
    elif onset_rate > 4.5 and bpm > 120:
        return "High-Energy / Fast Electronic"
    elif 70 <= bpm <= 125 and harmonic_ratio > 0.5:
        return "Melodic / Mid-Tempo"
    elif spectral_bandwidth > 2500 and onset_rate > 3.0:
        return "Dynamic / Rhythm-Driven"
    else:
        return "General Electronic"

def analyze_track_rhythm(fpath_str, db_bpm):
    """Worker function executed in parallel processes."""
    try:
        y, sr = librosa.load(fpath_str, sr=22050)
        
        spectral_bandwidth = float(np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr)))
        
        y_harmonic, y_percussive = librosa.effects.hpss(y)
        harmonic_energy = np.sum(y_harmonic**2)
        total_energy = np.sum(y**2)
        harmonic_ratio = float(harmonic_energy / (total_energy + 1e-6))
        
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        bpm = float(tempo[0]) if isinstance(tempo, np.ndarray) else float(tempo)
        if not bpm or bpm <= 0:
            bpm = db_bpm or 120.0
        
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)
        duration_sec = len(y) / sr
        onset_rate = len(onsets) / (duration_sec / 60.0) if duration_sec > 0 else 0.0
        
        triplet_score, rhythm_grid_type = calculate_triplet_score(y, sr, beats)
        audio_vibe = classify_vibe(bpm, harmonic_ratio, onset_rate, spectral_bandwidth)
        
        data = {
            "spectral_bandwidth_hz": round(spectral_bandwidth, 2),
            "harmonic_ratio": round(harmonic_ratio, 3),
            "triplet_score": triplet_score,
            "rhythm_grid_type": rhythm_grid_type,
            "audio_vibe": audio_vibe
        }
        return True, data
    except Exception as e:
        return False, str(e)

def main():
    parser = argparse.ArgumentParser(description="Rhythm, Groove, and Vibe Analysis pass")
    parser.add_argument("-c", "--config", default="config.json", help="Path to JSON config file")
    parser.add_argument("--db", default="audio_database.db", help="SQLite database path")
    
    cpu_count = os.cpu_count() or 4
    default_workers = max(1, cpu_count - 1)
    parser.add_argument("-w", "--workers", type=int, default=default_workers, help="Concurrent workers (defaults to max-1)")
    
    parser.add_argument("-b", "--batch-size", type=int, default=50, help="Batch size")
    parser.add_argument("-s", "--sleep", type=float, default=1.0, help="Pause between batches")
    parser.add_argument("-d", "--directory", default=None, help="Target audio directory")
    args = parser.parse_args()

    workers = args.workers

    config = {}
    config_file = Path(args.config)
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)

    search_dir_val = args.directory or config.get("output_dir", "/home/audio-repo/128mp3")
    base_dir = Path(search_dir_val).resolve()
    
    db_file = Path(args.db).resolve()

    conn = setup_database(str(db_file))
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, file_path, dsp_bpm FROM tracks WHERE audio_vibe IS NULL AND processed_path IS NOT NULL')
    all_tracks = cursor.fetchall()
    
    total_remaining = len(all_tracks)
    if total_remaining == 0:
        print_ts("🎉 No pending tracks for rhythm/vibe analysis!")
        return
        
    print_ts(f"🚀 Processing rhythm metrics for {total_remaining} tracks across {workers} workers...")
    
    completed_count = 0
    for i in range(0, total_remaining, args.batch_size):
        batch = all_tracks[i : i + args.batch_size]
        
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(analyze_track_rhythm, str(base_dir / rel_path), db_bpm): (r_id, rel_path)
                for r_id, rel_path, db_bpm in batch
            }
            
            for future in as_completed(futures):
                r_id, rel_path = futures[future]
                completed_count += 1
                success, result = future.result()
                
                if success:
                    cursor.execute('''
                        UPDATE tracks SET 
                            spectral_bandwidth_hz = ?, harmonic_ratio = ?, 
                            triplet_score = ?, rhythm_grid_type = ?, audio_vibe = ?
                        WHERE id = ?
                    ''', (
                        result['spectral_bandwidth_hz'], result['harmonic_ratio'],
                        result['triplet_score'], result['rhythm_grid_type'], result['audio_vibe'], r_id
                    ))
                    conn.commit()
                    print_ts(f"   [{completed_count}/{total_remaining}] ✅ ID {r_id} | Vibe: {result['audio_vibe']} | Grid: {result['rhythm_grid_type']}")
                else:
                    print_ts(f"   [{completed_count}/{total_remaining}] ❌ Error on ID {r_id}: {result}")
                
        if args.sleep > 0 and (i + args.batch_size) < total_remaining:
            print_ts(f"    ⏱️ Batch complete. Sleeping for {args.sleep}s...")
            time.sleep(args.sleep)

    conn.close()
    print_ts("✅ Rhythm & Vibe analysis complete!")

if __name__ == "__main__":
    main()
