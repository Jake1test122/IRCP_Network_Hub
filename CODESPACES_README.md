# ICRP Network Hub — GitHub Codespaces

1. Create a PRIVATE GitHub repository for running this bot (the source files may be public, but never publish credentials).
2. Upload the extracted `ICRP_Network_Hub` folder to the repository.
3. Under GitHub Settings → Codespaces → Secrets, create `DISCORD_TOKEN` and `SERVER_ID`, granting this repository access.
4. In the repository choose Code → Codespaces → Create codespace.
5. In the Codespaces terminal run:
   `bash ICRP_Network_Hub/run_codespaces.sh`
6. Enable **Message Content Intent** for your bot in Discord Developer Portal → Bot.
7. In your Network Hub Discord server run `!preview_hub` then `!setup_hub`.
8. Run `!preview_hub_permissions`, then (server owner only) `!apply_hub_permissions CONFIRM` to update existing roles.

**WARNING:** `!rebuild_hub CONFIRM` deletes matching Hub channels and their message histories. `!wipe_hub_all CONFIRM_ALL_CHANNELS` deletes ALL channels. Back up content first.

Only Founder, Co-Founder, Owner, Head Director, Deputy Head Director receive mass-mention rights in the role template. Admin permission bypasses restrictions; audit all other roles.

Codespaces can stop when idle. This package is for one-time setup, not reliable 24/7 hosting.
