---
name: roblox-gfx-pipeline
description: "Roblox avatar GFX work in Blender () — pipeline, owner ratings, pending tuning list"
metadata:
  node_type: memory
  type: project
  originSessionId: f118cdcd-3565-4626-8b4f-e93fe0021dcb
  modified: 2026-10-25T22:08:22.422Z
---

Owner is making Roblox avatar GFX in Blender (5.2, MCP socket on 127.0.0.1:9876) from exact avatar-3d exports fetched through their logged-in Chrome. Untracked folder `C:SERSSIDDHARTH DPROJECTSGFX AND ANIMATION ROBLOX BLENDER` (MOVED OUT OF DRIVE-REEL-MCP ON 2026-10-26) holds tools: fetch_avatar3d.py, build_exact_gfx.py (auto-rig any R15), style_sunburst.py, style_moody.py.

Ratings (2026-10-25): sttvr_l1ght garage selfie = 3/10 (too clean/bright, loose framing, missing props, avatar didn't match the reference; lessons now in the roblox-gfx-match skill). ImmortalNico moody night GFX = 6.5/10. Owner said ALL 7 tuning items matter: armrest (darker, padded, stitched), pose (natural crossed arms, hands visible, hunched, head resting), moon glow (no hard edge, bloom), stars (soft twinkles + sparkles near hair), colour grade (cold blue, deep blacks), moon rim light on hat/hair, tighter camera + stronger blur.

Garage follow-up feedback (2026-10-25): "lighting, pose, everything is still off, the camera too, and im legit able to see the hand which means u havent zoomed enough". Rules: anything out of frame in the reference must be out of frame in the render (crop tighter); derive camera height/distance/angle/tilt from the reference's perspective, never guess; match pose limb by limb plus head tilt; dim one-source lighting. Pending: redo sttvr_l1ght garage selfie with these after the weekly reset.

Poly Haven/fonts library finished 2026-10-25: 102 assets, 941 MB in `library/`.

Garage v3 (2026-10-25) self-rated 5.5/10. Owner now posts references in `gfx_references/` (named by username); outputs go to `gfx_output/<username>/`. The 10/10 plan is written at `gfx_references/PLAN.md` (style playbook, measuring workflow, rubric) and linked from the skill. Tools built and tested 2026-10-26: `tools/gfx2d.py` (grid/compare/grade/post) and `tools/gfx_kit.py` (12 poses, frame_head, selfie_camera, props, 12 light presets, render_mask). References saved: `gfx_references/sttvr_l1ght_garage.png`, `ImmortalNico_moody.png`. Garage v4 (2026-10-26) self-rated 6/10: `gfx_output/sttvr_l1ght/sttvr_l1ght_GFX_garage_v4.png`, built with `tools/style_garage_v4.py` (stage_set, stage_selfie, stage_light, stage_final). Remaining: Yamaha boxes out of frame, top too dark (the reference has a bright concrete wall), face looks up where the reference's head dips with eyes under the hair, flatter floor detail. Measured garage ref: warmer (b +12), more saturated, strong vignette, head fills ~0.1–0.85 of width, steep ~25° roll, near arm fills bottom-left.

Garage v5 (2026-10-26) self-rated ~5/10 (`style_garage_v5.py`, Opus review rules now in skill section 5): wall reads as wood streaks, body small, near arm a white block at left edge, far hand floats, fence moire. Next: avatar-suited pose round.

**Why:** these were deferred because weekly usage hit 96%; owner said never exceed the limit.
**How to apply:** after the weekly reset, do all 7 on ImmortalNico_moody.blend / style_moody.py, check usage between renders, and ask for a new score rather than self-rating. See [[usage-cap]], [[owner-rates-lower]].

DI3STINY rainy bus stop DONE 2026-10-26: owner said "it's good, we're done" at v3 (self-rated 7/10), `gfx_output/DI3STINY/busstop_v3.png`, script `tools/style_busstop.py`, Blender client `tools/bl.py`. Lessons are logged in the PLAN.md "Mistakes log"; owner wants every new mistake appended there.

Moved 2026-10-26: everything (tools, library, avatars, gfx_references, gfx_output) now lives in `C:\Users\Siddharth D\Projects\gfx and animation roblox blender`, its own project. Garage v6 self-rated ~6/10 (`tools/style_garage_v6.py`). The roblox-gfx-ideas skill pitches concepts when there is no reference. Next username: DI3STINY (avatar already fetched in `avatars/DI3STINY/`).
