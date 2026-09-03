# YouTube URL Search Tool (`searchurl.py`)

An automated Python utility designed to scan your SQLite audio database for tracks lacking YouTube links, construct intelligent search queries using metadata and filenames, and concurrently fetch and populate official video URLs using `yt-dlp`. Features built-in confidence scoring to ensure title accuracy.

## Recommended Search Strategies

**1. Rapid Shotgun Search (Try this one first)**
* **Command:** `python3 searchurl.py -t 2` (Uses default workers: CPU cores - 1)
* **Details:** Highly concurrent with a short 2-second timeout. Requires fast internet and is best run when YouTube server traffic is low. Can be run multiple times to quickly scoop up the easiest/fastest matches.

**2. Slow Search**
* **Command:** `python3 searchurl.py -w 2 -t 20`
* **Details:** Drops down to 2 workers but increases the timeout to 20 seconds. Ideal for catching tracks that need more time to resolve without rate-limiting your connection.

**3. Difficult Search**
* **Command:** `python3 searchurl.py -w 1 -t 20 -m 80`
* **Details:** 1 worker, 20-second timeout, enforcing a strict 80% confidence match between your local tags and the YouTube title. 
* **Follow-up:** Can be run again at a 60% confidence level (`-m 60`) to catch the remaining stubborn tracks that might have slightly different naming conventions on YouTube.

## Command-Line Options

| Option | Flag | Default | Description |
| :--- | :--- | :--- | :--- |
| **Config File** | `-c`, `--config` | `config.json` | Path to an external JSON configuration file. |
| **Database Path** | `--db` | `audio_database.db` | Path to the target SQLite audio database file. |
| **Worker Threads** | `-w`, `--workers` | `CPU cores - 1` | Number of parallel worker threads for concurrent searching. |
| **Search Timeout** | `-t`, `--timeout` | `10` | Timeout threshold in seconds per track query. |
| **Confidence Level** | `-m`, `--min-confidence` | `0.0` | Minimum title similarity percentage (0-100) required to save the URL. |
