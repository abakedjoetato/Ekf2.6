#!/usr/bin/env python3

"""
Test Live Killfeed Detection
Direct test to check if new killfeed events are being generated on the server
"""

import asyncio
import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bot.utils.connection_manager import connection_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_live_killfeed_detection():
    """Test if new killfeed events are being generated"""
    try:
        logger.info("=== Testing Live Killfeed Detection ===")
        
        # Get server configuration
        mongo_client = AsyncIOMotorClient(os.environ.get('MONGO_URI'))
        db = mongo_client.emerald_killfeed
        
        guild_id = 1219706687980568769
        guild_config = await db.guild_configs.find_one({"guild_id": guild_id})
        
        if not guild_config or not guild_config.get('servers'):
            logger.error("No servers configured")
            return
            
        server_config = guild_config['servers'][0]
        server_name = server_config['name']
        
        logger.info(f"Testing server: {server_name}")
        
        # Check killfeed directory
        killfeed_path = f"/home/ds{server_config['server_id']}/killfeed/"
        
        async with connection_manager.get_connection(guild_id, server_config) as conn:
            if not conn:
                logger.error("Failed to connect to server")
                return
                
            sftp = await conn.start_sftp_client()
            
            # List killfeed directory
            try:
                logger.info(f"Checking killfeed directory: {killfeed_path}")
                killfeed_entries = await sftp.listdir(killfeed_path)
                logger.info(f"Found {len(killfeed_entries)} entries in killfeed directory")
                
                # Check world_0 subdirectory
                world_path = f"{killfeed_path}world_0/"
                logger.info(f"Checking world directory: {world_path}")
                
                world_entries = await sftp.listdir(world_path)
                csv_files = [f for f in world_entries if f.endswith('.csv')]
                logger.info(f"Found {len(csv_files)} CSV files in world_0")
                
                if csv_files:
                    # Get newest file
                    newest_file = max(csv_files)
                    newest_path = f"{world_path}{newest_file}"
                    
                    logger.info(f"Newest killfeed file: {newest_file}")
                    
                    # Check file size and last lines
                    stat = await sftp.stat(newest_path)
                    file_size = stat.st_size if hasattr(stat, 'st_size') else 0
                    logger.info(f"File size: {file_size} bytes")
                    
                    if file_size > 0:
                        async with sftp.open(newest_path, 'rb') as file:
                            # Read last 1000 bytes to see recent activity
                            if file_size > 1000:
                                await file.seek(file_size - 1000)
                            content = await file.read()
                            
                            lines = content.decode('utf-8', errors='ignore').splitlines()
                            logger.info(f"Last {len(lines)} lines from killfeed:")
                            
                            for i, line in enumerate(lines[-10:]):  # Show last 10 lines
                                logger.info(f"  {i+1}: {line}")
                                
                            # Check if file is being actively written to
                            logger.info(f"Total lines in file: {len(lines)}")
                    else:
                        logger.warning("Killfeed file is empty")
                        
                else:
                    logger.warning("No CSV files found in world_0")
                    
            except Exception as e:
                logger.error(f"Error accessing killfeed directory: {e}")
        
        mongo_client.close()
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_live_killfeed_detection())