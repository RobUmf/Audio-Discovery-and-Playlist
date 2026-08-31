# searchurl

> High-speed parallel YouTube URL resolver and SQLite database populator using `yt-dlp`.

A resilient, multi-threaded Python utility designed to query YouTube metadata and populate missing `youtube_url` fields directly into an SQLite audio database.

## Features

* **Multi-Threaded Concurrency:** Uses Python's `ThreadPoolExecutor` (`-w`) to execute parallel network searches, drastically reducing total execution time.
* **Smart Core Scaling:** Automatically defaults worker threads to `CPU Cores - 1` to maintain system responsiveness during heavy processing.
* **Flat Extraction (`--flat-playlist`):** Queries search result endpoints directly without loading full webpage resources or playing video streams.
* **Fallbacks & Deduplication:** Prefers `artist` metadata, falls back to `album_artist`, and automatically deduplicates artist names if present in the track title.
* **Multi-Result Failover:** Searches up to 3 results (`ytsearch3:`) to bypass dead, region-locked, or deleted videos.
* **Thread-Safe SQLite Commits:** Keeps database operations isolated to the main thread while worker threads fetch network data concurrently.
* **Configurable Timeout Safety:** Enforces strict per-track timeouts (`-t`) to prevent stalled connections from halting the batch.
* **Timestamped Logging:** Standardized ISO timestamp logging (`[YYYY-MM-DD HH:MM:SS]`) with completion counters.

## Command-Line Options

| Flag | Option | Default | Description |
| :--- | :--- | :--- | :--- |
| `-c` | `--config` | `config.json` | Path to JSON configuration file |
| | `--db` | `audio_database.db` | Path to target SQLite database |
| `-w` | `--workers` | `CPU cores - 1` | Number of concurrent search threads |
| `-t` | `--timeout` | `20` | Maximum time allowed (seconds) per search request |

## Usage Examples

**Default Parallel Run (Auto Cores - 1, 20s Timeout):**

python3 searchurl.py

Custom Timeout & Worker Count:


python3 searchurl.py -w 4 -t 25 

Custom Database Target:


python3 searchurl.py --db /storage/2013-1E1B/audio-repo/SQLite/audio_database.db 
