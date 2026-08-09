# Audio-Discovery-and-Playlist
A different advance way to make playlist.


# Community-Focused Audio Discovery & Playlist Engine

A modular, local-first Python pipeline and playlist generation engine designed to break free from rigid corporate streaming algorithms. This tool empowers independent music archives and fandom communities to curate, explore, and sequence music through data-driven neighborhoods and harmonic rules.

---

## Roadmap & Architecture

### Phase 1: Local Data Ingestion & Feature Extraction (The CSV Engine)
* **Library Scanner:** A lightweight Python script that traverses local compressed audio files or raw archives.
* **Feature Extraction:** Pulls essential structural and numerical audio data for each track:
  * **Rhythm & Dynamics:** BPM, LUFS (loudness), and spectral centroid (brightness).
  * **Harmonic Key:** Detects musical keys for Circle of Fifths mapping.
  * **Custom Tags:** Parses directories, file names, or metadata tags to populate custom fields (e.g., labels and groupings like *A State of Sugar* or *Ponies at Dawn*).
* **Portable CSV Database:** Outputs structured data into a local CSV file acting as a fast, offline database.

### Phase 2: The Multi-Dimensional "Neighborhood" & Math Engine
* **Vector Normalization:** Normalizes numerical audio features (BPM, keys, brightness) onto a shared scale.
* **Similarity Calculation:** Uses Euclidean distance and cosine similarity algorithms against a user-selected seed track to calculate mathematical distances across the catalog.
* **Cluster Selection:** Isolates the closest tracks (e.g., top 50 songs) to form a cohesive, data-driven "neighborhood" sharing a distinct sonic vibe.

### Phase 3: Harmonic Sequencing (The Circle of Fifths & Modes)
* **Circle Mapping:** Programs the 12 major and 12 minor keys into a mathematical matrix representing the continuous loop of the Circle of Fifths.
* **Mode Pivoting Logic:** Builds intelligent sorting rules allowing playlists to step smoothly between adjacent fifths or bridge major and minor modes (relative/parallel keys) for intentional emotional shifts.
* **The 24-Track Full Cycle Option:** An optional generative mode that strings together a complete 24-track arc, executing a full circuit of major and minor keys before returning home.

### Phase 4: User Interaction & Direction Control
* **Seed Input Interface:** CLI or web UI integration allowing users to anchor their discovery journey using any starting track.
* **Direction of Travel Filters:** Customizable parameters to steer playlist creation:
  * *Vibe Density:* Control whether the engine stays tightly bound to the neighborhood cluster or expands its radius.
  * *Harmonic Journey:* Choose between pure energy/tempo grouping or strict Circle of Fifths sorting.
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
