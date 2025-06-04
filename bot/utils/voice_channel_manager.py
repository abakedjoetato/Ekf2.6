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
        """Update voice channel name with current player count"""
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
                
            # Calculate total player count
            total_count = online_count + queued_count
            
            # Format channel name with player count
            base_name = "Players Online"
            if hasattr(voice_channel, 'original_name'):
                base_name = voice_channel.original_name
            else:
                # Extract base name from current name if it contains count
                current_name = voice_channel.name
                if ":" in current_name:
                    base_name = current_name.split(":")[0].strip()
                    
            new_name = f"{base_name}: {total_count}"
            
            # Update channel name if changed
            if voice_channel.name != new_name:
                await voice_channel.edit(name=new_name)
                logger.info(f"Updated voice channel '{voice_channel.name}' to '{new_name}' (Online: {online_count}, Queued: {queued_count})")
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
            
    async def _get_server_name(self, guild_id: int, server_id: str) -> Optional[str]:
        """Get server name from configuration"""
        try:
            guild_config = await self.bot.db_manager.guild_configs.find_one({'guild_id': guild_id})
            if not guild_config:
                return None
                
            servers = guild_config.get('servers', [])
            for server in servers:
                if str(server.get('server_id')) == str(server_id) or str(server.get('_id')) == str(server_id):
                    return server.get('server_name') or server.get('name')
                    
            return None
            
        except Exception as e:
            logger.error(f"Error getting server name: {e}")
            return None