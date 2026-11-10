---
name: session-is-own-project
description: Treat each session as a separate project; never reuse avatars/assets/outputs from other GFX projects unless told
metadata:
  node_type: memory
  type: feedback
  originSessionId: 418ab616-8563-42d3-a196-c609d5db19aa
  modified: 2026-10-26T17:16:40.814Z
---

Each session is its own project. Don't pull in avatars, sets or outputs from earlier GFX/animation projects (e.g. other clients' avatars in avatars/) unless the owner says so. Source new assets fresh (e.g. from Roblox itself).

**Why:** 2026-10-26 Suhaa concert animation: I put cached avatars of other clients (Bio, DI3STINY, Nico, Qsi2408, sttvr_l1ght, old Suhaa) in the crowd; owner: "this video is completely unrelated to the previous gfx's".
**How to apply:** at the start of each build, only use assets fetched for this project; ask before reusing anything else.
