# searchurl

A resilient, automated Python tool that uses `yt-dlp` to query YouTube for track metadata and populate missing video URLs directly into an SQLite audio database.

## Key Features

* **Smart Query Construction:** Combines `artist` or `album_artist` metadata with the track filename, automatically preventing duplicate artist names if already present in the title.
* **Fallback Search Handling:** Uses `ytsearch3:` to skip dead, deleted, or blocked top results and retrieve the first accessible valid video link.
* **Timeout & Stall Protection:** Enforces a strict 20-second timeout per search query to prevent stalled network requests from freezing the queue.
* **Incremental Commits:** Commits updates to SQLite after every successful match, ensuring no progress is lost if the script is interrupted.
* **Ad-Free API Querying:** Fetches direct metadata endpoints using `yt-dlp`, bypassing browser players and video ads completely.

## Requirements

* Python 3.10+
* `yt-dlp` (`pip install yt-dlp`)
* SQLite3

## Database Schema Expectation

The script targets a table named `tracks` containing at least the following columns:

| Column | Description |
| :--- | :--- |
| `original_path` | Full local path to the audio file |
| `artist` | Track artist name |
| `album_artist` | Album artist name (fallback) |
| `youtube_url` | Target field to populate (`NULL` or empty initially) |

##Usage Examples

python3 searchurl.py

python3 searchurl.py --db /path/to/your/audio_database.db
