# Plan for 10/10 Roblox GFX

Scores so far: garage 3 → 4 → 5.5, Nico night 6.5. The pattern: I guessed the camera, lit everything too evenly,
left out props, and only compared by eye at the end. A 10 means that, laid side by side, the only differences are
the ones Blender can't change (the avatar's own hair, outfit and face).

## 1. Workflow for every reference

1. **Name the style.** Match the reference to a style in the table in section 2. That gives the starting camera,
   lighting and grade. Most references mix two styles; note both.
2. **Measure, don't guess.** Load the reference as the camera's background image at 50% opacity and draw a grid
   over it. Measure and write down:
   - **Head size:** head width ÷ frame width, and the eye line's height in the frame.
   - **Feet:** where they are, or whether they're cropped.
   - **Horizon:** where the floor meets the wall, and where lines converge. This sets camera height and tilt.
   - **Lens:** strong perspective (big near parts, converging lines) means 14–24 mm; flat means 50–85 mm.
   - **Depth of field:** how blurry the background is.
   - **Light:** where the brightest spot is, which side the shadows fall on, and whether the rim light is on the left
     or right.
   - **Edges:** everything that touches the frame edge (sleeves, props, cropped hair).
3. **Pose by overlay.** Pose each limb until its outline sits on the reference's outline: torso, head, upper arm,
   forearm, hand, legs.
4. **Build the set** from the prop list (tick every object in the reference). Use real textures from
   `library/textures`.
5. **Light to the reference's light ratio.** Compare a greyscale version of both images. The darkest and brightest
   areas should be in the same places at similar levels.
6. **Grade by numbers.** Copy the reference's colour statistics (Reinhard colour transfer in Lab space), then add
   bloom, grain and vignette at the reference's strength.
7. **Compare each round.** Make a side-by-side and a 50% blend of render and reference. Score each part, fix
   anything under 9, and repeat until every part is 9 or above, or the budget runs out. Record the self-score
   honestly; the owner rates 2–3 points lower.
8. **Do 2D post work last.** Real Roblox GFX artists finish in Photoshop. I can do the same in Python:
   - glow on light sources;
   - light leaks;
   - sparkle and star overlays;
   - chromatic aberration;
   - smudge and paint softening on hair edges;
   - text.

## 2. Style playbook

| Style | Camera and zoom | Pose | Background and props | Lighting | Colour grade |
|---|---|---|---|---|---|
| **Selfie (high, wide)** | Lens 14–20 mm, close (head 45–60% of width), high, looking down, 5–15° tilt. Selfie hand out of frame, sleeve in a corner. | Leans into the lens, head tilted toward the camera arm, other hand on hip, cheek or a peace sign. | Real place seen from above: garage, street, bedroom floor. Props from the reference. | One soft source from above or the side, low fill, cool rim. | Slight desaturation, grain, vignette, deep blacks. |
| **Mirror selfie** | 24–35 mm at chest height, straight on. The phone held in front of the face is visible. | Hip pop, one knee bent, phone hand up, free hand in a pocket. | Mirror frame, bathroom or bedroom, clutter, posters, LED strips. | Ceiling light plus LED colour from the side, phone flash optional. | Warm, or pink and purple from the LEDs, slight bloom. |
| **Close-up portrait** | 85–135 mm, head and shoulders, eye level or slightly high, f/1.4–2 (strong blur). | Small head tilt, hand near the face, looking at the lens or away. | Bokeh lights, flowers, sky or plain gradient; little detail. | Soft key at 45°, strong rim, catchlights. | Pastel or teal-orange, soft contrast, glow. |
| **Night and moody sky** | 35–50 mm, waist up, slightly low. | Leaning, arms crossed, sitting on a ledge, looking up or away. | Night sky, moon, stars, city lights, rooftop. | Cold moonlight rim, very dim fill, warm practical light optional. | Blue, lifted or crushed blacks, bloom on the moon, sparkles. |
| **Comic and sunburst** | 35–50 mm, full or 3/4 body, centred, straight on. | Big pose: jump, point, fist up, wink. | Sunburst rays, halftone dots, speed lines, outline. | Flat front light, hard shadow. | Saturated primary colours, high contrast, thick outlines. |
| **Action and VFX** | 18–28 mm, low angle, dynamic tilt, motion blur. | Mid-attack: lunge, swing, cast, hair and cloth flying. | Arena, ruins, sky. VFX: slashes, sparks, smoke, energy. | Coloured key from the effect, strong backlight, volumetric beams. | Teal-orange or the effect's colour, heavy bloom. |
| **Room and lifestyle** | 24–35 mm, eye level or seated height. | Sitting on a bed or desk, gaming, holding a drink or plush. | Detailed room: fairy lights, posters, plants, monitor glow. | Practical lights (lamps, screen), warm. | Warm, soft, slight haze, film look. |
| **Outfit showcase** | 50–85 mm, full body, eye level, centred. | Neutral or model pose, weight on one leg. | Studio cyclorama or simple gradient. | Three-point: key, fill, rim. | Clean, neutral, high clarity. |
| **Flash and Y2K** | 28–35 mm, eye level, direct on-camera flash. | Candid: peace sign, tongue out, hand over the mouth. | Party, bedroom or street at night; dark behind. | Hard flash from the lens, hard shadow behind the subject. | High contrast, bright skin, crushed blacks, timestamp text. |
| **Horror and grunge** | 18–35 mm, low or Dutch angle. | Stiff, head tilted, hiding, crawling. | Dark corridor, fog, chains, blood or grime. | Light from below, single red or green light. | Red or green tint, heavy grain, vignette, chromatic aberration. |
| **Street and car** | 24–35 mm, low, 3/4 view. | Leaning on the car, crouching, hands in pockets. | Wet asphalt, neon signs, car, reflections. | Neon colour key, reflections, rim. | Cyberpunk teal-magenta or warm sodium orange, glow. |
| **Thumbnail and logo** | 24–35 mm, close, slight wide distortion. | Exaggerated pose, shocked face, pointing. | Bright gradient, icons, big text, white outline around the character. | Bright and even, strong rim. | Very saturated, high clarity, glow outlines. |

**Zoom rule:** anything cut off by the frame in the reference is cut off in mine. Size the head first, then set
the crop.

## 3. Tools (built 2026-10-26, tested on the garage scene)

**`tools/gfx2d.py`** (run with `python -I`):

| Command | What it does |
|---|---|
| `grid REF OUT` | Labels a 10×10 grid on the reference, so positions can be read as fractions. |
| `compare REF RENDER DIR` | Writes a gridded side-by-side, a 50% blend and an edge overlay (red = reference, cyan = render, white = match). The report lists the edge-overlap score, exposure, contrast, black and white points, tint, saturation, vignette, grain and brightness by region, plus fix hints. |
| `grade REF RENDER OUT --auto [--mask m.png]` | Copies the reference's colours (Lab colour transfer), then adds the vignette and grain automatically. `--mask` keeps the avatar's own colours, such as black hair. Also takes `--bloom`, `--ca`, `--grain` and `--vignette`. |
| `post SRC OUT` | Adds `--glow`, `--sparkles N` or `--sparkle-at x,y,size`, `--leak r,g,b,corner,strength`, `--outline mask.png` (white outline around the character) and `--text` (fonts from `library/fonts`). |

**`tools/gfx_kit.py`** (import inside a Blender style script):

| Area | Functions |
|---|---|
| Poses | `apply_pose(name, mirror)` with 12 presets: idle, selfie, hip, mirror, peace, cross_arms, lean, sit, point, shy, look_up, action. Hands follow their forearm unless set. The presets are starting points; fine-tune with `aim()`. `sit` needs a seat under the hips. |
| Camera | `ref_camera(ref)` sets the reference's aspect and shows it over the camera at 50%. `frame_head(head_frac, head_xy, view_dir, lens, roll)` places the head at a size and position measured from the reference. `selfie_camera(corner)` keeps the hand out of frame with the elbow in the chosen corner. `measure()` and `project()` read where things are in the frame. |
| Props | `pbr(texture)`, `cardboard_box`, `chain_fence`, `post`, `mirror`, `neon_text`, `led_strip`, `bokeh_lights` and `import_model(category, name)` (Poly Haven glTF), plus `clean_stray()` and `clear()`. |
| Lighting | `light_preset(name)` with 12 presets, one per style in the playbook. They're placed relative to the camera, so they follow any framing. `world(color, haze, hdri)` sets the background and haze. |
| Render | `setup_cycles` sets up GPU rendering. `render(path, percent)` renders. `render_mask(path)` renders the avatar's alpha for `--mask` and `--outline`. |

**Still to add:**
- a car model (none in the library);
- a bed (GothicBed_01 exists);
- a ceiling for the garage;
- style scripts that use the kit, one per new reference.

## 4. Scoring rubric (each part out of 10)

| Score | Meaning |
|---|---|
| 10 | Can't tell which is the reference except by the avatar. |
| 8–9 | Same framing, pose and mood; small offsets (less than 5% of the frame), slight colour shift. |
| 6–7 | Same idea, but there's a visible camera or pose difference or a missing prop. |
| 4–5 | Recognisably the same style, but several big differences. |
| 1–3 | Wrong framing, lighting or set. |

The parts scored are camera, pose, background and props, lighting, colour grade, and post effects. The total is
the lowest part plus 1, not the average: one weak part sinks the whole picture.

## 5. What limits a 10

- **The avatar's own items:** hair, clothing and face decals can't be changed. Say so first; the owner can change
  the outfit in Roblox.
- **Finger poses on block hands:** these can't be done.
- **Hand-painted effects:** these get close only through `post2d.py`.
- **Budget:** each style needs about 3–5 render rounds. Check usage before each one, and stop at the agreed limit.

## Opus review rules (2026-10-26)

See section 5 of the roblox-gfx-match skill: camera solve plus assert first, head by face-to-camera angle, 10×10 frame
map, fixed stage order with a clay lighting preview, real-scale textures with dirt, masked grade, scene lint, score =
lowest part + 1. Tools still to build (ranked): spec.json + solve_camera, camera_assert, frame-map checker (object-index
pass), pose/view assert, clay luminance gate, place_at_frame, scene lint, grade auto-tuner, richer compare.
The pose may differ from the reference when another pose suits the avatar better (owner rule).

## Mistakes log (read every session; add every new mistake here the moment you find it)

From DI3STINY rainy bus stop (2026-10-26):
1. **Don't "fix" a mood the owner likes.** They preferred the first warm, rainy preview over my cold relight. After each
   preview, keep what reads well and change only the broken parts.
2. **Framing:** a seated shot cut at the shins needs `frame_head(head_frac≈0.3)`. At 0.2-0.24 the whole body showed,
   with an empty floor band.
3. **Place props by projection:** solve each prop's x/z with `k.project()` so it lands at its planned frame position
   (`project` y is 0 at the TOP). Guessing world coordinates put the advert off-frame, the roof at z=5, and the sign
   right in front of the lens.
4. **Check that props clear the subject:** a roof solved at 1.16 m cut through her hair. Clamp it to above the avatar's
   top plus 0.35.
5. **Occluders steal the key light:** a new roof shadowed her face. Set `visible_shadow = False` on overhead set
   pieces, or check the subject's brightness after adding any prop above or beside the key.
6. **Lit panels:** base colour black with emission ≤1.5, or AgX blows them out white or peach. Big flat panels behind
   the subject dominate and float behind transparent glass, so drop them or give them visible support.
7. **Pole through sign:** end the pole under the panel.
8. **Text objects:** `neon_text` with rot (90,0,rz) faces the direction rz+90. Check it isn't mirrored. For
   real-world signage use a clean static sans: **Bebas Neue**, dark ink on a light panel. Anton looked odd to the
   owner. Never use variable fonts (`Montserrat[wght].ttf`): Blender mis-fills overlapping contours, and "B" and "P"
   vanished. Zoom-crop the text in a test render before the final.
9. **Rain:** one mesh of ~4000 streaks, none within 1.3 m of the lens. Dense rain plus haze sells the mood.
10. **Hands:** forearms pointing straight forward read as "holding cups". For seated poses, rest the forearms down
    onto the knees with the hands angled ~0.3 inward.
11. **Grading:** `gfx2d.py grade` with the render as its own reference crushed the image dark and red. Without a
    reference, use a gentle custom pass: bloom 0.18, contrast 1.08, vignette 0.35, grain 0.012.
12. **Renders:** the owner allows the full GPU and CPU (`setup_cycles` now enables all devices).
13. **Repos:** `Projects/external-repos` and `github-repos` are desktop editing apps, not useful inside Blender.

From sttvr_l1ght haunting-spirits misty forest (2026-11-02), full list in roblox-gfx-ideas SKILL.md:
14. Don't build before the owner picks an idea; choose the idea from the avatar's proportions (chibi goth doll), not just the moodboard.
15. Remove base-stage `Backdrop` and `Halo` before the first preview; dense low mist and strong backlight both wash fog scenes white.
16. `gfx2d.py grade --levels` is Lab L 0-100 (0.04,0.97 made a white image). Flat translucent veils read as slabs; skip them.
