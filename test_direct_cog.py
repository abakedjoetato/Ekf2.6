#!/usr/bin/env python3
"""
Test direct cog registration without load_extension
"""

import asyncio
import discord
from discord.ext import commands

class TestCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @discord.slash_command(name="test", description="Test command")
    async def test_command(self, ctx):
        await ctx.respond("Direct cog registration working!")

async def test_direct_registration():
    """Test direct cog registration bypassing load_extension"""
    
    intents = discord.Intents.default()
    intents.message_content = True
    
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    try:
        print("Testing direct cog registration...")
        
        # Direct registration instead of load_extension
        cog = TestCog(bot)
        bot.add_cog(cog)
        
        print("✅ Successfully registered cog directly")
        
        # Check if commands were loaded
        commands_count = len(bot.application_commands) if hasattr(bot, 'application_commands') else 0
        print(f"✅ Commands loaded: {commands_count}")
        
    except Exception as e:
        print(f"❌ Failed to register cog: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
    
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(test_direct_registration())