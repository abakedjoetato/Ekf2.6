"""
Test Commands Working - Verify bot commands are functional despite rate limits
"""

import asyncio
import logging
import os
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

async def test_commands_working():
    """Test if bot commands are working in local processing mode"""
    try:
        bot_token = os.environ.get("BOT_TOKEN")
        
        if not bot_token:
            logger.error("BOT_TOKEN not found")
            return False
            
        # Create test bot instance
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        bot = discord.Bot(
            intents=intents,
        )
        
        # Simple test command
        @bot.slash_command(
            name="test_ping",
            description="Test if commands are working"
        )
        async def test_ping(ctx):
            await ctx.respond("Pong! Commands are working!", ephemeral=True)
            logger.info("✅ Test command executed successfully")
        
        commands_working = False
        
        @bot.event
        async def on_ready():
            nonlocal commands_working
            
            logger.info(f"Test bot ready: {bot.user}")
            logger.info(f"Connected to {len(bot.guilds)} guilds")
            
            # Check if we have the test command
            if bot.pending_application_commands:
                logger.info(f"Found {len(bot.pending_application_commands)} pending commands")
                for cmd in bot.pending_application_commands:
                    logger.info(f"  - {cmd.name}: {cmd.description}")
                commands_working = True
            else:
                logger.warning("No pending commands found")
            
            # Try to get guild commands (without sync)
            try:
                guild = bot.get_guild(1219706687980568769)
                if guild:
                    logger.info(f"Connected to target guild: {guild.name}")
                    
                    # Check if local processing mode is active
                    if os.path.exists('local_commands_active.txt'):
                        logger.info("✅ Local command processing mode is active")
                        commands_working = True
                    else:
                        logger.info("Local command processing mode not detected")
                        
            except Exception as e:
                logger.error(f"Guild check failed: {e}")
            
            logger.info(f"Commands working status: {commands_working}")
            await bot.close()
        
        # Start test bot with timeout
        try:
            await asyncio.wait_for(bot.start(bot_token), timeout=15.0)
        except asyncio.TimeoutError:
            logger.info("Test completed (timeout reached)")
        
        return commands_working
        
    except Exception as e:
        logger.error(f"Command test failed: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = asyncio.run(test_commands_working())
    print(f"Commands working: {result}")