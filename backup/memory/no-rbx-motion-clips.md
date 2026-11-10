---
name: no-rbx-motion-clips
description: Owner finds retargeted Roblox default animation clips look weird; animate procedurally instead
metadata:
  node_type: memory
  type: feedback
  originSessionId: 418ab616-8563-42d3-a196-c609d5db19aa
  modified: 2026-10-26T16:21:01.782Z
---

Don't drive characters with the retargeted Roblox default clips (rbx_anims / anim_motion clip layer). Hand-key / procedural motion instead (beat bounce, breathing, weight shift, overlapping arms, eased poses).

**Why:** owner said (2026-10-26, Suhaa concert animation) the Roblox motion "makes it look weird".
**How to apply:** for any animation, build motion from eased acting poses + procedural layers; still follow [[animation-standards]].
