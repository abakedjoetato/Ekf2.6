#!/usr/bin/env python3
"""
Premium System Cog - Server-scoped premium with guild feature unlocking
"""

import discord
from discord.ext import commands
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class Premium(commands.Cog):
    """Premium subscription management with server-scoped system"""
    
    def __init__(self, bot):
        self.bot = bot
        self._premium_cache: Dict[int, Dict[str, Any]] = {}
        
    async def check_premium_access(self, guild_id: int, server_id: Optional[int] = None) -> bool:
        """Check if guild has premium access"""
        try:
            if guild_id in self._premium_cache:
                cached_data = self._premium_cache[guild_id]
                if datetime.now() < cached_data['expires']:
                    return cached_data['has_premium']
            
            # Check database for premium servers in this guild
            guild_features = await self.bot.db.guild_features.find_one({"guild_id": guild_id})
            
            if not guild_features:
                # Initialize guild if not exists
                await self.bot.db.guild_features.insert_one({
                    "guild_id": guild_id,
                    "premium_servers": [],
                    "features_enabled": False,
                    "created_at": datetime.now()
                })
                self._premium_cache[guild_id] = {
                    'has_premium': False,
                    'expires': datetime.now() + timedelta(minutes=5)
                }
                return False
            
            has_premium = len(guild_features.get('premium_servers', [])) > 0
            
            # Cache result
            self._premium_cache[guild_id] = {
                'has_premium': has_premium,
                'expires': datetime.now() + timedelta(minutes=5)
            }
            
            return has_premium
            
        except Exception as e:
            logger.error(f"Error checking premium access: {e}")
            return False
    
    @discord.slash_command(name="premium_status", description="Check premium status for this guild")
    async def premium_status(self, ctx: discord.ApplicationContext):
        """Check premium status"""
        try:
            guild_id = ctx.guild.id if ctx.guild else None
            if not guild_id:
                await ctx.respond("❌ This command can only be used in a server.", ephemeral=True)
                return
            
            guild_features = await self.bot.db.guild_features.find_one({"guild_id": guild_id})
            
            if not guild_features:
                embed = discord.Embed(
                    title="💎 Premium Status",
                    description="**Status:** Free Tier\n**Premium Servers:** 0",
                    color=discord.Color.red()
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return
            
            premium_servers = guild_features.get('premium_servers', [])
            features_enabled = guild_features.get('features_enabled', False)
            
            status_color = discord.Color.gold() if len(premium_servers) > 0 else discord.Color.red()
            status_text = "Premium Active" if len(premium_servers) > 0 else "Free Tier"
            
            embed = discord.Embed(
                title="💎 Premium Status",
                color=status_color
            )
            
            embed.add_field(
                name="Status",
                value=status_text,
                inline=True
            )
            
            embed.add_field(
                name="Premium Servers",
                value=str(len(premium_servers)),
                inline=True
            )
            
            embed.add_field(
                name="Guild Features",
                value="✅ Enabled" if features_enabled else "❌ Disabled",
                inline=True
            )
            
            if premium_servers:
                servers_list = "\n".join([f"• Server {sid}" for sid in premium_servers[:5]])
                if len(premium_servers) > 5:
                    servers_list += f"\n• ... and {len(premium_servers) - 5} more"
                embed.add_field(
                    name="Premium Servers",
                    value=servers_list,
                    inline=False
                )
            
            await ctx.respond(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in premium status: {e}")
            await ctx.respond("❌ An error occurred while checking premium status.", ephemeral=True)
    
    @discord.slash_command(name="premium_add", description="Add premium subscription to a server")
    @commands.has_permissions(administrator=True)
    async def premium_add(
        self, 
        ctx: discord.ApplicationContext,
        server_id: discord.Option(int, description="Server ID to upgrade to premium")
    ):
        """Add premium subscription to a server"""
        try:
            guild_id = ctx.guild.id if ctx.guild else None
            if not guild_id:
                await ctx.respond("❌ This command can only be used in a server.", ephemeral=True)
                return
            
            # Check if server exists in database
            server_doc = await self.bot.db.servers.find_one({"server_id": server_id})
            if not server_doc:
                await ctx.respond(f"❌ Server {server_id} not found in database.", ephemeral=True)
                return
            
            if server_doc.get('guild_id') != guild_id:
                await ctx.respond(f"❌ Server {server_id} does not belong to this guild.", ephemeral=True)
                return
            
            # Add premium subscription
            result = await self.bot.db.guild_features.update_one(
                {"guild_id": guild_id},
                {
                    "$addToSet": {"premium_servers": server_id},
                    "$set": {
                        "features_enabled": True,
                        "updated_at": datetime.now()
                    }
                },
                upsert=True
            )
            
            # Clear cache
            if guild_id in self._premium_cache:
                del self._premium_cache[guild_id]
            
            embed = discord.Embed(
                title="💎 Premium Added",
                description=f"✅ Server {server_id} has been upgraded to premium!\n\n"
                           f"🎉 Guild features are now enabled for all members.",
                color=discord.Color.gold()
            )
            
            await ctx.respond(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error adding premium: {e}")
            await ctx.respond("❌ An error occurred while adding premium subscription.", ephemeral=True)

def setup(bot):
    bot.add_cog(Premium(bot))