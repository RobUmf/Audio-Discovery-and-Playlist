# Audio Discovery Library Scanner & Compressor

A high-performance, multi-core Python utility designed to recursively scan, normalize, compress, and organize large multimedia and music libraries (optimized for open-source karaoke setups like UltraStar Deluxe and UltraSinger).

## Features

- **Multi-Core Processing:** Utilizes a process pool executor to saturate CPU cores for lightning-fast batch conversions.
- **Crash-Safe Resume Logic:** Automatically checks existing CSV manifests upon startup, skips already processed tracks, and picks up right where it left off.
- **Live Disk Flushing:** Writes database records to disk immediately as tracks finish to prevent data loss during interruptions.
- **Smart Deduplication:** Filters duplicate tracks dynamically based on directory depth.
- **Embedded Cover Art Optimization:** Automatically maps, re-encodes (as MJPEG), and scales cover art to precise dimensions.

## Requirements

- Python 3.8+
- `ffmpeg` installed and available in your system path.

## Usage

Run the scanner from your terminal using command-line arguments for your input root and target destination:

```bash
python scanner.py -i "/path/to/source/music" -o "/path/to/destination/music" -b 128k --cover --cover-size 500 -w 3
