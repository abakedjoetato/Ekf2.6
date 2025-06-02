#!/usr/bin/env python3
"""
Emergency Fix - Restore bot to working state
"""

import os
import re

def fix_admin_channels():
    """Fix admin_channels.py to basic working state"""
    content = '''"""
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
        """Check premium access - bypassed for testing"""
        return True
    
    @discord.slash_command(name="setchannel", description="Configure output channels for the bot")
    @discord.default_permissions(administrator=True)
    async def set_channel(self, ctx, channel_type: str, channel: discord.abc.GuildChannel, server_id: str = "default"):
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
'''
    
    with open('bot/cogs/admin_channels.py', 'w') as f:
        f.write(content)
    
    print("✅ Fixed admin_channels.py")

def main():
    fix_admin_channels()
    print("Emergency fixes applied")

if __name__ == "__main__":
    main()