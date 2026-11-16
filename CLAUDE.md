# Roblox GFX and animation project

**Before any new GFX, GFX edit or animation in this folder, read these in full, every session:**
1. `gfx_mistake_log.md`: every mistake and lesson from past GFX and animations, plus the owner's rules. Don't repeat any of them.
2. `docs/GFX_MASTER_PIPELINE.md`: the reviewed production pipeline (stages, quality gates, never-again checklist).
3. `START_PROMPT.md`: the owner's standing rules and the tool list.

**Quality bar (owner, 2026-11-16):** every GFX must match `gfx_references/quality_bar/alley_v2_final.png` (in git; same file as `gfx_output/Bio_IsHere/alley_v2_final.png`). Use `tools/alley_v2.py` as the worked example and follow the "Quality baseline for every GFX" section at the end of both GFX skills: plan in the docstring, `tools/gate.py` before renders, passes, `tools/finish.py`, final gate, side-by-side. Put the new final next to the approved image before presenting.

Then use the matching skill: `roblox-gfx-match` (owner sent a reference) or `roblox-gfx-ideas` (no reference).

**Append every new mistake to `gfx_mistake_log.md` as soon as you find it** (owner: "save every mistake and update them in this file").
Before presenting a GFX, have Opus review it strictly against the owner's reference pictures.
