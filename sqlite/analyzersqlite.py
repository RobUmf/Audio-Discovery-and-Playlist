#!/usr/bin/env python3
import os
import sys
import json
import argparse
import gc
import time
sqlite3 = __import__('sqlite3')
from datetime import datetime
import numpy as np
import librosa
from pydub import AudioSegment
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import warnings

warnings.filterwarnings('ignore', module='librosa')

import scipy.signal
if not hasattr(scipy.signal, 'hann'):
    scipy.signal.hann = scipy.signal.windows.hann

def analyze_track_assets(file_path, target_sr=22050, max_analyze_sec=120.0):
    try:
        file_path_obj = Path(file_path).resolve()
        file_path_str = str(file_path_obj)
        filename = file_path_obj.name
        parent_dir = file_path_obj.parent.name

        # PyDub handles the entire file for accurate full-track loudness
        audio = AudioSegment.from_mp3(file_path_str)
        duration_sec = float(len(audio) / 1000.0)
        rms_db = float(audio.dBFS)

        # --- SMART LOADING LOGIC ---
        if duration_sec > max_analyze_sec:
            # Grab a chunk from the middle to avoid long intros
            load_offset = (duration_sec - max_analyze_sec) / 2.0
            load_duration = max_analyze_sec
        else:
            load_offset = 0.0
            load_duration = None

        # Downsample to save RAM (if target_sr > 0), else native rate
        sr_arg = target_sr if target_sr and target_sr > 0 else None
        
        # Librosa only decodes the exact slice we need, saving massive amounts of RAM
        y, sr = librosa.load(file_path_str, sr=sr_arg, mono=True, offset=load_offset, duration=load_duration)
        
        peak_val = float(np.max(np.abs(y)))
        peak_db = float(20 * np.log10(peak_val)) if peak_val > 0 else -99.0
        crest_factor_db = float(peak_db - rms_db)

        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        dsp_bpm = int(round(float(np.atleast_1d(tempo)[0])))
        
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        rhythm_pulse_clarity = float(np.max(librosa.autocorrelate(onset_env)) / (np.sum(onset_env) + 1e-5))
        rhythm_pulse_clarity = round(min(max(rhythm_pulse_clarity, 0.0), 1.0), 4)

        y_harmonic, y_percussive = librosa.effects.hpss(y)
        power_h = float(np.sum(y_harmonic ** 2))
        power_p = float(np.sum(y_percussive ** 2))
        total_power = power_h + power_p
        hpss_harmonic_ratio = round(power_h / total_power, 4) if total_power > 0 else 0.0

        spectral_centroid_hz = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
        spectral_rolloff_hz = float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr)))
        spectral_flatness = float(np.mean(librosa.feature.spectral_flatness(y=y)))

        dc_offset = float(np.mean(y))
        clipped_samples = np.sum(np.abs(y) >= 0.99)
        health_clip_pct = float((clipped_samples / len(y)) * 100) if len(y) > 0 else 0.0

        # Match string to link local paths to the DB paths agnostically
        match_suffix = f"%/{parent_dir}/{filename}"

        row_data = {
            "match_suffix": match_suffix,
            "loudness_lufs": round(rms_db, 2),
            "loudness_rms_db": round(rms_db, 2),
            "loudness_peak_db": round(peak_db, 2),
            "dynamics_crest_factor_db": round(crest_factor_db, 2),
            "dsp_bpm": dsp_bpm,
            "rhythm_pulse_clarity": rhythm_pulse_clarity,
            "hpss_harmonic_ratio": hpss_harmonic_ratio,
            "spectral_centroid_hz": round(spectral_centroid_hz, 2),
            "spectral_rolloff_hz": round(spectral_rolloff_hz, 2),
            "spectral_flatness": round(spectral_flatness, 6),
            "health_dc_offset": round(dc_offset, 6),
            "health_clip_pct": round(health_clip_pct, 3)
        }
        
        # Explicit memory purge before worker returns (added 'audio' to clear PyDub bloat)
        del audio, y, y_harmonic, y_percussive, onset_env
        gc.collect()

        return True, row_data

    except Exception as e:
        return False, f"{Path(file_path).name} - Error: {e}"

def main():
    parser = argparse.ArgumentParser(description="Audio Database Feature Ingester")
    parser.add_argument("-c", "--config", default="config.json", help="Path to JSON config file")
    parser.add_argument("-d", "--directory", default=None, help="Target audio directory (overrides config)")
    parser.add_argument("--db", default=None, help="SQLite database path (overrides config)")
    
    cpu_count = os.cpu_count() or 4
    default_workers = max(1, cpu_count - 1)
    parser.add_argument("-w", "--workers", type=int, default=default_workers, help="Concurrent workers")
    parser.add_argument("--sr", type=int, default=22050, help="Downsample rate to save RAM (default 22050, 0 for native)")
    
    # --- NEW THROTTLE CONTROLS ---
    parser.add_argument("-b", "--batch-size", type=int, default=50, help="Reboot workers after N files to clear RAM")
    parser.add_argument("-s", "--sleep", type=float, default=2.0, help="Pause in seconds between batches")
    parser.add_argument("--max-dur", type=float, default=120.0, help="Max duration in seconds to analyze per track")
    
    args = parser.parse_args()

    # Load configuration
    config = {}
    config_file = Path(args.config)
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)

    # Resolve paths dynamically
    search_dir_val = args.directory or config.get("output_dir", "/storage/2013-1E1B/128mp3")
    search_dir = Path(search_dir_val).resolve()

    db_path_val = args.db or config.get("db_path", "audio_database.db")
    db_file = Path(db_path_val).resolve()

    print(f"Connecting to database: {db_file}")
    print(f"Scanning target directory: {search_dir}")
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    local_files = [f.resolve() for f in search_dir.rglob('*.mp3') if not f.name.endswith('.m3u')]
    
    # Pull already processed suffixes so we can safely pause and resume
    cursor.execute("SELECT file_path FROM tracks WHERE loudness_rms_db IS NOT NULL")
    processed_db_paths = [row[0] for row in cursor.fetchall() if row[0]]
    processed_suffixes = {f"{Path(p).parent.name}/{Path(p).name}" for p in processed_db_paths}

    remaining_files = [f for f in local_files if f"{f.parent.name}/{f.name}" not in processed_suffixes]
    total_remaining = len(remaining_files)

    if remaining_files:
        print(f"🚀 Processing {total_remaining} unindexed tracks across {args.workers} workers")
        print(f"⚙️  Settings: Batch Size={args.batch_size}, Sleep={args.sleep}s, Max Duration Slice={args.max_dur}s...")
        
        completed_count = 0
        
        # --- BATCH CHUNKING FOR HARD RAM CLEARING ---
        for i in range(0, total_remaining, args.batch_size):
            batch = remaining_files[i : i + args.batch_size]
            
            with ProcessPoolExecutor(max_workers=args.workers) as executor:
                futures = {executor.submit(analyze_track_assets, f, args.sr, args.max_dur): f for f in batch}
                
                for future in as_completed(futures):
                    success, result = future.result()
                    completed_count += 1
                    current_time = datetime.now().strftime("%H:%M:%S")
                    
                    if success:
                        cursor.execute("""
                            UPDATE tracks SET 
                                loudness_lufs = ?, loudness_rms_db = ?, loudness_peak_db = ?, 
                                dynamics_crest_factor_db = ?, dsp_bpm = ?, rhythm_pulse_clarity = ?, 
                                hpss_harmonic_ratio = ?, spectral_centroid_hz = ?, spectral_rolloff_hz = ?, 
                                spectral_flatness = ?, health_dc_offset = ?, health_clip_pct = ?
                            WHERE file_path LIKE ?
                        """, (
                            result['loudness_lufs'], result['loudness_rms_db'], result['loudness_peak_db'],
                            result['dynamics_crest_factor_db'], result['dsp_bpm'], result['rhythm_pulse_clarity'],
                            result['hpss_harmonic_ratio'], result['spectral_centroid_hz'], result['spectral_rolloff_hz'],
                            result['spectral_flatness'], result['health_dc_offset'], result['health_clip_pct'],
                            result['match_suffix']
                        ))
                        conn.commit()
                        
                        if cursor.rowcount > 0:
                            print(f"    [{current_time}] [{completed_count}/{total_remaining}] Updated: {Path(result['match_suffix']).name}")
                        else:
                            print(f"    [{current_time}] [{completed_count}/{total_remaining}] ⚠️ No DB match found for: {Path(result['match_suffix']).name}")
                    else:
                        print(f"    [{current_time}] [{completed_count}/{total_remaining}] Failed: {result}")
                        
            # Pause between batches to allow CPU and RAM to completely settle
            if args.sleep > 0 and (i + args.batch_size) < total_remaining:
                print(f"    ⏱️ Batch complete. Sleeping for {args.sleep}s to cool down before next batch...")
                time.sleep(args.sleep)

        print(f"\n✅ DSP feature updates complete into {db_file}")
    else:
        print("\n✅ Database is fully up to date with DSP metrics!")

    conn.close()

if __name__ == "__main__":
    main()