import discord
from discord.ext import commands
import os
import sys
import logging
from datetime import datetime, timedelta
import asyncio
from dotenv import load_dotenv
import time
import json
import traceback

# Set up logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

# Constants
POLL_OPTIONS = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
OWNER_ID = None
START_TIME = datetime.now()

# Initialize bot with all intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Utility Functions
async def notify_owner(message, error=False):
    """Send a DM to the bot owner"""
    if OWNER_ID:
        try:
            owner = await bot.fetch_user(OWNER_ID)
            if owner:
                embed = discord.Embed(
                    title="🔴 Error Alert" if error else "Bot Status Notification",
                    description=message,
                    color=discord.Color.red() if error else discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                await owner.send(embed=embed)
        except Exception as e:
            logging.error(f"Failed to notify owner: {str(e)}")

def load_custom_responses():
    """Load custom responses from JSON file"""
    try:
        with open('custom_responses.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_custom_responses(responses):
    """Save custom responses to JSON file"""
    with open('custom_responses.json', 'w') as f:
        json.dump(responses, f, indent=4)

# Events
@bot.event
async def on_ready():
    logging.info(f'{bot.user} has connected to Discord!')
    await bot.change_presence(activity=discord.Game(name="!commands for help"))
    await notify_owner(f"🟢 Bot is now online and ready!\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check for welcome channel in all guilds
    for guild in bot.guilds:
        welcome = discord.utils.get(guild.text_channels, name='welcome')
        if not welcome:
            try:
                welcome = await guild.create_text_channel('welcome')
                logging.info(f'Created welcome channel in {guild.name}')
                await welcome.send("👋 Welcome channel has been created!")
            except Exception as e:
                logging.error(f"Failed to create welcome channel in {guild.name}: {str(e)}")

@bot.event
async def on_member_join(member):
    """Welcome new members"""
    # Send welcome message
    welcome_channel = discord.utils.get(member.guild.text_channels, name='welcome')
    if welcome_channel:
        embed = discord.Embed(
            title="Welcome to the Server! 🎉",
            description=f"Welcome {member.mention}! We're glad to have you here!\n\n"
                       f"• Use !commands to see available commands\n"
                       f"• Check out our rules channel\n"
                       f"• Have fun!",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f"Member #{len(member.guild.members)}")
        await welcome_channel.send(embed=embed)
    
    # Give default role if it exists
    default_role = discord.utils.get(member.guild.roles, name="Member")
    if default_role:
        await member.add_roles(default_role)

@bot.event
async def on_member_remove(member):
    """Log when members leave"""
    logging.info(f"Member {member.name} has left {member.guild.name}")
    welcome_channel = discord.utils.get(member.guild.text_channels, name='welcome')
    if welcome_channel:
        embed = discord.Embed(
            title="Member Left",
            description=f"**{member.name}** has left the server",
            color=discord.Color.red()
        )
        await welcome_channel.send(embed=embed)

# Admin Commands
@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    """Kick a member from the server"""
    try:
        await member.kick(reason=reason)
        embed = discord.Embed(
            title="Member Kicked",
            description=f"{member.name} has been kicked | Reason: {reason}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        await notify_owner(f"Member {member.name} was kicked from {ctx.guild.name} by {ctx.author.name}")
    except Exception as e:
        await ctx.send(f"Failed to kick member: {str(e)}")

@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    """Ban a member from the server"""
    try:
        await member.ban(reason=reason)
        embed = discord.Embed(
            title="Member Banned",
            description=f"{member.name} has been banned | Reason: {reason}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        await notify_owner(f"Member {member.name} was banned from {ctx.guild.name} by {ctx.author.name}")
    except Exception as e:
        await ctx.send(f"Failed to ban member: {str(e)}")

@bot.command(name='clear')
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    """Clear a specified number of messages"""
    if amount > 100:
        await ctx.send("Cannot delete more than 100 messages at once.")
        return
    deleted = await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f'Cleared {len(deleted)-1} messages')
    await asyncio.sleep(3)
    await msg.delete()

@bot.command(name='slowmode')
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, seconds: int):
    """Set slowmode for the channel"""
    try:
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(f"Slowmode set to {seconds} seconds")
    except Exception as e:
        await ctx.send(f"Failed to set slowmode: {str(e)}")

@bot.command(name='lock')
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    """Lock the channel"""
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("🔒 Channel locked")

@bot.command(name='unlock')
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    """Unlock the channel"""
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send("🔓 Channel unlocked")

# Utility Commands
@bot.command(name='ping')
async def ping(ctx):
    """Check bot's latency"""
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Bot Latency: {latency}ms",
        color=discord.Color.green() if latency < 100 else discord.Color.orange()
    )
    await ctx.send(embed=embed)

@bot.command(name='uptime')
async def uptime(ctx):
    """Show bot's uptime"""
    uptime = datetime.now() - START_TIME
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)
    
    embed = discord.Embed(
        title="Bot Uptime",
        description=f"Online for: {days}d {hours}h {minutes}m {seconds}s",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

@bot.command(name='serverinfo')
async def serverinfo(ctx):
    """Display detailed server information"""
    guild = ctx.guild
    
    # Get channel counts
    text_channels = len(guild.text_channels)
    voice_channels = len(guild.voice_channels)
    categories = len(guild.categories)
    total_channels = text_channels + voice_channels
    
    # Get member counts
    total_members = guild.member_count
    online_members = sum(1 for m in guild.members if m.status != discord.Status.offline)
    bot_count = sum(1 for m in guild.members if m.bot)
    
    embed = discord.Embed(
        title=f"Server Information - {guild.name}",
        color=discord.Color.blue()
    )
    
    # General Info
    embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
    embed.add_field(name="Region", value=str(guild.region).title(), inline=True)
    embed.add_field(name="Created On", value=guild.created_at.strftime("%B %d, %Y"), inline=True)
    
    # Channel Info
    embed.add_field(name="Categories", value=categories, inline=True)
    embed.add_field(name="Text Channels", value=text_channels, inline=True)
    embed.add_field(name="Voice Channels", value=voice_channels, inline=True)
    
    # Member Info
    embed.add_field(name="Total Members", value=total_members, inline=True)
    embed.add_field(name="Human Members", value=total_members - bot_count, inline=True)
    embed.add_field(name="Bots", value=bot_count, inline=True)
    
    # Server Features
    embed.add_field(name="Roles", value=len(guild.roles), inline=True)
    embed.add_field(name="Emojis", value=len(guild.emojis), inline=True)
    embed.add_field(name="Boost Level", value=f"Level {guild.premium_tier}", inline=True)
    
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    await ctx.send(embed=embed)

@bot.command(name='poll')
async def create_poll(ctx, duration: int, question: str, *options):
    """Create a poll with reactions and timer"""
    if len(options) < 2:
        await ctx.send("You need at least 2 options for a poll!")
        return
    if len(options) > 10:
        await ctx.send("Maximum 10 options allowed!")
        return
    
    # Create embed for poll
    embed = discord.Embed(
        title="📊 " + question,
        description="\n".join(f"{POLL_OPTIONS[idx]} {option}" for idx, option in enumerate(options)),
        color=discord.Color.blue()
    )
    
    end_time = datetime.now() + timedelta(minutes=duration)
    embed.set_footer(text=f"Poll ends: {end_time.strftime('%Y-%m-%d %H:%M:%S')} | Started by: {ctx.author.name}")
    
    # Send poll and add reactions
    poll_message = await ctx.send(embed=embed)
    for idx in range(len(options)):
        await poll_message.add_reaction(POLL_OPTIONS[idx])
    
    # Wait for poll duration
    await asyncio.sleep(duration * 60)
    
    # Fetch updated message and count votes
    poll_message = await ctx.channel.fetch_message(poll_message.id)
    results = []
    
    for idx, option in enumerate(options):
        reaction = discord.utils.get(poll_message.reactions, emoji=POLL_OPTIONS[idx])
        count = reaction.count - 1  # Subtract bot's reaction
        results.append((option, count))
    
    # Sort and create results embed
    results.sort(key=lambda x: x[1], reverse=True)
    winner = results[0][0]
    
    results_embed = discord.Embed(
        title="📊 Poll Results: " + question,
        description=f"**Winner: {winner}**\n\n" + "\n".join(f"{option}: {count} votes" for option, count in results),
        color=discord.Color.green()
    )
    results_embed.set_footer(text=f"Poll ended | Started by: {ctx.author.name}")
    
    await ctx.send(embed=results_embed)

@bot.command(name='help')
async def show_help(ctx):
    """Show detailed help information"""
    embed = discord.Embed(
        title="🤖 Bot Commands Help",
        description="Here's a list of all available commands:",
        color=discord.Color.blue()
    )
    
    # Admin Commands
    admin_commands = """
    `!kick @user [reason]` - Kick a member
    `!ban @user [reason]` - Ban a member
    `!clear [number]` - Clear messages
    `!slowmode [seconds]` - Set channel slowmode
    `!lock` - Lock the channel
    `!unlock` - Unlock the channel
    """
    embed.add_field(name="👑 Admin Commands", value=admin_commands, inline=False)
    
    # Utility Commands
    utility_commands = """
    `!ping` - Check bot latency
    `!uptime` - Show bot uptime
    `!serverinfo` - Display server information
    `!poll [duration] [question] [options]` - Create a poll
    `!help` - Show this help message
    """
    embed.add_field(name="🛠️ Utility Commands", value=utility_commands, inline=False)
    
    # Usage Examples
    examples = """
    Poll: `!poll 5 "What's for dinner?" "Pizza" "Burger" "Salad"`
    Clear: `!clear 10`
    """
    embed.add_field(name="📝 Examples", value=examples, inline=False)
    
    await ctx.send(embed=embed)

# Error Handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f"❌ Sorry {ctx.author.mention}, you don't have permission to use this command!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument. Use !help to see command usage.")
    else:
        error_message = f"Error in {ctx.guild.name}/{ctx.channel.name}:\n{str(error)}\n\n{traceback.format_exc()}"
        logging.error(error_message)
        await notify_owner(error_message, error=True)
        await ctx.send("❌ An error occurred. The bot owner has been notified.")