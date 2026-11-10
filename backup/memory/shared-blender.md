---
name: shared-blender
description: The GUI Blender on port 9876 is shared by every session; check for busy peer sessions first, prefer a private headless Blender
metadata:
  type: feedback
---

Several Claude sessions work in this folder at once and they all reach the same GUI Blender over bl.py (port 9876). On 2026-10-26 my Bio_IsHere stage_set wiped the Suhaa session's gamer-corner scene. The owner then said to wait for the other session before using Blender.

**Why:** a scene wipe or avatar rebuild in the shared instance destroys another session's live work, and cross-session warnings can be held and expire undelivered.
**How to apply:** before any bl.py call, run ListAgents; if another gfx session is busy, don't touch port 9876. For renders and animations, run my own headless Blender (`blender -b --factory-startup -P script.py -- args`, saving a scene .blend) as tools/anim_door.py does. See [[watch-in-blender]] and [[usage-cap]].
