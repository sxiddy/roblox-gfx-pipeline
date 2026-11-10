---
name: animation-pipeline-lessons
description: "Technical lessons from the Suhaa Cortis concert animation (headless Blender, Roblox exports, choreo tracking, catalog/user APIs)"
metadata:
  node_type: memory
  type: project
  originSessionId: 418ab616-8563-42d3-a196-c609d5db19aa
  modified: 2026-10-26T19:09:31.328Z
---

Lessons from the 2026-10-26/27 Suhaa concert animation (`tools/anim_concert2.py`, `tools/member_avatar.py`, `tools/track_one.py`, `tools/choreo_from_track.py`, `tools/cache_avatar.py`, `tools/user_sheet.py`):

**Owner preferences**
- Extra characters = normal cool real Roblox avatars of the asked vibe/gender. Never likeness replicas, never hand-built mannequins (see [[stage-avatars-normal]]).
- Story beats must read literally: "comes out of the dark" = invisible (hide_render keyed) until lights are down, then lit by a backlight.
- Owner sends quick corrections mid-turn; switch immediately, don't finish the old idea.
- Ask the purpose/vibe before building; one sentence plan, then build.

**Roblox data**
- Logged-in Chrome tab (claude-in-chrome) for avatar-3d / assets-thumbnail-3d / users/search / friends; the CDN JSON and files are public (`fetch_avatar3d.py`, host = t{xor hash %8}).
- javascript_tool output truncates ~1000 chars: store results in `window.X` and read in slices. roblox.com CSP blocks POSTing to localhost.
- Finding styled avatars: username search is mostly default avatars; friends lists of a good avatar (friends.roblox.com/v1/users/{id}/friends) give similar-style avatars. Contact-sheet with `tools/user_sheet.py ids out.jpg cols`.
- `cache_avatar.py` fails the rig assertion on ~1 in 3 exports: pick 1-2 backups.
- Clothing assets' 3D thumbnails are an R6 dummy facing -Y with the grey body colour (229,228,223) baked opaque; classic face assets have no 3D thumbnail (use the 2D thumbnail png).
- Hair/accessory exports are in studs: scale by head_width/1.2, never "fit to head width".

**Blender (5.2 headless, `-b --factory-startup`)**
- Hidden objects keep stale bound_box: read bounds from mesh vertices or before hiding.
- ClassicMannequin.fbx parts carry FBX animation + parent inverse: `animation_data_clear()` and reset before parenting.
- Data Transfer UV writes to a new layer unless dst layers are removed first.
- Big bash heredocs with Windows paths/nested quotes break: write scripts with the Write tool into the scratchpad and run them.
- Run builds in the background; renders of 285 frames take long, check usage first.

**Choreo**
- MediaPipe heavy single-dancer tracking with a moving crop (`track_one.py`) worked; multi-person failed. Smooth sigma 1.2, resample to 24 fps.
- Avatar space everywhere: +X right, +Y forward, +Z up; dancers rotated pi to face the crowd.

## Concert v3 lessons (2026-10-27) — full list in roblox-gfx-ideas SKILL.md mistake log
- Dance = designed key poses on the measured beat grid, overlap via per-bone key offsets, continuous roll + quaternion sign match, ≤12°/frame speed cap, motion check script before renders (tools/anim_concert3.py `check`).
- Story needs 20-25 s; hero entrance ~10 s; hero walk 80-95 steps/min.
- Crowd camera 6-12 m back, ~4 m high, 50-85 mm. Motion blur on. Owner's smoothness bar: Ink Game Roblox animation (youtu.be/hCnsaahr2cc).
- Useful installed skills: blender-motion-state-inspection, blender-lighting, blender-materials (via `skills` CLI, vercel-labs).
