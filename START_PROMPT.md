# Roblox GFX and animation in Blender: start here

You make Roblox avatar GFX (and animations) in my Blender for any username I give you. This folder,
`C:\Users\Siddharth D\Projects\gfx and animation roblox blender`, is the whole project. It was moved out of
drive-reel-mcp, so any old path with `drive-reel-mcp\bio_avatar_assets` now means this folder.

**Next job: username DI3STINY.** There is no reference picture, so use the `roblox-gfx-ideas` skill: read the avatar
(already fetched in `avatars/DI3STINY/`), pitch 3-4 GFX concepts that suit it, wait for me to pick one, then build it.

## Read first

- **`gfx_mistake_log.md` and `docs/GFX_MASTER_PIPELINE.md` first, in full, every session.** Append new mistakes to the log.
- Skills: `roblox-gfx-ideas` (no reference: pitch concepts, then build), `roblox-gfx-match` (I sent a reference:
  recreate it; section 5 is the never-again checklist), and the Blender skills: `blender-shader-nodes`,
  `blender-compositing-nodes`, `blender-scene-rendering`, `blender-animation-rigging`, `blender-polyhaven-*`,
  `blender-slow-zoom`, `blender-turntable`, `blender-crane-shot`, `blender-dolly-rotate`, `blender-perfect-loop`.
- `gfx_references/PLAN.md`: the style playbook, measuring workflow, scoring rubric and tools.
- Tools in `tools/`:
  - `gfx_kit.py`: 12 pose presets, frame_head, selfie_camera, props, 12 light presets, render_mask, and
    `skin_clothes()`.
  - `gfx2d.py`: grid, compare, grade and post.
  - `build_exact_gfx.py`: auto-rigs any R15 avatar and skins its layered clothing.
  - `fetch_avatar3d.py`
  - `style_garage_v6.py`: the latest worked example.
- Blender 5.2 runs a socket on 127.0.0.1:9876 (null-byte JSON, `{"type":"execute","code":..,"strict_json":false}`).
- My references go in `gfx_references/` (named by username); outputs go to `gfx_output/<username>/`.

## My rules (I've said all of these before; don't make me repeat them)

### Usage
- **Never go over the limit, at any cost.** Run `get_usage` before every step and every render. Never pass 98% of the
  5-hour or the weekly limit unless I explicitly allow more. If you're near it, stop and tell me what's left.
- Don't waste my tokens: no trial-and-error loops. Plan first, then build once and fine-tune with `gfx2d.py compare`
  (read report.txt before viewing images; it's cheaper).
- Talk tersely. Answer first, no fluff.

### Asking vs doing
- **"can u do X?" is a QUESTION.** Answer it and wait for "go". I once said "i said can u do it, i didnt ask u to
  start rn".
- Commit, PDF and ultracode only when I ask. Get my OK on an idea before spawning review or build subagents.
- **Rate it yourself.** Compare against the reference (or the concept) part by part out of 10, harshly. I rate 2-3
  points lower than your first instinct (I gave 3/10 and 4/10 where you thought 7). Never ask me for a score
  ("u compare it with my reference and u rate it yourself").
- Don't call it done, fixed or passing without real evidence: render it, look at it, compare it.

### Watching live
- I want to **watch in my Blender**: maximised, the normal **Layout** workspace (not a single fullscreen area), the
  viewport in **camera view** (Material Preview), not stuck in Local view. Use `gfx_kit.show_camera()`, `label()` and
  `play_steps()`.
- Never cache Blender area objects across timer ticks (it crashed Blender). Look areas up fresh every time.
- **Never save over my open .blend.** Save copies.

### Pose: plan it exactly first
- "whenever i ask u to do a gfx make a plan on the pose exactly then start instead of wasting my tokens."
  Before any Blender call, write down:
  - the camera type (selfie, tripod or mirror), its position, lens and roll;
  - every body part's direction: torso lean, head tilt/turn/roll, upper arm, forearm and hand, legs;
  - what touches each frame edge and what is cut off;
  - which tool you'll use.
- **The pose doesn't have to copy the reference.** Pose it to suit the avatar (chibi, classic or tall body), and keep
  the reference's camera, set, lighting and grade.
- Chibi bodies have no forearm mesh. Layered clothing (sleeves, skirts) must be skinned to the bones
  (`skin_clothes()`), or "some of her body parts are missing" and hands float. Check the whole body in every preview:
  no missing limbs, no floating hands, no sleeve covering the face.
- Hands follow the forearm unless the reference bends the wrist. Block hands can't make finger poses: say so.

### Camera and zoom (where I complained most)
- "lighting, pose, everything is still off, the camera too, and im legit able to see the hand which means u havent
  zoomed enough." **Anything out of frame in the reference must be out of frame in yours.** Crop tighter.
- Work out the camera height, distance, angle and tilt **from the reference's perspective** (floor lines, wall lines,
  head size), never by guessing. Assert them in code (e.g. elevation 38-62°). A 2D-only search once left the camera
  side-on, looking from below, inside the head, or showing the back of the head.
- "Selfie" is only a clue. Classify the shot from 3+ clues. In a real selfie the near shoulder or sleeve fills a
  corner and the arm leaves the frame edge.
- Make the subject fill the frame like the reference: measure head size and position as fractions of the frame and
  match them.

### Look and quality ("what u made rn is basic and not hard at all")
- References are **gritty, not clean and bright**:
  - real PBR textures at real scale, with dirt, wear, cracks, stains and joints;
  - haze or volumetrics, dark edge falloff, grain, deep blacks;
  - start darker than you think.
- **Every prop in the reference must exist** and sit in the same part of the frame (boxes, posts, braces, fences,
  lights, wall corners). List them and tick them off.
- **Lighting:** match the light ratio, where the brightest spot is, and how dark the shadows get. Moody means one soft
  source and low ambient, not a flat overcast fill. Light to suit the avatar's colours.
- **Colour grade with the avatar mask** (`gfx2d.py grade --mask`) and keep the character's colours close. Match tint,
  saturation, contrast, black and white points, vignette and grain.
- Watch out for:
  - procedural streaks that read as wood planks (use real concrete or plaster textures in object space);
  - fence moiré;
  - stray untextured meshes (run `clean_stray()`).
- If the avatar differs from the reference (hair, outfit), flag it in one line at the start. Don't change the avatar;
  fix everything else.

### Workflow order (from the Opus review)
1. **Camera solve and assert:** elevation, azimuth, pitch, roll, lens, distance.
2. **Pose,** with the head described by its angle to the camera.
3. **Layout:** raycast props onto the floor at their positions in the frame.
4. **Clay lighting preview:** match the luminance map.
5. **Materials:** real scale, dirt layer.
6. **Masked grade.**
7. **Post:** bloom, dust, sparkles, text.

Then a 10×10 frame-map check, a scene check before each render, and score = lowest part + 1. Anything under 7 gets
another round, or I'm told honestly what's unfinished.

### Delivering
- Render at 100% in Cycles on the GPU (RTX 4050, OptiX).
- Save the PNG and a .blend copy, and send me the image plus a side-by-side.
- Give the per-part rating: camera, pose, background/props, lighting, grade.
- Don't send a first draft as final; usually 3-5 rounds.

## History, so you know where things stand

- **sttvr_l1ght garage selfie** (`gfx_references/sttvr_l1ght_garage.png`):
  - v1: I rated it 3/10.
  - v3: 5.5. v4: 6. v5: ~5 (missing limbs).
  - v6: ~6/10, with a hand-on-cheek chibi pose, the selfie arm out to the left and a grey concrete wall.
  - Still weak: empty floor in the bottom third, and the wall a bit warm and flat.
- **ImmortalNico moody night GFX:** 6.5/10. Seven items are still pending:
  1. a darker, padded, stitched armrest;
  2. a natural crossed-arms hunched pose with the head resting;
  3. a soft moon glow;
  4. soft star twinkles and sparkles;
  5. a cold blue grade with deep blacks;
  6. a moon rim light on the hat and hair;
  7. a tighter camera with stronger blur.
- **Tools still to build** (Opus ranking):
  1. spec.json + solve_camera;
  2. camera_assert;
  3. frame-map checker;
  4. pose/view assert;
  5. clay luminance gate;
  6. place_at_frame;
  7. scene lint;
  8. grade auto-tuner;
  9. richer compare.

  Ask me before building them.
