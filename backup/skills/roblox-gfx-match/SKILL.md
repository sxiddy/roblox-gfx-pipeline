---
name: roblox-gfx-match
description: Recreate a Roblox GFX from a reference image for any Roblox username, in Blender. Use whenever the owner sends a reference picture (and usually a username) and asks for a GFX, render, edit or "make it like this".
---

**Step 0 (every time):** read `C:/Users/Siddharth D/Projects/gfx and animation roblox blender/gfx_mistake_log.md` and `docs/GFX_MASTER_PIPELINE.md` in full before planning anything, and append each new mistake to gfx_mistake_log.md.


# Recreate a reference GFX

The owner sends a new style almost every time and will not explain how. Work out everything from the
reference yourself. Never ask "how should the pose/lighting look". Ask only for the username if it is missing.

Tools live in `C:\Users\Siddharth D\Projects\gfx and animation roblox blender\tools\`:
- `fetch_avatar3d.py meta.json out_dir`: exact avatar export. Get `meta.json` with the logged-in Chrome tab:
  POST users.roblox.com/v1/usernames/users -> id -> thumbnails.roblox.com/v1/users/avatar-3d?userId=id
  (credentials include, poll until Completed) -> fetch imageUrl JSON. Save under `avatars/<Username>/`.
- `build_exact_gfx.py`: auto-rigs any R15 export (prepend `AVATAR_DIR = "..."` and `POSE = "idle"`).
  Armature object `Avatar`, bones LowerTorso, UpperTorso, Head, UpperArm/LowerArm/Hand/UpperLeg/LowerLeg/Foot `.P`/`.N`
  (P = avatar's right, +X; avatar faces +Y). R6 avatars are not supported yet.
- `style_sunburst.py`, `style_moody.py`: worked examples of a style script (pose via `aim()`, props, sky, lights, camera, Cycles).
- Library: `library/` (Poly Haven HDRIs, models, textures, fonts), `hdri/`, `rigs_official/`, `rigs_community/`.
- Blender is driven through the socket client `bl.py` (null-byte JSON, `{"type":"execute","code":..,"strict_json":false}` on 127.0.0.1:9876).

References arrive in `gfx_references/` (file named by username); write outputs to
`gfx_output/<username>/`. **Read `gfx_references/PLAN.md` first**: it has the style playbook, the measuring workflow,
the scoring rubric and the tools: `tools/gfx2d.py` (grid, compare, grade, post) and `tools/gfx_kit.py` (poses,
reference camera, frame_head, selfie_camera, props, light presets, render_mask). Each round: run `gfx2d.py compare`
and read report.txt before viewing images, since it costs fewer tokens.
While working, keep the owner's Blender viewport in camera view (Material Preview) so they can watch. Never save
over their open .blend; save copies.

## 0. Pose plan first (owner's rule: don't burn tokens on trial-and-error posing)

Before any Blender call, decide and write down:
1. **Camera type.** Selfie (the lens is at the phone hand, and the near shoulder or sleeve fills a corner while
   the arm leaves the frame edge), tripod or third person, or mirror.
2. **Camera position relative to the body.** Which side, how high above the head, distance (head width ÷ frame
   width), lens and roll.
3. **Every body part's direction.** Torso lean, head tilt, roll and turn, each arm segment, legs.
4. **What touches each frame edge, and what is cut off.**
5. **Which tool to use.** `gfx_kit.apply_pose` presets, `frame_head`, or `style_garage_v4.stage_selfie` (a search
   over arm direction, lens offset, roll and head roll against measured targets).

Clues: a big body part near a corner plus a distorted wide lens means a selfie. A level horizon with the whole body
in frame means a tripod.

## 1. Write a spec before touching Blender

Study the reference and write these down in a few lines each:
- **Camera**: shot size (close-up / waist / full), aspect ratio, camera height and angle (low, eye, high, dutch tilt),
  lens feel (wide 24-35, normal 50, tele 85+), where the face sits in frame, depth-of-field strength.
- **Pose**: per body part. Torso lean and twist, head tilt and turn, each arm (upper, fore, hand), legs, weight shift,
  contact with props. Note what is hidden by the frame.
- **Background**: what it is (sky, room, sunburst, abstract, solid), colours, depth layers, elements (moon, stars,
  particles, text), how blurred.
- **Lighting**: key direction, colour and hardness; rim lights (side, colour); fill level; practical lights; shadow darkness.
- **Colour grade**: palette, saturation, contrast, black level, tint, bloom or glow, grain, vignette.
- **Props and effects**: furniture, items, overlays, sparkles, text.
- **Not replicable**: hand-painted art, finger poses on block hands, expressions the avatar's face doesn't have,
  hair shape (the avatar's own hair is used). Say these up front in one line.

## 2. Build

1. Fetch and rig the avatar.
2. Copy the closest example style script to `tools/style_<short-name>.py` and change it to match the spec:
   camera first, then pose, props, background, lights, grade. Use library assets for props and HDRIs.
3. Keep hands in line with forearms unless the reference bends the wrist, so nothing looks detached.

## 3. Compare and fix

- Render a 50% preview and put it next to the reference. List every difference under the spec headings,
  biggest first, then fix them. Repeat. Camera and pose mismatches matter most, then lighting, then grade.
- Check usage (`get_usage`) before each render round. Never let the weekly or 5-hour limit go past 98%: stop and
  tell the owner what is left instead.
- Usually 3-5 rounds. Do not send a first draft as final.

## Lessons from low scores (read every time)

Garage selfie for sttvr_l1ght scored 3/10. What was missing compared with the reference:
- **Avatar mismatch not flagged first.** The reference showed white/red hair and a red jacket; the user's current avatar
  was black goth. Compare the fetched avatar with the reference before building and tell the owner in one line if
  hair, outfit or body type differ, because that alone sinks similarity.
- **Too clean and too bright.** References are gritty: stained, cracked concrete, worn paint, dirt, haze or fog in the
  air, dark falloff toward the frame edges, film grain, deep blacks. Use real PBR textures from `library/textures`,
  volumetric haze (world or a box with Volume Scatter), a vignette and grain in the compositor. Start darker than you think.
- **Composition too loose.** The subject must fill the frame like the reference: measure where the head, eyes and
  frame edges sit in the reference (fractions of width/height) and match them in the preview. Wide-lens selfies sit
  very close (head ~45-60% of frame width) with the near arm or sleeve filling a corner.
- **Missing props and set dressing.** Every visible object in the reference (boxes, posts, braces, wall corners,
  ceilings, small lights) must exist and sit in the same part of the frame. List them in the spec and tick them off.
- **Lighting too flat.** Match the reference's light ratio: where the brightest spot is, how dark the shadows get, and
  how quickly light falls off. Dim, moody references need low ambient and one soft source, not big overcast fills.
- **Zoom, camera and pose (owner's follow-up).** If something is out of frame in the reference (e.g. the selfie
  hand), it must be out of frame in the render too. Seeing the hand meant the camera was too far. Crop tighter until
  only what the reference shows is visible. Match the camera's height, distance, angle and tilt from the reference's
  perspective (how much floor shows, how big the head is, where the horizon or wall line runs), not from a guess.
  Match the pose by checking each limb's direction and the head tilt in the preview against the reference, part by part.
- **Stray stage objects.** A leftover untextured `Plane` from the base stage sat on the floor and washed it white
  for two renders. Before the first preview, list visible unparented meshes and delete anything without a material.
- **Selfie camera.** Put the lens near the phone hand and search offsets with `world_to_camera_view`: wrist out of
  frame, elbow in frame. See `style_garage_selfie.py`.
- **Too few rounds.** Score each spec heading out of 10 against the reference before sending. Anything under 7 gets
  another round, or, if the budget runs out, is named honestly as unfinished. Spend the first rounds on composition and
  grade, since they change the whole look.

## 4. Deliver

Render 100% with Cycles on GPU (RTX 4050, OptiX), save the PNG and a `.blend` copy in ``, send the
image, then rate it yourself against the reference, part by part out of 10, harshly (the owner rates 2-3 points lower
than first instinct). Do not ask the owner to score it; they want the self-comparison.

## 5. Never-again checklist (from the Opus review of garage v5)

Turn the spec into numbers and gate each stage before moving on:
1. **Camera first, asserted.** Solve elevation, azimuth, pitch, roll, lens and distance from the reference (floor lines,
   wall lines, head size) and assert them in code (for example elevation 38-62°). A 2D-target search alone ended up
   side-on (el 9°, az 87°). "Selfie" is only a clue; classify the shot from 3+ clues.
2. **Head by its angle to the camera** (face-to-lens angle, dip, turn, roll), not by bone directions. Check the face
   is visible in the preview.
3. **10×10 frame map.** For each cell, write what the reference shows (head, shoulder, arm, floor, prop, wall) and check
   the render against it. Every body part that touches an edge in the reference must touch the same edge.
4. **Fixed order:** camera → pose → layout (raycast props onto the floor at their frame positions) → clay light
   (Workbench/clay preview, match the luminance map) → materials → grade → post.
5. **Materials at real scale** with a dirt/wear layer; check fine detail (Laplacian) against the reference. Procedural
   streaks read as wood; use real textures for concrete walls.
6. **Grade with the avatar mask** and keep the character's colours close (ΔE gate).
7. **Scene lint** before each render: stray meshes, missing materials, floating hands, moiré on fine meshes (fences).
8. **Score = the lowest part's score + 1.** Anything under 7 gets another round.
9. **Owner rule (2026-10-26):** the pose does not have to copy the reference. Pick a pose that suits the avatar
   (proportions, outfit, vibe) while keeping the reference's camera, set, lighting and grade.

## Quality baseline for every GFX (owner, 2026-11-16: alley v2 "is FIRE, every gfx must build in the same quality")

The approved bar is `gfx_output/Bio_IsHere/alley_v2_final.png`. Its script `tools/alley_v2.py` is the worked example: copy its structure for every new GFX, do not start from the older `style_*.py` files. Look at the approved image before building and put the new final next to it before presenting; if the new one is weaker on any part, do another round.

Every GFX must do all of these, in this order:
1. One script with `build`, `render`, `passes` and `gate` modes, run in your own headless Blender. The exact pose, camera, frame-edge, set and light plan goes in the docstring before any Blender call.
2. Before listing set pieces, work out what the frame can show: body width in head-widths, and the bottom ray angle of the camera. Build only what is in view.
3. Camera solved with `frame_head` and asserted; character large in frame (head about 25-30% of the width); low or otherwise chosen angle, 40 mm class lens, f/2.8.
4. Block hands hidden by pose or framing, solved by counting visible hand vertices with ray casts. Anything crossing the face (aura, props, rain) is hidden or moved, and its size reported.
5. Every prop placed from its frame position (ray from the camera onto a wall or floor plane), never by guessed world coordinates.
6. Light: one warm key, one coloured rim as a narrow beam (spread about 50), fill near 4 W, no world haze, background lit by its own practicals. Dark hair stays dark (multiply the hair texture, lower the rim). No words anywhere; check neon shapes for accidental letters.
7. `job.json` + `tools/gate.py` stages scene, body, face, frame, camera, light before any render; all must pass.
8. One or two 50% previews at 64 samples, fix only what is broken, then Cycles OptiX 256 samples at 100%.
9. Passes (mask, hair, emission, depth, normal), then `tools/finish.py finish`; read its per-layer change numbers and raise strengths until each layer is visible but subtle. Gentle grade, grain 0.006.
10. `gate.py final`, then send the final plus a side-by-side, with a harsh per-part self-rating and a list of what differs from the plan and what was not verified.

Known weak parts to push further each time (alley v2 scored these lowest): set density and depth, body acting (no stiff plank poses), and a face expression from `tools/face_rig.py` instead of the neutral default.
