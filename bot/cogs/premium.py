"""
Emerald's Killfeed - Premium Management System (REFACTORED - PHASE 4)
Premium subscription management and bot owner utilities
Uses py-cord 2.6.1 syntax with proper error handling
"""

import discord
import logging
from typing import Optional
import asyncio
import os

logger = logging.getLogger(__name__)

class Premium(discord.Cog):
    """Premium subscription management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID", "0"))
        logger.info("Premium cog initialized")

    def is_bot_owner(self, user_id: int) -> bool:
        """Check if user is bot owner"""
        return user_id == self.BOT_OWNER_ID

    async def check_premium_access(self, guild_id: int) -> bool:
        """Check if guild has premium access"""
        try:
            premium_data = await self.bot.db_manager.premium_guilds.find_one({"guild_id": guild_id})
            return premium_data is not None and premium_data.get("active", False)
        except Exception as e:
            logger.error(f"Error checking premium access: {e}")
            return False

    @discord.slash_command(name="sethome", description="Set this server as the bot's home server")
    async def sethome(self, ctx: discord.ApplicationContext):
        """Set this server as the bot's home server (BOT_OWNER_ID only)"""
        # Immediate defer to prevent Discord timeout
        await ctx.defer()
        
        try:
            pass
            # Check if user is bot owner
            if not self.is_bot_owner(ctx.user.id):
                await ctx.followup.send("Only the bot owner can use this command!", ephemeral=True)
                return

            guild_id = ctx.guild.id if ctx.guild else None
            if not guild_id:
                await ctx.followup.send("This command can only be used in a server!", ephemeral=True)
                return
            
            # Set as home server with premium access
            try:
                await asyncio.wait_for(
                    self.bot.db_manager.premium_guilds.update_one(
                        {"guild_id": guild_id},
                        {
                            "$set": {
                                "active": True,
                                "home_server": True,
                                "last_updated": discord.utils.utcnow()
                            }
                        },
                        upsert=True
                    ),
                    timeout=3.0
                )
                
                embed = discord.Embed(
                    title="✅ Home Server Set",
                    description=f"Successfully set {ctx.guild.name} as the bot's home server with premium access!",
                    color=0x00ff00
                )
                await ctx.followup.send(embed=embed)
                
            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="⚠️ Configuration Failed",
                    description="Database timeout. Please try again.",
                    color=0xFFAA00
                )
                await ctx.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error in sethome command: {e}")
            try:
                await ctx.followup.send("An error occurred while setting home server.", ephemeral=True)
            except:
                pass

    @discord.slash_command(name="premium_status", description="Check premium status for this server")
    async def premium_status(self, ctx: discord.ApplicationContext):
        """Check premium status for current server"""
        # Immediate defer to prevent Discord timeout
        await ctx.defer()
        
        try:
            if not ctx.guild:
                await ctx.followup.send("This command can only be used in a server!", ephemeral=True)
                return
                
            guild_id = ctx.guild.id
            
            # Check premium status
            try:
                premium_data = await asyncio.wait_for(
                    self.bot.db_manager.premium_guilds.find_one({"guild_id": guild_id}),
                    timeout=3.0
                )
                
                embed = discord.Embed(
                    title="💎 Premium Status",
                    color=0x00d38a if premium_data and premium_data.get("active") else 0x808080
                )
                
                if premium_data and premium_data.get("active"):
                    embed.description = "✅ This server has premium access!"
                    if premium_data.get("home_server"):
                        embed.add_field(
                            name="Special Status",
                            value="🏠 Bot Home Server",
                            inline=False
                        )
                else:
                    embed.description = "❌ This server does not have premium access."
                    embed.add_field(
                        name="Get Premium",
                        value="Contact the bot owner for premium access.",
                        inline=False
                    )
                    
                await ctx.followup.send(embed=embed, ephemeral=True)
                
            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="⚠️ Database Timeout",
                    description="Database is currently slow. Please try again.",
                    color=0xFFAA00
                )
                await ctx.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error in premium_status command: {e}")
            try:
                await ctx.followup.send("An error occurred while checking premium status.", ephemeral=True)
            except:
                pass

def setup(bot):
    """Load the Premium cog"""
    bot.add_cog(Premium(bot))
    logger.info("Premium cog loaded")
