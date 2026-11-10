# Superior plan for every GFX and animation in this folder

Written 2026-11-11. Read after `gfx_mistake_log.md`, `docs/GFX_MASTER_PIPELINE.md` and `START_PROMPT.md`.
Those three stay the rule books. This file says what to build on top of them so the work reaches the two bars
the owner named, and so Opus cannot repeat the logged mistakes.

Nothing here is built yet. Section 7 is the build order; each item needs the owner's "go".

## 1. The two quality bars

**Animation bar: "Ink Game - Roblox Animation" by GibbsonTV (youtu.be/hCnsaahr2cc).**
Seen in four frames of the video (thumbnail + three auto stills); the motion itself was not watched, because
this project does not download YouTube video. What the frames show:

| Trait in the reference | What we have today | Gap |
|---|---|---|
| Faces act: brows, eyelids, pupils and mouth change per shot (smirk, grin, glare) | One static face decal | **Biggest gap.** Needs a face rig (section 3). |
| Close and medium shots, head fills 40-60% of frame height, shallow depth of field | Concert used far cameras; log section 10 already says this looked cheap | Shot rules (section 4) |
| Cloth has weave and soft folds, heads have rounded edges with a soft highlight | Flat colour, sharp cubes | Fabric micro-normal + small bevel (already allowed in the pipeline doc) |
| One soft key, a cooler rim, dark set behind, letterbox bars | Done well only in the bus stop job | Light recipe per shot |
| Decals on faces (blood smears) that follow the head | Not built | Second UV decal layer, cheap |
| Smooth motion | Hand-keyed poses, 24 fps, some stiffness | Motion system (section 4) |

**GFX bar: top commissioned Roblox GFX.** Web search on 2026-11-11 returned mostly SEO pages; the points they
and the DevForum agree on are: lighting decides the result, a rim light separates the character, haze catches
light, and the raw render is never the final (it is finished in a 2D pass). From the owner's own references
(graveyard ref2, garage) the bar also includes: character large in frame, an expressive face, real hands or
hidden hands, dense detailed props, foreground blur, lens flares, and a painted finish.

## 2. Why Opus keeps making "stupid mistakes", and the fix

The log has ~200 lessons. Opus reads them, then forgets one mid-job. Reading is not enough.
**Fix: turn the repeatable lessons into code that fails loudly.** One command, `tools/gate.py <stage>`, run in
the headless Blender before every preview and every render. It prints PASS/FAIL lines and exits non-zero on
any FAIL. Opus may not render or present while a gate fails.

| Gate | Checks (each maps to logged mistakes) |
|---|---|
| `scene` | No `Backdrop`/`Halo`; no mesh without a material; no unparented stray mesh; engine set explicitly; right armature name; avatar fetched today (meta.json date) |
| `body` | Every avatar part visible from the camera or listed as "planned hidden"; no floating hand (hand to forearm distance); avatar lowest evaluated vertex within 5 mm of the ground or seat |
| `face` | Render a face-plate mask: at least 70% of the face plate visible from the shot camera, not covered by hair, prop or hand |
| `frame` | Head size and head position within 5% of the spec; every prop's projected box inside its planned frame cell; no prop box crossing the head box; nothing that the spec lists as out-of-frame is in frame |
| `camera` | Elevation, azimuth, roll, lens, distance inside the asserted ranges from the spec |
| `light` | 25% clay render: face mean luma above background luma; mean luma 90-125 (or the spec's range); no emissive above its cap; hair still dark |
| `motion` (animation) | Max deg/frame per bone, zero frames over the cap, no quaternion flips, feet do not slide while planted (< 1 cm), no frozen bone longer than 12 frames during a "live" shot, hits land within 1 frame of the beat grid |
| `final` | Graded file exists and is newer than the raw; black point and saturation inside the spec; delta-E of the avatar mask under the limit |

Each job starts from a `job.json` spec (shot type, head_frac, head_xy, lens range, prop list with frame cells,
light ratio, palette taken from the reference, out-of-frame list). The pose and camera plan the owner demands
is this file, written before any Blender call. Gates read it. This replaces the nine "planned-but-unbuilt
tools" in START_PROMPT with one spec and one gate runner.

Process rules that stay human (code cannot check them): owner picks idea and cast first; "can u" is a
question; keep a liked mood; no cringe text; self-rate = lowest part + 1 and expect the owner 2-3 lower; Opus
review against the owner's references only, after the owner OKs the spend; usage check before every step.

## 3. What is missing entirely, and how to get it

| Missing | Why it matters | How we overcome it | Cost / risk |
|---|---|---|---|
| **Face acting** | The reference video lives on faces. Our faces never move. | `tools/face_rig.py`: split the avatar's face decal into layers (brow L/R, eye L/R, mouth) with Pillow, put each on its own small plane shrink-wrapped 1 mm off the head, parented to the Head bone. Brows and eyes move/rotate/scale with keyframes; blink = eye plane scale Y; mouth = swap between 6-8 drawn mouth shapes (image sequence offset). Expression presets: neutral, smirk, grin, glare, shock, sad, blink. | Medium. Works on classic faces (flat decal). Dynamic-head avatars need a per-avatar check. Say so at the start of the job. |
| **Lip sync** | Voices on every line is already the rule; mouths must match. | `rhubarb-lip-sync` (repo exists, checked with `git ls-remote`; has a Windows release) turns each edge-tts wav into timed mouth shapes A-H. Map them to the mouth sequence. | Needs the owner's OK to download the release exe. Fallback without it: drive mouth open amount from the wav's loudness envelope (numpy, already installed). |
| **Planted feet and reaching hands (IK)** | Foot slide and floaty arms read as amateur. | Add IK constraints for both legs and both arms to the armature that `build_exact_gfx.py` makes (pole targets at knees/elbows). `rigs_community/IKR15.blend` is already here as a worked example. | Low. Bake to FK before render. |
| **Follow-through on hair, coats, accessories** | "Smooth" is mostly overlap: things keep moving after the body stops. | Own spring bake in `anim_motion.py`: for chosen bones/accessories, a damped spring follows the parent and is baked to keys (no addon). `blender-wiggle-2` exists as a fallback addon. | Low. |
| **Fingers** | Block hands cannot grip or gesture. | Three honest options per job: hide the hands by pose and framing (default), mitten poses (current), or a `hands_kit` that swaps the block for a simple 5-finger low-poly hand with 3 preset shapes (open, fist, grip) coloured from the avatar skin. | Hands kit is a real build and changes the avatar's look: owner decides per job. |
| **Painted finish (GFX)** | Top GFX get a hand overpaint. Opus cannot paint by hand. | Render passes instead of one PNG: beauty, avatar mask, depth, normal, emission. `gfx2d.py finish` then adds what an artist paints: rim glow from normal + mask, haze from depth, glow from the emission pass only (faces never bloom), light streaks and dust on the depth layers, soft hair highlight along the rim side. | Medium. All local, Pillow + numpy. |
| **60 fps smoothness** | The reference feels fluid. | Animate and render at 30 fps with Cycles/EEVEE motion blur (shutter 0.5). Optional RIFE to 60 fps: `rife-ncnn-vulkan` is cloned but has no exe; needs a release download and the owner's OK. Do not interpolate shots with fast cuts or text. | Low without RIFE. |
| **Watching the reference motion** | Plan above is from four stills. | Owner drops the video file (or a screen recording) into `gfx_references/`; then measure it: cut lengths (PySceneDetect is cloned, needs pip OK), shot sizes, motion per frame. | Owner action. |

Not needed (checked, skip): filmcraft/Natron/kdenlive/olive (desktop apps, not installed), sam2 (large
checkpoints; our render mask is exact), open-higgsfield (sends keys to a third party), retargeted rbx_anims
(owner dislikes them).

## 4. Animation system (to reach the Ink Game bar)

**Order of work, each with a gate:**
1. **Script and beat sheet**: one line per shot: length, who, action, emotion, sound. Owner approves.
2. **Voices first** (edge-tts, ranked with earshot), real lengths into `voice/lengths.json`. Timing comes from audio.
3. **Animatic**: Workbench stills, one per shot, cut to the audio with ffmpeg. Owner approves pacing before
   any motion is keyed. This is the cheapest place to catch "too quick" and "unreadable".
4. **Blocking**: key poses only (stepped), every bone keyed at each pose. Golden poses must read as a black
   silhouette (render the mask, look at it).
5. **Splining**: auto-clamped Bezier, then the smooth pass below. `gate.py motion`.
6. **Face pass**: expressions on the story beats, blinks every 2-4 s and on head turns, lip sync.
7. **Camera pass**, **light pass**, low-res beat stills, then render, then post and mix.

**Smooth pass (what "smooth" means in numbers):**
- Ease in and out of every pose; no linear segments. Holds are moving holds (2-4% drift), never frozen.
- Anticipation 4-8 frames opposite the move; overshoot 2-3 frames past the pose, settle 4-6 frames.
- Overlap offsets down the chain (already logged): torso +1, head +2, upper arm +2, lower arm +3, hand +4 frames.
- Hands and head travel on arcs: check the hand's path as a drawn curve; no straight lines or zig-zags.
- Hips lead: every weight shift starts at the pelvis; feet planted by IK; one foot always down in walks.
- Breathing 0.25 Hz on the chest, 1-2 deg; idle sway; eye darts before head turns.
- 30 fps, motion blur shutter 0.5.

**Shot rules (from the reference and log section 10):**
- 60% of shots are close or medium (head 35-60% of frame height). Wide shots only to place the scene, under 2 s.
- Lens 35-85 mm, f/2.0-2.8 for faces at full-size avatar scale; focus distance keyed to the eyes.
- Every camera breathes: handheld noise 0.2-0.5 deg at 0.3-0.8 Hz, plus a slow push-in of 2-5% per shot.
- Cut on action; shot length 1.5-4 s; never cut mid-phrase of music.
- Letterbox 2.39:1 only if the owner wants the film look.
- Light per shot, not per scene: soft key 45 deg to the face, cool rim opposite, background 1.5-2 stops darker.

**Look:** bevel 0.004-0.008 m on blocky parts, tiled fabric normal 0.15-0.3 on clothes, face layers crisp,
optional head decals (dirt, scratches) on a second layer. One grade for the whole film: build a LUT once from
the approved hero frame and apply it to every shot with ffmpeg, so shots match.

**Sound:** unchanged from the log (voices -17, real Kenney SFX, -16 LUFS, plain subtitles, no title card).

## 5. GFX system (to reach the top-GFX bar)

1. **Reference or concept to `job.json`** (frame map 10x10, camera clues, prop list, light ratio, palette from
   the reference pixels, never from a prompt).
2. **Fresh avatar fetch**, numbered contact sheet if there are extras, owner's pick.
3. **Camera solve + assert, pose, layout, clay light, materials** in the fixed order, a gate after each.
4. **Density rule:** count the distinct props in the reference frame cells and match the count. Use Poly Haven
   models (linked instances), real PBR textures with a dirt layer, a displaced ground, and 3-5 foreground
   objects near the lens for blur. Empty floor or a flat wall fails the `frame` gate.
5. **Expression:** pick a face preset from the face rig that fits the mood. A neutral stare is a choice, not a default.
6. **Render passes** at 100%, 256 samples, OptiX, avatar textures 2x upscaled.
7. **Finish** with `gfx2d.py finish` (section 3), then the masked grade, then grain and vignette.
8. **Three-distance check** before presenting: 100% crop of the face, full frame, and a 200 px thumbnail.
   The subject must read in all three.
9. **Self-rate harshly, Opus review vs the owner's references (after OK), then present graded + side-by-side.**

## 6. "Uncopiable": what is true and what we do

No picture or video can be made impossible to copy or imitate. What we can do is make ours hard to
reproduce and easy to prove as the owner's:
- **Own look:** every set is built for the job from the kit (no free-model packs or preset scenes other
  artists share), one signature grade LUT, the face-acting rig, and the painted finish pass. A copier would
  need the whole toolchain.
- **Never ship sources:** only the flattened final PNG/MP4 leaves the folder. No .blend, passes or LUT.
- **Proof of authorship:** keep the .blend, passes and `job.json` with dates; export a small hidden
  mark (a faint pattern in the grain, off the face) plus a visible signature only if the owner asks for one.
- **Detail density:** many small real details are what make tracing or re-rendering expensive.

## 7. Build order (each step small enough for one Opus session, each needs "go")

| # | Build | Done when |
|---|---|---|
| 1 | `job.json` schema + `tools/gate.py` with `scene`, `body`, `face`, `frame`, `camera` gates | Gates run on the saved spirits v7 and garage v6 scenes and catch the known faults (hidden face, floating avatar, stray plane) |
| 2 | `light` and `final` gates | Fails the old white-washed fog render, passes bus stop v3 |
| 3 | `face_rig.py` + 7 expression presets | Three expressions on one avatar, 300% crops look drawn, not smeared |
| 4 | IK legs/arms + spring follow-through in `anim_motion.py` + `motion` gate | A 4 s walk-stop-turn test: 0 cm foot slide, hair keeps moving 6+ frames after the stop |
| 5 | Lip sync (rhubarb after OK, loudness fallback first) | One voiced line, mouth matches by eye in a 50% clip |
| 6 | Render passes + `gfx2d.py finish` | Before/after on one old GFX; owner judges |
| 7 | Animatic tool (stills + audio to mp4) and the film LUT step | A 10 s animatic from a beat sheet |
| 8 | Pilot: one 10-15 s, 4-shot scene with one avatar the owner picks, and one GFX redo | Owner's rating; log every mistake |
| 9 | Optional: hands kit, RIFE 60 fps | Owner decides after the pilot |

Each session: `get_usage` first and before every render; stop under the owner's current cap (90% stated on
2026-11-11, other sessions share it).

## 8. Honest limits

- Not verified: the reference video's motion (only stills seen), and the flags of the `tools/bin` craft CLIs.
- The face rig is unproven on dynamic-head avatars.
- "Perfect" is not a state the plan can promise. The plan's promise is narrower: no logged mistake reaches
  the owner again, faces act, feet stay planted, and every frame passes numeric gates before it is shown.
