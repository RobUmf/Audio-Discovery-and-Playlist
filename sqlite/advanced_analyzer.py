import sqlite3
import os
import json
import warnings
import numpy as np
import librosa
import time
import argparse
from datetime import datetime
from pathlib import Path

# Suppress warnings for clean console output
warnings.filterwarnings('ignore', category=UserWarning)

def print_ts(msg):
    """Print message with a clear timestamp prefix."""
    now = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{now} {msg}")

def setup_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    new_columns = {
        "onset_rate": "REAL",
        "attack_strength": "REAL",
        "spectral_contrast": "REAL",
        "mfcc_profile": "TEXT"
    }
    for col, dtype in new_columns.items():
        try:
            cursor.execute(f"ALTER TABLE tracks ADD COLUMN {col} {dtype}")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    return conn

def estimate_key(chroma):
    maj_profile = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
    min_profile = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
    keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    chroma_vals = np.sum(chroma, axis=1)
    best_corr = -1
    best_key = "Unknown"
    
    for i in range(12):
        maj_test = np.roll(maj_profile, i)
        min_test = np.roll(min_profile, i)
        
        maj_corr = np.corrcoef(maj_test, chroma_vals)[0, 1]
        min_corr = np.corrcoef(min_test, chroma_vals)[0, 1]
        
        if maj_corr > best_corr:
            best_corr = maj_corr
            best_key = f"{keys[i]} Major"
        if min_corr > best_corr:
            best_corr = min_corr
            best_key = f"{keys[i]} Minor"
            
    return best_key, round(float(best_corr), 3)

def get_cutoff_hz(y, sr):
    S = np.abs(librosa.stft(y))
    mean_spectrum = np.mean(S, axis=1)
    db_spectrum = librosa.amplitude_to_db(mean_spectrum, ref=np.max)
    
    cutoff_bin = len(db_spectrum) - 1
    for i in range(len(db_spectrum)-1, 0, -1):
        if db_spectrum[i] > -60:
            cutoff_bin = i
            break
            
    freqs = librosa.fft_frequencies(sr=sr)
    cutoff_hz = int(freqs[cutoff_bin])
    is_upscaled = 1 if cutoff_hz < 16500 else 0
    return cutoff_hz, is_upscaled

def main():
    parser = argparse.ArgumentParser(description="Advanced Audio DSP pass")
    parser.add_argument("-c", "--config", default="config.json", help="Path to JSON config file")
    parser.add_argument("--db", default="/home/audio-repo/sqlite/audio_database.db", help="SQLite database path")
    parser.add_argument("-b", "--batch-size", type=int, default=50, help="Reboot workers after N files to clear RAM")
    parser.add_argument("-s", "--sleep", type=float, default=2.0, help="Pause in seconds between batches")
    parser.add_argument("-d", "--directory", default=None, help="Target audio directory (overrides config)")
    args = parser.parse_args()

    # Load configuration
    config = {}
    config_file = Path(args.config)
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)

    # Resolve paths dynamically
    search_dir_val = args.directory or config.get("output_dir", "/home/audio-repo/128mp3")
    base_dir = Path(search_dir_val).resolve()
    
    db_path_val = args.db or config.get("db_path", args.db)
    db_file = Path(db_path_val).resolve()

    conn = setup_database(str(db_file))
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, file_path FROM tracks WHERE dsp_key IS NULL')
    all_tracks = cursor.fetchall()
    
    total_remaining = len(all_tracks)
    if total_remaining == 0:
        print_ts("🎉 No pending tracks for advanced DSP!")
        return
        
    print_ts(f"🚀 Processing {total_remaining} unindexed tracks...")
    print_ts(f"⚙️ Settings: Batch Size={args.batch_size}, Sleep={args.sleep}s, Base Dir={base_dir}")

    completed_count = 0
    
    # Batch chunking
    for i in range(0, total_remaining, args.batch_size):
        batch = all_tracks[i : i + args.batch_size]
        
        for r_id, rel_path in batch:
            full_path = base_dir / rel_path
            fpath_str = str(full_path)
            completed_count += 1
            
            if not full_path.exists():
                print_ts(f"   [{completed_count}/{total_remaining}] ⚠️ Missing file for ID {r_id}: {fpath_str}")
                continue
                
            print_ts(f"   [{completed_count}/{total_remaining}] ⚙️ Analyzing ID {r_id}: {full_path.name}...")
            
            try:
                try:
                    dur = librosa.get_duration(path=fpath_str)
                except TypeError:
                    dur = librosa.get_duration(filename=fpath_str)
                    
                offset = max(0, (dur / 2) - 30)
                y, sr = librosa.load(fpath_str, sr=22050, offset=offset, duration=60.0)
                
                chroma = librosa.feature.chroma_stft(y=y, sr=sr)
                dsp_key, key_conf = estimate_key(chroma)
                cutoff_hz, is_upscale = get_cutoff_hz(y, sr)
                
                onset_env = librosa.onset.onset_strength(y=y, sr=sr)
                onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)
                attack_strength = float(np.mean(onset_env))
                onset_rate = len(onsets) / 60.0
                
                contrast = float(np.mean(librosa.feature.spectral_contrast(y=y, sr=sr)))
                mfccs = np.mean(librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13), axis=1).tolist()
                mfccs_rounded = [round(x, 2) for x in mfccs]
                
                cursor.execute('''
                    UPDATE tracks SET 
                        dsp_key = ?, key_confidence = ?, 
                        health_est_cutoff_hz = ?, health_is_upscaled_lossy = ?,
                        onset_rate = ?, attack_strength = ?,
                        spectral_contrast = ?, mfcc_profile = ?
                    WHERE id = ?
                ''', (
                    dsp_key, key_conf, 
                    cutoff_hz, is_upscale, 
                    round(onset_rate, 2), round(attack_strength, 3), 
                    round(contrast, 3), json.dumps(mfccs_rounded), 
                    r_id
                ))
                conn.commit()
                print_ts(f"      ✅ Key: {dsp_key} | Cutoff: {cutoff_hz}Hz | Upscaled: {bool(is_upscale)}")
                
            except Exception as e:
                print_ts(f"      ❌ Error on ID {r_id}: {e}")
                
        # Pause between batches
        if args.sleep > 0 and (i + args.batch_size) < total_remaining:
            print_ts(f"    ⏱️ Batch complete. Sleeping for {args.sleep}s to cool down before next batch...")
            time.sleep(args.sleep)

    conn.close()
    print_ts("✅ DSP Batch complete!")

if __name__ == "__main__":
    main()
