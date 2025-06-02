#!/usr/bin/env python3
"""
Simple test bot to verify basic Discord functionality without complex cogs
"""

import os
import sys

# Test Discord import
try:
    import discord
    from discord.ext import commands
    print(f"✅ Discord library loaded: {discord.__version__}")
    print(f"✅ Has AutocompleteContext: {hasattr(discord, 'AutocompleteContext')}")
    print(f"✅ Has SlashCommandGroup: {hasattr(discord, 'SlashCommandGroup')}")
    discord_available = True
except ImportError as e:
    print(f"❌ Discord import failed: {e}")
    discord_available = False

if discord_available:
    # Simple bot setup
    intents = discord.Intents.default()
    intents.message_content = True
    
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    @bot.event
    async def on_ready():
        print(f"✅ Bot connected: {bot.user}")
        print(f"✅ Connected to {len(bot.guilds)} guilds")
        
        # Test command registration
        commands_count = len(bot.application_commands) if hasattr(bot, 'application_commands') else 0
        print(f"✅ Application commands available: {commands_count}")
    
    @bot.slash_command(name="test", description="Simple test command")
    async def test_command(ctx):
        await ctx.respond("✅ Test command working!")
    
    # Get bot token
    token = os.getenv('BOT_TOKEN')
    if token:
        print("🚀 Starting simple bot test...")
        bot.run(token)
    else:
        print("❌ BOT_TOKEN not found")
else:
    print("❌ Cannot test bot - Discord library not available")