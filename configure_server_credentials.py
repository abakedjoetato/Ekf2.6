"""
Configure Server Credentials - Update database with environment variable references
"""

import asyncio
import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bot.models.database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def configure_server_credentials():
    """Configure server with SFTP credentials from environment variables"""
    
    try:
        # Connect to database
        mongo_uri = os.environ.get('MONGO_URI')
        client = AsyncIOMotorClient(mongo_uri)
        db_manager = DatabaseManager(client)
        
        # Get SSH credentials from environment
        ssh_host = os.environ.get('SSH_HOST')
        ssh_username = os.environ.get('SSH_USERNAME')
        ssh_password = os.environ.get('SSH_PASSWORD')
        ssh_port = int(os.environ.get('SSH_PORT', 22))
        
        if not all([ssh_host, ssh_username, ssh_password]):
            logger.error("Missing SSH credentials in environment variables")
            return False
        
        logger.info(f"Configuring server credentials for host: {ssh_host}")
        
        # Update the server configuration in database
        guild_id = 1219706687980568769  # Emerald Servers guild
        
        # Find and update the server configuration
        guild_config = await db_manager.guild_configs.find_one({'guild_id': guild_id})
        
        if not guild_config:
            logger.error(f"No guild configuration found for guild {guild_id}")
            return False
        
        servers = guild_config.get('servers', [])
        if not servers:
            logger.error("No servers configured in guild")
            return False
        
        # Update the first server with SFTP credentials
        server = servers[0]
        server_id = server.get('server_id', '7020')
        
        # Configure SFTP credentials
        server['sftp_credentials'] = {
            'host': ssh_host,
            'username': ssh_username,
            'password': ssh_password,
            'port': ssh_port
        }
        
        # Ensure paths are configured
        if not server.get('log_path'):
            server['log_path'] = '/home/steam/deadside/server/logs/DeadSide-game.log'
        
        if not server.get('killfeed_path'):
            server['killfeed_path'] = '/home/steam/deadside/server/killfeed/killfeed.csv'
        
        # Update the database
        await db_manager.guild_configs.update_one(
            {'guild_id': guild_id},
            {'$set': {'servers': servers}}
        )
        
        logger.info(f"✅ Server {server_id} configured with SFTP credentials")
        logger.info(f"   Host: {ssh_host}:{ssh_port}")
        logger.info(f"   Log path: {server.get('log_path')}")
        logger.info(f"   Killfeed path: {server.get('killfeed_path')}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to configure server credentials: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(configure_server_credentials())