# Audio-Discovery-and-Playlist

**Community-Focused Audio Discovery & Harmonic Playlist Engine**

A modular, local-first Python pipeline and playlist generation engine designed to break free from rigid corporate streaming algorithms. This tool empowers independent music archives, record labels, and fandom communities to index, mathematically profile, and sequence their collections into cohesive sonic neighborhoods and harmonically aligned journeys.

---

## Architecture Overview

The system is built on a distributed, cross-environment workflow that cleanly separates heavy mathematical computing from lightweight portable playback:

* **Central Relational Hub (`audio_database.db`)**: A unified SQLite database storing extracted ID3 metadata alongside deep Digital Signal Processing (DSP) measurements[cite: 1, 2].
* **Desktop Workstation (e.g., EliteDesk)**: Handles heavy CPU-bound tasks, multi-core DSP audio analysis, transient calculations, and batch database enrichment[cite: 2].
* **Mobile / Edge Node (e.g., Android / Termux)**: Manages local file ingestion, lightweight playback, database queries, and relative-path `.m3u` playlist generation[cite: 1].
* **Environment-Aware Configuration (`config.json`)**: Unifies path resolution across desktop and mobile filesystems seamlessly[cite: 1, 2].

---

## Current Implementation Status

### 1. Ingestion & Transcoding Engine (`ingest.py`)
* **Multi-Threaded Conversion**: Converts diverse raw archives (`.flac`, `.wav`, `.m4a`, etc.) down to optimized 128 kbps MP3s using parallel FFmpeg workers[cite: 1].
* **Automated Tag Extraction**: Captures key ID3 tags (artist, album, title, year, track/disc numbers) via `mutagen` during conversion[cite: 1].
* **Database Registration**: Initializes the complete table schema and records baseline audio properties (sample rate, format, duration) into SQLite[cite: 1].
* **Resumable Processing**: Automatically queries existing database records to skip already processed files on subsequent runs[cite: 1].

### 2. Multi-Core DSP Audio Analyzer (`analyzersqlite.py`)
* **Smart Slicing & Memory Optimization**: Combines `pydub` for overall loudness with centered `librosa` audio slicing to minimize RAM overhead on long tracks[cite: 2].
* **Comprehensive Audio Metrics**: Computes and updates deep sonic measurements directly in the database[cite: 2]:
  * **Loudness & Dynamics**: LUFS, RMS dB, Peak dB, and Crest Factor[cite: 2].
  * **Rhythm & Tempo**: Estimated BPM and Rhythm Pulse Clarity[cite: 2].
  * **Harmonic Profile**: Harmonic-to-Percussive Separation (HPSS Harmonic Ratio)[cite: 2].
  * **Spectral Properties**: Spectral Centroid (brightness), Spectral Rolloff, and Spectral Flatness[cite: 2].
  * **Audio Health**: DC offset calculation and digital clipping percentages[cite: 2].
* **Resource Throttling**: Features configurable worker counts, batch chunking, forced garbage collection, and cooldown sleep timers to maintain hardware stability under heavy loads[cite: 2].

### 3. Multi-Dimensional Neighborhood Engine
* **Euclidean Vector Distance**: Computes multi-axis mathematical distance against seed tracks across normalized DSP metrics.
* **ASCII Radar Visualizations**: Generates terminal-based radar charts to inspect and compare acoustic profiles across the catalog.

---

## Roadmap & Planned Enhancements

### Phase 1: Advanced DSP Expansion (Instrument & Vocal Profiling)
* **Fundamental Frequency ($F_0$) Tracking**: Measure median fundamental frequencies (in Hz) to estimate pitch centers and vocal presence.
* **Transient & Attack Envelope Analysis**: Calculate transient attack speeds to characterize percussive punch versus sustained ambient textures.
* **Multi-Band Energy Distribution**: Compute spectral energy splits across Sub, Mid, and High frequency bands to infer dominant instrumentation (e.g., acoustic vs. synth-heavy).

### Phase 2: Harmonic Sequencing & Circle of Fifths
* **24-Key Circle Mapping**: Map detected musical keys to a mathematical matrix representing the continuous Circle of Fifths.
* **Mode Pivoting**: Implement sorting rules that transition smoothly across adjacent fifths or shift between relative and parallel major/minor modes.
* **24-Track Full Cycle**: An optional generative mode that strings together a complete 24-track arc, executing a full circuit of major and minor keys before returning to the tonic.

### Phase 3: Traversal Filters & Playlist Generation
* **Direction of Travel Controls**:
  * **Vibe Density**: Adjust Euclidean search radius to keep playlists tightly bound or expansively varied.
  * **Harmonic Journey**: Toggle between pure energy/tempo matching and strict harmonic key steps.
  * **Grouping Filters**: Constrain generation to specific releases, labels, or community archives[cite: 1].
* **Recursive Portable Playlists**: Output finalized sequences into standardized `.m3u` files using clean relative file paths for universal playback across devices.

### Phase 4: Bi-Directional Synchronization & Data Integrity
* **Safe Database Transport**: Automated SQLite backup and checkpoint workflows prior to synchronization to eliminate database corruption risks.
* **Targeted Rsync Workflows**: Structured push/pull synchronization scripts tailored for transferring databases and media between desktop and mobile nodes.

### Phase 5: Streaming Bridges & Community Integration
* **Broadcast Integration**: Modular export hooks for streaming automation software (such as AzuraCast).
* **Community Sharing**: Open-source presets and custom weighting profiles shared across fandom curation communities.

---

## License & Contributions

Distributed under the open-source MIT License. Pull requests, community feature suggestions, and harmonic curation discussions are welcome!  * *Harmonic Journey:* Choose between pure energy/tempo grouping or strict Circle of Fifths sorting.
  * *Grouping Filters:* Restrict search pools to specific custom collections.
* **Export Options:** Packages final customized selections into downloadable `.m3u` playlists or structured bundles.

### Phase 5: Scaling, Community, & Public Sharing
* **Open Source Repository:** Structured for public collaboration on GitHub.
* **Integration Bridge (Optional):** Modular wrapper support for pushing generated playlists directly into streaming tools like AzuraCast.
* **Community & Support:** Built as an independent hub for fandom music discovery, backed by community involvement and creator-focused support platforms like Patreon.

---

## Getting Started
*(Setup instructions, installation steps, and usage documentation coming soon as code implementation progresses.)*
* discussion are welcome
