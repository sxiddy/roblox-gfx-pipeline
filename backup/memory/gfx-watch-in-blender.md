---
name: gfx-watch-in-blender
description: Owner wants to watch GFX work live in their open Blender; keep viewport in camera view
metadata:
  node_type: memory
  type: feedback
  originSessionId: f118cdcd-3565-4626-8b4f-e93fe0021dcb
  modified: 2026-10-25T20:36:48.973Z
---

The owner wants to see GFX work happening in their own Blender window ("open blender and do it in front of me so I see what ur doing", 2026-10-26).

**Why:** my socket scripts ran invisibly; they only saw final PNGs.
**How to apply:** at the start of GFX work, maximise the Blender window and bring it to the front, switch to the normal **Layout** workspace (they want the default editing layout, not a single fullscreen area or the Animation tab), set every 3D view to camera perspective with Material Preview, and label steps with `area.header_text_set`. For multi-step demos, use `gfx_kit.play_steps()` so changes appear one by one. Never cache area objects across timer ticks: on 2026-10-26 a cached area was freed after a workspace switch, and `header_text_set` on it crashed Blender (EXCEPTION_ACCESS_VIOLATION in ED_area_status_text). `gfx_kit.label()` looks the areas up fresh on every call. Related: [[roblox-gfx-pipeline]].
