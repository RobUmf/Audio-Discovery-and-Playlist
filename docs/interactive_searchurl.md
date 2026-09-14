# Interactive YouTube URL Review Tool (`interactive_searchurl.py`)

An interactive Python utility designed to review unmapped audio tracks one-by-one using multi-tiered search queries, title similarity scoring, and manual URL entry options.

## Features
* **Tiered Query Fallbacks:** Automatically generates search variants including artist/title combinations, "Topic" channels, album titles, cleaned punctuation, and feature tag removal.
* **Similarity Scoring:** Uses `SequenceMatcher` to compute a percentage similarity score between your local track metadata and the returned YouTube video title.
* **Manual Override & Skipping:** Allows manual URL pasting for rare or hard-to-find tracks, or skipping to review later.
* **Clean Session Control:** Built-in `[q]` quit option cleanly closes database connections and saves progress at any point.

## Execution

Run using Python:
```bash
python3 interactive_searchurl.py
