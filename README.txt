ICRP NETWORK HUB ONLY — separate from Staff Information.

1. Extract ZIP. Install Python 3.10+ and check Add Python to PATH.
2. Create a Discord application/bot at https://discord.com/developers/applications .
3. In Bot settings, enable MESSAGE CONTENT INTENT (needed for ! commands).
4. Under OAuth2 URL Generator choose bot, then permissions Manage Channels, Manage Roles, View Channels, Send Messages, Read Message History, Manage Messages. Use the generated URL to invite the bot to the NETWORK HUB server only. Do not use the token as a Client ID.
5. Put the bot role ABOVE the roles it should manage in Server Settings > Roles.
6. Double-click START_HUB.bat. Paste BOT TOKEN and NETWORK HUB server ID when prompted. Do not share the token or screenshot it.
7. In the Hub Discord server, as an Administrator, type !hub_status then !setup_hub.

Commands:
!setup_hub — create missing roles/channels and post available screenshot text, without deleting.
!preview_hub — preview deletion counts.
!rebuild_hub CONFIRM — remove only matching Hub channels, recreate and repost. Deletes messages in those channels.
!wipe_hub_all CONFIRM_ALL_CHANNELS — SERVER OWNER ONLY; permanently delete ALL Hub server channels (including unrelated/nuked channels) and rebuild from scratch. Cannot restore old messages. Roles are preserved; matching roles are created if absent.
!hub_invites — explains other bot installation.

IMPORTANT: Run only in a new/authorized Hub server. This bot is locked to the SERVER_ID supplied on startup. The Staff Information server is NOT included. The bot does not remove or install third-party bots, nor can it restore deleted messages. Add those apps yourself via Discord official invite flows. All channel permission overwrites must be reviewed after setup; sensitive HR channels are NOT automatically made private. Screenshots and existing ZIP contents may not contain every historic message; posts.json contains only text previously captured.
