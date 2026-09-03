# Audio Similarity Playlist Generator (`like_song.py`)

An interactive command-line tool that builds custom `.m3u` playlists based on audio feature similarity. By querying your SQLite audio database for a seed track, `like_song.py` calculates Euclidean distance across extracted DSP metrics to find and chain acoustically similar tracks.

## Features

* **Multi-Criteria Seed Search:** Find target songs easily by Database ID, Artist/Author, or Track Title.
* **DSP Audio Matching:** Calculates multi-variable similarity across core audio features:
  * `dsp_bpm` (BPM / Tempo)
  * `loudness_lufs` (Loudness level)
  * `spectral_centroid_hz` (Timbre / Brightness)
  * `spectral_rolloff_hz` (High-frequency distribution)
  * `rhythm_pulse_clarity` (Rhythmic sharpness)
  * `hpss_harmonic_ratio` (Harmonic vs. Percussive ratio)
  * `duration_sec` (Track length)
* **Mapped Tracks Filter:** Restricts candidates to tracks with verified YouTube URLs mapped in the database.
* **Strict Session Deduplication:** Tracks are filtered by both Database ID and normalized string fingerprints (`artist - title`) to prevent duplicate entries across extended chaining sessions.
* **Flexible Path Export:** Option to write `.m3u` playlists using either absolute file paths or relative paths grounded to a custom root folder.
* **Seed Chaining:** Allows picking any matched track as the next seed to continuously expand the playlist in new acoustic directions without leaving the active session.

## Usage

Execute the script using Python:

```bash
python3 like_song.py
