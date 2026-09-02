#!/usr/bin/env python3
import json
import argparse
from pathlib import Path
from collections import Counter

def format_size(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def analyze_folder(folder_path):
    p = Path(folder_path)
    if not p.exists():
        print(f"❌ Path does not exist: {p}")
        return None, 0, 0
    
    extensions = ('.mp3', '.flac', '.opus', '.wav', '.m4a')
    found_files = [f for f in p.rglob('*') if f.suffix.lower() in extensions]
    
    counts = Counter(f.suffix.lower() for f in found_files)
    total_size = sum(f.stat().st_size for f in found_files if f.is_file())
    return counts, len(found_files), total_size

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audio Repository Format Audit")
    parser.add_argument("-c", "--config", default="config.json", help="Path to JSON config file")
    parser.add_argument("-i", "--input", help="Input music directory (overrides config)")
    parser.add_argument("-o", "--output", help="Output compressed directory (overrides config)")
    args = parser.parse_args()

    config = {}
    config_file = Path(args.config)
    if config_file.exists():
        print(f"📄 Loading configuration from {config_file}")
        with open(config_file, 'r') as f:
            config = json.load(f)
    else:
        print(f"⚠️ Warning: Config file '{args.config}' not found. Using default paths.")

    # Added .expanduser() to dynamically resolve ~ to the user's home directory
    input_dir = Path(args.input or config.get("input_dir", '/storage/2013-1E1B/musicraw')).expanduser()
    output_dir = Path(args.output or config.get("output_dir", '/storage/2013-1E1B/128mp3')).expanduser()

    folders = {
        "Raw Library (musicraw)": input_dir,
        "Compressed Library (128mp3)": output_dir
    }

    print("=========================================")
    print("      AUDIO REPOSITORY FORMAT AUDIT      ")
    print("=========================================")

    for name, path in folders.items():
        print(f"\n📁 {name}")
        print(f"   Path: {path}")
        counts, total_count, total_size = analyze_folder(path)
        
        if counts is not None:
            if total_count == 0:
                print("   (Folder is empty)")
            else:
                for ext, count in counts.most_common():
                    print(f"   ├── {ext.upper()}: {count} files")
                print(f"   └── Total: {total_count} files | Size: {format_size(total_size)}")
        print("-" * 41)
