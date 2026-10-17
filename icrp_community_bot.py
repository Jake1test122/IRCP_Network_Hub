"""ICRP ICRP Community RP server builder: non-destructive, explicit server ID allowlist."""
import asyncio
import json
import os
import secrets
import time
import discord
from discord.ext import commands

with open(os.path.join(os.path.dirname(__file__), 'community_template.json'), encoding='utf-8') as fh:
    TEMPLATE = json.load(fh)

TOKEN = os.environ.get('DISCORD_TOKEN', '').strip()
SERVER_ID = int(os.environ.get('ICRP_SERVER_ID', '0') or 0)
WIPE_ENABLED = os.environ.get('ICRP_ALLOW_FULL_WIPE', 'false').strip().lower() == 'true'
if not TOKEN or not SERVER_ID:
    raise SystemExit('Set DISCORD_TOKEN and ICRP_SERVER_ID in environment/Codespaces secrets. No token will be printed.')

intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

ROLE_LEVELS = {r['name']: r['tier'] for r in TEMPLATE['roles']}
OWNER_NAME = 'ICRP | Owner'
BOT_MARKERS = ('wick', 'ticket tool', 'carl-bot', 'dyno')


def role_perms(name, tier):
    # Permissions are intentionally conservative. Role hierarchy governs control over other roles.
    allowed = {'view_channel': True, 'read_message_history': True, 'send_messages': True,
               'connect': True, 'speak': True, 'add_reactions': True}
    if tier == 'owner':
        return discord.Permissions(administrator=True)
    if tier == 'lead':
        allowed.update(manage_messages=True, moderate_members=True, kick_members=True,
                       manage_channels=True, manage_roles=True)
    elif tier == 'moderator':
        allowed.update(manage_messages=True, moderate_members=True, kick_members=True)
    elif tier == 'trial':
        allowed.update(manage_messages=True, moderate_members=True)
    elif tier == 'staff':
        allowed.update(manage_messages=True)
    if tier == 'muted':
        allowed.update(send_messages=False, speak=False, add_reactions=False)
    allowed['mention_everyone'] = name in TEMPLATE['mass_mention_roles']
    return discord.Permissions(**allowed)


def can_view(guild, access):
    if access == 'public':
        return None
    permitted = {
        'member': {'owner','lead','staff','moderator','trial','factionlead','faction','member','applicant'},
        'staff': {'owner','lead','staff','moderator','trial'},
        'moderation': {'owner','lead','moderator'},
        'lead': {'owner','lead'},
        'leo': {'owner','lead','moderator','staff'},
        'fire': {'owner','lead','moderator','staff'},
        'dispatch': {'owner','lead','moderator','staff'},
        'civilian': {'owner','lead','moderator','staff'},
    }[access]
    allowed_names = set()
    if access == 'leo':
        allowed_names = {n for n in ROLE_LEVELS if any(x in n for x in ('LSPD','BCSO','State Police','State Trooper'))}
    if access == 'fire':
        allowed_names = {n for n in ROLE_LEVELS if 'Fire' in n or 'EMS' in n}
    if access == 'dispatch':
        allowed_names = {n for n in ROLE_LEVELS if 'Dispatch' in n}
    if access == 'civilian':
        allowed_names = {n for n in ROLE_LEVELS if 'Civilian' in n or 'Business Owner' in n}
    overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False)}
    for role in guild.roles:
        if ROLE_LEVELS.get(role.name) in permitted or role.name in allowed_names:
            overwrites[role] = discord.PermissionOverwrite(view_channel=True, read_message_history=True,
                                                            send_messages=True, connect=True, speak=True)
    # Bot can see/log moderation or staff areas when explicitly installed.
    for member in guild.members:
        if member.bot and any(marker in member.name.lower() for marker in BOT_MARKERS):
            # Avoid granting ticket/security bots access to every restricted area implicitly.
            pass
    return overwrites


async def allowed(ctx):
    if not ctx.guild or ctx.guild.id != SERVER_ID:
        await ctx.send('This bot is locked to the configured ICRP Community server ID. No changes made.')
        return False
    if ctx.author.id != ctx.guild.owner_id:
        await ctx.send('Only the Discord server owner may run ICRP Community setup commands.')
        return False
    return True


def missing(guild):
    existing_roles = {r.name for r in guild.roles}
    existing_cats = {c.name: c for c in guild.categories}
    out = {'roles': [], 'categories': [], 'channels': []}
    for r in TEMPLATE['roles']:
        if r['name'] not in existing_roles:
            out['roles'].append(r['name'])
    for c in TEMPLATE['categories']:
        if c['name'] not in existing_cats:
            out['categories'].append(c['name'])
        cat = existing_cats.get(c['name'])
        names = {(ch.name, 'voice' if isinstance(ch, discord.VoiceChannel) else 'text') for ch in cat.channels} if cat else set()
        for ch in c['channels']:
            if (ch['name'],ch['type']) not in names:
                out['channels'].append(c['name'] + ' / ' + ch['name'])
    return out


@bot.event
async def on_ready():
    print(f'ICRP ICRP Community template bot online as {bot.user} / target server {SERVER_ID}')


@bot.command(name='preview_icrp')
async def preview_icrp(ctx):
    if not await allowed(ctx): return
    m = missing(ctx.guild)
    t = TEMPLATE
    await ctx.send(f"ICRP Community TEMPLATE PREVIEW: {len(t['roles'])} roles, {len(t['categories'])} categories, "
                   f"{sum(len(x['channels']) for x in t['categories'])} channels (text + voice). "
                   f"Missing: {len(m['roles'])} roles, {len(m['categories'])} categories, "
                   f"{len(m['channels'])} channels. No deletion will occur.")



@bot.command(name='build_channels')
async def build_channels(ctx, confirm=''):
    """Create missing categories/channels only. Never deletes or modifies existing channels."""
    if not await allowed(ctx): return
    if confirm != 'CONFIRM':
        await ctx.send('Channel-only builder: !build_channels CONFIRM. No wipe or role deletion.')
        return
    guild = ctx.guild
    me = guild.me
    if not me or not me.guild_permissions.manage_channels:
        await ctx.send('Missing Manage Channels permission for the Community bot.')
        return
    progress = await ctx.send('Building missing ICRP categories and channels now. Existing channels will be preserved.')
    counts = [0, 0]
    failures = []
    for cat_data in TEMPLATE['categories']:
        try:
            category = discord.utils.get(guild.categories, name=cat_data['name'])
            if category is None:
                category = await guild.create_category(
                    cat_data['name'], overwrites=can_view(guild, cat_data['access']) or {},
                    reason='ICRP channel-only setup')
                counts[0] += 1
            present = {(ch.name, 'voice' if isinstance(ch, discord.VoiceChannel) else 'text')
                       for ch in category.channels}
            for ch_data in cat_data['channels']:
                key = (ch_data['name'], ch_data['type'])
                if key in present:
                    continue
                try:
                    if ch_data['type'] == 'voice':
                        await guild.create_voice_channel(ch_data['name'], category=category,
                                                         user_limit=ch_data.get('limit', 0),
                                                         reason='ICRP channel-only setup')
                    else:
                        await guild.create_text_channel(ch_data['name'], category=category,
                                                        reason='ICRP channel-only setup')
                    counts[1] += 1
                    present.add(key)
                    if counts[1] % 20 == 0:
                        print(f'ICRP channel build progress: {counts[1]} channels created', flush=True)
                    await asyncio.sleep(0.18)
                except (discord.HTTPException, discord.Forbidden) as e:
                    failures.append(f"{cat_data['name']}/{ch_data['name']}: {e}")
        except (discord.HTTPException, discord.Forbidden) as e:
            failures.append(f"{cat_data['name']}: {e}")
    await progress.edit(content=f'Channel build finished: {counts[0]} categories and {counts[1]} channels created; '
                                f'{len(failures)} errors. Nothing was deleted.'
                                + (' First errors: ' + '; '.join(failures[:2])[:450] if failures else ''))
    print(f'ICRP channel build finished: {counts}, errors={len(failures)}', flush=True)


@bot.command(name='setup_icrp')
async def setup_icrp(ctx, confirm=''):
    if not await allowed(ctx): return
    if confirm != 'CONFIRM':
        await ctx.send('Non-destructive setup. Run !setup_icrp CONFIRM. It creates missing items only.')
        return
    guild=ctx.guild
    me=guild.me
    if not me or not me.guild_permissions.manage_channels or not me.guild_permissions.manage_roles:
        await ctx.send('Bot requires Manage Channels and Manage Roles; role hierarchy must permit changes.')
        return
    created,failures=await install_template(guild)
    await ctx.send(f'ICRP Community setup complete: created {created[0]} roles, {created[1]} categories, {created[2]} channels. '
                   f'{len(failures)} errors. Existing roles/categories unchanged. '
                   + ('Errors: '+ '; '.join(failures[:2])[:500] if failures else ''))


async def install_template(guild):
    created=[0,0,0]; failures=[]
    # Lower-priority roles first; never elevate any role higher than the setup bot's own highest role.
    for r in reversed(TEMPLATE['roles']):
        if discord.utils.get(guild.roles,name=r['name']): continue
        try:
            await guild.create_role(name=r['name'], permissions=role_perms(r['name'],r['tier']),
                                    mentionable=False, hoist=r['tier'] in ('owner','lead','moderator'),
                                    reason='ICRP ICRP Community template installation')
            created[0]+=1
        except discord.HTTPException as e: failures.append(f"Role {r['name']}: {e}")
    for c in TEMPLATE['categories']:
        category=discord.utils.get(guild.categories,name=c['name'])
        try:
            ow=can_view(guild,c['access'])
            if not category:
                category=await guild.create_category(c['name'], overwrites=ow or {},
                                                     reason='ICRP ICRP Community template installation')
                created[1]+=1
            present={(ch.name,'voice' if isinstance(ch,discord.VoiceChannel) else 'text') for ch in category.channels}
            for ch in c['channels']:
                if (ch['name'],ch['type']) in present: continue
                if ch['type']=='voice':
                    await guild.create_voice_channel(ch['name'], category=category, user_limit=ch.get('limit',0),
                                                      reason='ICRP ICRP Community voice channel')
                else:
                    await guild.create_text_channel(ch['name'], category=category,
                                                    reason='ICRP ICRP Community text channel')
                created[2]+=1
                await asyncio.sleep(.18)
        except discord.HTTPException as e: failures.append(f"Category {c['name']}: {e}")
    return created, failures





# Full reset: separately preview, arm, and confirm a fresh one-time challenge.
# Never remove managed roles, @everyone, or the server owner's ICRP owner role.
RESET_ARMED = {}  # (guild id, owner id): (one-time confirmation code, expiry)


def reset_targets(guild):
    me = guild.me
    if me is None:
        return [], [], ['Setup bot is not present as a guild member']
    channels = list(guild.channels)
    # Managed bot/integration roles cannot be deleted using the API.
    roles = [r for r in guild.roles if not r.is_default() and not r.managed and r.name != OWNER_NAME]
    blocked = [r.name for r in roles if r >= me.top_role]
    return channels, roles, blocked


@bot.command(name='preview_icrp_reset')
async def preview_icrp_reset(ctx):
    if not await allowed(ctx): return
    channels, roles, blocked = reset_targets(ctx.guild)
    preserved = [r.name for r in ctx.guild.roles if r.managed or r.is_default() or r.name == OWNER_NAME]
    await ctx.send(
        f'ICRP Community FULL RESET PREVIEW: Would permanently DELETE {len(channels)} channels '
        f'(including voice, categories and all message history), and {len(roles)} removable roles; '
        f'REBUILD {len(TEMPLATE["roles"])} template roles, {len(TEMPLATE["categories"])} categories, '
        f'{sum(len(c["channels"]) for c in TEMPLATE["categories"])} text/voice channels. '
        f'Preserves @everyone, existing {OWNER_NAME} and managed/bot roles '
        f'({len(preserved)} roles total). '
        + (f'BLOCKED by bot hierarchy: {", ".join(blocked[:8])}. Fix before resetting.' if blocked else
           'No role hierarchy blockers found. Backup messages and save important content first.')
    )


@bot.command(name='arm_icrp_reset')
async def arm_icrp_reset(ctx, confirmation=''):
    if not await allowed(ctx): return
    if not WIPE_ENABLED:
        await ctx.send('Full wipe is DISABLED. Set ICRP_ALLOW_FULL_WIPE=true in the bot environment and restart to enable it.')
        return
    if confirmation != 'I_UNDERSTAND_PERMANENT_DELETION':
        await ctx.send('To arm a FULL RESET, run !arm_icrp_reset I_UNDERSTAND_PERMANENT_DELETION. '
                       'This will delete all existing channels/messages and removable roles when confirmed.')
        return
    g=ctx.guild
    me=g.me
    if not me or not me.guild_permissions.manage_roles or not me.guild_permissions.manage_channels:
        await ctx.send('Setup bot needs Manage Roles and Manage Channels; no reset armed.')
        return
    _, roles, blocked = reset_targets(g)
    if blocked:
        await ctx.send('RESET REFUSED. These roles are at or above the setup bot role: '+', '.join(blocked[:15]))
        return
    # A server with bots positioned below removable staff roles must be audited before reset.
    code=secrets.token_hex(4).upper()
    RESET_ARMED[(g.id, ctx.author.id)] = (code, time.monotonic()+120)
    await ctx.send(f'RESET ARMED for 2 minutes in server ID {g.id}. '
                   f'FINAL WARNING: deleting ALL channels (and their messages), including this channel, '
                   f'and {len(roles)} removable non-bot roles. '
                   f'To proceed, run !confirm_icrp_reset {code} {g.id}. '
                   'Do not run this on your Network Hub.')


@bot.command(name='confirm_icrp_reset')
async def confirm_icrp_reset(ctx, code='', server_id=''):
    if not await allowed(ctx): return
    if not WIPE_ENABLED:
        await ctx.send('Full wipe is disabled by ICRP_ALLOW_FULL_WIPE.')
        return
    key=(ctx.guild.id,ctx.author.id)
    entry=RESET_ARMED.pop(key,None)
    if not entry or time.monotonic()>entry[1] or code!=entry[0] or server_id!=str(ctx.guild.id):
        await ctx.send('Invalid/expired reset confirmation. Start again with !preview_icrp_reset and !arm_icrp_reset.')
        return
    g=ctx.guild
    channels, roles, blocked=reset_targets(g)
    if blocked:
        await ctx.send('RESET CANCELLED: bot hierarchy changed. Resolve: '+', '.join(blocked[:8]))
        return
    if not g.me.guild_permissions.manage_channels or not g.me.guild_permissions.manage_roles:
        await ctx.send('RESET CANCELLED: Manage Channels/Manage Roles missing.')
        return
    try:
        await ctx.author.send(f'ICRP ICRP Community reset started on server {g.name} ({g.id}). '
                              'The command channel will be deleted. Check this DM and Codespaces terminal for progress.')
    except discord.HTTPException:
        await ctx.send('Could not DM you. Progress will only be visible in Codespaces terminal.')
    print(f'ICRP ICRP Community reset BEGIN guild={g.id}: {len(channels)} channels, {len(roles)} removable roles',flush=True)
    errors=[]
    # Delete non-category channels first; then categories.
    for ch in sorted(channels,key=lambda c: isinstance(c,discord.CategoryChannel)):
        try:
            await ch.delete(reason=f'ICRP Community full reset expressly confirmed by Discord owner {ctx.author.id}')
            await asyncio.sleep(.25)
        except discord.HTTPException as e:
            errors.append(f'Channel {ch.name}: {e}')
    for r in roles:
        try:
            await r.delete(reason=f'ICRP Community full reset expressly confirmed by Discord owner {ctx.author.id}')
            await asyncio.sleep(.25)
        except discord.HTTPException as e:
            errors.append(f'Role {r.name}: {e}')
    # Run builder directly, without needing the command channel to survive.
    created, build_errors = await install_template(g)
    errors.extend(build_errors)
    report=(f'ICRP ICRP Community reset finished. Created {created[0]} roles, {created[1]} categories, '
            f'{created[2]} channels. Errors: {len(errors)}. '
            'Run !audit_icrp after opening a new command channel. '
            'Reinvite/configure external bots as needed; managed bot roles were preserved.')
    print(report,flush=True)
    if errors: print('Reset errors:', '\n'.join(errors[:30]),flush=True)
    try: await ctx.author.send(report)
    except discord.HTTPException: pass

@bot.command(name='audit_icrp')
async def audit_icrp(ctx):
    if not await allowed(ctx): return
    guild=ctx.guild
    owner=discord.utils.get(guild.roles,name=OWNER_NAME)
    bot_roles=sorted([r for r in guild.roles if r.managed and r.tags and r.tags.bot_id],key=lambda r:r.position,reverse=True)
    # Existing bot role positions are NOT changed automatically; moving privileged roles can break security.
    items=[]
    for r in bot_roles[:12]:
        checks=[]
        if owner and r.position >= owner.position: checks.append('NOT BELOW OWNER')
        if r.permissions.administrator: checks.append('ADMIN ENABLED')
        managed=[x for x in guild.roles if x.name.startswith('ICRP |') and x != owner]
        if managed and r.position <= max(x.position for x in managed): checks.append('BELOW SOME ICRP ROLES')
        items.append(f'{r.name} [position {r.position}] '+(', '.join(checks) if checks else 'OK'))
    if not bot_roles: items.append('No managed third-party bot roles found.')
    await ctx.send('BOT HIERARCHY AUDIT (no changes):\n'+'\n'.join(items)[:1700]+
                   '\nArrange in Server Settings > Roles: Owner > trusted bot roles > staff/moderation roles > members. '
                   'Discord bots can only manage roles below their own highest role. '
                   'Configure each bot dashboard after inviting it.')


@bot.command(name='help_icrp')
async def help_icrp(ctx):
    if not await allowed(ctx): return
    await ctx.send('Commands: !preview_icrp | !setup_icrp CONFIRM | !audit_icrp | !help_icrp. '
                   'Full reset: !preview_icrp_reset then !arm_icrp_reset I_UNDERSTAND_PERMANENT_DELETION.')

bot.run(TOKEN, log_handler=None)
