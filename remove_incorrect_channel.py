"""
Remove Incorrect Killfeed Channel Configuration
Remove the wrongly set channel ID 1219745194346287226
"""
import asyncio
import os
import motor.motor_asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def remove_incorrect_channel():
    """Remove the incorrectly set killfeed channel"""
    try:
        # Connect to database
        mongo_uri = os.getenv('MONGO_URI')
        client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
        db = client.EmeraldDB
        
        guild_id = 1219706687980568769
        incorrect_channel = 1219745194346287226
        
        logger.info(f"Removing incorrect killfeed channel {incorrect_channel}")
        
        # Remove the incorrect channel configuration
        result = await db.guilds.update_one(
            {"guild_id": guild_id},
            {
                "$unset": {
                    "server_channels.Emerald EU.killfeed": "",
                    "server_channels.default.killfeed": "",
                    "channels.killfeed": ""
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"✅ Successfully removed incorrect killfeed channel configuration")
        else:
            logger.info("No changes made to database")
            
        # Verify removal
        guild_config = await db.guilds.find_one({"guild_id": guild_id})
        if guild_config:
            server_channels = guild_config.get('server_channels', {})
            emerald_killfeed = server_channels.get('Emerald EU', {}).get('killfeed')
            default_killfeed = server_channels.get('default', {}).get('killfeed')
            legacy_killfeed = guild_config.get('channels', {}).get('killfeed')
            
            logger.info(f"=== Verification ===")
            logger.info(f"Emerald EU killfeed: {emerald_killfeed}")
            logger.info(f"Default killfeed: {default_killfeed}")
            logger.info(f"Legacy killfeed: {legacy_killfeed}")
        
        client.close()
        
    except Exception as e:
        logger.error(f"Failed to remove channel config: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(remove_incorrect_channel())