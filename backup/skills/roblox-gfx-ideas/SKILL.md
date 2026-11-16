---
name: roblox-gfx-ideas
description: Suggest GFX concepts that suit a Roblox character, then build the chosen one in Blender. Use when the owner gives a username (or avatar) without a reference picture, or asks "what gfx would suit her/him", "give me ideas", "make something that fits this avatar".
---

**Step 0 (every time):** read `C:/Users/Siddharth D/Projects/gfx and animation roblox blender/gfx_mistake_log.md` and `docs/GFX_MASTER_PIPELINE.md` in full before planning anything, and append each new mistake to gfx_mistake_log.md.


# GFX ideas for a character, then build

No reference picture this time: you are the art director. Read the avatar, pitch concepts, build the one the owner picks.

## 1. Read the character (no Blender yet)

Fetch the avatar the same way as `roblox-gfx-match` (avatar-3d export into `avatars/<Username>/` in `C:SERSSIDDHARTH DPROJECTSGFX AND ANIMATION ROBLOX BLENDER`)
and look at its textures plus a quick Workbench front render. Write down in one line each:
- **Palette:** 2-3 main colours and the accent (e.g. black + white, red accent).
- **Body type:** chibi/mini (big head, short limbs, no forearm mesh), blocky classic, or tall/realistic. This sets what
  poses work: chibi needs head-dominant close shots and cute poses; tall bodies can do full-body and action shots.
- **Outfit and accessories:** layered clothing, headphones, weapons, wings, hats, props they hint at.
- **Vibe:** goth, emo, cute/kawaii, y2k, sporty/streetwear, preppy, grunge, fantasy, villain, soft/pastel, hacker.
- **Face:** expression (smile, smirk, blank, scary), so the scene's mood fits it.

## 2. Pitch 3-4 concepts

Each concept fits on a few lines and must feel different (place, mood, camera). For each give:
- **Name + one-line pitch.**
- **Setting:** location and props (use `library/` models, textures and HDRIs where possible).
- **Pose:** per body part, chosen for this body type (see table).
- **Camera:** shot type, height, angle, lens, roll, where the head sits.
- **Lighting:** key, rim and practicals with colours that flatter the palette.
- **Grade:** palette, contrast, effects (bloom, grain, sparkles, text).

Ask the owner to pick one (or mix). Rank your favourite first and say why it suits the character in one line.

### Vibe to concept starters

| Vibe | Settings that suit it | Light and grade |
|---|---|---|
| Goth / emo | rainy alley, cemetery at night, church window, parking garage, bedroom with candles | cold blue or deep red rim, crushed blacks, grain, moon or neon |
| Cute / kawaii | pastel bedroom, cloud sky, candy shop, sakura park | soft pink/white key, bloom, sparkles, low contrast |
| Y2K / streetwear | rooftop at sunset, subway, convenience store, graffiti wall | warm sunset key + teal fill, chromatic aberration, flash look |
| Sporty | court, track, garage with bike, gym | hard sun, high contrast, motion feel |
| Grunge / hacker | messy room with monitors, server room, LED strips | RGB practicals, haze, green or purple tint |
| Fantasy / villain | throne, forest with fog, ruins, floating rocks | god rays, volumetric haze, strong rim, saturated accent |
| Soft / pastel | flower field, beach at golden hour, window seat | backlight, haze, lifted blacks, warm tint |

Match accent colours: if the avatar has a red accent, put red in a practical light or prop; for black-and-white avatars
use one strong colour in the set so the character pops.

### Body type to pose

| Body | Good poses | Avoid |
|---|---|---|
| Chibi / mini | selfie close-up, hand on cheek, sitting hugging knees, peeking over an object, lying on the bed | full-body action, finger poses, wide shots (tiny body) |
| Classic blocky | sitting on a ledge, leaning on a wall, hands in pockets, mirror selfie | close-ups needing a face expression |
| Tall / realistic | walking, action, back-to-camera look, full-body fashion shot | ultra-close selfies that hide the outfit |

## Lessons (DI3STINY rainy bus stop, 2026-10-26)

- Owner preferred the first warm, rain-heavy preview over my "fixed" cold relight. Keep the mood that works and fix
  only the broken parts (framing, props). Don't relight the whole scene to chase a plan bullet.
- Measure framing first: `frame_head(head_frac≈0.3)` for a seated shot cut at the shins. 0.2-0.24 showed the
  whole body with an empty floor band.
- Before placing a prop, check `k.project(loc)` puts it inside the frame. Camera-relative left/right flips easily.
- Lit panels: base colour black plus a low emission, or AgX blows them out white. Big flat panels behind the subject
  dominate and float behind transparent glass, so drop them or give them visible support.
- Rain: one mesh of ~4000 streaks, none within 1.3 m of the lens. Dense rain plus haze sells the mood.
- Owner allows the full GPU and CPU for renders (setup_cycles enables both).

## 3. Build the chosen one

Follow `roblox-gfx-match` from section 0 on, using your concept as the spec:
pose plan first, camera solve and assert, frame map, clay light check, materials, masked grade, scene lint.
- Rig with `build_exact_gfx.py` (it skins layered clothing so sleeves follow the arms).
- Use `gfx_kit` (poses, frame_head, props, light presets, render_mask) and `gfx2d.py` (grade, post).
- Installed Blender skills help: `blender-shader-nodes`, `blender-compositing-nodes`, `blender-scene-rendering`,
  `blender-polyhaven-*`, and camera-move skills (`blender-slow-zoom`, `blender-turntable`, `blender-crane-shot`) when
  the owner wants an animation instead of a still.
- Write the script as `tools/style_<concept>.py` and output to `gfx_output/<username>/`.
- With no reference to compare against, judge it against the concept's own spec, part by part, harshly
  (the owner rates 2-3 points lower). Check usage between renders and stay under 98%.

## Mistake log (owner: "save every mistake and update them in this file"). Append new ones as they happen.

Suhaa_Official welcome-back, 2026-10-26:
- **Asked the owner to fetch the avatar-3d JSON by hand.** I can do it myself with the Claude-in-Chrome tools (the
  logged-in Chrome). The built-in browser pane is NOT logged in and returns "Invalid authentication data". Go
  straight to Chrome: load tabs_context_mcp, navigate, get_page_text, close the tab afterwards.
- **avatar-3d answers `Pending` the first time.** Reload the same URL until `Completed`, then open `imageUrl`.
- **Called one tool at a time.** Batch independent calls (and use browser_batch) to save round trips and tokens.
- **Plan said "hand wave" before checking the doll arm can bend.** Test the arm range first; have a fallback pose.
- **build_exact_gfx.py leaves a `Halo` ring and a `Backdrop` mesh in the scene.** They show up as a stray ring behind the head. Delete both right after import (done in the Suhaa run) before the first preview.
- **Wrote helper scripts to $TEMP and a background run lost them (silent no-op, preview never appeared).** Put scripts in the scratchpad dir and run bl.py in the foreground.
- **gfx_kit.plane(rot=...) takes DEGREES, I passed math.radians(90) (1.5 deg).** Wall and window plane lay flat, the window rendered black. Check rotation_euler of a placed plane before the first Cycles render; also pass rot in degrees to cube(rot_z) too.
- **gfx2d post --text-pos is the text CENTRE, not its left edge.** Pos 0.05 clipped "welcome" off the frame. Use ~0.25 for a left-side caption. Random --sparkles also landed on her arm; place them with --sparkle-at.
- **gfx2d `--sparkle-at` is nargs="*": pass all spots after ONE flag (x,y,size x,y,size ...).** Repeating the flag keeps only the last.
- **3D text outline copy was placed toward the camera (+Y) and hid the pink text; also the text was ~2x too wide.** Camera sits at +Y, so "behind" is -Y. Check the text width in frame (project the ends) before rendering.

## What worked (Suhaa_Official window seat, keep doing)
- Pipeline that ran clean: Chrome fetch of avatar-3d -> `fetch_avatar3d.py` -> `build_exact_gfx.py` -> `style_<name>.py` stages
  (avatar, pose, set, light, camera, text) run through `bl.py`, scripts kept in the scratchpad dir.
- Seat a chibi by measuring the pelvis and foot lowest points (`low()`), then raising the avatar so the lower one sits on the cushion.
  Shin direction (0,-0.85,-0.52) tucks the feet near the hips for a hugging-knees pose.
- Doll hands are plain blocks: a wave reads as a mitten, not fingers. Face the block's flat side to the camera (hint (0,1,0)); the "rock-on" prongs look worse.
- Hide the stage `Halo`, `Backdrop` and the held bag (`Handle3`) that clips through a seated lap.
- Soft pastel look: emissive window pane with a colour-ramp gradient (peach -> pink), exposure about -0.35, one warm key through the window,
  weak pink fill and rim, bokeh spheres sitting just in front of the pane, squashed-sphere plushies with ear spheres.
- Lit pastel scenes blow out fast: start exposure low and key power near 380 W for a 2 m window, not 900.
- 3D text in Blender beats 2D text: `Text` curve + Pacifico font, extrude 0.035, bevel 0.012, pink glossy (coat) material, a white
  offset copy behind it as a sticker outline. Rotate (90,0,180) to face a camera on +Y, then place it by projecting to the frame.
- Preview loop that cost little: Workbench 40% for pose/framing, Cycles 50% at 48 samples for light, 100% at 160 samples for the final.
- **Piled on sparkles and glow for a calm kawaii/pastel theme.** Owner: "doesn't that overdo the effects? it should be a little calm". For soft themes use glow <= 0.12 and no sparkles (or one or two tiny ones); let the 3D text carry the message.
- **Pale pink text on a pale pink window was unreadable.** Fix that worked: hot-pink glossy face + dark berry (0.42,0.04,0.2) thick-bevel copy behind it, scaled ~0.55, kept clear of the raised hand.
- **No "photocraft" tool or repo exists in this session** (ToolSearch found nothing). Do the typography in Blender 3D text instead of hunting for one.
- **3D extruded text looked "odd" on a calm scene** (thick slab, perspective skew, jagged outline artifacts, clashes with the soft look). For calm/kawaii themes use FLAT 2D typography: `tools/caption.py IN OUT` (Pacifico name, small letter-spaced Montserrat SemiBold line, drawn heart, soft blurred shadow, rose (206,84,124)). Render the 3D scene without text, then caption it. Use the 3D text only for bold/loud styles.

Suhaa_Official new avatar, 2026-10-26 (candy goth room):
- **Pitched concepts from the textures alone and never showed the owner the avatar.** They had to ask "show me how she looks". Fetch the public 720px render (`thumbnails.roblox.com/v1/users/avatar?userIds=<id>&size=720x720&format=Png`, no login needed) and show it with SendUserFile BEFORE pitching, and describe the real outfit (not guessed from textures).
- **Assumed the body type (chibi) without looking.** Check the front render first.
- **Took "use every repo" literally and ran wide disk searches that found nothing Blender-specific.** The Blender/Roblox tooling is already in the project folder and `~/.claude/skills/blender-*`. Check there first, then ask for the repo name instead of scanning the disk.
- **Wrote a PowerShell regex with unbalanced parentheses** (silent parse error killed the whole search). Keep -match patterns simple.
- **Started building the "best recommendation" without asking what the GFX is FOR.** The owner's friend wanted a Cortis-themed GFX (K-pop, cool, not cutesy) and I built a candy-goth room from her pink outfit alone. Ask the theme/use (group, event, song, mood) before pitching, and never let "cute avatar" decide the mood.
- **`gfx_kit.show_camera()` crashes in Blender 5.2: default shading "MATERIAL" is not a valid enum here (WIREFRAME/SOLID/RENDERED).** Fix the default to "RENDERED" or "SOLID" before the next run; it aborted stage_set after the scene was built.

Suhaa_Official rooftop blue hour (Cortis style), 2026-10-26, self-rated 5/10:
- **Avatar sat INSIDE the ledge (owner: "she is inside the seat").** I aligned only the pelvis to the ledge top, but the thighs hang lower. Measure the lowest point of LowerTorso + both UpperLegs with `low()` and put THAT on the surface top (+0.003), then print each part's low point to confirm.
- **`cleanup()` copied from the old avatar hid `Handle2` (her scarf).** Handle numbers differ per avatar. List each Handle's dimensions/material before hiding any, and look at the first render for missing clothes.
- **Skyline built from ~3000 `bpy.ops` cubes froze Blender for 10 min (socket timeout).** Build many small objects as ONE bmesh mesh, and run build and render as separate bl.py calls.
- **Skyline placed 12-45 m away with 6-16 m boxes = a black wall; windows inside the building faces.** `obj.dimensions` is stale right after setting `scale`; use the size variable you passed. Put the skyline 90-260 m away, tops mostly BELOW the roof eye line so the sky shows, and keep the roof floor on the camera side of the ledge only.
- **World node gradient from Generated coords stayed black.** An emissive gradient plane far behind (UV Y -> colour ramp) worked.
- Still weak in the result: baggy-pants blocks read as boxes when seated, the fist over the knee reads as a cup, windows are blocky, the skyline is flat silhouettes. Next time pick a pose that shows her face and scarf with the legs cropped, and give buildings varied roofs/antennas plus a haze layer.

Suhaa_Official glitch heart hacker room, 2026-10-26, self-rated 5.5/10 (`tools/style_hacker.py`, `tools/make_screens.py`):
- **Laptop lid hid her whole face (first preview) and a 38 W screen light blew her face and black hair out to white/grey.** Seat her so the eyes clear the lid top (pelvis ~0.62 m, lid <= 0.27 m tall) and start screen-glow lights around 7 W. Black hair turns grey when any key light is too strong; check the hair is still black in the preview.
- **First glitch grade put a shifted RGB band straight through her eyes.** Keep glitch bands off the face band (here y 330-720 of 1080); place them by hand, not random.
- **Heavy bloom (threshold 0.45) washed the face to a white blob.** Use threshold >= 0.65 and strength <= 0.3 for faces.
- **Stickers on the lid back were out of frame once the lid was lowered.** A camera above the lid never sees the lid back; put stickers elsewhere (desk, monitor bezel) or use a lower camera.
- **A long bash call mixing two heredocs, python -c and file writes failed to parse and wrote nothing.** Use the Write tool for files, keep bash calls short.
- Still weak: monitor hearts are flat blobs, the laptop lid is a plain dark slab, hair reads brown-grey, no keyboard glow.

Hacker room v2, 2026-10-26, self-rated 6/10 (`style_hacker.py`, `make_screens.py` rewritten with app windows, waveform, chat, neon heart):
- **Placed the laptop at world x=+0.6 and it appeared at the LEFT, half out of frame.** The camera on +Y looks toward -Y, so world +X is screen-LEFT. Project the prop's centre with `k.project()` before rendering, and mirror X when it should sit screen-right.
- **Hair was grey-brown because of light + bright hair texture.** Darkening the hair material (Handle1Mtl) with a Multiply mix node (0.3 grey) and lowering specular fixed it without relighting. Do this first instead of dimming the scene.
- **Laptop lid back could not be seen from a camera above it.** Moving the laptop to the side at 30 deg, with a glowing heart logo and stickers on the lid back, made it readable.
- Still weak: hair still has a slight brown tint, hands are plain blocks on the desk, the keyboard glow looks white, the shot is a bit empty on the right.

Subway platform (idea 3 of the 50 list), 2026-10-26, self-rated 4.5/10 (`tools/style_subway.py`):
- **"Idea 3" was ambiguous (three different lists had a #3).** I assumed the newest list (Subway Platform) without saying so up front. Number the ideas once and state which list a number refers to, or confirm before building.
- **First train was just a black box with a few huge glowing rectangles; the owner said it "looks like windows".** A train needs a readable rhythm: silver body, colour stripe, door pairs, window groups between doors, gaps between carriages, dark undercarriage, roofline. Build all of that, not only lit windows.
- **Glowing windows at strength 9 / 3.5 blew out to flat white slabs under AgX.** Emissive window strips need strength ~2 and a warm colour.
- **Horizontal motion-blur kernel (241 px) was shorter than the windows (500 px), so only the edges softened.** The kernel must be longer than the features you want to streak (700+ px for a rushing train), and a weak blur still reads as a static wall.
- **Camera 4 m from a train placed 3 m behind a chibi makes the train giant.** For a believable train put it further back and use a wider, lower frame so several doors and windows show.
- Still weak: train looks too close and huge, the door is a flat pale slab, motion blur is subtle, the bench is a plain slab and the floor is dull.

Subway platform bullet train v1 rebuild, 2026-10-26, self-rated 5.5/10:
- **Owner: "make a proper train like a bullet train that is easy to identify".** A side-on box train is never identifiable. A shinkansen reads from its silhouette: long pointed nose lofted from superellipse rings (bmesh, scale ~u^0.62), white body, two blue stripes, cab window, window row, dark skirt. Show the nose AND the body.
- **Owner: "the nose is the only visible part of the image".** I framed the nose and left the body off-frame. Calibrate world X to screen X with two known points (here 0.099 W per metre, +X is screen-left), then place nose tip, body start and windows so all of them land inside the frame. Check the preview for the thing the owner will name.
- **Stripe plates on a curved nose were a row of blocky tiles.** Next time use a texture/vertex-colour band or a shrinkwrapped curve instead of stacked cubes.
- **Motion blur only on the train body (left of x=0.42 W, kernel 201 px) kept the nose crisp and read as speed.**
- Still weak: head only ~12% of frame, one bright blown spot on the body from the overhead light, cab window is a flat slab, bench is a plain slab.

Suhaa_Official gamer corner, 2026-10-26:
- **Head aim args swapped.** In `k.aim("Head", up, hint)` the first vector is UP and the hint is FACING. Swapping them showed the back of her hair.
- **Screen plane showed its back (blank).** Check the plane normal via `matrix_world.to_3x3() @ (0,0,1)` against the camera before rendering. The screen must also sit ~3 cm in front of the bezel cube, otherwise the bezel hides it.
- **Blender crashed on a combined stage+render call.** Run build stages and the render as separate bl.py calls.
- **Screen faced away from the camera, so she looked at nothing.** The camera sees a seated figure's face only if the monitor is on the camera side. Put the monitor at her front-side (+X appears screen-left), turn the head about 60 degrees, and set the camera slightly toward that side. The owner allowed rotating the chair, which is the easier fix.
- **Real Discord messages needed the owner's login, and search results were mostly the owner's own.** The owner then preferred a Cortis performance on the screen over Discord. Ask what the screen should show before gathering references.
- **Open v1 flaws:** keyboard glow blown white, hand not on the keys, stick-figure dancers, dark desk. Rated about 5/10.
- **Gamer v2:** chibi arm reach is only ~0.43 m from the shoulder, so put the keyboard at the lap edge (not 1 m away) and use the arm on the desk side (.P for +X). Keyboard emission 0.5, not 3. Remove the armrest on the desk side. The owner said: never build anything (animation etc.) without approval first.

Bio_IsHere neon alley, 2026-10-26:
- **Used the shared Blender while another session was building in it, and wiped its scene.** Blender on port 9876 is
  ONE instance shared by every session. My stage_set deleted all non-avatar objects, which destroyed the Suhaa
  session's gamer-corner set (Gm* objects). Before the first bl.py call, run ListAgents / list_sessions: if another
  gfx session in this folder is busy, do not touch Blender; SendMessage it with notify_when_idle and wait.
- **Read "wait for the previous one to finish" as my own GFX-then-animation order.** The owner meant the OTHER session.
  When the owner says "the previous one / the other one", check the running sessions before assuming.
- **`k.clear()` matches the whole name before the dot, so the prefix "Dump" never removed "Dumpster"** and reruns piled
  up duplicates. Use exact base names, or wipe by "not in keep set".
- **First Workbench preview silently rendered with Cycles** (engine was left on CYCLES by the scene), and old leftovers
  showed up. List non-avatar objects and set the engine explicitly before every preview.
- **Neon text rot=(90,0,0) faces away (-Y).** Keep neon_text's default (90,0,180) for a camera on +Y.
- **Projecting a sign's centre isn't enough for a wide sign**: its backing panel covered the head. Size the sign to
  the frame (~40% width) and check both ends.
- **Rain 3500 streaks at 2.5 mm width, strength 0.6 looked like snow-white scratches.** 2200 streaks, 1.1 mm,
  strength 0.25, alpha 0.25 read as rain at this distance.
- **Gamer v5:** (1) Owner wanted a real frame from the playing video, not a thumbnail. Chrome: open the official video, seek, draw the `<video>` to a canvas and trigger a download via `<a download>` (Chrome blocks posting to 127.0.0.1 from an https page and CDP calls time out after 45 s, so do one frame per call). Only the first download of several in one call landed, so use one download per call. (2) Check the live Blender scene before building: it had silently switched to a different project (other avatar, dumpster set), and my stage scripts had already touched it. Back it up with `save_as_mainfile(copy=True)` before clearing, and assert the armature is the right avatar. (3) A single-threaded http.server hangs on idle browser connections; use ThreadingHTTPServer.

Qsi2408 night skate spot, 2026-10-26, v1 5/10, v2 ~6/10 (`tools/style_skate.py`, `make_graffiti.py`, `post_night.py`):
- **Filled the graffiti wall with slogan tags ("no rules", "x_x", "SK8", "404", "crew") and the username.** Owner: "dont put
  any cringe stuff in any of my gfx's". No words, meme text, emoji faces or names in sets unless asked.
- **Abstract zig-zag strokes looked like a stock chart.** Soft spray clouds + grime over a real concrete texture read better.
- **Seat ledge depth was fixed (0.55 m), so the shins sank inside the ledge.** Put the ledge front just behind the measured knee y.
- **A cube skateboard reads as a post/slab.** Model a popsicle deck (rounded kicked ends, grip/graphic/maple faces) with
  baseplates, hangers, axles and bevelled wheels (`build_board`). Turn it to show the trucks and wheels to the lens.
- **Light-grey cargo pants on top-lit chibi thighs read as pale tubes.** Give the legs their own material copy: multiply ~0.4,
  wave-texture crease bump, low specular.
- **A wall prop (utility box) behind the head looked like a block growing out of the cap.** Project wall props against the head silhouette.
- **PowerShell `Set-Content -Encoding utf8` writes a BOM that breaks bl.py exec.** Write scratch scripts with the Write tool, new names.

## Animations (Bio x Suhaa door visit, 2026-10-26: `tools/anim_door.py` + `tools/anim_post.py`)

Tools that worked (all already installed, use them again):
- **Headless Blender 5.2** (`C:\Program Files\Blender Foundation\Blender 5.2\blender.exe -b --factory-startup -P script -- args`):
  its own process, so it never clashes with the shared GUI Blender. Pattern: `build` saves `scene.blend`, then
  `stills f1,f2,...` (50%) to check, then `frames a b` to render the PNG sequence in the background.
- **EEVEE** 1920x1080 at 48 samples: ~2.5 s per frame at 50%, so a 15 s / 360-frame shot fits a coffee break. Cycles would be far slower.
- **Two avatars in one scene:** build_exact_gfx wipes the scene, so build avatar A, `bpy.data.libraries.write` it to a
  temp .blend, build B, rename both armatures, then append A back.
- **Pose keys:** aim() directions are in the armature's own space (+Y = where it faces), so they stay right however
  the armature object is turned. Key every bone at each pose key (rest + listed bones) so poses never leak.
- **Camera cuts** with timeline markers (`marker.camera`); for single-frame renders set `scene.camera` from markers by hand.
- **Pillow** for subtitles (rounded frosted pill, speaker-coloured name chip and accent bar, fade + rise, italic grey
  sound captions, Montserrat variable font via `set_variation_by_axes`) and a numpy vignette.
- **numpy + scipy** to synthesize the sound (crickets, wind, footsteps, wood knocks, door creak, thud) as a WAV.
- **ffmpeg** (WinGet build on PATH) for the H.264 + AAC mp4 (`-crf 17 -preset slow -pix_fmt yuv420p -movflags +faststart`).
- Also installed and unused this time: **moviepy 2.2**, **OpenCV 5**; `rigs_community/rbx_anims_v3.1.2.zip` (Roblox
  animation importer) and `rigs_community/IKR15.blend` (R15 IK rig) for richer motion next time; the
  `blender-animation-rigging` skill and the camera-move skills (`blender-slow-zoom`, `blender-crane-shot`, `blender-dolly-rotate`).

Mistakes made:
- **Over-the-shoulder shot from behind Bio:** his big head and the spear on his back covered Suhaa twice. With a
  back accessory, shoot the dialogue from the other side of the conversation (inside the house) and offset the camera
  sideways so the two heads don't line up.
- **Waved with the arm on the side hidden by the door frame.** Pick the gesture arm from the camera's side.
- **Doormat text read upside down:** flat text on the floor needs rot z=180 for a camera on +Y.
- **Bright PorchFill (120 W) and window emission 2.2 made the night look like day;** 35 W cool fill, window strength 0.35.
- **A big multi-replace patch aborted on one stale string and silently skipped the rebuild check.** Print the missing
  keys instead of asserting, and patch by line number when a line was already edited.
- **Default "relaxed" poses looked stiff.** The owner wants character: give each character a base pose (Bio: pocket hand,
  hip shift, lean back, chin up, swagger walk with a slow period and small swing; Suhaa: hands together, head tilt, open-arm welcome).

Owner review of the door-visit v1 video (rated it unfinished):
- **No voices.** Every spoken line needs a voice. Use edge-tts (owner picked Microsoft neural voices): a laid-back low male
  voice for a "cool" character, a warm bright female voice for a "kind" one; make 3 variants each, rank with
  `earshot match`, and re-time the animation to the real clip lengths.
- **Synthesized numpy SFX sounded fake.** Use real recordings: `library/sfx/kenney_rpg` and `library/sfx/kenney_impact`
  (CC0: doorOpen/doorClose, creak1-3, footstep_concrete/wood, impactWood for knocks). Rank takes with earshot and run
  `earshot critique` on the final mp4.
- **Chat-bubble "subtitles" were wrong.** Subtitles = plain white text, thin dark outline + soft shadow, bottom centre.
  Sound captions in italics like *[knocking]* are fine.
- **Username title card was unwanted.** Don't add titles unless asked. Night ambience only, no music unless asked.
- **Both characters looked stiff.** Causes: few hand keys with frozen holds, no breathing or weight shift, walk without
  hip bob and with sliding feet, pendulum arms, no anticipation or follow-through, frozen bodies while talking.
  Fix: retarget Roblox default animations (`rigs_community/rbx_anims_v3.1.2.zip`, `IKR15.blend`) for walk/idle, then add
  breathing, idle sway, weight shifts, head micro-moves, overlapping arms, ease in/out, anticipation, and head bobs
  timed to each voice line. Check a low-res draft as frame strips for freezes before the final render.
- **Started building before the repos the owner gave had finished downloading.** Wait for all clones, read their
  REPO.md cards, then choose the toolset. Repo library: `C:\Users\Siddharth D\Projects\github-repos\<category>\<repo>\REPO.md`.

Door visit v2 (2026-10-26), what worked — reuse for every animation:
- **Real Roblox motion:** default animation ids walk 507777826, idle 507766951 (classic R15; 507766666 is the new
  face-rig idle with extra bones), wave 507770239, point 507770453, run 507767714. In the logged-in Chrome open
  `https://assetdelivery.roblox.com/v2/asset?id=<id>` and curl the `location` (zstd). JS fetch of that URL is blocked by
  the browser tool; navigate + get_page_text works. `tools/rbx_anim_json.py` converts to `library/anims/<name>.json`
  using the rbx_anims parser (add Pose/Keyframe to `_PROPS_CLASSES`, load core/rbxm.py without its bpy imports).
- **`tools/anim_motion.py` Actor:** clips (cross-faded Roblox anims, Roblox->armature axes via conjugation with the bone
  rest matrix) + acting poses slerped in with eased windows + breathing, sway, head micro-moves and talking nods.
  Walk playback 0.6x for a casual pace. It bakes a key on every bone every frame (15 s builds in ~15 s).
- **Voices:** `edge-tts --voice en-US-AndrewNeural --rate=-8% --pitch=-6Hz` (cool guy) and `en-US-AvaNeural --rate=-4%
  --pitch=+2Hz` (kind woman) won `earshot rank`. Put each line's real length in voice/lengths.json and time the scene to it.
- **SFX:** earshot rank picked footstep04/06/09 (porch), footstep_carpet_003/004 (inside), impactWood_medium_002/003/001
  (knocks), doorOpen_1 + creak1, doorClose_1 + low-passed doorClose_4 (thud). Crickets: Wikimedia
  `Crickets_choir.ogg` (CC BY-SA 4.0, credit in library/sfx/ambience/CREDITS.txt).
- **Mix check with earshot:** `earshot timeline video.mp4` lists every event with its level. First mix: knocks peaked
  at -1 dBFS and the whole film sat at -22 LUFS. Fix: RMS-level each sound, knocks around -21 dB RMS, steps around -30,
  voices -17, then bring the mix to about -16 LUFS with a tanh soft clip at -1 dBFS. `earshot realness` scored 0.88 (real).
- **Plain subtitles** in tools/anim_post2.py (Montserrat 600, stroke 2.5 px black, blurred shadow); sound captions italic grey.

Suhaa_Official Cortis concert animation, 2026-10-27:
- **Over-engineered the stage members** (mannequin + primitive details, then photo-real member heads, then per-member hair/face matching). Owner: "just make it normal… street wear… men only". For extra characters use normal real Roblox avatars of the requested vibe/gender (users/search -> tools/user_sheet.py -> avatar-3d -> cache_avatar.py), not likeness replicas, and not the crowd pool.
- **Suhaa was visible standing at the start** when she should come out of the dark: key hide_render until the lights are down.
- cache_avatar.py fails its rig assertion on some exports (arm/leg part count); keep 1-2 backups when picking avatars.
- **Finding styled avatars:** username search returns mostly defaults; friends lists of one good avatar give many similar ones (friends.roblox.com/v1/users/{id}/friends -> tools/user_sheet.py contact sheet).
- **Catalog clothing 3D exports** are an R6 dummy facing -Y with the grey body colour baked opaque; hair exports are in studs (scale = head width / 1.2). Full notes in memory `animation-pipeline-lessons`.
- **Owner corrects mid-turn**: drop the old idea at once; one-line plan before each new approach.
- **Picked avatars without showing the owner** (front-row "random users" were mostly default avatars; dancers chosen by me were rejected). Every character goes through a numbered contact sheet and the owner's pick.
- **Built 520 crowd fans when only 4 ever reach the camera.** Before building extras, project positions through the camera path and only build what is seen (count first, then build).
- **Strobe light ramped up between bezier keys** (0 at 4.2 s -> 30000 at 8.1 s) and washed a whole section white. Light cues need a hold key before each flash or CONSTANT interpolation.
- **Reveal keyframes un-hid accessories that the avatar builder had hidden** (speech bubble came back). Only key objects that are visible at build time.
- **Didn't check stills of each beat (start, reveal, mid, hit, end) before asking to render;** always render 5 beat stills and fix before the long render.

Suhaa concert v2→v3, 2026-10-27 (owner: "dancers look like they're having a seizure", "too quick, didn't know when Suhaa came"):
- **Copied a noisy video track onto every bone, keyed every frame.** Result: jitter = "seizure". Use designed KEY POSES on beats/half-beats with Bezier auto-clamped in between; tracked data only as loose reference.
- **aim() switched its roll hint when a bone neared it → 180° roll flips in one frame (hands hanging down).** Carry each bone's previous side axis forward (parallel transport); explicit hint only for torso/head/feet. Sign-match quaternions to the previous key.
- **All bones arrived on the same frame = robotic.** Key children later: UpperTorso +1, Head +2, UpperArm +2, LowerArm +3, Hand +4 frames.
- **Per-frame foot snap + sharp |sin| bounce = popping body / twitch on every beat.** Snap feet only on keys; bounce via knee bend lowest on the downbeat.
- **Anticipation key 2 frames before a hit → arms swung 146°/frame.** Put wind-ups ≥0.3 s before hits and cap every bone at ~12° per frame between keys (slerp toward the target). Run a numeric motion check (max deg/frame per bone, buckets by frame) before ANY render; fail >30°.
- **12 s clip for a whole story** — the owner couldn't follow it. Story beats need breathing room: 20-25 s, a hero entrance gets ~10 s (silhouette → slow walk → hero pose on a downbeat).
- **Hero walk at 3.2 steps/s read as running.** Use 80-95 steps/min, step ≈0.6× leg, one foot always down, pelvis bob/roll small, chin up.
- **Camera put right behind the front row → giant blurry fan heads filled the frame.** Crowd shots from 6-12 m behind the front row, 3.5-4.5 m high, 50-85 mm; fan heads stay in the bottom ~10-25%. Project heads into frame and check before rendering.
- **Fixed BPM=120 assumed.** Measure beats with librosa on the actual audio and key to that grid.
- **No motion blur, far camera, harsh light** made it look cheap vs a good Roblox animation (Ink Game ref). Turn motion blur on, use close/medium shots with shallow DOF, fewer held deliberate moves, soft rim+key lights, cloth sheen.
- **Built a test before checking what the camera sees** and wasted a full build. Render 6-10 low-res stills at story beats first.
- **Downloading songs from YouTube is not done** — ask the owner for the audio file.
- **Front-row fans loaded at full Roblox export size (~5-6 m tall) next to 0.28-scaled stage avatars** → the "giant heads blocking the camera" bug in v2 AND v3. Before any crowd shot, print every armature's world bounding-box height; all characters must be ~1.4-2 m. Cached avatar_cache exports are in studs: scale 0.28.
- **Over-smoothed the dance (Gaussian r=4 + 12°/frame cap + quarter-beat keys) → "almost no dance".** Smooth ≠ small. Remove only jitter (light smoothing r≈2), keep big readable poses (exaggerate tracked shapes ~1.2×), cap ~20°/frame, key every ~2 frames. Measure motion amplitude (mean arm deg/frame in the chorus) next to the jitter check and look at a test clip before any full render. Owner: "maintain the quality while having more dance steps".
- **Killed a render chain mid-way and the post step still ran, overwriting Downloads/suhaa_concert.mp4 with a 7-frame video.** Chain the post/copy with `&&` on a frame-count check, or kill the whole shell job, not just Blender.

Suhaa concert v3 dance similarity, 2026-10-27 (owner: "u said 55-70% but the clip barely had 10%"):
- **Reused an 11.9 s choreo track for a 24 s piece on a different song section.** The track (lv_0 clip, likely a social-media mashup of the practice video) does not match REDRED 69-94 s, so the moves never fit the music. Before animating, align the reference clip's audio with the song (onset cross-correlation) and track footage of EXACTLY the section being animated. No matching footage = say so and ask for it; don't loop other moves.
- **Claimed a similarity % without measuring it.** Gate every dance test on a number: per-bone cosine match vs the tracked reference for the same section (target >= 0.55 mean), plus jitter (0 frames over 30 deg).
- **The groove layer and the 45% leg blend overwrite the real moves.** Keep the track at full weight on arms/torso; add groove only where the track is flat.
- **Ran ffmpeg on a git-bash `/c/...` path holding Korean text; it failed, and the chained librosa step (joined with `;`) recomputed beats from the OLD audio.** Pass `cygpath -w` paths to ffmpeg and chain dependent steps with `&&`.
- **Chroma alignment put the owner's chorus clip on the SECOND chorus (1:39) when it was the first (0:35.8).** Repeated choruses score nearly the same in chroma. Use mel/onset features with 3 s windows, check that every window gives the same offset, look at the runner-up, and confirm visually against the source video (play it in the browser, never download it).
- **Gave the owner timestamps from the wrong upload/section twice** (song 1:39 second chorus, then guessed offsets). Practice uploads have different offsets (Fix ver. +4.19 s, mirrored +0.35 s vs the film audio); always map times per video by audio match + a visual frame check, and say how confident the match is.
- **Ended the dance by holding the last tracked frame after the finale hit.** Plan a real freeze pose landing ON the final hit, then ~1 s hold with a 1 s audio fade; never cut the song mid-phrase.
- **Tight transitions (0.25-0.4 s) from a held pose into tracked moves made forearms snap >30 deg/frame** (the check measures WORLD rotation, so parent + child turns add up). Give pose->track blends >= 0.5 s and grooves >= 0.7 s before a hit pose.
- **Put a dancer straight behind the (shorter) hero in the formation** → from the crowd camera they merged into one blob with his hair above her head. Check formations through the actual camera: no one directly behind the hero within ~1.2 m in x, or push them ≥2 m back.
- **Chorus shot at 64-70 mm with a 6 m-wide line** made each dancer ~1/4 frame tall and the moves unreadable. Keep the line ≤5 m and use ~80-85 mm from 16 m so dancers are ~1/3 of the frame.
- **Tightened the chorus lens (64→85 mm) without re-balancing lights** → the bright LED screen and beam pops filled more of the frame and washed the last 8 s white. When the framing changes, re-check exposure on stills from that section (mean luma ~110-125) and dim emissive screens/beam pops for close shots.

sttvr_l1ght haunting-spirits misty forest, 2026-11-02:
- **Built a first render before the owner picked an idea.** They wanted ideas first, then their choice. List the concepts, wait (or take their delegation "choose by how the avatar looks"), then build.
- **Picked the concept from the moodboard, not from the avatar.** sttvr_l1ght is a chibi goth doll (short bob, big head, 1.25 m tall). Tall wafting-ghost scale and a 22% head frame made her tiny. Read the avatar's proportions first; frame chibi avatars with head_frac ~0.3.
- **Left the base stage's `Backdrop` and `Halo` in the scene** (the grey wall and a glowing ring showed up in the first render). Remove them or list unparented meshes before the first preview.
- **Camera sat inside a dense ground-mist box.** It hid the body and ended in a hard table-top edge. Keep volume density low (<=0.3), make it fade with height (Generated.z power curve), and don't let a volume's top be visible.
- **Moon backlight (5500 W) scattered through the fog into a white wash.** Start fog-lit scenes at 600-1500 W and world strength ~0.1; judge from a 50% render.
- **Translucent flat veil sheets and ribbons read as lit wall slabs / light pillars.** The Wave modifier didn't flutter them. Drop cloth props that can't be shaped, or sculpt real folds.
- **`gfx2d.py grade --levels 0.04,0.97` blew the whole image to white.** `--levels` takes Lab L units 0-100, not 0-1. Use the gentle recipe bloom 0.15, grain 0.014, vignette 0.4, sat 0.7 and view the result before calling it done.
- **Patched a path with `sed` and a raw backslash string in Python** twice; both mangled the Windows path. Use the Edit tool for paths with backslashes.
- **Said I'd use library repos for post work, but photocraft/lightcraft/effectcraft need a Rust build and Real-ESRGAN isn't installed.** Check a repo's REPO.md "installed?" line before promising it; gfx2d.py already covers grade/glow/grain.

sttvr_l1ght Halloween pumpkin graveyard + autumn lantern, 2026-11-02 (Opus review: pumpkin 4/10, lantern 5/10 before round 2):
- **Owner thought I sent ungraded renders.** I hadn't sent anything yet, but I also hadn't shown the grade step. Always say "preview, grade comes after" and show the graded result, not the raw one.
- **Image textures on scaled cubes showed as wood stripes.** pbr() mapped Object coords, so side faces smeared. Fixed in gfx_kit (Box projection) and solid() applies scale; check any new texture on a box for streaks at 50%.
- **Mirrored the set the wrong way.** Camera looks along -Y, so image-right is world -X; the pumpkin cluster at +X went out of frame left. Check each prop with k.project() before rendering.
- **Front point light inside the pumpkin washed its face and skin to flat peach.** Keep face emission strong and the point light ~0.5-1x scaled, check the face still reads.
- **Dense flat polygon "leaves" and white ember dots looked like stray geometry** (Opus flagged both). Keep leaves tiny and few, or use real alpha leaf cards; bokeh dots must be warm and low strength.
- **Lantern glass was white (emission blown out) and brass glowed too.** Set only glass emissive (~2.5), make brass dark metal, and add a flame sphere + a strong warm point light.
- **Sent the owner's "ask Opus" request late.** Run the Opus review against only the owner's reference pictures before presenting renders.

## 14. Gates, face rig, motion kit [2026-11-11]
- New tools: `tools/gate.py` (stages scene, body, face, frame, camera; by name: light, final, motion; spec = job.json, see `tools/job_example.json`), `tools/face_rig.py` (build/pose/blink; expression presets), `tools/motion_kit.py` (`spring()` follow-through for bone-parented hair/accessories). Run the gates before every preview and render; a FAIL means do not render or present.
- Shader drivers built from Python were evaluated once while half built, got flagged invalid and then wrote 0 into the node (zero scale -> NaN -> the whole face rendered black). After creating drivers, re-assign every `driver.expression`, update the view layer, and assert `is_valid` on all of them. Printing node values before and after found it; guessing did not.
- Face rig first try: drawn brows at 9% of eye height in pure black looked like tape on a soft anime face. Use ~4.5% and blend the colour 35% toward skin. Mouth placement from eye height put the mouth off the plate on big-eyed faces (eye height 0.3 of the plate): clamp it onto the plate.
- Known open issues: the "blink" preset still shows a squashed eye instead of only the lid line; faint light-brown native brows are not detected (drawn brows are used); IK legs/arms are not built; gate `light` defaults (mean luma 80-130, face 70-215) fail dark night scenes like bus stop v3, so set the luma ranges in job.json from the reference.
- Gate re-check of old scenes found real faults: graveyard v3 face 52% visible (hair `Handle2`), head only 18% of frame width, avatar fetch 16 days old; haunt head darker than the fog behind it (91 vs 114).
- [2026-11-11] Owner allowed downloading the reference video ("install whatever repo you need to watch the video frame by frame"): yt-dlp, PySceneDetect and OpenCV are installed in the system Python. Measured facts are in `docs/SUPERIOR_PLAN.md` section 10 (24 fps on ones, 304 shots, median 1.9 s, no letterbox). I had planned 30/60 fps and letterbox from four thumbnails: measure the reference before writing targets.
- Face rig: driven Math-node factors rendered stale in EEVEE (eye stayed visible at blink 1); layers are now hidden by pushing their UV off the image. The FIRST render after `face_rig.build()` still showed a wrong eye; render one throwaway frame after build, and look at the blink before using it. Blink is still unverified.
- `agent-reach` (skill + CLI at ~/.local/bin, v1.6.1) is installed: read-only reading/search of YouTube subtitles, Reddit, X, Bilibili, GitHub and other sites when the built-in web tools fail. It does not post or log in for you.
- [2026-11-11] `tools/ik_kit.py` built: `add()` (IK targets IK_Foot.*/IK_Hand.*, poles IK_Knee.*/IK_Elbow.*), `key()`, `bake()`. Test on DI3STINY: body moved 45 cm down and sideways over 30 frames, both feet moved 0.0 cm, knees bent 11 cm forward, same result after bake with 0 constraints left. Not yet used in a real animation.
- Face rig blink: the "ghost eye" under a hidden eye was the BASE image, not the drivers. A diffusion inpaint dragged the eye's grey/white fringe inward. Fill removed features with flat skin colour instead, and let each layer carry its own fringe. I chased drivers and stale renders for three rounds first: when a hidden layer still shows, look at the layer underneath before the logic.
- I deferred approved work (IK, blink) when new requests arrived mid-turn and then asked for approval again. Say "X is deferred because Y" at once and do not re-ask for an approval already given.
- Face rig blink outline FIXED [2026-11-16]. Two causes, both found by measuring, not by looking: (1) rays that land exactly on a mesh edge miss the head; each miss became a transparent spot in the plate (the border feather widened it to ~15 px) and the head's own open eye showed through. `_sample()` now fills enclosed misses from their neighbours. (2) DI3STINY's head is 77 loose pieces (face shell 2 x 589 faces with eye sockets, eye pieces 272, eye rims 96, lashes 28 and 6); the eye piece steps up to 24 mm from the shell, so a plate laid on the coarse grid hits sat behind it. The plate is now a smooth cover over the finely sampled face, faded to zero at the border, and lash/rim-sized pieces are hidden with a Mask modifier `FaceRigHide`. Proof: `gfx_output/_kit_test/blinkfix_sheet.png` (7 expressions) and `blinkfix_side.png` (three-quarter and profile).
- Same job, what cost 18 render rounds: I changed the plate five ways on a guess each time (per-vertex lift = lumpy cheeks; hiding all eye-sized pieces = holes at the sockets; hiding only lashes = rim pokes through; a 96-cell plate = eyeball relief and facets; one constant push = plate edge off the jaw). The round that ended it was a 30-line script that ray-casts head and plate and prints which piece stands in front and by how many mm. When geometry shows through a cover, write that measurement first. Also list the head's loose pieces (count, size, extent) before assuming a head is one closed surface.
- Face rig, still open [2026-11-16]: drawn brows sit under the hair fringe on this avatar and read as a tan bar where they cross strands; the flat skin fill is now a local-tone fill (a flat median left a pale patch); in near-profile the far edge of the plate shows as a small step on the cheek. Still tested on one avatar only.
- [2026-11-16] `tools/lipsync.py` built (plan step 5): `rhubarb(wav, text)` -> timed mouth shapes A-H/X, `loudness(wav)` fallback, `apply(cues, start_frame)` keys only `f_mouth_open` and `f_mouth_sx` (key expressions first, lip sync after). Test line (edge-tts Ava, 3.4 s) on DI3STINY: the rendered mouth area matched the cue on every one of 76 frames (measured from the frames, not judged by eye). Clips: `gfx_output/_kit_test/lipsync/lipsync_rhubarb.mp4` and `lipsync_loudness.mp4`. Not checked by ear (I cannot hear): the owner's watch is the real test.
- Lip sync gotchas: rhubarb.exe prints nothing to a piped stdout here, so read its result with `-o file`; it needs PCM wav (edge-tts gives mp3: `ffmpeg -i line.mp3 -ar 44100 -ac 1 -c:a pcm_s16le line.wav`); mux with `-itsoffset (start_frame-1)/fps` on the audio. The open-mouth width was `0.75 + 0.25*sx`, so a pucker stayed a flat line; now `0.35 + 0.65*sx` (this also makes the shock mouth rounder and the grin wider; presets not re-reviewed after the change). I misread one tile of a contact strip as a wrong mouth; the per-frame pixel count settled it in one call.
- [2026-11-16] Pilot shot 1 (plan step 8, `tools/pilot_shot.py`, Bio_IsHere, 110 frames, EEVEE 960x540): self 5/10 vs the Ink Game close-up at 1:07. First stills were flat and bright (mean luma 80, wall evenly lit): key 150 W + wall pool 60 W + fill 9 W at 1.5 m is far too much for a 1.3 m avatar. What worked: key 70 W size 0.7 spread 80, rim 520 W, fill 2.5 W, wall pool 34 W, wall tint 0.3. Still weaker than the reference: frame darker (38 vs 70), no bloom on the key side, plain eye-level angle (reference looks down with a head tilt), no fabric weave, subtitle sits on the shirt print. `gate.py` was NOT run on this shot (face angle 12.6 deg and face/wall luma 111/21 were measured by hand); run the gates on the next round.
- Pilot lessons: a sparkle-aura accessory (Bio's Handle2, on the Head) floats stars across the face in a close-up; hide it for the shot (`hide_render`) and tell the owner. A blocky head 12 deg off the lens still reads as looking past the camera; aim closer than 10 deg for a to-camera line. Bone rotations in armature space via `B^-1 R B` on the rest matrix worked first time (yaw + = his left, pitch + = chin up). edge-tts can return 'No audio was received' once; retry before changing anything.
- [2026-11-16] Owner on the pilot's subtitle (Arial bold, white, dark outline, burned in with Pillow): "the subtitles can look MUCH better", to be done later with the repo library (hyperframes for HTML overlays, `tools/anim_post2.py` Montserrat 600 style), not a blocker now. Do not ship Pillow-default subtitles as final; also keep them off busy shirt prints.
- [2026-11-16] Usage rule broken: I checked usage at 33% before the pilot, then ran three full re-renders (mouth fix, v2, v3) without checking again and found the 5-hour window at 91%, past the 90% cap. Long sessions also cost more per step as the context grows. Check `get_usage` before EVERY render round, not once per job.
- 2026-11-16 Pilot subtitles redone (`tools/pilot_post.py`, v4): Montserrat 600 drawn at 4x and scaled down, no hard stroke, tight dark halo + soft drop shadow + faint dark pool behind the line, 3-frame fade, lower in frame (baseline at 90.5%). Lesson: Arial bold with a 2 px stroke at 540p looks like a default player caption; draw text supersampled and separate it with soft shadow, not a thick outline. Owner allowed a small overshoot of the 5-hour cap for this one task only (was 96% at start).
- [2026-11-16] Pilot film (4 shots, `tools/pilot_scene.py`, `tools/animatic.py`, `tools/film_lut.py`). Mistakes and lessons: (1) shot 1 rendered pure black: a low-angle `frame_head` solve put the camera 13 cm UNDER the floor; the gate said "face blocked by Floor 81%" before I looked. For any camera below the head, compute camera z = head z - dist*sin(elevation) and keep it above 0.2 m; get closer rather than steeper. (2) `gate.py` face.visible counted the face rig's own plate as a blocker: put "FaceRig" in the job's `see_through`. (3) `gate.py` head_frac measures the bare head mesh and reads about 0.8x of `frame_head`'s number (hair included): write the job spec as frame_head value x 0.8. (4) Usage went 15% -> 47% of the 5-hour window in one stretch, mostly from re-reading the three rule files into an already long session: start a FRESH session per plan step and hand over with the status table in `docs/SUPERIOR_PLAN.md` section 9. (5) Arms keyed with outward roll on both upper and lower arm puff out like a bodybuilder; roll only the upper arm (5 deg).
- [2026-11-16] Render passes + finish built (plan step 6): `tools/alley_v2.py passes` renders mask, hair (head accessories, body as holdout), emission-only (lights hidden, world 0, max_bounces 0), depth (Camera Data view distance / 14 m, 16-bit grey, view transform Raw) and camera-space normal, all by view-layer `material_override`, no compositor. `tools/finish.py finish BEAUTY PASSDIR OUT_FINISH OUT_FINAL` paints depth haze, glow from the emission pass only, rim glow from normal + mask edge, a hair highlight and depth-layered dust, then a gentle grade (contrast 1.06, sat 1.05, vignette 0.3, grain 0.006); `finish.py side OUT HEIGHT imgs...` makes side-by-sides. Its printout gives the mean change per layer: the defaults were almost invisible (dust 0.02 of 255), so read those numbers and raise strengths before looking (used: `--dust 600 --dust-strength 1.2 --rim 0.5 --hair 0.5 --glow 0.75`). Too many dust specks on a black area read as stars.
- [2026-11-16] Bio_IsHere neon alley v2 (`tools/alley_v2.py`, final `gfx_output/Bio_IsHere/alley_v2_final.png`, self 6/10: camera 7, pose 6, light 6.5, finish 6, set 5, face 5). Mistakes and lessons: (1) A blocky R15 body with arms is 3.3 head-widths wide, so "head 30% of the width" means the body fills the whole frame width and a low camera looking up 18 deg sees no ground: the planned wet asphalt and dumpster are built but out of view. Work out what the frame can show (body width in head-widths, bottom ray angle) BEFORE listing set pieces. (2) Preview 1 was purple everywhere: a side "rim" 0.1 m off a wall floods the wall. Use a narrow beam (spread 50) from high on the wall side and light the background with the warm source. (3) Preview 2: rim 120 W turned black hair grey; 60 W plus hair texture x0.45 kept it dark. (4) A neon zigzag inside a ring read as the letters "WV": check wordless neon shapes for accidental letters; a four-point sparkle is safe. (5) `gate.py` body.support fails when the lowest vertex sits exactly on the ground plane (the ray starts under it): put the ground 2 mm lower. (6) Hands behind the back hide block hands in a waist-up shot: solve the arm angles by counting hand vertices the camera can see (ray casts), not by eye. (7) His sparkle aura `Handle2` (0.63 x 0.6 x 0.7 m, 264 faces) had 24 faces over the face from this camera and was hidden. (8) The passes run took over 10 minutes in one shell call and hit the tool timeout: run long renders in the background.
- [2026-11-16] Honest comparison of new vs old work (frames looked at, films not watched at speed): the pilot film beats door v2 and concert on camera (close and low shots, depth of field), face (lip sync and blink) and subtitles, but door v2 still has the better set (a real place: porch lamp, windows, plant, mat), two characters and a story, and the concert has far more motion (five dancers). Alley v2 beats alley v1 on every part, but bus stop v3 still has the more natural pose and mood, and spirits v6 / graveyard v3 have deeper, denser sets. The new tools raise camera, face and finish; set density and body acting are now the weakest parts.

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
