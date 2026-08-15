import os
import csv
import argparse
import subprocess
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

def run_ffmpeg(input_file, output_file, bitrate, include_cover, cover_size="300", start=None, duration=None):
    """Core Engine: Sweet Spot with Cover Resizing."""
    clean_name = Path(input_file).stem 
    cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-i', str(input_file)]
    
    if start: 
        cmd.insert(cmd.index('-i'), '-ss')
        cmd.insert(cmd.index('-ss')+1, start)
    if duration: 
        cmd.extend(['-t', str(duration)])
        
    cmd.extend(['-map', '0:a'])

    if include_cover:
        cmd.extend([
            '-map', '0:v?', 
            '-c:v', 'mjpeg', 
            '-vf', f'scale={cover_size}:{cover_size}'
        ]) 
    
    cmd.extend([
        '-map_metadata', '0', 
        '-id3v2_version', '3', 
        '-metadata', f'title={clean_name}', 
        '-b:a', bitrate, 
        '-ar', '44100',                     
        str(output_file)
    ])
    
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def process_track(f, input_root, output_root, flat, bitrate, cover, cover_size, custom_grouping):
    """Worker function to process a single track independently."""
    if flat:
        relative_path = Path(f.name)
    elif input_root.is_dir():
        relative_path = f.relative_to(input_root)
    else:
        relative_path = Path(f.name)

    target_path = output_root / relative_path.with_suffix('.mp3')
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    success = run_ffmpeg(f, target_path, bitrate, cover, cover_size)
    
    if success:
        row_data = {
            'original_path': str(f),
            'processed_path': str(target_path),
            'filename': f.name,
            'title': f.stem,
            'grouping': custom_grouping if custom_grouping else f.parent.name
        }
        return success, row_data, str(relative_path)
    return success, None, str(relative_path)

if __name__ == "__main__":
    # Determine base paths dynamically relative to repository location
    REPO_DIR = Path(__file__).resolve().parent
    PARENT_DIR = REPO_DIR.parent
    
    DEFAULT_INPUT = PARENT_DIR / "musicraw"
    DEFAULT_OUTPUT = PARENT_DIR / "128mp3"
    DEFAULT_CSV = REPO_DIR / "audio_manifest.csv"
    
    # Automatically calculate default CPU workers (Leave 1 core free)
    cpu_count = os.cpu_count() or 4
    DEFAULT_WORKERS = max(1, cpu_count - 1)

    parser = argparse.ArgumentParser(description="Audio Discovery Library Scanner & Compressor (Multi-Core)")
    parser.add_argument("-i", "--input", default=str(DEFAULT_INPUT), help=f"Input Root Directory (Default: {DEFAULT_INPUT})")
    parser.add_argument("-o", "--output", default=str(DEFAULT_OUTPUT), help=f"Target Root Directory (Default: {DEFAULT_OUTPUT})")
    parser.add_argument("-b", "--bitrate", default="128k", choices=["128k", "192k", "256k", "320k"], help="Bitrate")
    parser.add_argument("--cover", action="store_true", help="Include and resize Cover Art")
    parser.add_argument("--cover-size", default="300", help="Square pixel size for cover art (default: 300)")
    parser.add_argument("--flat", action="store_true", help="Flatten all files into a single output folder")
    parser.add_argument("--csv", default=str(DEFAULT_CSV), help=f"Path to save CSV database manifest (Default: {DEFAULT_CSV})")
    parser.add_argument("-w", "--workers", type=int, default=DEFAULT_WORKERS, help=f"Number of concurrent CPU workers (Default: {DEFAULT_WORKERS})")
    parser.add_argument("--grouping", type=str, default=None, help="Custom grouping name (overrides the default parent folder name)")
    
    args = parser.parse_args()
    input_root = Path(args.input).resolve()
    output_root = Path(args.output).resolve()
    csv_path = Path(args.csv).resolve()

    if not input_root.exists():
        print(f"❌ Input directory does not exist: {input_root}")
        print("Please create the 'musicraw' directory or pass a custom path with -i / --input.")
        exit(1)

    if input_root.is_file():
        files_to_process = [input_root]
    else:
        # Added .opus to the supported extensions list
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

    # --- RESUME LOGIC ---
    processed_files = set()
    file_mode = 'w'
    write_header = True

    if csv_path.exists():
        file_mode = 'a'
        write_header = False
        try:
            with open(csv_path, mode='r', encoding='utf-8') as read_csv:
                reader = csv.DictReader(read_csv)
                for row in reader:
                    processed_files.add(row['original_path'])
            print(f"🔄 Found existing CSV. Skipping {len(processed_files)} previously processed tracks...")
        except Exception as e:
            print(f"⚠️ Error reading existing CSV: {e}. Starting fresh.")
            file_mode = 'w'
            write_header = True
            processed_files = set()

    remaining_files = [f for f in files_to_process if str(f) not in processed_files]
    
    if not remaining_files:
        print("✅ All files are already processed!")
        exit(0)
        
    print(f"🚀 Processing {len(remaining_files)} tracks using {args.workers} concurrent workers...")

    # --- MULTIPROCESSING EXECUTION ---
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, mode=file_mode, newline='', encoding='utf-8') as csv_file:
        fieldnames = ['original_path', 'processed_path', 'filename', 'title', 'grouping']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        
        if write_header:
            writer.writeheader()

        # Launch worker pool
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(
                    process_track, f, input_root, output_root, 
                    args.flat, args.bitrate, args.cover, args.cover_size, args.grouping
                ): f for f in remaining_files
            }
            
            for future in as_completed(futures):
                success, row_data, rel_path = future.result()
                print(f"    Finished: {rel_path}")
                
                if success and row_data:
                    writer.writerow(row_data)
                    csv_file.flush()

    print(f"\n✅ Clean Migration Complete to: {output_root}")
    print(f"📊 CSV Manifest Saved to: {csv_path}")
