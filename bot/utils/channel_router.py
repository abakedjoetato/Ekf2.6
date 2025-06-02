"""
Channel Router - Hierarchical Channel Resolution System
Handles server-scoped channel configuration with guild defaults and fallbacks
"""

import discord
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class ChannelRouter:
    """
    Channel routing system with hierarchical fallback
    Priority: Server-specific → Guild default → Disabled output
    """
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.channel_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    async def resolve_output_channel(self, bot: discord.Bot, guild_id: int, server_id: str, channel_type: str) -> Optional[discord.TextChannel]:
        """
        Resolve output channel with hierarchical fallback
        Returns the actual Discord channel object or None
        """
        try:
            # Get channel ID from configuration
            channel_id = await self._get_channel_id(guild_id, server_id, channel_type)
            if not channel_id:
                return None
            
            # Get guild object
            guild = bot.get_guild(guild_id)
            if not guild:
                logger.warning(f"Guild {guild_id} not found")
                return None
            
            # Get channel object
            channel = guild.get_channel(channel_id)
            if not channel:
                logger.warning(f"Channel {channel_id} not found in guild {guild_id}")
                return None
            
            # Verify channel type and permissions
            if not isinstance(channel, discord.TextChannel):
                logger.warning(f"Channel {channel_id} is not a text channel")
                return None
            
            # Check bot permissions
            permissions = channel.permissions_for(guild.me)
            if not permissions.send_messages:
                logger.warning(f"No send permissions in channel {channel_id}")
                return None
            
            return channel
            
        except Exception as e:
            logger.error(f"Error resolving output channel: {e}")
            return None
    
    async def _get_channel_id(self, guild_id: int, server_id: str, channel_type: str) -> Optional[int]:
        """Get channel ID with caching and hierarchical lookup"""
        cache_key = f"{guild_id}:{server_id}:{channel_type}"
        
        # Check cache
        if cache_key in self.channel_cache:
            cached_data = self.channel_cache[cache_key]
            if (datetime.now(timezone.utc) - cached_data['timestamp']).seconds < self.cache_ttl:
                return cached_data['channel_id']
        
        try:
            guild_config = await self.db_manager.guilds.find_one({"guild_id": guild_id})
            if not guild_config:
                return None
            
            channel_id = None
            
            # Check server-specific configuration first
            server_channels = guild_config.get('server_channels', {})
            if server_id in server_channels:
                server_config = server_channels[server_id]
                if channel_type in server_config:
                    channel_id = server_config[channel_type]
            
            # Fall back to guild default if no server-specific config
            if channel_id is None:
                default_channels = guild_config.get('default_channels', {})
                if channel_type in default_channels:
                    channel_id = default_channels[channel_type]
            
            # Cache the result
            self.channel_cache[cache_key] = {
                'channel_id': channel_id,
                'timestamp': datetime.now(timezone.utc)
            }
            
            return channel_id
            
        except Exception as e:
            logger.error(f"Error getting channel ID: {e}")
            return None
    
    async def send_to_channel(self, bot: discord.Bot, guild_id: int, server_id: str, channel_type: str, 
                             content: str = None, embed: discord.Embed = None, view: discord.ui.View = None) -> bool:
        """
        Send message to resolved channel
        Returns True if message was sent successfully
        """
        try:
            channel = await self.resolve_output_channel(bot, guild_id, server_id, channel_type)
            if not channel:
                logger.debug(f"No output channel configured for {channel_type} in server {server_id}")
                return False
            
            await channel.send(content=content, embed=embed, view=view)
            return True
            
        except discord.Forbidden:
            logger.warning(f"No permission to send to channel for {channel_type}")
            return False
        except discord.HTTPException as e:
            logger.error(f"HTTP error sending to channel: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending to channel: {e}")
            return False
    
    async def get_channel_configuration(self, guild_id: int, server_id: str = None) -> Dict[str, Any]:
        """Get current channel configuration for debugging/display"""
        try:
            guild_config = await self.db_manager.guilds.find_one({"guild_id": guild_id})
            if not guild_config:
                return {}
            
            result = {
                'default_channels': guild_config.get('default_channels', {}),
                'server_channels': guild_config.get('server_channels', {})
            }
            
            if server_id:
                result['resolved_channels'] = {}
                channel_types = ['killfeed', 'events', 'connections', 'bounties', 'leaderboard', 'voice']
                
                for channel_type in channel_types:
                    channel_id = await self._get_channel_id(guild_id, server_id, channel_type)
                    result['resolved_channels'][channel_type] = channel_id
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting channel configuration: {e}")
            return {}
    
    def clear_cache(self, guild_id: int = None, server_id: str = None, channel_type: str = None):
        """Clear channel cache entries"""
        if guild_id is None:
            # Clear all cache
            self.channel_cache.clear()
            return
        
        keys_to_remove = []
        for key in self.channel_cache.keys():
            key_parts = key.split(':')
            if len(key_parts) != 3:
                continue
                
            key_guild_id, key_server_id, key_channel_type = key_parts
            
            if str(guild_id) != key_guild_id:
                continue
                
            if server_id is not None and server_id != key_server_id:
                continue
                
            if channel_type is not None and channel_type != key_channel_type:
                continue
                
            keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.channel_cache[key]
    
    async def validate_channel_permissions(self, bot: discord.Bot, guild_id: int) -> Dict[str, Any]:
        """Validate all configured channels have proper permissions"""
        try:
            guild = bot.get_guild(guild_id)
            if not guild:
                return {"error": "Guild not found"}
            
            guild_config = await self.db_manager.guilds.find_one({"guild_id": guild_id})
            if not guild_config:
                return {"error": "No guild configuration"}
            
            validation_results = {
                'default_channels': {},
                'server_channels': {},
                'summary': {'valid': 0, 'invalid': 0, 'missing': 0}
            }
            
            # Validate default channels
            default_channels = guild_config.get('default_channels', {})
            for channel_type, channel_id in default_channels.items():
                result = await self._validate_single_channel(guild, channel_id)
                validation_results['default_channels'][channel_type] = result
                validation_results['summary'][result['status']] += 1
            
            # Validate server-specific channels
            server_channels = guild_config.get('server_channels', {})
            for server_id, channels in server_channels.items():
                validation_results['server_channels'][server_id] = {}
                for channel_type, channel_id in channels.items():
                    if channel_type == 'last_updated':
                        continue
                    result = await self._validate_single_channel(guild, channel_id)
                    validation_results['server_channels'][server_id][channel_type] = result
                    validation_results['summary'][result['status']] += 1
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating channel permissions: {e}")
            return {"error": str(e)}
    
    async def _validate_single_channel(self, guild: discord.Guild, channel_id: int) -> Dict[str, Any]:
        """Validate a single channel's existence and permissions"""
        try:
            channel = guild.get_channel(channel_id)
            if not channel:
                return {
                    'status': 'missing',
                    'channel_id': channel_id,
                    'error': 'Channel not found'
                }
            
            if not isinstance(channel, discord.TextChannel):
                return {
                    'status': 'invalid',
                    'channel_id': channel_id,
                    'channel_name': channel.name,
                    'error': 'Not a text channel'
                }
            
            permissions = channel.permissions_for(guild.me)
            missing_perms = []
            
            if not permissions.view_channel:
                missing_perms.append('view_channel')
            if not permissions.send_messages:
                missing_perms.append('send_messages')
            if not permissions.embed_links:
                missing_perms.append('embed_links')
            
            if missing_perms:
                return {
                    'status': 'invalid',
                    'channel_id': channel_id,
                    'channel_name': channel.name,
                    'error': f'Missing permissions: {", ".join(missing_perms)}'
                }
            
            return {
                'status': 'valid',
                'channel_id': channel_id,
                'channel_name': channel.name,
                'channel_mention': channel.mention
            }
            
        except Exception as e:
            return {
                'status': 'invalid',
                'channel_id': channel_id,
                'error': str(e)
            }