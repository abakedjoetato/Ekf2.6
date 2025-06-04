"""
Check User Configured Channels - Show only channels configured via /setchannel commands
"""

import asyncio
import logging
import os
import discord
from motor.motor_asyncio import AsyncIOMotorClient
from bot.models.database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_user_configured_channels():
    """Check what channels the user actually configured via /setchannel commands"""
    
    try:
        # Connect to database
        mongo_uri = os.environ.get('MONGO_URI')
        client = AsyncIOMotorClient(mongo_uri)
        db_manager = DatabaseManager(client)
        
        # Get Discord bot token
        bot_token = os.environ.get('BOT_TOKEN')
        if not bot_token:
            logger.error("BOT_TOKEN not found")
            return
        
        # Create Discord client to get actual channel names
        intents = discord.Intents.default()
        discord_client = discord.Client(intents=intents)
        
        @discord_client.event
        async def on_ready():
            try:
                guild_id = 1219706687980568769
                
                guild = discord_client.get_guild(guild_id)
                if not guild:
                    logger.error(f"Guild {guild_id} not found")
                    await discord_client.close()
                    return
                
                # Get guild configuration
                guild_config = await db_manager.get_guild(guild_id)
                
                if not guild_config:
                    logger.error("No guild configuration found")
                    await discord_client.close()
                    return
                
                logger.info("=== USER CONFIGURED CHANNELS (via /setchannel) ===")
                
                # Check server_channels structure
                server_channels = guild_config.get('server_channels', {})
                
                if not server_channels:
                    logger.info("NO CHANNELS CONFIGURED via /setchannel")
                    await discord_client.close()
                    return
                
                # Show what's actually configured for each server
                for server_name, channels in server_channels.items():
                    logger.info(f"\nServer: {server_name}")
                    
                    if not channels:
                        logger.info("  No channels configured for this server")
                        continue
                    
                    for embed_type, channel_id in channels.items():
                        if channel_id:
                            # Get actual Discord channel name
                            discord_channel = guild.get_channel(channel_id)
                            
                            if discord_channel:
                                logger.info(f"  {embed_type}: #{discord_channel.name} (ID: {channel_id})")
                            else:
                                logger.info(f"  {embed_type}: INVALID CHANNEL (ID: {channel_id})")
                        else:
                            logger.info(f"  {embed_type}: NOT CONFIGURED")
                
                # Now check what the current server (7020) will actually use
                logger.info("\n=== ACTUAL ROUTING FOR SERVER 7020 ===")
                
                # Check if there's a specific configuration for "Emerald EU" server
                emerald_eu_config = server_channels.get('Emerald EU', {})
                default_config = server_channels.get('default', {})
                
                embed_types = ['killfeed', 'events', 'missions', 'helicrash', 'airdrop', 'trader']
                
                for embed_type in embed_types:
                    # Check server-specific first, then default
                    channel_id = emerald_eu_config.get(embed_type) or default_config.get(embed_type)
                    
                    if channel_id:
                        discord_channel = guild.get_channel(channel_id)
                        if discord_channel:
                            logger.info(f"{embed_type.upper()}: #{discord_channel.name}")
                        else:
                            logger.info(f"{embed_type.upper()}: INVALID CHANNEL (ID: {channel_id})")
                    else:
                        logger.info(f"{embed_type.upper()}: NOT CONFIGURED")
                
            except Exception as e:
                logger.error(f"Error checking configured channels: {e}")
                import traceback
                traceback.print_exc()
            
            finally:
                await discord_client.close()
        
        # Start Discord client
        await discord_client.start(bot_token)
        
    except Exception as e:
        logger.error(f"Failed to check configured channels: {e}")

async def main():
    """Check user configured channels"""
    await check_user_configured_channels()

if __name__ == "__main__":
    asyncio.run(main())