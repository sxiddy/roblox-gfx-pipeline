---
name: animation-standards
description: "What the owner expects from a Roblox character animation video (voices, real SFX, plain subtitles, natural motion)"
metadata:
  node_type: memory
  type: feedback
  originSessionId: a05d36aa-cafd-4e07-9e75-3f648a78515c
  modified: 2026-10-26T12:48:23.027Z
---

The owner's v1 door-visit animation (2026-10-26) was rejected for: no voices, fake-sounding synthesized SFX, chat-bubble "subtitles", a username title card nobody asked for, and stiff characters.

Their standard for every animation:
- **Voices on every spoken line.** Default: edge-tts (Microsoft neural voices) chosen to fit each character, picked with earshot. Re-time the animation to the real clip lengths.
- **Real recorded SFX** (library/sfx: Kenney CC0 packs), picked/checked with earshot. Never pure numpy synthesis.
- **Plain movie subtitles:** white text, thin outline/shadow, bottom centre. No boxes or name chips. Sound captions like *[knocking]* are welcome.
- **No title card** with usernames unless asked. Night ambience instead of music unless asked.
- **Natural motion:** Roblox default animations retargeted (rigs_community/rbx_anims, IKR15.blend) plus breathing, idle sway, weight shifts, head micro-moves, overlapping arms, ease in/out, hip bob and planted feet in walks, anticipation before actions, head bobs synced to dialogue. Check a draft render as video strips for freezes before the final.
- **Personality:** keep each character's attitude (e.g. Bio = cool guy, Suhaa = kind) in every pose and the walk.

**Why:** the owner judges the video as a viewer; silence, fake sounds and frozen bodies make it feel unfinished.
**How to apply:** plan voices/SFX/subtitles/motion before building, check the repo library (Projects/github-repos, cards in each REPO.md) for tools first. See [[shared-blender]], [[usage-cap]], [[log-every-mistake]].
