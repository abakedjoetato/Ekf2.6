"""
Emerald's Killfeed - Economy System (PHASE 3)
Currency stored per Discord user, scoped to guild
Earned via /work, PvP, bounties, online time
Admin control: /eco give, /eco take, /eco reset
"""

import discord
from discord.ext import commands
import asyncio
import random
import logging
from datetime import datetime, timezone
from typing import Dict, Any

logger = logging.getLogger(__name__)

class Economy(commands.Cog):
    """
    ECONOMY (PREMIUM)
    - Currency stored per Discord user, scoped to guild
    - Earned via /work, PvP, bounties, online time
    - Admin control: /eco give, /eco take, /eco reset
    - Tracked in wallet_events
    """

    def __init__(self, bot):
        self.bot = bot
        self.user_locks: Dict[str, asyncio.Lock] = {}

    def get_user_lock(self, user_key: str) -> asyncio.Lock:
        """Get or create a lock for a user to prevent concurrent transactions"""
        if user_key not in self.user_locks:
            self.user_locks[user_key] = asyncio.Lock()
        return self.user_locks[user_key]

    async def check_premium_server(self, guild_id: int, server_id: str = "default") -> bool:
        """Check if guild has premium access for economy features"""
        try:
            # Economy is guild-wide premium feature - check if guild has any premium access
            return await self.bot.db_manager.has_premium_access(guild_id)
        except Exception as e:
            logger.error(f"Error checking premium server: {e}")
            return False

    async def add_wallet_event(self, guild_id: int, discord_id: int, 
                              amount: int, event_type: str, description: str):
        """Add wallet transaction event for tracking"""
        try:
            await self.bot.db_manager.add_wallet_event(
                guild_id, discord_id, amount, event_type, description
            )
        except Exception as e:
            logger.error(f"Failed to add wallet event: {e}")

    @discord.slash_command(name="balance", description="Check your wallet balance")
    async def balance(self, ctx: discord.ApplicationContext):
        """Check user's wallet balance"""
        try:
            if not ctx.guild:
                await ctx.respond("❌ This command must be used in a server", ephemeral=True)
                return
                
            guild_id = ctx.guild.id
            discord_id = ctx.user.id

            # Check premium access
            if not await self.check_premium_server(guild_id):
                embed = discord.Embed(
                    title="Access Restricted",
                    description="Economy features require premium subscription!",
                    color=0xFF6B6B
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return

            # Get wallet data
            wallet = await self.bot.db_manager.get_wallet(guild_id, discord_id)

            embed = discord.Embed(
                title="💰 Wallet Balance",
                description=f"<@{discord_id}>'s financial status",
                color=0x00FF7F,
                timestamp=datetime.now(timezone.utc)
            )

            embed.add_field(
                name="💵 Current Balance",
                value=f"**${wallet['balance']:,}**",
                inline=True
            )

            await ctx.respond(embed=embed)

        except Exception as e:
            logger.error(f"Balance command error: {e}")
            await ctx.respond("❌ Error retrieving balance", ephemeral=True)

    @discord.slash_command(name="work", description="Work to earn money")
    async def work(self, ctx: discord.ApplicationContext):
        """Work command to earn money"""
        try:
            if not ctx.guild:
                await ctx.respond("❌ This command must be used in a server", ephemeral=True)
                return
                
            guild_id = ctx.guild.id
            discord_id = ctx.user.id

            # Check premium access
            if not await self.check_premium_server(guild_id):
                embed = discord.Embed(
                    title="Access Restricted",
                    description="Economy features require premium subscription!",
                    color=0xFF6B6B
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return

            # Random earnings between $50-200
            earnings = random.randint(50, 200)
            
            # Update wallet
            user_key = f"{guild_id}:{discord_id}"
            async with self.get_user_lock(user_key):
                await self.bot.db_manager.update_user_balance(
                    guild_id, discord_id, earnings, f"Work earnings: ${earnings}"
                )
                
                # Add wallet event
                await self.add_wallet_event(
                    guild_id, discord_id, earnings, "work", f"Work earnings: ${earnings}"
                )

            embed = discord.Embed(
                title="💼 Work Complete",
                description=f"You earned **${earnings:,}** from work!",
                color=0x00FF7F
            )

            await ctx.respond(embed=embed)

        except Exception as e:
            logger.error(f"Work command error: {e}")
            await ctx.respond("❌ Error processing work command", ephemeral=True)

    eco = discord.SlashCommandGroup("eco", "Economy administration commands")

    @eco.command(name="give", description="Give money to a user (admin only)")
    async def eco_give(self, ctx: discord.ApplicationContext, 
                       user: discord.Member, amount: int):
        """Give money to a user (admin only)"""
        try:
            if not ctx.guild:
                await ctx.respond("❌ This command must be used in a server", ephemeral=True)
                return

            # Check admin permissions
            if not ctx.user.guild_permissions.administrator if hasattr(ctx.user, "guild_permissions") else False:
                await ctx.respond("❌ You need administrator permissions", ephemeral=True)
                return
                
            guild_id = ctx.guild.id

            # Check premium access
            if not await self.check_premium_server(guild_id):
                embed = discord.Embed(
                    title="Access Restricted",
                    description="Economy features require premium subscription!",
                    color=0xFF6B6B
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return

            # Update wallet
            user_key = f"{guild_id}:{user.id}"
            async with self.get_user_lock(user_key):
                await self.bot.db_manager.update_user_balance(
                    guild_id, user.id, amount, f"Admin give: ${amount} from {ctx.user.display_name}"
                )
                
                # Add wallet event
                await self.add_wallet_event(
                    guild_id, user.id, amount, "admin_give", 
                    f"Admin give: ${amount} from {ctx.user.display_name}"
                )

            embed = discord.Embed(
                title="💰 Money Given",
                description=f"Gave **${amount:,}** to {user.mention}",
                color=0x00FF7F
            )

            await ctx.respond(embed=embed)

        except Exception as e:
            logger.error(f"Eco give command error: {e}")
            await ctx.respond("❌ Error giving money", ephemeral=True)

def setup(bot):
    bot.add_cog(Economy(bot))
