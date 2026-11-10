---
name: concert-v3-state
description: "Where the Suhaa concert v3 (32 s REDRED) job stands, and what's left to do. Read this first if the session was compacted mid-job."
metadata:
  node_type: memory
  type: project
  originSessionId: 167bb8f1-68cf-4456-a1c8-d7f08c3c4b99
  modified: 2026-10-26T23:16:30.126Z
---

Suhaa concert v3 as of 2026-10-27 (owner approved the 32 s plan).

- **Script:** `tools/anim_concert3.py` (`build`, `check` = jitter + match gates, `stills`, `frames a b pct subdir`). Output in `gfx_output/anim_concert2/`.
- **Audio:** `audio_v3.mp3` = REDRED Performance Film audio 23.97-55.97 s (32.0 s, 1 s fade). END = 768 frames.
- **Song mapping (verified by audio + frame check):** owner clip `Downloads/lv_0_20261027003944.mp4` = practice Fix ver (kuVNutQeBBA) 0:40.0-0:51.9 = mirrored practice (u_vusNeo6xI) 0:36.2-0:48.0 = song 35.81-47.70 = video 11.84-23.73. Final hit: mirrored 0:55.3 = video 30.93 (T_HIT2).
- **Story:** dancers 0-2.5, blackout 2.5, silhouette 3-5.5, Suhaa walk 5.5-9.65 (80 spm), hero 10-11.84, chorus part 1 11.84-23.73 (choreo.json), part 2 23.73-30.93 (owner is sending mirrored 0:48-0:56 clip: hflip it, track with track_one.py + choreo_from_track.py, append to choreo), CO2/confetti 30.93, freeze + fade to 32.
- **Gates now PASS:** jitter 0 frames, match 0.974 (arms part1 0.954, part2 0.930). Part 2 = owner screen recording (Videos/Screen Recordings/Screen Recording 2026-10-27 045554.mp4, rec 0 s = song 44.35), hflipped -> ref/part2.mp4, red dancer tracked -> choreo_p2.json, joined by tools/choreo_join.py (skip 0.335 s) -> choreo_full.json, seam window smoothed sigma 4.
- **Full render started** (frames_v3, 768 frames, chained post + copy to Downloads/suhaa_concert.mp4 only if 768 frames exist). After: view a strip of every section, rate harshly, send.
- **Owner OK (2026-10-27): full render + post + copy overnight if both gates pass; no need to wait for test approval.**
- **Left:** track part 2, final freeze pose on the hit, jitter to 0, 3 s test at 50% to the owner, then full render + post (`CONCERT_DIR=anim_concert2 CONCERT_FRAMES=frames_v3 CONCERT_GRADED=graded_v3`), copy to `Downloads/suhaa_concert.mp4`.

Related: [[animation-pipeline-lessons]], [[owner-picks-characters]].
