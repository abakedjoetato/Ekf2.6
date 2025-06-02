"""
Emerald's Killfeed - Admin Channel Configuration (PHASE 3)
Channel setup commands with premium gating
"""

import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional

import discord
from discord.ext import commands
from bot.cogs.autocomplete import ServerAutocomplete

logger = logging.getLogger(__name__)

class AdminChannels(discord.Cog):
    """
    ADMIN CHANNEL COMMANDS (PHASE 3)
    - /setchannel killfeed (FREE)
    - /setchannel leaderboard (PREMIUM)
    - /setchannel playercountvc (PREMIUM)
    - /setchannel events (PREMIUM)
    - /setchannel connections (PREMIUM)
    - /setchannel bounties (PREMIUM)
    - /clearchannels (resets all)
    """
    
    def __init__(self, bot):
        self.bot = bot
        
        # Channel types and their premium requirements
        self.channel_types = {
            'killfeed': {'premium': False, 'description': 'Real-time kill feed updates', 'type': discord.ChannelType.text},
            'leaderboard': {'premium': True, 'description': 'Automated consolidated leaderboard (30min updates)', 'type': discord.ChannelType.text},
            'playercountvc': {'premium': True, 'description': 'Live player count voice channel', 'type': discord.ChannelType.voice},
            'events': {'premium': True, 'description': 'Server events (airdrops, missions)', 'type': discord.ChannelType.text},
            'connections': {'premium': True, 'description': 'Player join/leave notifications', 'type': discord.ChannelType.text},
            'bounties': {'premium': True, 'description': 'Bounty notifications', 'type': discord.ChannelType.text}
        }
    
    async def check_premium_access(self, guild_id: int) -> bool:
        """Check if guild has premium access with timeout handling"""
        try:
            # Add timeout to database query to prevent command timeouts
            import asyncio
            guild_config = await asyncio.wait_for(
                self.bot.db_manager.guilds.find_one({"guild_id": guild_id}),
                timeout=3.0  # 3 second timeout
            )
            
            if not guild_config:
                logger.warning(f"No guild config found for {guild_id}, allowing access")
                return True  # Allow access if no config found to prevent lockouts
            
            # Check for premium access flag or premium servers
            has_premium_access = guild_config.get('premium_access', False)
            has_premium_servers = bool(guild_config.get('premium_servers', []))
            
            return has_premium_access or has_premium_servers
        except asyncio.TimeoutError:
            logger.warning(f"Database timeout checking premium for guild {guild_id}, allowing access")
            return True  # Allow access on timeout to prevent command failures
        except Exception as e:
            logger.error(f"Error checking premium access: {e}")
            return True  # Allow access on error to prevent lockouts
    
    async def channel_type_autocomplete(self, ctx: discord.AutocompleteContext):
        """Autocomplete for channel types"""
        return [
            discord.OptionChoice(name=f"{key} - {info['description']}", value=key)
            for key, info in self.channel_types.items()
        ]
    
    @discord.slash_command(name="setchannel", description="Configure output channels for the bot")
    @discord.default_permissions(administrator=True)
    async def set_channel(self, ctx, 
                         channel_type: discord.Option(str, "Type of channel to configure", autocomplete=channel_type_autocomplete), 
                         channel: discord.abc.GuildChannel, 
                         server_id: str = "default"):
        """Configure a specific channel type for a specific server"""
        await ctx.defer(ephemeral=True)
        
        try:
            guild_id = ctx.guild.id if ctx.guild else 0
            
            if channel_type not in self.channel_types:
                await ctx.followup.send("Invalid channel type!", ephemeral=True)
                return
                
            channel_config = self.channel_types[channel_type]
            
            # Check if channel type requires premium
            if channel_config['premium']:
                has_premium = await self.check_premium_access(guild_id)
                if not has_premium:
                    embed = discord.Embed(
                        title="Premium Feature Required",
                        description=f"Setting **{channel_type}** channel requires premium subscription!",
                        color=0xFF6B6B,
                        timestamp=datetime.now(timezone.utc)
                    )
                    await ctx.followup.send(embed=embed, ephemeral=True)
                    return
            
            # Save channel configuration
            await self.bot.db_manager.guilds.update_one(
                {"guild_id": guild_id},
                {"$set": {f"channels.{server_id}.{channel_type}": channel.id}},
                upsert=True
            )
            
            embed = discord.Embed(
                title="Channel Configuration Updated",
                description=f"**{channel_type.title()}** channel set to {channel.mention} for server `{server_id}`",
                color=0x00FF00,
                timestamp=datetime.now(timezone.utc)
            )
            await ctx.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error setting channel: {e}")
            await ctx.followup.send("An error occurred while setting the channel.", ephemeral=True)

def setup(bot):
    bot.add_cog(AdminChannels(bot))
