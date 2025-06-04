"""
Emerald's Killfeed - Voice Channel Updater System
Automatically updates voice channel names with current player counts
"""

import discord
import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

class VoiceChannelUpdater(discord.Cog):
    """Automated voice channel updater for real-time player counts"""
    
    def __init__(self, bot):
        self.bot = bot
        self.update_interval = 30  # Update every 30 seconds
        self.is_running = False
        self.update_task = None
        logger.info("VoiceChannelUpdater cog initialized")

    async def cog_ready(self):
        """Start the voice channel updater when the cog is ready"""
        if not self.is_running:
            self.update_task = self.bot.loop.create_task(self.voice_channel_update_loop())
            logger.info("Voice channel updater started")

    def cog_unload(self):
        """Stop the voice channel updater when the cog is unloaded"""
        if self.update_task:
            self.update_task.cancel()
            logger.info("Voice channel updater stopped")

    async def voice_channel_update_loop(self):
        """Main loop for updating voice channels"""
        self.is_running = True
        logger.info("🔊 Voice channel update loop started")
        
        while self.is_running:
            try:
                await self.update_all_voice_channels()
                await asyncio.sleep(self.update_interval)
                
            except asyncio.CancelledError:
                logger.info("Voice channel update loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in voice channel update loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def update_all_voice_channels(self):
        """Update all configured voice channels across guilds"""
        try:
            # Get all guild configurations with voice_counter channels
            guild_configs = await self.bot.db_manager.guild_configs.find({
                "server_channels.default.voice_counter": {"$exists": True}
            }).to_list(length=None)
            
            if not guild_configs:
                return
                
            logger.debug(f"Updating voice channels for {len(guild_configs)} guilds")
            
            for guild_config in guild_configs:
                guild_id = guild_config.get('guild_id')
                if not guild_id:
                    continue
                    
                try:
                    await self.update_guild_voice_channels(guild_id, guild_config)
                except Exception as e:
                    logger.error(f"Error updating voice channels for guild {guild_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in update_all_voice_channels: {e}")

    async def update_guild_voice_channels(self, guild_id: int, guild_config: dict):
        """Update voice channels for a specific guild"""
        try:
            # Get guild
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return
                
            # Get server configurations
            server_channels = guild_config.get('server_channels', {})
            
            for server_name, server_config in server_channels.items():
                voice_channel_id = server_config.get('voice_counter')
                if not voice_channel_id:
                    continue
                    
                # Get voice channel
                voice_channel = guild.get_channel(voice_channel_id)
                if not voice_channel or not isinstance(voice_channel, discord.VoiceChannel):
                    continue
                    
                # Get current player count for this server
                player_count = await self.get_server_player_count(guild_id, server_name)
                
                # Update channel name
                await self.update_voice_channel_name(voice_channel, server_name, player_count)
                
        except Exception as e:
            logger.error(f"Error updating guild voice channels for {guild_id}: {e}")

    async def get_server_player_count(self, guild_id: int, server_name: str) -> int:
        """Get current player count for a specific server"""
        try:
            # Get active player sessions from database
            active_sessions = await self.bot.db_manager.player_sessions.find({
                "guild_id": guild_id,
                "server_id": server_name,
                "state": "online"
            }).to_list(length=None)
            
            # Count unique players
            unique_players = set()
            for session in active_sessions:
                player_name = session.get('player_name')
                if player_name:
                    unique_players.add(player_name.lower())
                    
            player_count = len(unique_players)
            logger.debug(f"Server {server_name} has {player_count} active players")
            
            return player_count
            
        except Exception as e:
            logger.error(f"Error getting player count for {server_name}: {e}")
            return 0

    async def update_voice_channel_name(self, voice_channel: discord.VoiceChannel, server_name: str, player_count: int):
        """Update voice channel name with current player count"""
        try:
            # Format channel name
            if server_name.lower() == 'default':
                new_name = f"🎮 Players Online: {player_count}"
            else:
                new_name = f"🎮 {server_name}: {player_count} Online"
                
            # Only update if name has changed
            if voice_channel.name != new_name:
                await voice_channel.edit(name=new_name)
                logger.info(f"✅ Updated voice channel: {new_name}")
                
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                logger.warning(f"Rate limited updating voice channel {voice_channel.id}")
            else:
                logger.error(f"HTTP error updating voice channel {voice_channel.id}: {e}")
        except Exception as e:
            logger.error(f"Error updating voice channel name: {e}")

    @discord.slash_command(name="voice_update", description="Manually update voice channel player count")
    @discord.default_permissions(administrator=True)
    async def voice_update(self, ctx: discord.ApplicationContext, 
                          server: discord.Option(str, description="Server name (default: 'default')", default="default")):
        """Manually trigger voice channel update"""
        await ctx.defer()
        
        try:
            if not ctx.guild:
                await ctx.followup.send("This command can only be used in a server!", ephemeral=True)
                return
                
            guild_id = ctx.guild.id
            
            # Get guild configuration
            guild_config = await self.bot.db_manager.guild_configs.find_one({"guild_id": guild_id})
            if not guild_config:
                embed = discord.Embed(
                    title="❌ No Configuration Found",
                    description="No voice channel configuration found. Use `/setchannel voice_counter` to configure a voice channel.",
                    color=0xFF0000
                )
                await ctx.followup.send(embed=embed, ephemeral=True)
                return
                
            # Check if voice channel is configured for this server
            voice_channel_id = guild_config.get('server_channels', {}).get(server, {}).get('voice_counter')
            if not voice_channel_id:
                embed = discord.Embed(
                    title="❌ Voice Channel Not Configured",
                    description=f"No voice channel configured for server '{server}'. Use `/setchannel voice_counter` to configure one.",
                    color=0xFF0000
                )
                await ctx.followup.send(embed=embed, ephemeral=True)
                return
                
            # Update voice channel
            await self.update_guild_voice_channels(guild_id, guild_config)
            
            # Get updated player count
            player_count = await self.get_server_player_count(guild_id, server)
            
            embed = discord.Embed(
                title="✅ Voice Channel Updated",
                description=f"Voice channel updated with current player count: **{player_count} players online**",
                color=0x00FF00
            )
            await ctx.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in voice_update command: {e}")
            embed = discord.Embed(
                title="❌ Update Failed",
                description="An error occurred while updating the voice channel.",
                color=0xFF0000
            )
            await ctx.followup.send(embed=embed, ephemeral=True)

def setup(bot):
    """Load the VoiceChannelUpdater cog"""
    bot.add_cog(VoiceChannelUpdater(bot))