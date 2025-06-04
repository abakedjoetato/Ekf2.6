"""
Voice Channel Manager - Updates voice channel names with current player counts
"""

import logging
import discord
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class VoiceChannelManager:
    """Manages voice channel updates with player counts"""
    
    def __init__(self, bot):
        self.bot = bot
        self.channel_cache = {}
        
    async def update_voice_channel_count(self, guild_id: int, server_id: str, online_count: int, queued_count: int = 0) -> bool:
        """Update voice channel name with server name, player count, max count, and queued count"""
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                logger.error(f"Guild {guild_id} not found")
                return False
            
            # Get voice channel configuration from database
            voice_channel_id = await self._get_voice_channel_id(guild_id, server_id)
            if not voice_channel_id:
                logger.warning(f"No voice channel configured for guild {guild_id}, server {server_id}")
                return False
                
            voice_channel = guild.get_channel(voice_channel_id)
            if not voice_channel:
                logger.error(f"Voice channel {voice_channel_id} not found in guild {guild_id}")
                return False
                
            # Get server configuration for name and max players
            server_name, max_players = await self._get_server_info(guild_id, server_id)
            if not server_name:
                server_name = f"Server {server_id}"
            if not max_players:
                max_players = 60  # Default Deadside server size
                
            # Format channel name: "Server Name | current/max" or "Server Name | current/max 🕑queued"
            if queued_count > 0:
                new_name = f"{server_name} | {online_count}/{max_players} 🕑{queued_count}"
            else:
                new_name = f"{server_name} | {online_count}/{max_players}"
            
            # Update channel name if changed
            if voice_channel.name != new_name:
                await voice_channel.edit(name=new_name)
                logger.info(f"Updated voice channel to '{new_name}' (Online: {online_count}, Max: {max_players}, Queued: {queued_count})")
                return True
            else:
                logger.debug(f"Voice channel name unchanged: {new_name}")
                return True
                
        except discord.Forbidden:
            logger.error(f"No permission to edit voice channel in guild {guild_id}")
            return False
        except discord.HTTPException as e:
            logger.error(f"HTTP error updating voice channel: {e}")
            return False
        except Exception as e:
            logger.error(f"Error updating voice channel: {e}")
            return False
            
    async def _get_voice_channel_id(self, guild_id: int, server_id: str) -> Optional[int]:
        """Get voice channel ID from guild configuration"""
        try:
            # Get guild configuration from database
            guild_config = await self.bot.db_manager.guild_configs.find_one({'guild_id': guild_id})
            if not guild_config:
                return None
                
            server_channels = guild_config.get('server_channels', {})
            
            # Try server-specific configuration first
            server_name = await self._get_server_name(guild_id, server_id)
            if server_name and server_name in server_channels:
                # Check multiple possible voice channel field names
                for field_name in ['playercountvc', 'voice_counter', 'voice_channel']:
                    voice_channel_id = server_channels[server_name].get(field_name)
                    if voice_channel_id:
                        return voice_channel_id
                    
            # Fall back to default configuration
            if 'default' in server_channels:
                # Check multiple possible voice channel field names
                for field_name in ['playercountvc', 'voice_counter', 'voice_channel']:
                    voice_channel_id = server_channels['default'].get(field_name)
                    if voice_channel_id:
                        return voice_channel_id
                    
            return None
            
        except Exception as e:
            logger.error(f"Error getting voice channel ID: {e}")
            return None
            
    async def _get_server_info(self, guild_id: int, server_id: str) -> tuple[Optional[str], Optional[int]]:
        """Get server name and max players from configuration"""
        try:
            guild_config = await self.bot.db_manager.guild_configs.find_one({'guild_id': guild_id})
            if not guild_config:
                return None, None
                
            servers = guild_config.get('servers', [])
            for server in servers:
                if str(server.get('server_id')) == str(server_id) or str(server.get('_id')) == str(server_id):
                    server_name = server.get('server_name') or server.get('name')
                    max_players = server.get('max_players') or server.get('player_limit')
                    return server_name, max_players
                    
            return None, None
            
        except Exception as e:
            logger.error(f"Error getting server info: {e}")
            return None, None
            
    async def _get_server_name(self, guild_id: int, server_id: str) -> Optional[str]:
        """Get server name from configuration"""
        server_name, _ = await self._get_server_info(guild_id, server_id)
        return server_name