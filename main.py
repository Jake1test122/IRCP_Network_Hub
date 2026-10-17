import os, json, asyncio, discord
from discord.ext import commands

ROOT=os.path.dirname(os.path.abspath(__file__))
def load(name):
    with open(os.path.join(ROOT,name),encoding='utf-8') as f: return json.load(f)
CFG=load('config.json'); POSTS=load('posts.json'); ROLE_TIERS=load('role_permissions.json')
TOKEN=os.environ.get('DISCORD_TOKEN','').strip()
GUILD_ID=int(os.environ.get('SERVER_ID','0'))
if not TOKEN or not GUILD_ID: raise SystemExit('Set DISCORD_TOKEN and SERVER_ID before running.')
intents=discord.Intents.default(); intents.message_content=True
bot=commands.Bot(command_prefix='!',intents=intents,help_command=None)

async def authorize(ctx, owner_only=False):
    if not ctx.guild or ctx.guild.id != GUILD_ID:
        await ctx.send('Wrong server: this bot is locked to the configured NETWORK HUB ID.'); return False
    if not ctx.author.guild_permissions.administrator:
        await ctx.send('Administrator permission required.'); return False
    if owner_only and ctx.author.id != ctx.guild.owner_id:
        await ctx.send('Only the server owner can perform a full wipe.'); return False
    if not ctx.guild.me.guild_permissions.manage_channels or not ctx.guild.me.guild_permissions.manage_roles:
        await ctx.send('Bot requires Manage Channels and Manage Roles permissions.'); return False
    return True

def expected_names():
    return {name for entries in CFG['categories'].values() for name,kind in entries}

# Conservative permissions: only three owner-level roles get Administrator.
# Existing roles are not overwritten until the server owner explicitly confirms.
MENTION_ALLOWED_ROLES = {'ICRP | Founder','ICRP | Co-Founder','ICRP | Owner',
                         'ICRP | Head Director','ICRP | Deputy Head Director'}
def permissions_for_tier(tier, role_name=''):
    if tier=='admin': return discord.Permissions(administrator=True)
    if tier=='lead': return discord.Permissions(mention_everyone=role_name in MENTION_ALLOWED_ROLES,
        view_channel=True, send_messages=True, read_message_history=True,
        manage_guild=True, manage_channels=True, manage_roles=True,
        manage_messages=True, moderate_members=True, kick_members=True)
    if tier=='moderator': return discord.Permissions(
        view_channel=True, send_messages=True, read_message_history=True,
        manage_messages=True, moderate_members=True, kick_members=True)
    if tier=='hr': return discord.Permissions(
        view_channel=True, send_messages=True, read_message_history=True,
        manage_messages=True)
    if tier=='staff': return discord.Permissions(
        view_channel=True, send_messages=True, read_message_history=True)
    return discord.Permissions(view_channel=True,send_messages=True,read_message_history=True,
                               connect=True,speak=True,add_reactions=True)

def private_overwrites(guild,category_name):
    if category_name not in ('[Human Resources]','OFFICES'): return None
    allowed={'admin','lead','moderator','hr','staff'}
    overwrites={guild.default_role:discord.PermissionOverwrite(view_channel=False)}
    for role in guild.roles:
        if ROLE_TIERS.get(role.name) in allowed:
            overwrites[role]=discord.PermissionOverwrite(view_channel=True,
                send_messages=True,read_message_history=True,connect=True,speak=True)
    return overwrites

async def lock_default_mentions(guild):
    default=guild.default_role
    if default.permissions.mention_everyone:
        perms=default.permissions
        perms.update(mention_everyone=False)
        await default.edit(permissions=perms,reason='ICRP restrict @everyone and @here')

async def apply_role_permissions(guild):
    await lock_default_mentions(guild)
    me=guild.me
    changed=[]; skipped=[]
    for name,tier in ROLE_TIERS.items():
        role=discord.utils.get(guild.roles,name=name)
        if not role or role.managed or role.is_default(): continue
        if me is None or role >= me.top_role:
            skipped.append(name); continue
        desired=permissions_for_tier(tier,name)
        if role.permissions != desired:
            try:
                await role.edit(permissions=desired,reason='ICRP approved role permissions')
                changed.append(name)
            except discord.HTTPException as exc:
                skipped.append(f'{name}: {exc}')
    return changed,skipped

async def apply_private_categories(guild):
    for name in ('[Human Resources]','OFFICES'):
        cat=discord.utils.get(guild.categories,name=name)
        if not cat: continue
        overwrite=private_overwrites(guild,name)
        await cat.edit(overwrites=overwrite,reason='ICRP private staff category access')
        for ch in cat.channels:
            await ch.edit(sync_permissions=True,reason='ICRP private staff channel access')

async def build(guild):
    await lock_default_mentions(guild)
    for role in reversed(CFG['roles']):
        if not discord.utils.get(guild.roles,name=role):
            await guild.create_role(name=role[:100],permissions=permissions_for_tier(ROLE_TIERS.get(role,'member'),role),reason='ICRP Network Hub build')
            await asyncio.sleep(.25)
    for cname,entries in CFG['categories'].items():
        cat=discord.utils.get(guild.categories,name=cname)
        if not cat: cat=await guild.create_category(cname[:100],overwrites=private_overwrites(guild,cname) or {},reason='ICRP Network Hub build')
        for name,kind in entries:
            if any(ch.name==name and ((isinstance(ch,discord.VoiceChannel))==(kind=='voice')) for ch in cat.channels): continue
            if kind=='voice': await guild.create_voice_channel(name[:100],category=cat,reason='ICRP Network Hub build')
            else: await guild.create_text_channel(name[:100],category=cat,reason='ICRP Network Hub build')
            await asyncio.sleep(.25)

async def post_text(guild):
    for name,messages in POSTS.items():
        ch=discord.utils.get(guild.text_channels,name=name)
        if not ch: continue
        if not ch.permissions_for(guild.me).send_messages: continue
        # Don't duplicate posts on reruns: use a recognizable marker.
        async for old in ch.history(limit=100):
            if old.author.id==bot.user.id and old.content.startswith('[ICRP HUB CONTENT]'):
                try: await old.delete()
                except discord.Forbidden: pass
        for msg in messages:
            for offset in range(0,len(msg),1800):
                await ch.send('[ICRP HUB CONTENT]\n'+msg[offset:offset+1800],allowed_mentions=discord.AllowedMentions.none())

async def remove_hub_channels(guild, command_channel):
    expected=expected_names(); cats=set(CFG['categories'])
    # Only delete channels with expected names in expected categories.
    targets=[ch for ch in guild.channels if ch.id!=command_channel.id and ch.category and ch.category.name in cats and ch.name in expected]
    for ch in targets:
        await ch.delete(reason='ICRP Network Hub targeted rebuild')
        await asyncio.sleep(.3)
    # Keep the command channel alive, and never delete unrelated categories/channels.
    for cat in list(guild.categories):
        if cat.name in cats and not cat.channels: await cat.delete(reason='ICRP Hub targeted rebuild')
    return len(targets)

@bot.event
async def on_ready():
    print('ICRP Network Hub bot ready:',bot.user,'target server:',GUILD_ID)

@bot.command()
async def hub_status(ctx):
    if not await authorize(ctx): return
    await ctx.send(f'Network Hub target: {GUILD_ID}. Existing channels: {len(ctx.guild.channels)}. Expected Hub channels: {len(expected_names())}. Use !setup_hub, !preview_hub, !rebuild_hub CONFIRM or !wipe_hub_all CONFIRM_ALL_CHANNELS.')

@bot.command()
async def setup_hub(ctx):
    if not await authorize(ctx): return
    await ctx.send('Creating missing Network Hub roles and channels. Existing unrelated content will be left alone.')
    try:
        await build(ctx.guild); await apply_private_categories(ctx.guild); await post_text(ctx.guild)
        await ctx.send('ICRP Network Hub setup complete. Verify role hierarchy, permissions, and bot access.')
    except discord.HTTPException as e: await ctx.send(f'Setup failed: {e}')

@bot.command()
async def preview_hub(ctx):
    if not await authorize(ctx): return
    cats=set(CFG['categories']); names=expected_names()
    matched=[ch for ch in ctx.guild.channels if ch.category and ch.category.name in cats and ch.name in names]
    await ctx.send(f'Targeted rebuild would delete {len(matched)} matching Hub channels (and their messages) then recreate them. Unrelated channels remain. Full wipe would delete ALL {len(ctx.guild.channels)} channels. Back up messages first.')

@bot.command()
async def rebuild_hub(ctx, confirmation=''):
    if not await authorize(ctx): return
    if confirmation!='CONFIRM':
        await ctx.send('Destructive: deletes matching Hub channels and their message history. Run !rebuild_hub CONFIRM to proceed.'); return
    try:
        n=await remove_hub_channels(ctx.guild,ctx.channel)
        await build(ctx.guild); await apply_private_categories(ctx.guild); await post_text(ctx.guild)
        await ctx.send(f'Rebuilt Hub; replaced {n} matching channels. Current command channel was preserved.')
    except discord.HTTPException as e: await ctx.send(f'Rebuild failed: {e}')

@bot.command()
async def wipe_hub_all(ctx, confirmation=''):
    if not await authorize(ctx,owner_only=True): return
    if confirmation!='CONFIRM_ALL_CHANNELS':
        await ctx.send('DANGER: This deletes EVERY channel in this Network Hub server and its messages, including unrelated channels. Server owner only. To continue: !wipe_hub_all CONFIRM_ALL_CHANNELS'); return
    guild=ctx.guild
    await ctx.send('Full channel wipe started. This is irreversible. The command channel will be deleted last.')
    try:
        for ch in list(guild.channels):
            if ch.id==ctx.channel.id or isinstance(ch,discord.CategoryChannel): continue
            await ch.delete(reason='ICRP Hub owner-requested full channel wipe'); await asyncio.sleep(.3)
        for cat in list(guild.categories):
            if cat.channels and any(ch.id==ctx.channel.id for ch in cat.channels): continue
            if not cat.channels: await cat.delete(reason='ICRP Hub full wipe')
        await build(guild); await apply_private_categories(guild); await post_text(guild)
        status=discord.utils.get(guild.text_channels,name='【💬】general-chat')
        if status: await status.send('ICRP Network Hub full channel rebuild completed. Review channel and role permissions.')
        await ctx.channel.delete(reason='ICRP Hub full wipe: remove old command channel')
    except discord.HTTPException as e:
        print('Full wipe incomplete:',e)
        try: await ctx.send(f'Full wipe stopped: {e}')
        except Exception: pass

@bot.command()
async def preview_hub_permissions(ctx):
    if not await authorize(ctx): return
    counts={}
    for tier in ROLE_TIERS.values(): counts[tier]=counts.get(tier,0)+1
    await ctx.send('ICRP permission tiers: '+str(counts)+
       '\\nOnly Founder, Co-Founder and Owner have Administrator in the template.'+
       '\\nTo UPDATE existing roles and lock staff categories, server owner runs: !apply_hub_permissions CONFIRM')

@bot.command()
async def apply_hub_permissions(ctx,confirmation=''):
    if not await authorize(ctx,owner_only=True): return
    if confirmation!='CONFIRM':
        await ctx.send('This changes permissions on existing ICRP roles and staff categories. Server owner only. Run !apply_hub_permissions CONFIRM'); return
    try:
        changed,skipped=await apply_role_permissions(ctx.guild)
        await apply_private_categories(ctx.guild)
        await ctx.send(f'Updated {len(changed)} roles; skipped {len(skipped)} (usually hierarchy restrictions). Staff areas restricted. Review Discord audit log.')
    except discord.HTTPException as e: await ctx.send(f'Permissions update incomplete: {e}')

@bot.command()
async def hub_invites(ctx):
    if not await authorize(ctx): return
    await ctx.send('Other bots cannot be installed by this bot. Use Discord App Directory or official developer invite links. Review requested permissions, then invite ticket, moderation/logging, application, and verification bots you actually use. Do not grant Administrator unless required.')

@bot.event
async def on_command_error(ctx,error):
    if isinstance(error,commands.CommandNotFound): return
    print('Command error:',repr(error))
    try: await ctx.send(f'Error: {str(error)[:300]}')
    except Exception: pass

bot.run(TOKEN)
