# GFX Master Pipeline (Halloween/Autumn, two scenes)

Rewrite of `docs/GFX_MASTER_PROMPT_original.md`, checked against Blender 5.2 and our tools on 2026-11-02.
Goals kept from the owner: two distinct scenes (Violet Graveyard + Jack-o'-Lantern, Autumn Woods + Kerosene Lamp),
tri-tone palette Amber `#FF7A00` / Violet `#9D00FF` / Midnight Indigo `#0B0416`, real 3D props, volumetrics, rim
light, DoF, no stiff pose.

## 0. Ground rules (owner rules, override everything below)

| Rule | What it means here |
|---|---|
| Owner picks first | Show the two concepts (one line each + pose sketch) and wait for a pick or "you choose". Build nothing before. |
| Check usage | `get_usage` before every render round; stop at 70% of the 5-hour cap. |
| Private Blender | Build/render in our own headless Blender (`blender -b --python ...`). Never touch the shared GUI on port 9876 except to show the camera view the owner asked to watch. |
| Pose fits the avatar | Pose may differ from any reference. Chibi bodies (sttvr_l1ght, ~1.25 m) cannot cradle big props or "pull a sleeve to the chin". |
| Keep liked mood | After each preview change only what is broken. |
| No cringe | No text, slogans, names, emoji faces, rune lettering in the set. |
| Opus review | Before showing finals, run an Opus review against the owner's references only. Score = lowest part + 1. Self-rate harshly. |
| Log mistakes | Every new mistake goes into `roblox-gfx-ideas/SKILL.md` and `gfx_references/PLAN.md`. |

## 1. What was wrong in the original, and the replacement

| Original claim | Reality (checked) | Replacement |
|---|---|---|
| Clone `github.com/matthewde/roblox-rig-pack` | `git ls-remote` -> "Repository not found". Fabricated. | `tools/build_exact_gfx.py` already builds an R15 armature from part overlaps and binds every part. |
| avatar-3d endpoint returns a zipped bundle | Returns JSON -> `imageUrl` -> metadata JSON with `obj`, `mtl`, `textures` hashes; files come one by one from `t{n}.rbxcdn.com`, sometimes gzipped. Needs a logged-in session. | `tools/fetch_avatar3d.py meta.json out_dir`, then `build_exact_gfx.py`. |
| Sapling `add_curve_sapling`, `mesh_extra_objects` via `addon_enable` | Neither is bundled in Blender 5.2 (`addon_utils.modules()` finds no sapling/extra module). They are extensions now; installing is a download. | Write `halloween_kit.gnarled_tree()` (bmesh/skin-modifier branches, see 4.3) or use a library model. Do not install without owner OK. |
| `pip install Pillow numpy scipy requests` in preflight | Would modify environments; Blender's python is separate. | No installs. gfx2d.py already runs with what is installed. |
| `read_factory_settings(use_empty=True)` to reset | Wipes the imported, rigged avatar and the kit's state. | Build each scene in a fresh process: `build_exact_gfx.py` -> `halloween_kit.keep_only_avatar()` -> scene script. |
| Subdivision level 1-2 + creases on the avatar | Roblox parts are blocky on purpose; Catmull-Clark rounds cubes into blobs, swims the face decal UVs, and inflates layered clothing into the body. That kills the Roblox look. | No subdivision on body/head. Allowed: Weighted Normal / shade-auto-smooth on accessories that are already smooth (hair UGC), and a 0.003-0.008 m bevel modifier (limit by angle) on blocky limbs for a highlight edge. |
| `remove_doubles` + `normals_make_consistent` | Merging verts welds separate accessory shells and breaks UV seams on decals. | Skip. Only recalc normals on a part that renders inverted, checked by eye. |
| Auto weights / bendy bones for "smooth joints" | Roblox R15 parts are separate rigid meshes; auto weights on them shear the blocks. Gaps at joints are the Roblox look. | Rigid bind per part (existing). Layered clothing only: `gfx_kit.skin_clothes()` (2-nearest-bone weights). Hide joint gaps by pose and camera angle. |
| Normal/roughness maps synthesised from 585x559 clothing PNG | Clothing templates are paint, not height. A gradient of printed colour embosses logos and text, and a 585x559 atlas on a 1.25 m chibi gives mush. Also flips sign conventions (green channel) per tool. | Optional, low: add a tileable fabric normal from `library/textures/fabric` via a separate UV-scaled Normal Map node at strength 0.15-0.3, masked off the face. Judge at 50% zoom crop; drop if it reads as noise. |
| SSS skin (Subsurface Weight 0.2, radius 1,0.35,0.15) | Inputs exist in 5.2, but skin is a flat colour plus a printed face decal. SSS at 0.2 on a 1.25 m blocky head softens the decal lines and glows orange near the pumpkin. | Skin: Roughness 0.45, Specular IOR Level 0.4, Subsurface Weight 0-0.05, Subsurface Scale 0.01. Face decal stays crisp. |
| Hair: Anisotropic 0.65 + "Clearcoat 0.3" | `Clearcoat` does not exist; 5.2 names are `Coat Weight`, `Coat Roughness`. `Anisotropic` needs a Tangent input or it barely shows on UGC hair cards. | Hair: Roughness 0.35, `Coat Weight` 0.15, `Coat Roughness` 0.2. Anisotropic only with a Tangent node (Radial Z), test at 50%. |
| Sheen 0.4 on clothing | Valid names (`Sheen Weight`, `Sheen Roughness`); 0.4 greys dark goth fabric under rim light. | `Sheen Weight` 0.1-0.2, `Sheen Tint` slightly violet. |
| Light wattages 120/60/40/80/15/10 W | Scene is chibi scale (avatar 1.25 m, head ~0.35 m) and our lights are placed per metre^2 of distance by `light_preset`. A 120 W point inside a 0.2 m pumpkin washed the face to flat peach (logged). Moon at 5500 W washed fog white (logged). | Use the energies in section 3, all relative to distance, and judge by face luma at 50%. |
| Volume density 0.022-0.025 on a world/domain | World volume fills to infinity, slows Cycles, flattens moon; a domain box whose top is visible shows a hard edge (logged). | `halloween_kit.fog()` box with height fade, density 0.02-0.06, anisotropy 0.5-0.65, top above frame. |
| 85 mm f/1.8-2.4 portrait | 85 mm works, but our framing goes through `frame_head(head_frac, head_xy, view_dir, lens)` which solves distance. f/1.8 at 1.25 m-tall chibi scale throws the whole body out of focus. | `frame_head(0.28-0.32, lens=70-85)`; DoF f/2.8-4 with focus on head; foreground bokeh from placement, not a lower f-stop. |
| Compositor: `scene.node_tree`, Glare "Fog Glow", Color Balance, Lens Distortion | In 5.2 `scene.node_tree` is gone; compositor is `scene.compositing_node_group` (a `CompositorNodeTree`). Glare type/threshold/size are now input sockets (`Type`, `Threshold`, `Strength`, `Size`, ...), not node properties. Old scripts fail. | Do post in `tools/gfx2d.py grade/post` (bloom, CA, vignette, grain, masked grade) as we already do. Compositor optional; if used, set sockets by name. |
| Render: CUDA, 512 samples, "Filmic High Contrast" | OptiX on RTX 4050 is faster; Filmic is legacy; 512 samples is wasted with denoise. | `gfx_kit.setup_cycles(samples=256, look="AgX - Punchy" or "AgX - High Contrast")`, all devices on. Preview 50% at 64 samples. |
| Pumpkin: UV sphere + Solidify + boolean cutter | Boolean on a solidified, ribbed sphere often fails (non-manifold after solidify, cutter faces coplanar with ribs) and leaves black slivers. | See 4.1: model shell, cut faces before solidify, apply bevel, inner emissive shell + light. |

## 2. Stage order (one script per stage, render a 50% preview at each gate)

| # | Stage | Tool | Gate before moving on (50% preview, 64 spp) |
|---|---|---|---|
| 0 | Concepts to owner | text | Owner picked or delegated. |
| 1 | Fetch avatar | `fetch_avatar3d.py` | OBJ/MTL/textures present; meta.json saved. |
| 2 | Rig + import | `build_exact_gfx.py` (AVATAR_DIR, POSE) then `halloween_kit.keep_only_avatar()` | Clay render front + 3/4: no missing accessory, hair attached, no `Backdrop`/`Halo`. List unparented meshes = 0 extras. |
| 3 | Materials | new `gfx_kit.avatar_materials()` (section 5) | Face decal sharp in a 300% crop, no orange glow on skin. |
| 4 | Pose | `gfx_kit.apply_pose` / `aim` + `skin_clothes()` | Clay from the shot camera: no clipping of hands into props/body, head tilt 6-12 deg, weight on one side; sleeves follow arms. |
| 5 | Camera | `frame_head(head_frac≈0.3, head_xy, view_dir, lens 70-85)` | Head at the planned frame spot within 5%; feet/shins cut where planned, no empty floor band. |
| 6 | Set | `halloween_kit` + new functions (section 4); place each prop with `k.project()` | Every prop lands at its planned frame position; none crosses the head; image-right = world -X checked. |
| 7 | Clay light | lights only, white clay override | Subject reads first: face luma > background; amber key and violet rim both visible on silhouette. |
| 8 | Full render | `setup_cycles(256)`, 100% | Mean luma 90-125, no blown emissives (panels emission <= 1.5, glass <= 2.5). |
| 9 | Grade | `gfx2d.py grade ... --mask` or gentle custom: bloom 0.15-0.18, contrast 1.08, vignette 0.35-0.4, grain 0.012-0.014, sat 0.7-0.9 | Compare raw vs graded side by side; never use the render as its own reference; `--levels` is Lab L 0-100. |
| 10 | Review | Opus vs owner references | Score each part; lowest part + 1 >= 7 or loop to the weak stage only. |

## 3. Lighting (energies scale with distance; values are a start, tune by luma)

Use `gfx_kit.area()` / point lights; numbers below are for a head-to-light distance of ~1 m. Multiply by distance^2.

| Scene | Light | Type | Colour | Start energy | Note |
|---|---|---|---|---|---|
| 1 | Pumpkin interior | Point, radius 0.03 | `#FF7700` | 8-20 W | Inside cavity; light leaves only through cut holes. Do not put a light in front of the face. |
| 1 | Step pumpkins | Point | `#FFA028` | 3-8 W each | |
| 1 | Violet rim | Area 0.6 m, high rear-left | `#9D00FF` | 40-60 W | Outline hair and shoulders; check it doesn't flood fog. |
| 1 | Moon | Sun 0.5 deg, or Area far back | `#3A6B9E` | Sun 0.3-1.0 | Through branches for shadow; fog-lit scenes start 600-1500 W area max. |
| 1 | Fog | `fog()` box | `#1F1135` | density 0.02-0.05, aniso 0.6 | Height fade; top out of frame. |
| 2 | Lantern flame | Point, radius 0.02 | `#FF9326` | 10-25 W | + flame sphere emission 15-30; glass emission <= 2.5; brass dark metal, not emissive. |
| 2 | Warm bounce | Area 1 m, front-low | `#FFC37A` | 3-6 W | Fill, not key. |
| 2 | Canopy ambient | World colour / large area above | `#1B172E` | world 0.08-0.15 | |
| 2 | Violet mist rim | Area rear | `#9D00FF` | 30-50 W | Keeps tri-tone. |

Palette check in the grade: shadows should sit near `#0B0416`, never pure black or grey.

## 4. Set pieces (new or fixed functions in `tools/halloween_kit.py`)

### 4.1 `carved_pumpkin(name, loc, r, face="classic")` (replaces emissive decals)
1. bmesh UV sphere 48x24, ribs as current `pumpkin()`, z scale 0.82.
2. Delete faces inside the eye/mouth outlines (project `_FACE` polygons onto the +Y hemisphere, delete faces whose centre falls inside). No boolean.
3. Solidify 0.06*r, `use_even_offset`, `use_rim=True`, then apply; bevel 0.004 limit-angle.
4. Material: outer `Base Color` (0.5,0.12,0.01), Roughness 0.55, `Subsurface Weight` 0.3, `Subsurface Radius` (1,0.3,0.1), `Subsurface Scale` 0.02*r (SSS is right for pumpkin flesh, unlike the avatar). Inner faces (by normal facing centre, separate material index) pale orange flesh, emission 2-4.
5. Point light at the centre, energy per table; stem with a twist.
Gate: carved holes show depth (rim thickness visible at 3/4 view), no black slivers, face glow does not wash avatar skin.

### 4.2 `tombstone(name, loc, size, style="gothic")`
Cube with pointed or rounded top (bmesh), Bevel modifier 0.02 m / 3 seg (applied), `pbr()` stone from `library/textures/concrete` or `wall` with Box projection, Noise Texture -> Bump 0.3 plus a moss mask (Geometry Pointiness or Z gradient). Slight random tilt 2-6 deg, sunk 0.03 m into ground. Not a wall-size slab behind the subject (the last render's left 50% was one flat stone).

### 4.3 `gnarled_tree(loc, h, seed)`
Recursive branch skeleton (verts + edges), Skin modifier, Subsurf 1 (fine here, it is not the avatar), displace with noise, bark `pbr()` from `library/textures/wood`. Roots: 4-6 short branches into the ground. Silhouette trees in fog may stay low-poly.

### 4.4 `moon(loc, radius)` fix
Sphere, not a disc; place it behind everything (no geometry crossing its disc in the frame map), emission 1.5-3; branches may pass in front only as thin silhouettes, never a mesh edge intersecting it.

### 4.5 `kerosene_lantern(loc, scale)`
Base and cap cylinders (dark brass, Metallic 1, Roughness 0.35), wire bail handle (curve with bevel), glass globe (`Transmission Weight` 1, Roughness 0.05, IOR 1.5, `Thin Wall` on for speed), flame sphere emissive, point light inside. Parent to the hand bone via `k._b()`/bone parent so it follows the pose.

### 4.6 Leaves
`leaves()` is flat polygons (flagged as stray geometry). New `leaf_cards(n, center, spread)`: maple-shaped alpha card (one PNG made with PIL from a polygon, saved under the scene output), slight curl via Simple Deform bend, 3-5 hero leaves 0.3-0.6 m in front of the lens for bokeh, 20-40 small ones in mid-ground. Embers warm and dim.

### 4.7 Ground
Never a bare plane: displaced ground with `library/textures/terrain`, leaf litter cards, small rocks from `library/models/rocks`.

## 5. Avatar materials: new `gfx_kit.avatar_materials(skin_spec=0.4)`
Walk imported materials; keep Base Color textures; set by role:

| Role (detect by part name / bone) | Settings (Blender 5.2 names) |
|---|---|
| Head/skin | Roughness 0.45, `Specular IOR Level` 0.4, `Subsurface Weight` 0-0.05 |
| Face decal | Image `interpolation='Closest'` if pixel-art, else Cubic; no bump |
| Hair | Roughness 0.35, `Coat Weight` 0.15, `Coat Roughness` 0.2; optional `Anisotropic` 0.3 with Tangent node |
| Clothing | Roughness 0.7, `Sheen Weight` 0.15, `Sheen Roughness` 0.5; optional tiled fabric normal strength 0.2 |
| Shoes/metal accessories | Roughness 0.3, Metallic only if clearly metal |

## 6. Scenes (concept kept, made fit for chibi scale)

**Scene 1, Violet Graveyard.** Avatar seated on a low double-stepped tombstone (step height ~0.35 m for a 1.25 m avatar), pumpkin (r 0.12-0.15) held at lap height *below the chin*, never covering the face (last render: pumpkin hid her mouth and body). Secondary pumpkins on the steps, resting on the surface (check z = step top + r*0.82). Background: 3-5 leaning headstones, iron fence, gnarled trees, violet wisp orbs (small emissive spheres, strength <= 5). Camera: `frame_head(0.3, head_xy=(0.6,0.38), lens=75)`, rule of thirds.

**Scene 2, Autumn Woods.** Lantern held out at shoulder height on the arm away from camera, other hand relaxed at the side or near the chest (chibi arms can't reach the chin). Three-quarter view; hero leaves in foreground bokeh. Camera `frame_head(0.3, view_dir=(0.5,1,0.25), lens=85)`, f/3.2.

Output names: `gfx_output/<user>/scene_1_graveyard.png`, `scene_2_autumn_woods.png`, plus `_graded` versions.

## 7. Post-flight report (per scene)
Camera lens, f-stop, head_frac; each light's type/colour/energy/distance; fog density; samples; grade command line; Opus score per part.

## 8. Never-again checklist

- [ ] Pumpkin is a real carved hollow shell with an interior light; no flat face decals; no light in front of the face.
- [ ] Moon is a sphere behind everything; no geometry edge cuts it.
- [ ] Tombstones beveled, textured, tilted, sunk; no wall-sized slab behind the subject.
- [ ] Trees have branches and roots; ground is displaced and littered, never a bare plane.
- [ ] Tri-tone visible: amber key, violet rim, indigo shadows. Fog density low, height-faded, top not visible.
- [ ] Pose fits the avatar's proportions; nothing clips; props don't cover the face; no floating props.
- [ ] No subdivision / auto weights / remove_doubles on the avatar.
- [ ] `Backdrop`, `Halo` and strays removed before the first preview.
- [ ] Every prop placed via `k.project()`; image-right = world -X checked.
- [ ] Emission caps: panels <= 1.5, glass <= 2.5, leaves/embers dim.
- [ ] Grade: never the render as its own reference; `--levels` in Lab L 0-100; show graded, say "preview, grade comes after".
- [ ] No text, slogans, names, emoji faces in the set.
- [ ] Owner picked the idea; usage checked before each round; own headless Blender; Opus review against owner refs before presenting.
- [ ] Don't promise tools that aren't installed (photocraft/lightcraft/effectcraft need a Rust build; Real-ESRGAN: check REPO.md).
- [ ] Log every new mistake in both logs immediately.
