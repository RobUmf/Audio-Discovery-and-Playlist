# Interactive YouTube URL Search Tool (`interactive_searchurl.py`)

An interactive, single-track review script designed to handle unmapped audio tracks in your SQLite database. It runs tiered search queries through `yt-dlp`, computes title similarity scores, and gives you direct control to accept, try next query variants, manually paste URLs, or skip.

## Features
* **Multi-Tier Query Fallbacks:** Automatically attempts multiple search variants per track:
  * `Artist - Title`
  * `Artist - Title - Topic`
  * `Title feat. Artist`
  * `Album Title`
  * Cleaned punctuation & stripped feature tags
* **Similarity Confidence Scoring:** Uses `difflib.SequenceMatcher` to measure the percentage match between local metadata and the returned YouTube video title.
* **Flexible Interactive Controls:**
  * `[y]` Accept result & save to database
  * `[m]` Manually enter/paste a custom YouTube URL
  * `[t]` Reject current result and try the next query tier
  * `[s]` Skip current track for later review
  * `[q]` Safely quit the session at any time
* **Database Auto-Schema Detection:** Detects `id`/`rowid` and `album`/`grouping` columns dynamically.

## Usage Example

Run the script directly from your terminal:
```bash
python3 interactive_searchurl.py
