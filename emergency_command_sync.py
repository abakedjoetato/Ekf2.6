"""
Emergency Command Sync - Immediate Recovery
Bypasses rate limits by using alternative sync strategies
"""

import asyncio
import logging
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

async def emergency_command_sync():
    """Emergency command sync to restore functionality"""
    try:
        # Import bot token
        import os
        bot_token = os.environ.get("BOT_TOKEN")
        
        if not bot_token:
            logger.error("BOT_TOKEN not found in environment")
            return False
            
        # Create minimal bot instance for emergency sync
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        bot = commands.Bot(
            command_prefix="!",
            intents=intents,
            help_command=None
        )
        
        @bot.event
        async def on_ready():
            logger.info(f"Emergency sync bot ready: {bot.user}")
            
            try:
                # Try global sync first (slower but more reliable)
                logger.info("Attempting emergency global command sync...")
                synced = await bot.tree.sync()
                logger.info(f"✅ Emergency global sync successful: {len(synced)} commands")
                return True
                
            except discord.HTTPException as e:
                if e.status == 429:
                    logger.warning("Global sync rate limited, trying guild-specific")
                    
                    # Try guild-specific sync
                    for guild in bot.guilds:
                        try:
                            synced = await bot.tree.sync(guild=guild)
                            logger.info(f"✅ Emergency guild sync successful for {guild.name}: {len(synced)} commands")
                            return True
                        except discord.HTTPException as guild_e:
                            if guild_e.status != 429:
                                logger.error(f"Guild sync failed for {guild.name}: {guild_e}")
                            continue
                    
                    logger.warning("All sync attempts rate limited")
                    return False
                else:
                    logger.error(f"Emergency sync failed: {e}")
                    return False
            finally:
                await bot.close()
        
        # Start emergency bot
        await bot.start(bot_token)
        
    except Exception as e:
        logger.error(f"Emergency command sync failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(emergency_command_sync())