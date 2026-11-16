# Backup of what lives outside this folder

- `skills/`: copies of `~/.claude/skills/roblox-gfx-ideas` and `roblox-gfx-match`. Restore by copying them back there.
- `memory/`: copies of the Claude Code memory notes for this project (owner rules and preferences).

Not in this repo (too large for GitHub): `library/`, `avatars/`, `gfx_output/`, `hdri/`, `textures/`, `tools/bin/`, `.blend` files, renders.
Re-create them with `tools/fetch_library.py`, `tools/fetch_assets.py` and `tools/fetch_avatar3d.py`.

Start any new session by reading `CLAUDE.md`, then `gfx_mistake_log.md`, `docs/GFX_MASTER_PIPELINE.md`, `START_PROMPT.md` and `docs/SUPERIOR_PLAN.md`.

Quality bar (owner-approved 2026-11-16): `gfx_references/quality_bar/alley_v2_final.png`, built by `tools/alley_v2.py` + `tools/finish.py`; its gate spec is `alley_v2_job.json` (paths inside are from the owner's machine). The recipe is the "Quality baseline for every GFX" section at the end of both skills.
