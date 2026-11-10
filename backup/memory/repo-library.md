---
name: repo-library
description: Where the owner's GitHub repo library lives, how it's organised, and which repos matter for Roblox animation work
metadata:
  type: reference
---

Library: `C:\Users\Siddharth D\Projects\github-repos\<category>\<repo>` (categories agent-skills, craft-shared-libs,
creative-editing, office-apps, ui-ux, video-audio, business-apps) plus `C:\Users\Siddharth D\Projects\external-repos`.
Every repo has a REPO.md card (what / use / how / safety verdict); the README.md in each root is the index. New repos
the owner gives: shallow clone into the matching category, write a card, add to README. Skip ones already present.

Useful for Roblox animation/GFX: earshot (audio "ears", venv at .venv), VoiceStudio (local voices), lemo-opuscar (film
styles, TTS, subtitles), hyperframes (HTML->video overlays), soundcraft/filmcraft (DAW / editor). CAUTION verdicts:
open-higgsfield (sends keys to a third party), token-optimizer and billion-context (edit ~/.claude settings/hooks).
See [[animation-standards]].
