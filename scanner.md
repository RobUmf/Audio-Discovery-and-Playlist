# Audio Discovery Library Scanner & Compressor

A high-performance, multi-core Python utility designed to recursively scan, normalize, compress, and organize large music libraries for maximum portability and streaming efficiency. 

By compressing high-bitrate files (such as 320k) down to efficient footprints (like 128k) while retaining pristine quality—virtually indistinguishable on standard earbuds, car stereos, or portable speakers unless you are using high-end audio gear—it slashes storage requirements by over 60%. Perfect for loading up MP3 players, mobile storage expansions, and lightweight portable streaming setups.

## Features

- **Multi-Core Processing:** Utilizes a process pool executor to saturate CPU cores for lightning-fast batch conversions.
- **Crash-Safe Resume Logic:** Automatically checks existing CSV manifests upon startup, skips already processed tracks, and picks up right where it left off.
- **Live Disk Flushing:** Writes database records to disk immediately as individual tracks finish to prevent data loss during interruptions.
- **Smart Deduplication:** Filters duplicate tracks dynamically based on directory depth.
- **Embedded Cover Art Optimization:** Automatically maps, re-encodes (as MJPEG), and scales cover art to precise dimensions.

## Requirements

- Python 3.8+
- `ffmpeg` installed and accessible in your system path.

---

## Detailed Command-Line Options

| Flag | Long Flag | Description | Choices / Default |
| :--- | :--- | :--- | :--- |
| `-i` | `--input` | Input root directory or a specific single audio file to process. | *Required* |
| `-o` | `--output` | Target root directory where processed files will be saved. | *Required* |
| `-b` | `--bitrate` | Target audio bitrate for the output MP3 files. | `128k`, `192k`, `256k`, `320k` <br>*(Default: `128k`)* |
| | `--cover` | Flag to include, re-encode, and scale embedded album cover art. | Flag (Default: `False`) |
| | `--cover-size`| Target square pixel resolution for the scaled cover art. | Integer <br>*(Default: `500`)* |
| | `--flat` | Flatten all discovered files into a single output folder, ignoring subdirectories. | Flag (Default: `False`) |
| | `--csv` | Custom file path to save or resume the output CSV database manifest. | Path <br>*(Default: `audio_manifest.csv`)* |
| `-w` | `--workers` | Number of concurrent CPU worker processes to spin up. | Integer <br>*(Default: `3`)* |

---

## Usage Examples

### 1. Standard Multi-Core Run (Recommended)
Processes a large music directory using 3 concurrent CPU cores, compresses to 128 kbps, and resizes cover art to 500x500 pixels.

```bash
python scanner.py -i "/media/robumf/SGmedia/00MusicMain/Ponies at Dawn 320k" -o "/home/music128/Ponies at Dawn" -b 128k --cover --cover-size 500 -w 3
```bash
python scanner.py -i "/media/robumf/SGmedia/00MusicMain/Ponies at Dawn 320k" -o "/home/music128/Ponies at Dawn" -b 128k --cover --cover-size 500 -w 3
