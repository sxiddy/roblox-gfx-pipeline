Read this whole file before any new GFX or animation in this folder.

## Mistake log (owner: "save every mistake and update them in this file"). Append new ones as they happen.

Consolidated 2026-11-02 from: roblox-gfx-ideas SKILL.md, roblox-gfx-match SKILL.md, gfx_references/PLAN.md, START_PROMPT.md, and every memory .md. Items are merged where lessons repeat; the source project/date is in [brackets]. New mistakes: append to the matching section AND to the roblox-gfx-ideas SKILL.md mistake log the same turn.

## Top rules (hard owner preferences + most-repeated mistakes)

1. Never go past the owner's usage cap (70% of the 5-hour window since 2026-10-26; never past 98% weekly/5h otherwise). Run `get_usage` before every step/render and quote the real number, never an estimate.
2. "can u do X?" is a QUESTION: answer yes/no + cost and wait for "go". Never build, review or spawn subagents before the owner OKs the idea.
3. Ask what the piece is FOR (group, event, song, mood) before pitching. Never let "cute avatar" decide the mood.
4. Show the real avatar (720px thumbnail) and describe the real outfit/body type BEFORE pitching. Chibi vs classic vs tall decides pose and framing (chibi head_frac ~0.3).
5. Every character/avatar goes through a numbered contact sheet and the owner's pick. Extras = normal real Roblox avatars of the vibe, never replicas, mannequins or other projects' assets.
6. Write the exact pose + camera plan (type, position, lens, roll, each limb, frame edges, tool) BEFORE any Blender call. No trial-and-error posing.
7. Camera first, solved from the reference perspective and asserted in code. Anything out of frame in the reference is out of frame in the render.
8. The pose may differ from the reference; keep camera/set/light/grade and choose the pose that suits the avatar.
9. Never "fix" a mood the owner liked (warm first preview). Change only broken parts.
10. No cringe: no slogan tags, meme words, emoji faces, usernames or title text in sets/animations unless asked.
11. Gritty, dark, real textures, haze, grain, deep blacks. Start darker and lower on light power than you think.
12. Check every prop with `k.project()` before rendering. Camera on +Y looks to -Y, so world +X is screen-LEFT.
13. Delete the base stage `Backdrop` and `Halo`, and list unparented meshes, before the first preview.
14. The GUI Blender on port 9876 is shared by all sessions. ListAgents first; prefer your own headless Blender. Never wipe a scene you did not build; back it up first.
15. Run build stages and renders as separate bl.py calls; use the Write tool for scripts (no big heredocs, no BOM, no `$TEMP`).
16. Self-rate harshly per part against the reference/spec (score = lowest part + 1, owner rates 2-3 lower). Never ask the owner for a score. Never say done without looking at real frames/output.
17. Run the Opus review against ONLY the owner's reference pictures BEFORE presenting renders (after the owner OKs spending on it). Show the graded result, not the raw one.
18. Animation: voices on every line (edge-tts), real SFX (Kenney), plain subtitles, no title card, no music unless asked; motion is hand-keyed/procedural with eased poses (no retargeted Roblox clips).
19. Dance/motion: designed key poses on the measured beat grid, speed cap per frame, run the numeric motion check and 5-10 beat stills before ANY long render.
20. Measure before you claim (beat grid, similarity %, avatar heights, frame positions). Check each repo's REPO.md "installed?" line before promising a tool.
21. Log every mistake the moment it happens. Owner corrections mid-turn: drop the old idea at once, one-line plan for the new one.
22. Terse answers, batch independent tool calls, never save over the owner's open .blend (save copies).

## 1. Owner preferences & workflow rules

- Terse replies, answer first, no fluff. Commit/PDF/ultracode only when asked. [START_PROMPT]
- "can u do X?" = question; answer and stop. [2026-10-25 garage "can u fix this within 99%"]
- Ask the owner before spawning Opus/subagent reviews or builds: plan -> ask -> review/build. [2026-10-22]
- Owner sends a new reference each time and will not explain; derive camera/pose/background/light/grade yourself, ask only for a missing username. [2026-10-25]
- No reference: use roblox-gfx-ideas: read avatar, pitch 3-4 concepts (name, setting, pose, camera, light, grade), rank your favourite first, wait for the pick (or their "choose by how the avatar looks" delegation). [sttvr_l1ght haunt 2026-11-02: built before the pick = mistake]
- Number ideas once and state which list a number refers to; three lists had a "#3". [subway 2026-10-26]
- "The previous one / the other one" may mean another running session: check sessions before assuming. [Bio 2026-10-26]
- Never build anything (animation etc.) without approval first. [gamer v2]
- Each session is its own project: never reuse avatars/sets/outputs from other projects unless told. [concert 2026-10-26: other clients' avatars in the crowd]
- Owner picks every character: numbered contact sheet (`tools/user_sheet.py "<ids>" out.jpg <cols>`), SendUserFile, wait for numbers, only then fetch/rig. [2026-10-27]
- Trendy-avatar bar and cast pool (still show a sheet): soft-boy lead 10961195698; dancers 8169968523, 8482641605, 8935233157, 8736472562; boys 8504354102, 9548075863, 7134078442, 8957563520; girls 10246329105, 1487690100, 8718570846, 9238004555, 10190740631, 9374822502.
- Watch live: maximise Blender, normal Layout workspace (not single fullscreen), every 3D view in camera perspective + Material Preview, `gfx_kit.show_camera()`, `label()`, `play_steps()`. Never cache area objects across timer ticks (crashed Blender, EXCEPTION_ACCESS_VIOLATION); `gfx_kit.label()` looks areas up fresh. Never save over the open .blend. [2026-10-26]
- Keep a liked mood: owner preferred the first warm rain-heavy preview to my cold relight. [DI3STINY 2026-10-26]
- Full GPU + CPU allowed for renders (`setup_cycles` enables all devices). RTX 4050, OptiX.
- Owner allows any repo and installing skills via the vercel-labs `skills` CLI (`skills find <need>`, `skills use`, `skills add <owner/repo@skill> -g -y --agent claude-code`); read a skill before installing, skip other-engine/paid ones, tell the owner which. [2026-10-27]
- Owner's explicit OK for the concert: full render + post + copy overnight if both gates pass. [2026-10-27] (per-job, do not generalise)
- Owner corrects mid-turn: switch immediately, one-line plan before each new approach.
- Repo library: `C:\Users\Siddharth D\Projects\github-repos\<category>\<repo>\REPO.md` (+ `external-repos`). Useful: earshot (audio ears, .venv), VoiceStudio, lemo-opuscar, hyperframes (HTML->video overlays), soundcraft/filmcraft. CAUTION: open-higgsfield (sends keys to a third party), token-optimizer and billion-context (edit ~/.claude settings). Wait for all clones to finish and read cards before choosing tools. `external-repos`/`github-repos` desktop apps are not useful inside Blender. [door v1, DI3STINY]
- Took "use every repo" literally and wide-scanned the disk for nothing: check the project folder and `~/.claude/skills/blender-*` first, then ask for the repo name.
- Fetching avatars yourself: use the logged-in Chrome (claude-in-chrome tools); the built-in browser pane is NOT logged in ("Invalid authentication data"). Never ask the owner to fetch JSON by hand.
- Owner rated the 51 s hackathon edit 4/10 where my trait checklist said 7-7.5: checklists measure structure, not feel. [2026-10-22]

## 2. GFX camera & framing

- Classify the shot from 3+ clues (selfie / tripod / mirror). Selfie: lens at the phone hand, near shoulder/sleeve fills a corner, arm leaves the frame edge, head ~45-60% of width, lens 14-20 mm. [garage]
- Solve elevation, azimuth, pitch, roll, lens, distance from floor/wall lines and head size and assert (e.g. elevation 38-62 deg). A 2D-only target search ended side-on (el 9, az 87). [garage v5]
- Describe the head by face-to-camera angle (dip, turn, roll), not bone directions; verify the face is visible.
- Match head size/eye line as fractions of the frame; draw a grid on the reference (`gfx2d.py grid`) and a 10x10 frame map (what each cell holds; every edge-touching part must touch the same edge).
- Hand visible when it should be out of frame = camera too far; crop tighter. [garage follow-up]
- Seated shot cut at the shins needs `frame_head(head_frac~0.3)`; 0.2-0.24 shows the whole body and an empty floor band. [DI3STINY]
- Chibi: head-dominant close shots, ~0.3 head frac; tall frames shrink a 1.25 m doll. [haunt]
- Camera sees a seated figure's face only if the monitor/target is on the camera side; rotate the chair or turn the head ~60 deg. [gamer]
- Over-the-shoulder from behind a big-head/back-accessory character hides the other head; shoot from the other side with a sideways offset. [door]
- Wide sign/prop: projecting the centre is not enough, size it (~40% width) and check both ends and that it does not cover the head. [Bio]
- Wall props behind the head read as blocks growing out of it: project against the head silhouette. [skate]
- Camera 4 m from a train 3 m behind a chibi = giant train: place far back, wider/lower frame so several doors show. [subway]
- Show the thing the owner will name: calibrate world X to screen X with two known points (0.099 W/m), put nose, body and windows all inside the frame. [bullet train]
- Mirror props knowing the camera looks along -Y: image-right = world -X. [pumpkin]
- `k.project()` returns y=0 at the TOP; solve prop x/z with it, do not guess world coordinates. [bus stop]

## 3. Pose

- Per-part plan first; presets via `gfx_kit.apply_pose` (idle, selfie, hip, mirror, peace, cross_arms, lean, sit, point, shy, look_up, action) then `aim()` fine-tune. For selfies `style_garage_v4.stage_selfie` searches arm dir/lens/roll.
- `k.aim("Head", up, hint)`: first vector is UP, hint is FACING; swapped = back of hair. [gamer]
- Test the doll arm's range before planning a wave; have a fallback. Doll hands are blocks: wave = mitten, face the flat side to the camera (hint (0,1,0)), no rock-on prongs, no finger poses (say so up front). [Suhaa]
- Chibi has no forearm mesh; skin layered clothing to bones (`skin_clothes()`, `build_exact_gfx.py`) or limbs go missing and hands float. Check the whole body every preview. [garage v5]
- Hands follow the forearm unless the reference bends the wrist. Forearms straight forward read as holding cups: seated, rest forearms on the knees, hands angled ~0.3 inward. [bus stop]
- Chibi arm reach is only ~0.43 m from the shoulder: keyboard at the lap edge, use the desk-side arm (.P = +X). Pick the gesture arm on the camera's side. [gamer v2, door]
- Seating: measure the lowest point of LowerTorso + both UpperLegs (`low()`) and put THAT on the surface top (+0.003); print each part's low point. Ledge front just behind the measured knee y. Shin dir (0,-0.85,-0.52) tucks feet for hugging knees. [rooftop, skate, window seat]
- Chibi good poses: selfie close-up, hand on cheek, hugging knees, peeking, lying; avoid full-body action and wide shots. Classic: ledge, lean, pockets, mirror. Tall: walking, action, back-to-camera.
- Baggy-pants seated reads as boxes and fist-over-knee as a cup: pick a pose showing face/scarf with legs cropped. [rooftop]
- Laptop/prop lid must not cover the face: pelvis ~0.62 m, lid <= 0.27 m tall. [hacker]
- Held props (`Handle3` bag) can clip through a lap: hide them. Never hide a `Handle` without listing its dimensions/material (hid her scarf). [window seat, rooftop]

## 4. Set & props

- List every visible object in the reference and tick it off (boxes, posts, braces, fences, lights, corners). Raycast props onto the floor at their frame positions.
- Prop clears the subject: clamp roofs to above avatar top + 0.35; set `visible_shadow=False` on overhead set pieces; check subject brightness after adding anything above/beside the key. [bus stop]
- A pole ends under its panel. Big flat panels behind the subject dominate; drop them or give support.
- Real-world signage: clean static sans (Bebas Neue, dark ink on a light panel). Never variable fonts (`Montserrat[wght].ttf`: "B"/"P" vanished); zoom-crop text in a test render. Neon text default rot (90,0,180) for a camera on +Y.
- `gfx_kit.plane(rot=...)` and `cube(rot_z)` take DEGREES. Check plane normals (`matrix_world.to_3x3() @ (0,0,1)`) face the camera; screen planes ~3 cm in front of the bezel. Flat floor text needs rot z=180. [Suhaa, gamer, door]
- Skyline: ONE bmesh mesh (3000 `bpy.ops` cubes froze Blender 10 min), 90-260 m away, tops mostly below roof eye line, varied roofs/antennas + haze; `obj.dimensions` is stale after `scale`, use your size variable. World-gradient from Generated coords stayed black; an emissive gradient plane behind works. [rooftop]
- Train = silhouette: lofted superellipse nose (bmesh, scale ~u^0.62), white body, two blue stripes, cab window, window rows between door pairs, carriage gaps, dark skirt; stripes via texture/vertex colour not stacked cubes. [subway]
- Skateboard = popsicle deck with trucks, axles, bevelled wheels (`build_board`); cube = slab. [skate]
- Graffiti: soft spray clouds + grime over real concrete, not zig-zags (stock-chart look). No tags/words.
- Rain: one mesh, 2200 streaks, 1.1 mm, strength 0.25, alpha 0.25; none within 1.3 m of the lens; dense rain + haze sells it (3500 x 2.5 mm looked like snow scratches). [bus stop, Bio]
- Fog/mist: low density (<=0.3), fade with height (Generated.z power curve), never expose a volume's top; camera outside dense boxes. [haunt]
- Veils/ribbons/translucent sheets read as slabs or light pillars; sculpt real folds or drop. Leaves: tiny and few or alpha cards; ember dots warm and low strength. [haunt, pumpkin]
- Pumpkin/lantern: hollow carved 3D pumpkin with interior light, flame sphere + warm point light (~0.5-1x scaled), lantern glass emissive ~2.5 only, brass dark metal. Moon = 3D disc/sphere without a seam. Trees = sapling/gnarled with roots, not cylinders; tombstones bevelled with displacement. [Halloween 2026-11-02, master prompt]
- Many small things: build only what the camera sees (project first, count, then build). [concert 520 fans]
- `k.clear()` matches the whole name before the dot ("Dump" never removed "Dumpster"); use exact names or "not in keep set". Set render engine explicitly before each preview.
- `gfx_kit.show_camera()` crashed in Blender 5.2 (shading "MATERIAL" invalid): use RENDERED/SOLID.
- Stray untextured `Plane` washed the floor white two renders; run `clean_stray()` / list meshes without material.

## 5. Lighting

- Match the reference light ratio: brightest spot, shadow darkness, falloff. Moody = low ambient + one soft source. `light_preset(name)` has 12 presets placed relative to the camera.
- Clay (Workbench) light check matching the luminance map before materials. Look at the first render for the subject's brightness, and check hair is still black.
- Lit pastel scenes blow out: exposure ~-0.35, key ~380 W for a 2 m window (not 900). Fog scenes: moon backlight 600-1500 W (5500 W washed white), world strength ~0.1.
- Night scene: PorchFill 35 W cool, window emission 0.35 (120 W / 2.2 = daytime). [door]
- Lit panels: base black + emission <=1.5 or AgX blows white/peach; emissive windows ~2 warm (9/3.5 = white slabs); keyboard emission 0.5; screen-glow lights start ~7 W (38 W blew face/hair grey). [bus stop, subway, hacker]
- Light cues: hold key before each flash or CONSTANT interpolation (ramp 0 -> 30000 over 4 s washed a section white). When the lens changes (64->85 mm) re-check exposure on stills (mean luma ~110-125) and dim emissive screens/beam pops. [concert]
- Tri-tone option for Halloween: amber #FF7A00, violet #9D00FF, midnight #0B0416; dual-tone separation, rim highlights, god rays. [master prompt]
- Moon rim on hat/hair; accent colour (red) as a practical; black-and-white avatars get one strong colour in the set.
- Front point light inside a pumpkin washed face/skin to flat peach; keep face emission strong. [pumpkin]

## 6. Materials & textures

- Real PBR textures from `library/textures` at real scale with a dirt/wear layer; procedural streaks read as wood (wall looked like planks). Check fine detail (Laplacian) vs reference. Image textures on scaled cubes smear: gfx_kit `pbr()` now uses Box projection and `solid()` applies scale; check at 50%.
- Hair too grey/brown from light + bright texture: multiply the hair material (Handle1Mtl) ~0.3 grey and lower specular before dimming the scene.
- Legs in light-grey cargo pants read as pale tubes: own material copy, multiply ~0.4, wave-texture crease bump, low specular. [skate]
- Clothing normal/roughness from flat Roblox PNGs (Pillow/numpy high-pass -> normal, master prompt recipe); SSS skin and anisotropic hair are optional upgrades.
- Pale text on pale background unreadable: hot-pink face + dark berry (0.42,0.04,0.2) thick-bevel copy ~0.55 scale.
- Avoid moire on fine meshes (fences).

## 7. Grade & post

- Grade by numbers (`gfx2d.py grade REF RENDER OUT --auto [--mask m.png]`) with the avatar mask (`render_mask`), keep character colours close (delta-E gate). With no reference a gentle custom pass: bloom 0.15-0.18, contrast 1.08, vignette 0.35-0.4, grain 0.012-0.014, sat 0.7. Render as its own reference crushed it dark/red.
- `--levels` is Lab L units 0-100 (0.04,0.97 made a white image). View the result before calling it done.
- Bloom threshold >= 0.65, strength <= 0.3 for faces (0.45 = white blob). Glitch bands by hand off the face band (y 330-720 of 1080).
- Calm/kawaii themes: glow <= 0.12, no sparkles; flat 2D typography `tools/caption.py IN OUT` (Pacifico + letter-spaced Montserrat SemiBold, rose (206,84,124)). 3D extruded text only for bold/loud styles (Pacifico, extrude 0.035, bevel 0.012, outline copy at -Y).
- `gfx2d post --text-pos` is the text CENTRE (use ~0.25 for left caption); `--sparkle-at` is nargs="*": all spots after ONE flag; place sparkles by hand.
- Motion blur kernel must be longer than the features (700+ px for a train); blur only the body, keep the nose crisp.
- Night/blue-hour post: `tools/post_night.py`. Reference stats to copy: tint, saturation, vignette, grain, black/white points.
- Give the owner the preview-then-grade order explicitly ("preview, grade comes after") and send the graded image.

## 8. Tools & commands

- Folder tools: `bl.py` (socket client, 127.0.0.1:9876, null-byte JSON `{"type":"execute","code":..,"strict_json":false}`), `fetch_avatar3d.py meta.json out_dir`, `build_exact_gfx.py` (prepend `AVATAR_DIR`, `POSE`; armature `Avatar`; P = +X right; leaves `Halo`+`Backdrop`), `gfx_kit.py` (poses, `frame_head`, `selfie_camera`, `measure/project`, props `pbr/cardboard_box/chain_fence/post/mirror/neon_text/led_strip/bokeh_lights/import_model`, `light_preset`, `world`, `setup_cycles`, `render`, `render_mask`, `clean_stray`, `clear`, `skin_clothes`, `show_camera/label/play_steps`), `gfx2d.py` (`grid`, `compare REF RENDER DIR`, `grade`, `post`; run `python -I`), `halloween_kit.py` + `run_halloween.py`/`run_haunt.py` (Halloween scenes; style_haunt/pumpkin/lantern), worked examples `style_*.py` (latest garage `style_garage_v6.py`), `cache_avatar.py`, `user_sheet.py`, `caption.py`, `make_screens.py`, `make_graffiti.py`.
- Each round: `gfx2d.py compare` and read report.txt BEFORE viewing images (cheaper); it writes side-by-side, 50% blend, edge overlay (red ref, cyan render, white match).
- `tools\bin` portable apps: `realesrgan\realesrgan-ncnn-vulkan.exe -i in.png -o out.png -n realesrgan-x4plus` (models realesr-animevideov3 default, x4plus, x4plus-anime; `-s 2|4`; tile stitching can leave block seams); `photocraft\photocraft-cli.exe`, `lightcraft\...\lightcraft-cli.exe`, `effectcraft\...\effectcraft-cli.exe` (portable CLIs, READMEs next to each; run `--help` first, I did not verify their flags). The earlier "photocraft/lightcraft/effectcraft need a Rust build, Real-ESRGAN not installed" note (haunt 2026-11-02) predates these binaries: check `tools/bin` first.
- Check a repo's REPO.md "installed?" before promising it; gfx2d already covers grade/glow/grain.
- Pipeline that ran clean: Chrome fetch avatar-3d -> `fetch_avatar3d.py` -> `build_exact_gfx.py` -> `style_<name>.py` stages (avatar, pose, set, light, camera, text) via bl.py; scripts in the scratchpad dir; outputs `gfx_output/<username>/`, references `gfx_references/<username>`.
- Preview loop: Workbench 40% (pose/framing), Cycles 50% @48 samples (light), 100% @160 (final). Deliver 100% Cycles GPU + PNG + .blend copy + side-by-side + per-part rating.
- avatar-3d answers `Pending` first: reload until `Completed`, then fetch `imageUrl`. Public 720px render: `thumbnails.roblox.com/v1/users/avatar?userIds=<id>&size=720x720&format=Png`.
- Fixed stage order: camera -> pose -> layout -> clay light -> materials -> masked grade -> post, with scene lint (stray meshes, missing materials, floating hands, moire) before each render. Planned-but-unbuilt tools (ask before building): spec.json + solve_camera, camera_assert, frame-map checker, pose/view assert, clay luminance gate, place_at_frame, scene lint, grade auto-tuner, richer compare.
- Installed Blender skills: blender-shader-nodes, -compositing-nodes, -scene-rendering, -animation-rigging, -lighting, -materials, -motion-state-inspection, -polyhaven-*, camera-move skills (slow-zoom, turntable, crane-shot, dolly-rotate, perfect-loop).
- Style playbook table lives in `gfx_references/PLAN.md` section 2 (selfie, mirror, portrait, night, comic, action, room, showcase, Y2K flash, horror, street, thumbnail); vibe->setting starters are in roblox-gfx-ideas.

## 9. Blender & Windows gotchas

- Blender 5.2: `show_camera` shading enum; hidden objects keep a stale `bound_box` (read mesh vertices or before hiding); Data Transfer UV writes a new layer unless dst layers are removed; ClassicMannequin.fbx parts carry FBX animation + parent inverse (`animation_data_clear()`, reset before parenting).
- Combined stage+render in one bl.py call crashed Blender; long bpy.ops loops hit the socket timeout.
- First Workbench preview silently rendered with Cycles (engine left on CYCLES) with old leftovers: set engine, list objects.
- Check the live scene before building: it had silently switched projects. Back up with `save_as_mainfile(copy=True)`, assert the armature is the right avatar. [Bio]
- PowerShell: `Set-Content -Encoding utf8` writes a BOM that breaks bl.py exec; unbalanced parentheses in a -match regex silently killed a search; a long bash call with two heredocs + python -c wrote nothing. Use the Write tool, new file names, short calls.
- Windows paths: `sed`/raw-backslash strings in Python mangled paths (use Edit); ffmpeg on git-bash `/c/...` paths with Korean text failed (use `cygpath -w`); chain dependent steps with `&&` not `;`.
- Background run lost scripts in `$TEMP`: use the scratchpad dir, run bl.py in the foreground.
- Big multi-replace patch aborted on one stale string and skipped the check: print missing keys, patch by line number.
- Killing a render chain mid-way let the post step overwrite Downloads/suhaa_concert.mp4 with a 7-frame video: chain post/copy with `&&` on a frame-count check, kill the whole shell job.
- Browser tooling: javascript_tool output truncates ~1000 chars (store in `window.X`, read in slices); roblox.com CSP blocks POST to localhost; Chrome blocks posting to 127.0.0.1 from https, CDP calls time out at 45 s, one download per call; single-threaded http.server hangs (use ThreadingHTTPServer); JS fetch of assetdelivery is blocked, navigate + get_page_text works.
- Batch independent tool calls (browser_batch) to save round trips.
- Headless Blender (own process, no clash): `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe -b --factory-startup -P script -- args`; pattern `build` (saves scene.blend) -> `stills f1,f2` at 50% -> `frames a b` in background. Run builds in background; check usage before multi-hundred-frame renders.
- Two avatars in one scene: `build_exact_gfx` wipes the scene, so build A, `bpy.data.libraries.write` to a temp .blend, build B, rename both armatures, append A.
- Roblox exports: avatar space +X right, +Y forward, +Z up; hair/accessory exports in studs (scale head_width/1.2); cached avatar_cache exports in studs: scale 0.28; Roblox full-size ~5-6 m tall vs 1.4-2 m stage avatars: print every armature's world bbox height before any crowd shot. Catalog clothing 3D exports = R6 dummy facing -Y with grey body colour baked opaque; classic face assets have no 3D thumbnail (use 2D png). `cache_avatar.py` fails rig assertion on ~1 in 3 exports: keep 1-2 backups.
- Reveal keyframes un-hid builder-hidden accessories (speech bubble): only key objects visible at build time. Key `hide_render` for "out of the dark" reveals.
- Finding styled avatars: user search mostly gives defaults; friends lists of a good avatar (friends.roblox.com/v1/users/{id}/friends) give similar ones. Downloading from YouTube is not done: ask for the audio/video file.

## 10. Animation (motion, choreography, audio, subtitles, voices)

- Owner standard: voices on every spoken line, real SFX, plain subtitles, no title card, night ambience not music unless asked, natural non-stiff motion, keep each character's personality (Bio cool: pocket hand, hip shift, lean back, chin up, slow swagger; Suhaa kind: hands together, head tilt, open-arm welcome). [door v1 rejected 2026-10-26]
- Motion: owner finds retargeted Roblox default clips (rbx_anims, anim_motion clip layer) look weird: animate procedurally with eased acting poses + breathing, idle sway, weight shifts, head micro-moves, overlapping arms, hip bob and planted feet in walks, anticipation, head bobs on voice lines. Check a low-res draft as frame strips for freezes. (The door v2 note on Roblox animation ids 507777826 walk / 507766951 idle / 507770239 wave / 507770453 point / 507767714 run and `rbx_anim_json.py` is kept for reference only.)
- aim() directions are in armature space (+Y = facing); key every bone at each pose key so poses never leak. Camera cuts with timeline markers (`marker.camera`).
- Dance/choreo: designed KEY POSES on beats/half-beats with auto-clamped Bezier between (a tracked video track keyed every frame = "seizure"). Light smoothing only (r~2), exaggerate tracked shapes ~1.2x, cap ~20 deg/frame, key every ~2 frames, "smooth != small" (r=4 + 12 deg cap = no dance). Offset child keys: UpperTorso +1, Head +2, UpperArm +2, LowerArm +3, Hand +4 frames. Snap feet only on keys; bounce via knee bend lowest on the downbeat (no per-frame |sin| bounce).
- Carry each bone's previous side axis forward (parallel transport) and sign-match quaternions to stop 180 deg roll flips; explicit hints only for torso/head/feet. Wind-ups >= 0.3 s before hits; pose->track blends >= 0.5 s, grooves >= 0.7 s before a hit pose (0.25-0.4 s snapped forearms; check measures WORLD rotation).
- Gates before ANY render: `anim_concert3.py check` (jitter 0 frames over 30 deg/frame, max deg/frame buckets), similarity per-bone cosine vs tracked reference >= 0.55 mean (concert reached 0.974), mean arm deg/frame in the chorus for amplitude, 5-10 low-res beat stills (start, reveal, mid, hit, end), then render.
- Align reference footage to the song (mel/onset features, 3 s windows, same offset in every window, check runner-up, confirm visually in the browser); chroma confuses repeated choruses (landed on the 2nd chorus). Practice uploads differ in offset (Fix ver +4.19 s, mirrored +0.35 s); map times per video and state confidence. Measure beats with librosa on the actual audio (do not assume 120 BPM). Do not reuse an 11.9 s choreo for a different song section; say so and ask for matching footage. Mirrored clips: hflip then track (`track_one.py` MediaPipe heavy single-dancer with moving crop, sigma 1.2, resample 24 fps; multi-person failed; `choreo_from_track.py`, `choreo_join.py`). Do not claim a similarity % unmeasured.
- Plan a freeze pose landing ON the final hit, ~1 s hold and a 1 s audio fade; never cut the song mid-phrase.
- Story length/pace: 12 s for a whole story was unreadable; use 20-25 s (32 s approved), hero entrance ~10 s (silhouette -> slow walk -> hero pose on a downbeat). Walk 80-95 steps/min, step ~0.6x leg, one foot down, small pelvis bob. "Comes out of the dark" literal: invisible until lights down.
- Formation: nobody directly behind the hero within ~1.2 m in x (or >= 2 m back); check through the camera. Chorus line <= 5 m wide at ~80-85 mm from ~16 m (64-70 mm with 6 m = dancers 1/4 frame).
- Crowd camera 6-12 m behind the front row, 3.5-4.5 m high, 50-85 mm; fan heads in the bottom 10-25%. Look: motion blur ON, close/medium shots, shallow DOF, soft rim + key, cloth sheen; far camera + harsh light looked cheap vs the Ink Game Roblox reference (youtu.be/hCnsaahr2cc, the owner's smoothness bar).
- Render: EEVEE 1920x1080 @48 samples ~2.5 s/frame at 50%; ffmpeg `-crf 17 -preset slow -pix_fmt yuv420p -movflags +faststart`; moviepy 2.2, OpenCV 5 installed.
- Voices: `edge-tts --voice en-US-AndrewNeural --rate=-8% --pitch=-6Hz` (cool male) and `en-US-AvaNeural --rate=-4% --pitch=+2Hz` (kind female) won `earshot rank` (make 3 variants each, `earshot match`); put each line's real length in voice/lengths.json and re-time the scene. VoiceStudio is local alternative.
- SFX: real recordings only (`library/sfx/kenney_rpg`, `kenney_impact`, CC0). Ranked picks: footstep04/06/09 (porch), footstep_carpet_003/004 (inside), impactWood_medium_002/003/001 (knocks), doorOpen_1 + creak1, doorClose_1 + low-passed doorClose_4. Crickets: Wikimedia `Crickets_choir.ogg` (CC BY-SA 4.0, credit in `library/sfx/ambience/CREDITS.txt`). Numpy-synthesized SFX sounded fake (early notes listing numpy/scipy synthesis as a "tool that worked" are superseded).
- Mix: RMS-level each sound (knocks ~-21 dB RMS, steps ~-30, voices -17), final ~-16 LUFS with tanh soft clip at -1 dBFS; `earshot timeline video.mp4`, `earshot critique`, `earshot realness` (0.88 = real). First mix had knocks at -1 dBFS and film at -22 LUFS.
- Subtitles: plain white text, thin dark outline (stroke ~2.5 px) + soft shadow, bottom centre, Montserrat 600 (`tools/anim_post2.py`); italic grey sound captions like *[knocking]*. No chat bubbles, frosted pills, name chips. Pillow + numpy vignette.
- Extra characters stay normal avatars; do not over-engineer ("just make it normal... street wear... men only").
- Wait for the owner's audio/footage; ask before assuming what a screen in the scene should show (Discord needed a login; owner preferred a real Cortis frame).

## 11. Budget / usage

- Cap history: 98% (skill/START_PROMPT) vs the owner's tighter 70% 5-hour cap set 2026-10-26 (earlier 95/90/85). Use the tightest the owner stated most recently. Call `get_usage` before every step/render and post "Your limit is now at X% (weekly Y%)"; an estimate was once 11 points off.
- Stop starting new work near the cap and leave background jobs in a safe state; say what is left. Weekly 96% once deferred the Nico tuning items.
- Cost savers: no trial-and-error loops, compare report.txt before images, low-res stills before long renders, build only what the camera sees, count before building.
- Typically 3-5 render rounds per style; do not send a first draft as final.

## 12. Reviews (Opus review vs the owner's references)

- Get the owner's OK first (idea -> ask -> review). Then run the Opus review against only the owner's reference pictures before presenting renders; late "ask Opus" request was a mistake. [Halloween 2026-11-02: pumpkin 4/10, lantern 5/10 before round 2]
- Avatar vs reference mismatch (hair, outfit, body type) flagged in one line at the start; do not change the avatar. Say non-replicable items up front (hand-painted art, block-hand fingers, expressions, the avatar's own hair).
- Self-score each part (camera, pose, background/props, lighting, grade, post) out of 10 with the rubric: 10 indistinguishable except avatar; 8-9 offsets <5%; 6-7 visible camera/pose diff or missing prop; 4-5 several big differences; 1-3 wrong framing/light/set. Total = lowest part + 1; <7 gets another round or is named honestly as unfinished. Owner rates 2-3 lower (gave 3/4 where I thought 7).
- Judge no-reference work against the concept's own spec, part by part.
- Opus review rules: camera solve + assert, face-to-camera head angle, 10x10 frame map, fixed stage order with clay preview, real-scale textures with dirt, masked grade, scene lint.

## What worked (Suhaa_Official window seat, keep doing)

- Pipeline that ran clean: Chrome fetch of avatar-3d -> `fetch_avatar3d.py` -> `build_exact_gfx.py` -> `style_<name>.py` stages (avatar, pose, set, light, camera, text) run through `bl.py`, scripts kept in the scratchpad dir.
- Seat a chibi by measuring pelvis and foot lowest points (`low()`), raising the avatar so the lower one sits on the cushion. Shin direction (0,-0.85,-0.52) tucks the feet near the hips for hugging knees.
- Doll hands are plain blocks: face the flat side to the camera (hint (0,1,0)).
- Hide the stage `Halo`, `Backdrop` and the held bag (`Handle3`) that clips through a seated lap.
- Soft pastel look: emissive window pane with colour-ramp gradient (peach -> pink), exposure about -0.35, one warm key through the window, weak pink fill and rim, bokeh spheres just in front of the pane, squashed-sphere plushies with ear spheres.
- Lit pastel scenes blow out fast: start key near 380 W for a 2 m window, not 900.
- 3D text in Blender: `Text` curve + Pacifico font, extrude 0.035, bevel 0.012, pink glossy (coat) material, white offset copy behind as outline; rotate (90,0,180) for a +Y camera, place by projecting to the frame. (For calm themes prefer flat 2D `caption.py`.)
- Preview loop: Workbench 40% for pose/framing, Cycles 50% @48 for light, 100% @160 for the final.
- Calm theme: glow <= 0.12, no sparkles; let text carry the message.
- No "photocraft" existed in that session (it is now in `tools/bin`); the 3D-vs-2D typography decision above supersedes it.

## Contradictions between sources (resolved here)

- Usage cap 98% (skills, START_PROMPT) vs 70% (memory): use the owner's latest stated cap.
- Roblox default clips as "what worked" (door v2) vs "no rbx motion clips" (owner, concert): do not use clips.
- Numpy-synthesized SFX listed under tools that worked vs owner rejected them as fake: use Kenney recordings.
- 3D text "beats 2D" vs 2D for calm themes: 3D for loud styles only.
- Ask the owner for a score (pipeline memory) vs never ask, self-rate (later memory, skill): self-rate.
- "Never ask how it should look" (reference jobs) vs "ask purpose/theme first" (no-reference jobs): ask only the purpose/vibe when there is no reference.
- Photocraft/lightcraft/effectcraft "need a Rust build" vs portable exes now in `tools/bin`.
- Opus review: ask owner before (memory) vs run before presenting (haunt): both, ask first.

## Session log (dated)

- 2026-10-22 hackathon re-render edit (not GFX): owner 4/10 vs my 7-7.5.
- 2026-10-25/26 sttvr_l1ght garage selfie: v1 3/10 (owner), v3 5.5, v4 6, v5 ~5 (missing limbs, white arm block, moire), v6 ~6 (hand-on-cheek chibi, selfie arm left, grey concrete); still weak: empty floor, flat warm wall.
- 2026-10-25 ImmortalNico moody night: 6.5/10; 7 tuning items pending (padded armrest, crossed-arms hunched pose, soft moon glow, star twinkles, cold blue grade, moon rim on hat/hair, tighter camera + blur).
- 2026-10-26 DI3STINY rainy bus stop: v3 self 7/10, owner "it's good, we're done" (`style_busstop.py`).
- 2026-10-26 Suhaa_Official window seat (pastel), candy goth room (wrong theme, Cortis wanted), rooftop blue hour 5/10, glitch hacker room 5.5 -> v2 6, gamer corner ~5, subway/bullet train 4.5 -> 5.5.
- 2026-10-26 Bio_IsHere neon alley (shared-Blender scene wipe incident); Bio x Suhaa door visit animation: v1 rejected, v2 with voices/real SFX (earshot realness 0.88).
- 2026-10-26 Qsi2408 night skate: v1 5/10, v2 ~6.
- 2026-10-27 Suhaa Cortis concert animation: v1/v2 rejected ("seizure", too quick), v3 32 s REDRED plan: jitter 0, match 0.974, full render + post queued to Downloads/suhaa_concert.mp4; owner's similarity gripe (barely 10% vs claimed 55-70%) led to measured gates.
- 2026-11-02 sttvr_l1ght haunting-spirits misty forest: built before pick, chibi scale error, white-wash fog; no final score recorded.
- 2026-11-02 sttvr_l1ght Halloween pumpkin graveyard + autumn lantern: Opus review pumpkin 4/10, lantern 5/10 before round 2; no later score recorded. Owner's master prompt saved at `docs/GFX_MASTER_PROMPT_original.md`.
- Bio_IsHere early Blender build: `README.md` documents rbxm download + procedural shirt/pants (401 for shirt 4944796350 / pants 1068331730).

## 13. Learnings from the owner's master GFX prompt + Opus plan review [2026-11-02]
Owner's quality bar (their listed failures; never repeat): pumpkin = squashed sphere with flat emissive decals; moon = flat disc with a seam/branch line through it; tombstones = sharp featureless boxes; trees = raw cylinders on a bare floor; flat, muddy light with no warm/cool split, god rays or rim; stiff, clipping pose.
Owner's goals to keep: tri-tone palette amber `#FF7A00` / violet `#9D00FF` / midnight indigo `#0B0416`; pumpkins lit from inside through carved holes; beveled, weathered, tilted stones; gnarled trees with roots; real volumetric mist; violet rim on hair/shoulders; 3-5 near-lens leaves for foreground bokeh; S-curve spine and a 6-12° head tilt; a post-flight report of camera, light ratios and nodes.
Verified traps in that prompt (don't copy them blindly):
- `github.com/matthewde/roblox-rig-pack` does not exist. Never clone a repo before `git ls-remote`, and our `build_exact_gfx.py` already rigs R15.
- avatar-3d returns JSON with hashes, not a zip. Use `fetch_avatar3d.py`.
- Sapling and `mesh_extra_objects` are not bundled in Blender 5.2. Build trees in our own kit, or ask the owner before downloading extensions.
- Blender 5.2: Principled uses `Coat Weight` (no "Clearcoat"); the compositor lives at `scene.compositing_node_group` (no `scene.node_tree`); Glare settings are node inputs. Do post in `gfx2d.py`.
- `read_factory_settings` wipes the rigged avatar. Never call it mid-pipeline.
- Don't subdivide, remove doubles, auto-weight or bendy-bone blocky Roblox parts: they turn into blobs. Don't build normal maps from clothing PNGs, since they emboss the printed logos. Keep skin SSS near 0, because it smears the face decal.
- Light watts must fit our scale (avatar ~1.25 m). Start pumpkin/lantern point lights low and tune by face luma, because 100 W+ washes the face out. f/1.8 blurs the whole chibi body, so use f/2.8-4. Use OptiX, not CUDA; 192-256 samples with the denoiser is enough.
- Pumpkin carving: cut the holes in the shell before Solidify (no boolean on a ribbed solidified sphere, which leaves black slivers), with a light at the centre.
- No `pip install` in a preflight without the owner's OK.
Full reviewed pipeline with stage gates: `docs/GFX_MASTER_PIPELINE.md`. Owner's original text: `docs/GFX_MASTER_PROMPT_original.md`.
- **Applied the master prompt's violet palette to BOTH scenes, so everything came out purple** [sttvr_l1ght halloween v2, 2026-11-02]. The owner's references were blue moonlight + orange pumpkins and warm amber. The references beat any palette in a prompt: take the colour split from the reference pictures, and keep violet to small accents unless the refs show it.
- **Graveyard v2 drifted away from the reference (owner: 2/10)** [sttvr_l1ght 2026-11-02]. ref2 has the character large in the left third, leaning on a big weathered tombstone with her hand to her cheek, a huge detailed jack-o-lantern bottom-right, blurred foreground pumpkins with lens flares, crypts and branches, a textured teal moon, cobblestones. Mine had a small seated figure, a plain empty step and few details. Rebuild the reference composition first, then detail every prop.
- Graveyard v3 [2026-11-02]: background stones placed with at_depth 3-5 m at 1.3-2.1 m tall became giant walls hiding the moon; place background props on the ground ray 7+ m back and size them to the frame.
- Graveyard v3: first arm guess put the cheek hand straight over the face; solve the hand tip to a cheek target beside the face (grid search) and check the face stays visible.
- Graveyard v3: camera above head height with head shifted to y 0.23 put the horizon at the top, so every stone covered the moon; for a moon-above-stones ref, put the camera slightly below the head (view_dir z -0.14).
- Graveyard v3: gfx2d grade --strength 0.5 vs ref2 lifted blacks and washed the scene hazy; 0.3 + --sat 1.2 + --levels 5,97 kept contrast.
- Graveyard v3: jack-o-lantern holes cut by deleting sphere faces give stair-step edges and the inner flesh glows flat white; needs bevelled hole rims / knife-cut outlines and lower flesh emission.
- **Used a cached avatar (fetched 2026-10-25) for every sttvr_l1ght GFX on 2026-11-02 while the owner had changed it.** Re-fetch the avatar at the start of EVERY new GFX job (avatar-3d via the logged-in Chrome), compare it with the cache, and pitch ideas from the current look.
- Spirits v1 [sttvr_l1ght new avatar, 2026-11-02]: avatar floated ~0.3 m because I grounded it with object bound_box (stale/rest pose); ground it from evaluated mesh vertices. frame_head on the long-hair head_obj gave dist 8.7 m (tiny figure): for long-hair avatars place the camera at a fixed distance and only solve lens shift. Spirits placed by world guess landed off-frame: place by frame x + depth along the camera ray.
- Spirits v1: emission+transparent cone spirits read as solid bowling pins with a fresnel outline; volume-emission noise smoke reads as ghosts. Head "glancing back" toward the camera side still hid the face behind the long front hair: turn the head to the lens and add a small face key. Moon-shaft spots in thin height-faded fog stayed invisible even at 90 kW.
- Spirits v2 (Opus review 3/10 on v1): a uniform 0.012 volume for moon shafts washed the whole frame grey (0.004 ok, still no shafts); camera at 2.5 m/85 mm on a 1.5 m avatar = head 55% of the frame and the raised candle covered the face (3.5 m + candle at chest height worked). Still open: pine trees with needle cards, spirits with readable shoulders, visible god rays.
- Spirits v3: pine tiers starting at 22% height cut the spirits' heads off (raise the first tier to ~42% or keep pines behind the spirits). Moon spots never showed through fog; a volume-only cone along the beam (density 0.05, self emission 0.3) finally made a visible shaft. Spirits read as figures only once they had a shoulder ellipsoid + head and a noise ramp of 0.3-0.6.
- Spirits v4 [2026-11-02]: real Poly Haven forest assets (tools/fetch_assets.py, tools/forest_kit.py place() linked instances) + avatar textures 2x upscaled with realesr-animevideov3 (alpha kept, avatars/<user>_hd, run with GFX_AVATAR) lifted the set; pine_tree_01 at 2k is 937 MB, so use linked copies only. Leftover: a moss/fern patch under a spirit glows lime green; tint or drop moss inside spirit volumes.
- Spirits v5 -> v6 (Opus 3/10 on v5): spirits read as white laundry bags until coloured saturated cyan (0.2,0.85,1) with lower density (x1.8) and a 10-15 deg lean; the beam cone right behind her became a glowing white pillar (no beam volume behind the subject); grade --levels 10 left milky blacks, 18 + sat 1.25 fixed it; candle 14 W was invisible, 40 W reads. Green hem glow under the front spirit is cyan spirit light on ferns: keep ferns out from under spirits.
- Spirits v6 [2026-11-03]: shipped a 6.5/10 with the face fully hidden by long front hair; owner: "where is her face". Check the face is visible before presenting. Fix: `part_hair()` in style_spirits.py deletes hair faces in a box in front of the face plate in rest pose (middle 62% width, chin to 78% height) -> blunt fringe, face reads.
- Spirits v7 [2026-11-03]: owner wanted the "torch under the chin" face but the candle kept at the chest. Moving the hand to the chin was wrong (owner: don't raise it). Fake it: hidden warm area light (visible_camera False) 5 cm under the chin aimed at the head; 3 W at that distance flattened the face, 1.1 W gave the warm-below / dark-brow horror look.
