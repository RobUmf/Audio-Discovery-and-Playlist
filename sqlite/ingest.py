#!/usr/bin/env python3
import os
import json
import argparse
import subprocess
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from mutagen import File as MutagenFile

def load_config(config_path):
    if Path(config_path).exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def init_db(db_path):
    """Initializes a fresh, empty SQLite database if it doesn't exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_path TEXT,
            processed_path TEXT,
            filename TEXT,
            grouping TEXT,
            format TEXT,
            sample_rate_hz INTEGER,
            duration_sec REAL,
            file_path TEXT UNIQUE,
            title TEXT,
            artist TEXT,
            album TEXT,
            album_artist TEXT,
            genre TEXT,
            year INTEGER,
            tracknumber TEXT,
            discnumber TEXT,
            loudness_lufs REAL,
            loudness_rms_db REAL,
            loudness_peak_db REAL,
            dynamics_crest_factor_db REAL,
            dsp_bpm INTEGER,
            rhythm_pulse_clarity REAL,
            dsp_key TEXT,
            key_confidence REAL,
            hpss_harmonic_ratio REAL,
            spectral_centroid_hz REAL,
            spectral_rolloff_hz REAL,
            spectral_flatness REAL,
            health_dc_offset REAL,
            health_clip_pct REAL,
            health_is_upscaled_lossy INTEGER,
            health_est_cutoff_hz INTEGER,
            buy_url TEXT,
            youtube_url TEXT
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_path ON tracks(file_path)")
    conn.commit()
    conn.close()

def get_processed_paths(db_path):
    if not Path(db_path).exists():
        return set()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT file_path FROM tracks WHERE file_path IS NOT NULL")
    paths = {row[0] for row in cursor.fetchall()}
    conn.close()
    return paths

def parse_bitrate_bps(bitrate_str):
    clean = str(bitrate_str).lower().replace('k', '').strip()
    if clean.isdigit():
        return int(clean) * 1000
    return 128000

def get_mp3_bitrate(input_file):
    cmd = [
        'ffprobe', '-v', 'error',
        '-select_streams', 'a:0',
        '-show_entries', 'stream=bit_rate',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(input_file)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        if output.isdigit():
            return int(output)
    except Exception:
        pass
    return None

def extract_id3_tags(file_path):
    data = {
        "title": Path(file_path).stem,
        "artist": "Unknown",
        "album": "Unknown",
        "album_artist": None,
        "genre": None,
        "year": None,
        "tracknumber": None,
        "discnumber": None,
        "format": Path(file_path).suffix.lstrip('.').lower(),
        "sample_rate_hz": None,
        "duration_sec": 0.0
    }
    try:
        audio = MutagenFile(file_path, easy=True)
        if audio is not None:
            if audio.info:
                data["duration_sec"] = round(getattr(audio.info, 'length', 0.0), 2)
                data["sample_rate_hz"] = getattr(audio.info, 'sample_rate', None)
            def get_tag(key):
                val = audio.get(key)
                return val[0] if val else None
            data["title"] = get_tag('title') or data["title"]
            data["artist"] = get_tag('artist') or "Unknown"
            data["album"] = get_tag('album') or "Unknown"
            data["album_artist"] = get_tag('albumartist')
            data["genre"] = get_tag('genre')
            year_val = get_tag('date') or get_tag('year')
            if year_val:
                digits = "".join(filter(str.isdigit, str(year_val)))
                data["year"] = int(digits[:4]) if digits else None
            data["tracknumber"] = get_tag('tracknumber')
            data["discnumber"] = get_tag('discnumber')
    except Exception:
        pass
    return data

def run_ffmpeg(input_file, output_file, bitrate, include_cover, cover_size="300"):
    clean_name = Path(input_file).stem 
    cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-i', str(input_file)]
    cmd.extend(['-map', '0:a'])
    
    if include_cover:
        cmd.extend(['-map', '0:v?', '-c:v', 'mjpeg', '-vf', f'scale={cover_size}:{cover_size}']) 
        
    cmd.extend([
        '-map_metadata', '0', '-id3v2_version', '3', 
        '-metadata', f'title={clean_name}', '-b:a', bitrate, '-ar', '44100', str(output_file)
    ])
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def process_track(f, input_root, output_root, flat, bitrate, cover, cover_size, override_group):
    if flat:
        relative_path = Path(f.name)
    elif input_root.is_dir():
        relative_path = f.relative_to(input_root)
    else:
        relative_path = Path(f.name)
        
    target_path = output_root / relative_path.with_suffix('.mp3')
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    target_bps = parse_bitrate_bps(bitrate)
    is_mp3 = f.suffix.lower() == '.mp3'
    should_copy = False

    if is_mp3:
        actual_bps = get_mp3_bitrate(f)
        if actual_bps and actual_bps <= (target_bps + 4000):
            should_copy = True

    if should_copy:
        try:
            shutil.copy2(f, target_path)
            success = True
        except Exception:
            success = False
    else:
        success = run_ffmpeg(f, target_path, bitrate, cover, cover_size)
    
    if success:
        meta = extract_id3_tags(f)
        group_name = override_group if override_group else f.parent.name
        
        row_data = {
            'original_path': str(f.resolve()),
            'processed_path': str(target_path.resolve()),
            'filename': f.name,
            'grouping': group_name,
            'file_path': str(target_path.resolve()),
            'format': meta['format'],
            'sample_rate_hz': meta['sample_rate_hz'],
            'duration_sec': meta['duration_sec'],
            'title': meta['title'],
            'artist': meta['artist'],
            'album': meta['album'],
            'album_artist': meta['album_artist'],
            'genre': meta['genre'],
            'year': meta['year'],
            'tracknumber': meta['tracknumber'],
            'discnumber': meta['discnumber']
        }
        return True, row_data, str(relative_path)
    return False, None, str(relative_path)

if __name__ == "__main__":
    REPO_DIR = Path(__file__).resolve().parent
    BASE_DIR = Path(os.environ.get("MUSIC_BASE", REPO_DIR.parent))
    DEFAULT_CONFIG = REPO_DIR / "config.json"
    
    cpu_count = os.cpu_count() or 4
    DEFAULT_WORKERS = max(1, cpu_count - 1)
    
    config = load_config(DEFAULT_CONFIG)
    
    parser = argparse.ArgumentParser(description="Config-Driven SQLite Audio Ingestion Engine")
    parser.add_argument("-c", "--config", default=str(DEFAULT_CONFIG), help="Path to config.json")
    parser.add_argument("-i", "--input", help="Input Root Directory (Overrides config)")
    parser.add_argument("-o", "--output", help="Target Root Directory (Overrides config)")
    parser.add_argument("-b", "--bitrate", help="Target Bitrate (Overrides config)")
    parser.add_argument("--cover", action="store_true", help="Include Cover Art (Overrides config)")
    parser.add_argument("--cover-size", help="Square pixel size for cover art")
    parser.add_argument("--flat", action="store_true", help="Flatten all files into a single output folder")
    parser.add_argument("-w", "--workers", type=int, help="Number of concurrent CPU workers")
    parser.add_argument("-g", "--group", help="Optional grouping tag override for this batch")
    parser.add_argument("--db", help="Path to SQLite database (Overrides config)")
    
    args = parser.parse_args()
    
    if args.config != str(DEFAULT_CONFIG):
         config = load_config(args.config)
    
    input_root = Path(args.input or config.get("input_dir", BASE_DIR / "musicraw")).expanduser().resolve()
    output_root = Path(args.output or config.get("output_dir", BASE_DIR / "128mp3")).expanduser().resolve()
    db_path = Path(args.db or config.get("db_path", REPO_DIR / "audio_database.db")).expanduser().resolve()
    bitrate = args.bitrate or config.get("bitrate", "128k")
    include_cover = args.cover or config.get("include_cover", True)
    cover_size = args.cover_size or str(config.get("cover_size", "300"))
    flat_mode = args.flat or config.get("flat", False)
    workers = args.workers or config.get("workers", DEFAULT_WORKERS)
    override_group = args.group

    if not input_root.exists():
        print(f"❌ Input directory does not exist: {input_root}")
        exit(1)

    init_db(db_path)

    if input_root.is_file():
        files_to_process = [input_root]
    else:
        extensions = ('.mp3', '.wav', '.flac', '.m4a', '.opus')
        all_found = [f for f in input_root.rglob('*') if f.suffix.lower() in extensions]
        
        files_to_process = []
        seen_filenames = {}
        for f in all_found:
            if f.name not in seen_filenames:
                seen_filenames[f.name] = f
                files_to_process.append(f)
            else:
                if len(f.parts) > len(seen_filenames[f.name].parts):
                    files_to_process.remove(seen_filenames[f.name])
                    seen_filenames[f.name] = f
                    files_to_process.append(f)
    
    processed_paths = get_processed_paths(db_path)
    
    remaining_files = []
    for f in files_to_process:
        if flat_mode:
            test_rel = Path(f.name)
        elif input_root.is_dir():
            test_rel = f.relative_to(input_root)
        else:
            test_rel = Path(f.name)
            
        expected_target = str((output_root / test_rel.with_suffix('.mp3')).resolve())
        if expected_target not in processed_paths:
            remaining_files.append(f)

    if not remaining_files:
        print("✅ All tracks are already compressed and registered in the database!")
        exit(0)

    total_tracks = len(remaining_files)
    completed_count = 0

    print(f"🚀 Processing {total_tracks} unique tracks at {bitrate} using {workers} workers...")
    if override_group:
        print(f"🏷️ Assigned Group Tag Override: '{override_group}'")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                process_track, f, input_root, output_root, flat_mode, 
                bitrate, include_cover, cover_size, override_group
            ): f 
            for f in remaining_files
        }
        
        for future in as_completed(futures):
            completed_count += 1
            success, row_data, rel_path = future.result()
            
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"[{timestamp}] [{completed_count:4d}/{total_tracks:4d}] Finished: {rel_path}")
            
            if success and row_data:
                keys = list(row_data.keys())
                values = list(row_data.values())
                placeholders = ",".join(["?"] * len(keys))
                columns = ",".join(keys)
                sql = f"INSERT OR REPLACE INTO tracks ({columns}) VALUES ({placeholders})"
                cursor.execute(sql, values)
                conn.commit()

    conn.close()
    print(f"\n✅ Ingestion Complete! Database updated: {db_path}")            album_artist TEXT,
            genre TEXT,
            year INTEGER,
            tracknumber TEXT,
            discnumber TEXT,
            loudness_lufs REAL,
            loudness_rms_db REAL,
            loudness_peak_db REAL,
            dynamics_crest_factor_db REAL,
            dsp_bpm INTEGER,
            rhythm_pulse_clarity REAL,
            dsp_key TEXT,
            key_confidence REAL,
            hpss_harmonic_ratio REAL,
            spectral_centroid_hz REAL,
            spectral_rolloff_hz REAL,
            spectral_flatness REAL,
            health_dc_offset REAL,
            health_clip_pct REAL,
            health_is_upscaled_lossy INTEGER,
            health_est_cutoff_hz INTEGER,
            buy_url TEXT,
            youtube_url TEXT
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_path ON tracks(file_path)")
    conn.commit()
    conn.close()

def get_processed_paths(db_path):
    if not Path(db_path).exists():
        return set()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT file_path FROM tracks WHERE file_path IS NOT NULL")
    paths = {row[0] for row in cursor.fetchall()}
    conn.close()
    return paths

def parse_bitrate_bps(bitrate_str):
    clean = str(bitrate_str).lower().replace('k', '').strip()
    if clean.isdigit():
        return int(clean) * 1000
    return 128000

def get_mp3_bitrate(input_file):
    cmd = [
        'ffprobe', '-v', 'error',
        '-select_streams', 'a:0',
        '-show_entries', 'stream=bit_rate',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(input_file)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        if output.isdigit():
            return int(output)
    except Exception:
        pass
    return None

def extract_id3_tags(file_path):
    data = {
        "title": Path(file_path).stem,
        "artist": "Unknown",
        "album": "Unknown",
        "album_artist": None,
        "genre": None,
        "year": None,
        "tracknumber": None,
        "discnumber": None,
        "format": Path(file_path).suffix.lstrip('.').lower(),
        "sample_rate_hz": None,
        "duration_sec": 0.0
    }
    try:
        audio = MutagenFile(file_path, easy=True)
        if audio is not None:
            if audio.info:
                data["duration_sec"] = round(getattr(audio.info, 'length', 0.0), 2)
                data["sample_rate_hz"] = getattr(audio.info, 'sample_rate', None)
            def get_tag(key):
                val = audio.get(key)
                return val[0] if val else None
            data["title"] = get_tag('title') or data["title"]
            data["artist"] = get_tag('artist') or "Unknown"
            data["album"] = get_tag('album') or "Unknown"
            data["album_artist"] = get_tag('albumartist')
            data["genre"] = get_tag('genre')
            year_val = get_tag('date') or get_tag('year')
            if year_val:
                digits = "".join(filter(str.isdigit, str(year_val)))
                data["year"] = int(digits[:4]) if digits else None
            data["tracknumber"] = get_tag('tracknumber')
            data["discnumber"] = get_tag('discnumber')
    except Exception:
        pass
    return data

def run_ffmpeg(input_file, output_file, bitrate, include_cover, cover_size="300"):
    clean_name = Path(input_file).stem 
    cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-i', str(input_file)]
    cmd.extend(['-map', '0:a'])
    
    if include_cover:
        cmd.extend(['-map', '0:v?', '-c:v', 'mjpeg', '-vf', f'scale={cover_size}:{cover_size}']) 
        
    cmd.extend([
        '-map_metadata', '0', '-id3v2_version', '3', 
        '-metadata', f'title={clean_name}', '-b:a', bitrate, '-ar', '44100', str(output_file)
    ])
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def process_track(f, input_root, output_root, flat, bitrate, cover, cover_size, override_group):
    if flat:
        relative_path = Path(f.name)
    elif input_root.is_dir():
        relative_path = f.relative_to(input_root)
    else:
        relative_path = Path(f.name)
        
    target_path = output_root / relative_path.with_suffix('.mp3')
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    target_bps = parse_bitrate_bps(bitrate)
    is_mp3 = f.suffix.lower() == '.mp3'
    should_copy = False

    if is_mp3:
        actual_bps = get_mp3_bitrate(f)
        if actual_bps and actual_bps <= (target_bps + 4000):
            should_copy = True

    if should_copy:
        try:
            shutil.copy2(f, target_path)
            success = True
        except Exception:
            success = False
    else:
        success = run_ffmpeg(f, target_path, bitrate, cover, cover_size)
    
    if success:
        meta = extract_id3_tags(f)
        group_name = override_group if override_group else f.parent.name
        
        row_data = {
            'original_path': str(f.resolve()),
            'processed_path': str(target_path.resolve()),
            'filename': f.name,
            'grouping': group_name,
            'file_path': str(target_path.resolve()),
            'format': meta['format'],
            'sample_rate_hz': meta['sample_rate_hz'],
            'duration_sec': meta['duration_sec'],
            'title': meta['title'],
            'artist': meta['artist'],
            'album': meta['album'],
            'album_artist': meta['album_artist'],
            'genre': meta['genre'],
            'year': meta['year'],
            'tracknumber': meta['tracknumber'],
            'discnumber': meta['discnumber']
        }
        return True, row_data, str(relative_path)
    return False, None, str(relative_path)

if __name__ == "__main__":
    REPO_DIR = Path(__file__).resolve().parent
    BASE_DIR = Path(os.environ.get("MUSIC_BASE", REPO_DIR.parent))
    DEFAULT_CONFIG = REPO_DIR / "config.json"
    
    cpu_count = os.cpu_count() or 4
    DEFAULT_WORKERS = max(1, cpu_count - 1)
    
    config = load_config(DEFAULT_CONFIG)
    
    parser = argparse.ArgumentParser(description="Config-Driven SQLite Audio Ingestion Engine")
    parser.add_argument("-c", "--config", default=str(DEFAULT_CONFIG), help="Path to config.json")
    parser.add_argument("-i", "--input", help="Input Root Directory (Overrides config)")
    parser.add_argument("-o", "--output", help="Target Root Directory (Overrides config)")
    parser.add_argument("-b", "--bitrate", help="Target Bitrate (Overrides config)")
    parser.add_argument("--cover", action="store_true", help="Include Cover Art (Overrides config)")
    parser.add_argument("--cover-size", help="Square pixel size for cover art")
    parser.add_argument("--flat", action="store_true", help="Flatten all files into a single output folder")
    parser.add_argument("-w", "--workers", type=int, help="Number of concurrent CPU workers")
    parser.add_argument("-g", "--group", help="Optional grouping tag override for this batch")
    parser.add_argument("--db", help="Path to SQLite database (Overrides config)")
    
    args = parser.parse_args()
    
    if args.config != str(DEFAULT_CONFIG):
         config = load_config(args.config)
    
    input_root = Path(args.input or config.get("input_dir", BASE_DIR / "musicraw")).resolve()
    output_root = Path(args.output or config.get("output_dir", BASE_DIR / "128mp3")).resolve()
    db_path = Path(args.db or config.get("db_path", REPO_DIR / "audio_database.db")).resolve()
    bitrate = args.bitrate or config.get("bitrate", "128k")
    include_cover = args.cover or config.get("include_cover", True)
    cover_size = args.cover_size or str(config.get("cover_size", "300"))
    flat_mode = args.flat or config.get("flat", False)
    workers = args.workers or config.get("workers", DEFAULT_WORKERS)
    override_group = args.group

    if not input_root.exists():
        print(f"❌ Input directory does not exist: {input_root}")
        exit(1)

    init_db(db_path)

    if input_root.is_file():
        files_to_process = [input_root]
    else:
        extensions = ('.mp3', '.wav', '.flac', '.m4a', '.opus')
        all_found = [f for f in input_root.rglob('*') if f.suffix.lower() in extensions]
        
        files_to_process = []
        seen_filenames = {}
        for f in all_found:
            if f.name not in seen_filenames:
                seen_filenames[f.name] = f
                files_to_process.append(f)
            else:
                if len(f.parts) > len(seen_filenames[f.name].parts):
                    files_to_process.remove(seen_filenames[f.name])
                    seen_filenames[f.name] = f
                    files_to_process.append(f)
    
    processed_paths = get_processed_paths(db_path)
    
    remaining_files = []
    for f in files_to_process:
        if flat_mode:
            test_rel = Path(f.name)
        elif input_root.is_dir():
            test_rel = f.relative_to(input_root)
        else:
            test_rel = Path(f.name)
            
        expected_target = str((output_root / test_rel.with_suffix('.mp3')).resolve())
        if expected_target not in processed_paths:
            remaining_files.append(f)

    if not remaining_files:
        print("✅ All tracks are already compressed and registered in the database!")
        exit(0)

    total_tracks = len(remaining_files)
    completed_count = 0

    print(f"🚀 Processing {total_tracks} unique tracks at {bitrate} using {workers} workers...")
    if override_group:
        print(f"🏷️ Assigned Group Tag Override: '{override_group}'")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                process_track, f, input_root, output_root, flat_mode, 
                bitrate, include_cover, cover_size, override_group
            ): f 
            for f in remaining_files
        }
        
        for future in as_completed(futures):
            completed_count += 1
            success, row_data, rel_path = future.result()
            
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"[{timestamp}] [{completed_count:4d}/{total_tracks:4d}] Finished: {rel_path}")
            
            if success and row_data:
                keys = list(row_data.keys())
                values = list(row_data.values())
                placeholders = ",".join(["?"] * len(keys))
                columns = ",".join(keys)
                sql = f"INSERT OR REPLACE INTO tracks ({columns}) VALUES ({placeholders})"
                cursor.execute(sql, values)
                conn.commit()

    conn.close()
    print(f"\n✅ Ingestion Complete! Database updated: {db_path}")
