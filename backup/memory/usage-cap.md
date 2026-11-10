---
name: usage-cap
description: "Hard 5-hour usage cap the owner sets (70% as of 2026-10-26), and always checking real usage before each step"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 12c72b5c-0e45-4de4-bffd-11500e40d7c6
  modified: 2026-11-10T19:57:27.892Z
---

Never go past the owner's cap on the 5-hour usage window. On 2026-10-26 the owner set it to 70% for the Bio x Suhaa animation work (earlier 95%, 90%, 85%). Before each step call get_usage and post "Your limit is now at X% (weekly Y%)"; never estimate. On 2026-11-11 the owner said "dont go over 90%" for the superior-plan session, noting other sessions share the limit; the cap changes per job, so use the number the owner stated most recently and ask if none was given.

**Why:** the owner treats the cap as absolute and once caught an estimated figure that was 11 points off.
**How to apply:** stop starting new work near the cap and leave background agents/downloads in a safe state. Full project rules are in HANDOFF.md in the repo ([[project-rules]]).
