#!/usr/bin/env python3
"""
Test individual cog loading to diagnose the issue
"""

import asyncio
import discord
from discord.ext import commands

async def test_cog_loading():
    """Test loading a single cog to identify the issue"""
    
    # Create a minimal bot instance
    intents = discord.Intents.default()
    intents.message_content = True
    
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    try:
        print("Testing cog loading...")
        await bot.load_extension('bot.cogs.core')
        print("✅ Successfully loaded bot.cogs.core")
        
        # Check if commands were loaded
        commands_count = len(bot.application_commands) if hasattr(bot, 'application_commands') else 0
        print(f"✅ Commands loaded: {commands_count}")
        
    except Exception as e:
        print(f"❌ Failed to load cog: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
    
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(test_cog_loading())