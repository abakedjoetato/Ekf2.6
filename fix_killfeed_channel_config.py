"""
Fix Killfeed Channel Configuration
Check actual Discord channels and update database config to use existing channels
"""
import asyncio
import logging
from main import EmeraldKillfeedBot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_channel_config():
    """Fix the killfeed channel configuration to use existing Discord channels"""
    try:
        # Access the bot instance
        bot = EmeraldKillfeedBot._instance if hasattr(EmeraldKillfeedBot, '_instance') else None
        
        if not bot:
            logger.error("No bot instance available")
            return
            
        guild_id = 1219706687980568769
        guild = bot.get_guild(guild_id)
        
        if not guild:
            logger.error(f"Guild {guild_id} not found")
            return
            
        logger.info(f"=== Available Channels in {guild.name} ===")
        
        # List all text channels
        text_channels = [ch for ch in guild.channels if hasattr(ch, 'send')]
        
        for channel in text_channels:
            logger.info(f"  {channel.name} (ID: {channel.id})")
        
        # Check current killfeed channel config
        guild_config = await bot.db_manager.get_guild(guild_id)
        if guild_config:
            server_channels = guild_config.get('server_channels', {})
            
            logger.info(f"\n=== Current Killfeed Configuration ===")
            
            # Check Emerald EU specific
            if 'Emerald EU' in server_channels:
                current_killfeed = server_channels['Emerald EU'].get('killfeed')
                logger.info(f"Emerald EU killfeed: {current_killfeed}")
                
                # Check if this channel exists
                if current_killfeed:
                    channel = bot.get_channel(current_killfeed)
                    if channel:
                        logger.info(f"✅ Channel exists: {channel.name}")
                    else:
                        logger.info(f"❌ Channel {current_killfeed} does not exist")
            
            # Check default
            if 'default' in server_channels:
                default_killfeed = server_channels['default'].get('killfeed')
                logger.info(f"Default killfeed: {default_killfeed}")
                
                if default_killfeed:
                    channel = bot.get_channel(default_killfeed)
                    if channel:
                        logger.info(f"✅ Channel exists: {channel.name}")
                    else:
                        logger.info(f"❌ Channel {default_killfeed} does not exist")
        
        # Suggest a working channel
        logger.info(f"\n=== Suggested Fix ===")
        
        # Look for channels that might work for killfeed
        potential_channels = []
        for channel in text_channels:
            name_lower = channel.name.lower()
            if any(keyword in name_lower for keyword in ['kill', 'feed', 'death', 'pvp', 'combat', 'log']):
                potential_channels.append(channel)
        
        if potential_channels:
            logger.info("Potential killfeed channels found:")
            for channel in potential_channels:
                logger.info(f"  {channel.name} (ID: {channel.id})")
        else:
            logger.info("No obvious killfeed channels found. Consider using a general channel.")
            if text_channels:
                logger.info(f"Available general channels: {text_channels[0].name} (ID: {text_channels[0].id})")
        
    except Exception as e:
        logger.error(f"Failed to fix channel config: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(fix_channel_config())