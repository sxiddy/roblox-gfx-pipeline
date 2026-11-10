---
name: gfx-pose-plan-first
description: "Before any GFX build, write an exact pose and camera plan from the reference; no trial-and-error posing"
metadata:
  node_type: memory
  type: feedback
  originSessionId: f118cdcd-3565-4626-8b4f-e93fe0021dcb
  modified: 2026-10-25T20:49:23.327Z
---

Owner (2026-10-26): "whenever i ask u to do a gfx make a plan on the pose exactly then start instead of wasting my tokens".

**Why:** the garage v4 round spent ~10 render iterations guessing the pose and camera, and only then realised the reference is a true selfie: camera at the phone hand, near shoulder filling the bottom-left, arm leaving the frame edge, head rolled about 18° toward the lens.

**How to apply:** before touching Blender, write a short pose plan from the reference and show it in one or two lines:
- **Camera type:** selfie at arm's length, tripod or third person; position relative to the body (side, height, distance); lens; roll.
- **Body parts:** for each, the direction it points in world terms (torso lean, head tilt and turn, each upper arm, forearm and hand, legs).
- **Frame:** what is cut off and which body part touches which edge.
- **Tools:** which `gfx_kit` preset or search function to use (for selfies, `style_garage_v4.stage_selfie` searches the arm direction and lens position).

Then build once and use compare to fine-tune. Related: [[gfx-self-direct]], [[roblox-gfx-pipeline]].
