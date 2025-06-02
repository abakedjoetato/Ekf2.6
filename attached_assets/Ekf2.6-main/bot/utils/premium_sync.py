"""
Premium Flag Synchronization
Automatically manages guild premium_enabled flag based on server premium status
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

class PremiumSyncManager:
    """Manages automatic synchronization of guild premium flags"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    async def sync_guild_premium_flag(self, guild_id: int) -> bool:
        """
        Synchronize guild premium_enabled flag based on server premium status
        Returns True if guild should have premium access
        """
        try:
            # Get guild configuration
            guild_config = await self.db_manager.guild_configs.find_one({'guild_id': guild_id})
            if not guild_config:
                logger.warning(f"No guild config found for guild {guild_id}")
                return False
            
            # Check if any servers have premium status
            servers = guild_config.get('servers', [])
            has_premium_server = any(server.get('premium', False) for server in servers)
            
            # Get current premium flag
            current_flag = guild_config.get('premium_enabled', False)
            
            # Update flag if it doesn't match server status
            if has_premium_server != current_flag:
                await self.db_manager.guild_configs.update_one(
                    {'guild_id': guild_id},
                    {
                        '$set': {
                            'premium_enabled': has_premium_server,
                            'premium_sync_updated': True
                        }
                    }
                )
                
                action = "enabled" if has_premium_server else "disabled"
                logger.info(f"Guild {guild_id}: Premium access {action} (auto-sync)")
                
                return has_premium_server
            
            return current_flag
            
        except Exception as e:
            logger.error(f"Failed to sync premium flag for guild {guild_id}: {e}")
            return False
    
    async def update_server_premium_status(self, guild_id: int, server_id: str, is_premium: bool) -> bool:
        """
        Update server premium status and sync guild flag
        """
        try:
            # Update server premium status
            result = await self.db_manager.guild_configs.update_one(
                {
                    'guild_id': guild_id,
                    '$or': [
                        {'servers._id': server_id},
                        {'servers.server_id': server_id}
                    ]
                },
                {
                    '$set': {
                        'servers.$.premium': is_premium
                    }
                }
            )
            
            if result.modified_count > 0:
                # Sync guild premium flag after server status change
                await self.sync_guild_premium_flag(guild_id)
                
                status = "activated" if is_premium else "deactivated"
                logger.info(f"Server {server_id} premium {status} for guild {guild_id}")
                return True
            else:
                logger.warning(f"Server {server_id} not found in guild {guild_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update server premium status: {e}")
            return False
    
    async def add_premium_server(self, guild_id: int, server_config: dict) -> bool:
        """
        Add a new premium server and sync guild flag
        """
        try:
            # Ensure server is marked as premium
            server_config['premium'] = True
            
            # Add server to guild
            result = await self.db_manager.guild_configs.update_one(
                {'guild_id': guild_id},
                {
                    '$addToSet': {'servers': server_config},
                    '$setOnInsert': {'guild_id': guild_id}
                },
                upsert=True
            )
            
            # Sync guild premium flag
            await self.sync_guild_premium_flag(guild_id)
            
            server_name = server_config.get('name', 'Unknown Server')
            logger.info(f"Premium server {server_name} added to guild {guild_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add premium server: {e}")
            return False
    
    async def remove_server(self, guild_id: int, server_id: str) -> bool:
        """
        Remove a server and sync guild flag
        """
        try:
            # Remove server from guild
            result = await self.db_manager.guild_configs.update_one(
                {'guild_id': guild_id},
                {
                    '$pull': {
                        'servers': {
                            '$or': [
                                {'_id': server_id},
                                {'server_id': server_id}
                            ]
                        }
                    }
                }
            )
            
            if result.modified_count > 0:
                # Sync guild premium flag after server removal
                await self.sync_guild_premium_flag(guild_id)
                
                logger.info(f"Server {server_id} removed from guild {guild_id}")
                return True
            else:
                logger.warning(f"Server {server_id} not found in guild {guild_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to remove server: {e}")
            return False
    
    async def validate_all_guilds(self) -> int:
        """
        Validate and sync premium flags for all guilds
        Returns number of guilds updated
        """
        try:
            updated_count = 0
            
            # Get all guild configurations
            async for guild_config in self.db_manager.guild_configs.find({}):
                guild_id = guild_config.get('guild_id')
                if guild_id:
                    # Check if sync is needed
                    servers = guild_config.get('servers', [])
                    has_premium_server = any(server.get('premium', False) for server in servers)
                    current_flag = guild_config.get('premium_enabled', False)
                    
                    if has_premium_server != current_flag:
                        await self.sync_guild_premium_flag(guild_id)
                        updated_count += 1
            
            if updated_count > 0:
                logger.info(f"Premium flag validation complete: {updated_count} guilds updated")
            
            return updated_count
            
        except Exception as e:
            logger.error(f"Failed to validate guild premium flags: {e}")
            return 0