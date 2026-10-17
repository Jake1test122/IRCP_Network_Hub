# ICRP ICRP Community Roleplay — Custom Detailed Edition

This is a fresh ICRP-original layout inspired by the user-provided Discord screenshots, not a copy of Diamond State branding. Contains detailed server info, staff operations and voice offices, economy, CAD/MDT, news, sessions, gangs, courts, case/appeals systems, departments, roleplay and voice chats.

## Launch in GitHub Codespaces
Upload the extracted folder to your repository. Set `DISCORD_TOKEN` and `ICRP_SERVER_ID` in Codespaces secrets and run `bash ICRP_COMMUNITY_SETUP/run_icrp_community.sh`. Enable Message Content Intent in the Discord developer portal.

## Commands
- `!preview_icrp` — see missing items and expected totals
- `!setup_icrp CONFIRM` — create missing roles/categories/channels without deleting existing server content
- `!audit_icrp` — check installed bot hierarchy (does not reorder roles)
- `!preview_icrp_reset` — count everything that will be permanently deleted
- `!arm_icrp_reset I_UNDERSTAND_PERMANENT_DELETION` — create short-lived owner-only confirmation
- `!confirm_icrp_reset CODE SERVER_ID` — delete channels and deletable roles then rebuild from this custom template

**IMPORTANT:** Full reset permanently destroys all channels including message history, with no undo. It will delete non-managed roles that the bot is allowed to delete, potentially removing member role assignments. Preserve backups before use. Roles managed by other bots are kept, as is `@everyone` and the `ICRP | Owner` role. The server owner must manually position trusted bot roles below Owner and above staff roles. Discord cannot promote a bot above its own top role; review individual bot permissions and dashboard after rebuild.

**Security:** Never commit your bot token to a public GitHub repository. The owner role has Administrator; other staff do not. Mass-mention rights are restricted. The design and role names are editable in `community_template.json`. This package creates channel structures; it does not supply full functional banking, CAD, ticket or economy backends.

## Expanded ICRP role system
This edition has **189 ICRP role definitions** (136 new positions beyond the prior detailed ZIP), with color-coded tiers in `community_template.json`. The titles are original ICRP labels inspired by the functionality and layout of the screenshots rather than using DSRP branding. They include staff duty/leave statuses, warnings/strikes, civilian ranks 0–10, roleplay jobs, police/fire/courts, executive leadership, moderators, HR, security, appeals, training, and community teams.

Permissions: only `ICRP | Owner` has Administrator. All added jobs, warning markers, achievements, and civilian ranks have normal member permissions. A Discord role icon displayed next to names requires eligible server features and icon assets; this template sets role colors, not custom role icons.

For incremental updates: use `!preview_icrp` then `!setup_icrp CONFIRM`. The full reset commands are irreversible; **do not use the wipe commands merely to add roles**. The setup bot's role must remain above roles it needs to manage but below the owner's role.


## Screenshot additions (October 2026)
Includes Business Income Levels 1-10, event status roles, and added economy, news, CAD, main chat, server info, staff office and punishment log channels. This is a structure template, not working banking, CAD or moderation automation. Run !preview_icrp then !setup_icrp CONFIRM to add missing items without a reset. Review permissions and access before opening private channels.

## Optional full wipe setting (disabled by default)
This package can live in the same **GitHub repository** as your Hub bot, but it is a **separate ICRP Community bot process**. Uploading code to the Hub repository does not mean you should point `ICRP_SERVER_ID` at the Hub server.

- `ICRP_SERVER_ID`: Discord ID of the **ICRP Community roleplay server only**, never the Network Hub or Staff Information server.
- `ICRP_ALLOW_FULL_WIPE=false`: default; blocks full-wipe commands.
- `ICRP_ALLOW_FULL_WIPE=true`: temporarily enable owner-only full wipe. Restart bot after changing this value.

In the **ICRP Community server**, use `!preview_icrp_reset`, `!arm_icrp_reset I_UNDERSTAND_PERMANENT_DELETION`, then `!confirm_icrp_reset CODE SERVER_ID` using the code returned by the bot. After rebuilding, set `ICRP_ALLOW_FULL_WIPE=false` again and restart.

**Warning:** The full wipe permanently deletes every channel and its message history, plus removable roles in the configured ICRP Community server, then rebuilds the template. It does not delete the Discord server itself. Back up anything important first. Never use your Hub server ID for this bot.

## Separate startup in the same Codespace
Run `bash ICRP_COMMUNITY_SETUP/run_icrp_community.sh` for Community. This does not start or rename the Hub bot. Community bot files use unique names (`icrp_community_bot.py`, `run_icrp_community.sh`, `requirements_icrp_community.txt`). Run Hub and Community in separate terminals/processes if both need to stay online.
