"""
Enhanced Channel Configuration System - Server Scoped with Guild Defaults
Complete hierarchical channel management with autocomplete and fallback support
"""

import discord
from discord.ext import commands
from discord import SlashCommandGroup, Option
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class AdminChannelsEnhanced(discord.Cog):
    """
    ENHANCED CHANNEL CONFIGURATION SYSTEM
    - Server-scoped channel configuration with guild defaults
    - Comprehensive autocomplete for all parameters
    - Smart fallback logic for parser output routing
    - Premium validation with feature gating
    """
    
    def __init__(self, bot):
        self.bot = bot
        
        # Enhanced channel types with descriptions and requirements
        self.channel_types = {
            'killfeed': {
                'premium': False, 
                'description': 'Real-time kill events from killfeed parser',
                'parser': 'killfeed',
                'type': discord.ChannelType.text
            },
            'events': {
                'premium': True, 
                'description': 'Connection/disconnection events from unified parser',
                'parser': 'unified',
                'type': discord.ChannelType.text
            },
            'connections': {
                'premium': True, 
                'description': 'Player join/leave notifications',
                'parser': 'unified',
                'type': discord.ChannelType.text
            },
            'bounties': {
                'premium': True, 
                'description': 'Bounty system notifications and completions',
                'parser': 'bounty_system',
                'type': discord.ChannelType.text
            },
            'leaderboard': {
                'premium': True, 
                'description': 'Automated leaderboard updates',
                'parser': 'scheduler',
                'type': discord.ChannelType.text
            },
            'voice': {
                'premium': True, 
                'description': 'Voice channel stats updates',
                'parser': 'voice_updater',
                'type': discord.ChannelType.voice
            }
        }
        
        # Premium cache for performance
        self.premium_cache = {}
        # Channel resolution cache
        self.channel_cache = {}
        
    @discord.Cog.listener()
    async def on_ready(self):
        """Initialize caches when bot is ready"""
        for guild in self.bot.guilds:
            await self.refresh_premium_cache(guild.id)
    
    async def refresh_premium_cache(self, guild_id: int):
        """Refresh premium status from database and cache it"""
        try:
            guild_config = await self.bot.db_manager.guilds.find_one({"guild_id": guild_id})
            if guild_config:
                has_premium_access = guild_config.get('premium_access', False)
                has_premium_servers = bool(guild_config.get('premium_servers', []))
                self.premium_cache[guild_id] = has_premium_access or has_premium_servers
            else:
                self.premium_cache[guild_id] = False
        except Exception as e:
            logger.error(f"Failed to refresh premium cache: {e}")
            self.premium_cache[guild_id] = False

    def check_premium_access(self, guild_id: int) -> bool:
        """Check premium access from cache"""
        return self.premium_cache.get(guild_id, False)
    
    async def get_configured_servers(self, guild_id: int) -> List[Dict[str, Any]]:
        """Get all configured servers for a guild"""
        try:
            guild_config = await self.bot.db_manager.guilds.find_one({"guild_id": guild_id})
            if guild_config and 'servers' in guild_config:
                return guild_config['servers']
            return []
        except Exception as e:
            logger.error(f"Failed to get configured servers: {e}")
            return []
    
    async def resolve_output_channel(self, guild_id: int, server_id: str, channel_type: str) -> Optional[int]:
        """
        Resolve output channel with hierarchical fallback
        Priority: Server-specific → Guild default → None
        """
        cache_key = f"{guild_id}:{server_id}:{channel_type}"
        
        # Check cache first (5-minute TTL handled elsewhere)
        if cache_key in self.channel_cache:
            return self.channel_cache[cache_key]
        
        try:
            guild_config = await self.bot.db_manager.guilds.find_one({"guild_id": guild_id})
            if not guild_config:
                return None
            
            # Check server-specific configuration first
            server_channels = guild_config.get('server_channels', {})
            if server_id in server_channels:
                server_config = server_channels[server_id]
                if channel_type in server_config:
                    channel_id = server_config[channel_type]
                    self.channel_cache[cache_key] = channel_id
                    return channel_id
            
            # Fall back to guild default
            default_channels = guild_config.get('default_channels', {})
            if channel_type in default_channels:
                channel_id = default_channels[channel_type]
                self.channel_cache[cache_key] = channel_id
                return channel_id
            
            # No channel configured
            self.channel_cache[cache_key] = None
            return None
            
        except Exception as e:
            logger.error(f"Failed to resolve output channel: {e}")
            return None
    
    # Autocomplete functions
    async def server_autocomplete(self, ctx: discord.AutocompleteContext):
        """Autocomplete for configured servers"""
        try:
            servers = await self.get_configured_servers(ctx.interaction.guild_id)
            choices = []
            
            for server in servers:
                server_name = server.get('name', 'Unknown Server')
                server_id = server.get('_id', 'unknown')
                host = server.get('host', 'unknown')
                port = server.get('port', 22)
                
                # Add status indicator
                status = "🟢" if server.get('connection_status') == 'connected' else "🔴"
                display_name = f"{status} {server_name} ({host}:{port})"
                
                choices.append(discord.OptionChoice(name=display_name, value=server_id))
            
            return choices[:25]  # Discord limit
            
        except Exception as e:
            logger.error(f"Server autocomplete error: {e}")
            return []
    
    async def channel_type_autocomplete(self, ctx: discord.AutocompleteContext):
        """Autocomplete for channel types with premium indicators"""
        try:
            guild_id = ctx.interaction.guild_id
            has_premium = self.check_premium_access(guild_id)
            
            choices = []
            for key, info in self.channel_types.items():
                if info['premium'] and not has_premium:
                    display_name = f"{key} (PREMIUM REQUIRED)"
                    choices.append(discord.OptionChoice(name=display_name, value=key))
                else:
                    display_name = f"{key} - {info['description']}"
                    choices.append(discord.OptionChoice(name=display_name, value=key))
            
            return choices
            
        except Exception as e:
            logger.error(f"Channel type autocomplete error: {e}")
            return []
    
    async def text_channel_autocomplete(self, ctx: discord.AutocompleteContext):
        """Autocomplete for text channels with permissions check"""
        try:
            guild = ctx.interaction.guild
            if not guild:
                return []
            
            choices = []
            for channel in guild.text_channels:
                # Check if bot has send permissions
                perms = channel.permissions_for(guild.me)
                if perms.send_messages:
                    status = "✅"
                else:
                    status = "❌"
                
                topic = channel.topic[:30] + "..." if channel.topic and len(channel.topic) > 30 else channel.topic or ""
                display_name = f"{status} #{channel.name}"
                if topic:
                    display_name += f" - {topic}"
                
                choices.append(discord.OptionChoice(name=display_name, value=str(channel.id)))
            
            return choices[:25]
            
        except Exception as e:
            logger.error(f"Text channel autocomplete error: {e}")
            return []
    
    async def voice_channel_autocomplete(self, ctx: discord.AutocompleteContext):
        """Autocomplete for voice channels"""
        try:
            guild = ctx.interaction.guild
            if not guild:
                return []
            
            choices = []
            for channel in guild.voice_channels:
                member_count = len(channel.members)
                display_name = f"🔊 {channel.name} (Members: {member_count})"
                choices.append(discord.OptionChoice(name=display_name, value=str(channel.id)))
            
            return choices[:25]
            
        except Exception as e:
            logger.error(f"Voice channel autocomplete error: {e}")
            return []
    
    # Command group
    channels = SlashCommandGroup("channels", "Enhanced channel configuration with server scoping")
    
    @channels.command(name="set", description="Set channel for specific server")
    @discord.default_permissions(administrator=True)
    async def set_server_channel(self, 
                               ctx: discord.ApplicationContext,
                               server: Option(str, "Server to configure", autocomplete=server_autocomplete),
                               channel_type: Option(str, "Type of channel", autocomplete=channel_type_autocomplete),
                               channel: Option(str, "Target channel", autocomplete=text_channel_autocomplete)):
        """Set server-specific channel configuration"""
        await ctx.defer(ephemeral=True)
        
        try:
            guild_id = ctx.guild.id
            
            # Validate channel type
            if channel_type not in self.channel_types:
                await ctx.followup.send("❌ Invalid channel type!", ephemeral=True)
                return
            
            channel_config = self.channel_types[channel_type]
            
            # Check premium requirements
            if channel_config['premium'] and not self.check_premium_access(guild_id):
                embed = discord.Embed(
                    title="🔒 Premium Feature Required",
                    description=f"Setting **{channel_type}** channel requires premium subscription!",
                    color=0xFF6B6B,
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(
                    name="Available Channel Types (Free)",
                    value="• killfeed - Real-time kill events",
                    inline=False
                )
                await ctx.followup.send(embed=embed, ephemeral=True)
                return
            
            # Validate channel exists and permissions
            try:
                target_channel = ctx.guild.get_channel(int(channel))
                if not target_channel:
                    await ctx.followup.send("❌ Channel not found!", ephemeral=True)
                    return
                
                # Check channel type compatibility
                expected_type = channel_config['type']
                if target_channel.type != expected_type:
                    await ctx.followup.send(
                        f"❌ Channel type mismatch! Expected {expected_type.name}, got {target_channel.type.name}",
                        ephemeral=True
                    )
                    return
                
                # Check permissions
                if expected_type == discord.ChannelType.text:
                    perms = target_channel.permissions_for(ctx.guild.me)
                    if not perms.send_messages:
                        await ctx.followup.send(
                            f"❌ Missing send message permissions in {target_channel.mention}!",
                            ephemeral=True
                        )
                        return
                
            except ValueError:
                await ctx.followup.send("❌ Invalid channel ID!", ephemeral=True)
                return
            
            # Save server-specific channel configuration
            await self.bot.db_manager.guilds.update_one(
                {"guild_id": guild_id},
                {
                    "$set": {
                        f"server_channels.{server}.{channel_type}": int(channel),
                        f"server_channels.{server}.last_updated": datetime.now(timezone.utc)
                    }
                },
                upsert=True
            )
            
            # Clear cache
            cache_pattern = f"{guild_id}:{server}:{channel_type}"
            if cache_pattern in self.channel_cache:
                del self.channel_cache[cache_pattern]
            
            # Get server name for display
            servers = await self.get_configured_servers(guild_id)
            server_name = next((s.get('name', server) for s in servers if s.get('_id') == server), server)
            
            embed = discord.Embed(
                title="✅ Server Channel Configuration Updated",
                description=f"**{channel_type.title()}** channel for **{server_name}** set to {target_channel.mention}",
                color=0x00FF00,
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(
                name="Channel Type",
                value=channel_config['description'],
                inline=False
            )
            embed.add_field(
                name="Parser Integration",
                value=f"Output from {channel_config['parser']} parser",
                inline=True
            )
            embed.add_field(
                name="Configuration Level",
                value="Server-specific",
                inline=True
            )
            
            await ctx.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error setting server channel: {e}")
            await ctx.followup.send("❌ An error occurred while setting the channel.", ephemeral=True)
    
    @channels.command(name="default", description="Set guild-wide default channel")
    @discord.default_permissions(administrator=True)
    async def set_default_channel(self,
                                ctx: discord.ApplicationContext,
                                channel_type: Option(str, "Type of channel", autocomplete=channel_type_autocomplete),
                                channel: Option(str, "Target channel", autocomplete=text_channel_autocomplete)):
        """Set guild-wide default channel configuration"""
        await ctx.defer(ephemeral=True)
        
        try:
            guild_id = ctx.guild.id
            
            # Validate channel type
            if channel_type not in self.channel_types:
                await ctx.followup.send("❌ Invalid channel type!", ephemeral=True)
                return
            
            channel_config = self.channel_types[channel_type]
            
            # Check premium requirements
            if channel_config['premium'] and not self.check_premium_access(guild_id):
                embed = discord.Embed(
                    title="🔒 Premium Feature Required",
                    description=f"Setting **{channel_type}** channel requires premium subscription!",
                    color=0xFF6B6B
                )
                await ctx.followup.send(embed=embed, ephemeral=True)
                return
            
            # Validate channel
            try:
                target_channel = ctx.guild.get_channel(int(channel))
                if not target_channel:
                    await ctx.followup.send("❌ Channel not found!", ephemeral=True)
                    return
                
                # Check permissions for text channels
                if channel_config['type'] == discord.ChannelType.text:
                    perms = target_channel.permissions_for(ctx.guild.me)
                    if not perms.send_messages:
                        await ctx.followup.send(
                            f"❌ Missing send message permissions in {target_channel.mention}!",
                            ephemeral=True
                        )
                        return
                
            except ValueError:
                await ctx.followup.send("❌ Invalid channel ID!", ephemeral=True)
                return
            
            # Save guild default channel configuration
            await self.bot.db_manager.guilds.update_one(
                {"guild_id": guild_id},
                {
                    "$set": {
                        f"default_channels.{channel_type}": int(channel),
                        "last_updated": datetime.now(timezone.utc)
                    }
                },
                upsert=True
            )
            
            # Clear related cache entries
            keys_to_remove = [key for key in self.channel_cache.keys() if key.startswith(f"{guild_id}:") and key.endswith(f":{channel_type}")]
            for key in keys_to_remove:
                del self.channel_cache[key]
            
            embed = discord.Embed(
                title="✅ Guild Default Channel Set",
                description=f"**{channel_type.title()}** default channel set to {target_channel.mention}",
                color=0x00FF00,
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(
                name="Fallback Behavior",
                value="This channel will be used when no server-specific channel is configured",
                inline=False
            )
            embed.add_field(
                name="Channel Type",
                value=channel_config['description'],
                inline=True
            )
            embed.add_field(
                name="Configuration Level",
                value="Guild-wide default",
                inline=True
            )
            
            await ctx.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error setting default channel: {e}")
            await ctx.followup.send("❌ An error occurred while setting the default channel.", ephemeral=True)
    
    @channels.command(name="list", description="Show channel configuration")
    @discord.default_permissions(administrator=True)
    async def list_channels(self,
                          ctx: discord.ApplicationContext,
                          server: Option(str, "Specific server (optional)", autocomplete=server_autocomplete, required=False)):
        """Display current channel configuration"""
        await ctx.defer(ephemeral=True)
        
        try:
            guild_id = ctx.guild.id
            guild_config = await self.bot.db_manager.guilds.find_one({"guild_id": guild_id})
            
            if server:
                # Show server-specific configuration
                servers = await self.get_configured_servers(guild_id)
                server_info = next((s for s in servers if s.get('_id') == server), None)
                
                if not server_info:
                    await ctx.followup.send("❌ Server not found!", ephemeral=True)
                    return
                
                embed = discord.Embed(
                    title=f"📋 Channel Configuration - {server_info.get('name', server)}",
                    color=0x3498DB,
                    timestamp=datetime.now(timezone.utc)
                )
                
                server_channels = guild_config.get('server_channels', {}).get(server, {}) if guild_config else {}
                default_channels = guild_config.get('default_channels', {}) if guild_config else {}
                
                for channel_type, config in self.channel_types.items():
                    if channel_type in server_channels:
                        channel_id = server_channels[channel_type]
                        channel = ctx.guild.get_channel(channel_id)
                        status = f"🟢 {channel.mention if channel else 'Channel Deleted'}"
                        level = "Server-specific"
                    elif channel_type in default_channels:
                        channel_id = default_channels[channel_type]
                        channel = ctx.guild.get_channel(channel_id)
                        status = f"🟡 {channel.mention if channel else 'Channel Deleted'} (default)"
                        level = "Using guild default"
                    else:
                        status = "🔴 Not configured"
                        level = "No output"
                    
                    embed.add_field(
                        name=f"{channel_type.title()} {'(Premium)' if config['premium'] else ''}",
                        value=f"{status}\n*{level}*",
                        inline=True
                    )
                
            else:
                # Show guild overview
                embed = discord.Embed(
                    title="📋 Guild Channel Configuration Overview",
                    color=0x3498DB,
                    timestamp=datetime.now(timezone.utc)
                )
                
                # Show defaults
                default_channels = guild_config.get('default_channels', {}) if guild_config else {}
                default_text = ""
                for channel_type, channel_id in default_channels.items():
                    channel = ctx.guild.get_channel(channel_id)
                    channel_mention = channel.mention if channel else "Channel Deleted"
                    default_text += f"• **{channel_type.title()}**: {channel_mention}\n"
                
                if default_text:
                    embed.add_field(
                        name="🌐 Guild Defaults",
                        value=default_text,
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="🌐 Guild Defaults",
                        value="No defaults configured",
                        inline=False
                    )
                
                # Show server-specific overrides
                server_channels = guild_config.get('server_channels', {}) if guild_config else {}
                if server_channels:
                    servers = await self.get_configured_servers(guild_id)
                    server_text = ""
                    
                    for server_id, channels in server_channels.items():
                        server_info = next((s for s in servers if s.get('_id') == server_id), None)
                        server_name = server_info.get('name', server_id) if server_info else server_id
                        
                        channel_list = []
                        for channel_type, channel_id in channels.items():
                            if channel_type != 'last_updated':
                                channel = ctx.guild.get_channel(channel_id)
                                if channel:
                                    channel_list.append(f"{channel_type}: {channel.mention}")
                        
                        if channel_list:
                            server_text += f"**{server_name}**\n" + "\n".join(channel_list) + "\n\n"
                    
                    if server_text:
                        embed.add_field(
                            name="🎯 Server-Specific Configurations",
                            value=server_text,
                            inline=False
                        )
                
                # Show legend
                embed.add_field(
                    name="📝 Legend",
                    value="🟢 Server-specific channel\n🟡 Using guild default\n🔴 Not configured",
                    inline=False
                )
            
            await ctx.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error listing channels: {e}")
            await ctx.followup.send("❌ An error occurred while retrieving channel configuration.", ephemeral=True)
    
    @channels.command(name="clear", description="Clear channel configuration")
    @discord.default_permissions(administrator=True)
    async def clear_channel(self,
                          ctx: discord.ApplicationContext,
                          channel_type: Option(str, "Type of channel to clear", autocomplete=channel_type_autocomplete),
                          server: Option(str, "Server (leave empty for guild default)", autocomplete=server_autocomplete, required=False)):
        """Clear channel configuration"""
        await ctx.defer(ephemeral=True)
        
        try:
            guild_id = ctx.guild.id
            
            if channel_type not in self.channel_types:
                await ctx.followup.send("❌ Invalid channel type!", ephemeral=True)
                return
            
            if server:
                # Clear server-specific configuration
                await self.bot.db_manager.guilds.update_one(
                    {"guild_id": guild_id},
                    {"$unset": {f"server_channels.{server}.{channel_type}": ""}}
                )
                
                # Clear cache
                cache_key = f"{guild_id}:{server}:{channel_type}"
                if cache_key in self.channel_cache:
                    del self.channel_cache[cache_key]
                
                # Get server name
                servers = await self.get_configured_servers(guild_id)
                server_name = next((s.get('name', server) for s in servers if s.get('_id') == server), server)
                
                embed = discord.Embed(
                    title="✅ Server Channel Configuration Cleared",
                    description=f"**{channel_type.title()}** channel cleared for **{server_name}**",
                    color=0x00FF00
                )
                embed.add_field(
                    name="Fallback Behavior",
                    value="Will now use guild default if configured",
                    inline=False
                )
                
            else:
                # Clear guild default
                await self.bot.db_manager.guilds.update_one(
                    {"guild_id": guild_id},
                    {"$unset": {f"default_channels.{channel_type}": ""}}
                )
                
                # Clear related cache entries
                keys_to_remove = [key for key in self.channel_cache.keys() if key.startswith(f"{guild_id}:") and key.endswith(f":{channel_type}")]
                for key in keys_to_remove:
                    del self.channel_cache[key]
                
                embed = discord.Embed(
                    title="✅ Guild Default Channel Cleared",
                    description=f"**{channel_type.title()}** default channel cleared",
                    color=0x00FF00
                )
                embed.add_field(
                    name="Impact",
                    value="Servers without specific configuration will have no output for this channel type",
                    inline=False
                )
            
            await ctx.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error clearing channel: {e}")
            await ctx.followup.send("❌ An error occurred while clearing the channel configuration.", ephemeral=True)

def setup(bot):
    bot.add_cog(AdminChannelsEnhanced(bot))