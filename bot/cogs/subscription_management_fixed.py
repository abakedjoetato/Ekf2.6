"""
Emerald's Killfeed - Subscription Management (FIXED)
Complete premium subscription system with advanced UI components
"""

import discord
from discord.ext import commands
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from bot.utils.embed_factory import EmbedFactory

logger = logging.getLogger(__name__)

class SubscriptionManagement(commands.Cog):
    """
    SUBSCRIPTION MANAGEMENT (ADMIN)
    - Premium subscription control
    - Server-scoped premium management
    - Subscription analytics
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.premium_cache: Dict[int, bool] = {}

    async def on_ready(self):
        """Initialize premium cache when bot is ready"""
        for guild in self.bot.guilds:
            await self.refresh_premium_cache(guild.id)
    
    async def refresh_premium_cache(self, guild_id: int):
        """Refresh premium status from database and cache it"""
        try:
            has_premium = await self.bot.db_manager.check_premium_access(guild_id)
            self.premium_cache[guild_id] = has_premium
        except Exception as e:
            logger.error(f"Failed to refresh premium cache for guild {guild_id}: {e}")
            self.premium_cache[guild_id] = False

    def check_premium_access(self, guild_id: int) -> bool:
        """Check premium access from cache (no database calls)"""
        return self.premium_cache.get(guild_id, False)

    subscription = discord.SlashCommandGroup("subscription", "Premium subscription management")

    @subscription.command(name="status", description="Check premium subscription status")
    async def subscription_status(self, ctx: discord.ApplicationContext):
        """Check current premium subscription status"""
        try:
            guild_id = ctx.guild.id if ctx.guild else None
            if not guild_id:
                await ctx.respond("This command can only be used in a server.", ephemeral=True)
                return

            has_premium = await self.bot.db_manager.check_premium_access(guild_id)
            
            embed = EmbedFactory.create_info_embed(
                title="Premium Subscription Status",
                description=f"Guild: **{ctx.guild.name}**"
            )
            
            status_text = "✅ **Active**" if has_premium else "❌ **Inactive**"
            embed.add_field(name="Status", value=status_text, inline=False)
            
            if has_premium:
                embed.add_field(
                    name="Premium Features Available",
                    value="• Economy system\n• Advanced casino games\n• Faction management\n• Bounty system\n• Automated leaderboards\n• Voice channel updates",
                    inline=False
                )
            else:
                embed.add_field(
                    name="Premium Features",
                    value="Upgrade to premium to unlock advanced features",
                    inline=False
                )
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logger.error(f"Error checking subscription status: {e}")
            await ctx.respond("An error occurred while checking subscription status.", ephemeral=True)

    @subscription.command(name="activate", description="Activate premium subscription (Admin only)")
    @commands.has_permissions(administrator=True)
    async def subscription_activate(self, ctx: discord.ApplicationContext):
        """Activate premium subscription for this guild"""
        try:
            guild_id = ctx.guild.id if ctx.guild else None
            if not guild_id:
                await ctx.respond("This command can only be used in a server.", ephemeral=True)
                return

            # Set premium status
            await self.bot.db_manager.set_premium_status(guild_id, True)
            await self.refresh_premium_cache(guild_id)
            
            embed = EmbedFactory.create_success_embed(
                title="Premium Activated",
                description=f"Premium subscription has been activated for **{ctx.guild.name}**"
            )
            
            embed.add_field(
                name="Features Unlocked",
                value="• Economy system with wallet management\n• Professional casino games\n• Advanced faction warfare\n• Automated bounty system\n• Real-time leaderboards\n• Voice channel integration",
                inline=False
            )
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logger.error(f"Error activating subscription: {e}")
            await ctx.respond("An error occurred while activating premium subscription.", ephemeral=True)

    @subscription.command(name="deactivate", description="Deactivate premium subscription (Admin only)")
    @commands.has_permissions(administrator=True)
    async def subscription_deactivate(self, ctx: discord.ApplicationContext):
        """Deactivate premium subscription for this guild"""
        try:
            guild_id = ctx.guild.id if ctx.guild else None
            if not guild_id:
                await ctx.respond("This command can only be used in a server.", ephemeral=True)
                return

            # Remove premium status
            await self.bot.db_manager.set_premium_status(guild_id, False)
            await self.refresh_premium_cache(guild_id)
            
            embed = EmbedFactory.create_warning_embed(
                title="Premium Deactivated",
                description=f"Premium subscription has been deactivated for **{ctx.guild.name}**"
            )
            
            embed.add_field(
                name="Affected Features",
                value="• Economy system disabled\n• Casino games limited\n• Faction management restricted\n• Bounty system disabled\n• Automated leaderboards stopped",
                inline=False
            )
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logger.error(f"Error deactivating subscription: {e}")
            await ctx.respond("An error occurred while deactivating premium subscription.", ephemeral=True)

def setup(bot):
    bot.add_cog(SubscriptionManagement(bot))