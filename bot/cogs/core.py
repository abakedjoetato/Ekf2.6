"""
Emerald's Killfeed - Core System Commands
Basic bot management, info, and utility commands
"""

import logging
from datetime import datetime, timezone
from typing import Optional

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

class Core(discord.Cog):
    """
    CORE SYSTEM
    - Basic bot information and utility commands
    - Server management and configuration
    - General purpose commands
    """

    def __init__(self, bot):
        self.bot = bot
    
    async def check_premium_access(self, guild_id: int) -> bool:
        """Check if guild has premium access - unified validation"""
        try:
            if hasattr(self.bot, 'premium_manager_v2'):
                return await self.bot.premium_manager_v2.has_premium_access(guild_id)
            else:
                return False
        except Exception as e:
            logger.error(f"Premium access check failed: {e}")
            return False

    @discord.slash_command(name="info", description="Show bot information")
    async def info(self, ctx: discord.ApplicationContext):
        """Display bot information and statistics"""
        try:
            # Create bot info embed manually for reliability
            embed = discord.Embed(
                title="🤖 Emerald's Killfeed Bot",
                description="Advanced Discord bot for Deadside server monitoring",
                color=0x00d38a,
                timestamp=datetime.now(timezone.utc)
            )

            # Add bot information fields
            embed.add_field(
                name="Server Statistics",
                value=f"**Guilds:** {len(self.bot.guilds)}\n**Users:** {sum(guild.member_count for guild in self.bot.guilds if guild.member_count):,}",
                inline=True
            )

            embed.add_field(
                name="⚙️ System Status", 
                value="**Status:** Online\n**Version:** v2.0",
                inline=True
            )

            embed.add_field(
                name="🔗 Links",
                value="[Discord Server](https://discord.gg/EmeraldServers)\n[Support](https://discord.gg/EmeraldServers)",
                inline=False
            )

            # Set thumbnail using main logo
            main_file = discord.File("./assets/main.png", filename="main.png")
            embed.set_thumbnail(url="attachment://main.png")
            embed.set_footer(text="Powered by Discord.gg/EmeraldServers")

            await ctx.respond(embed=embed, file=main_file)
        except Exception as e:
            logger.error(f"Failed to show bot info: {e}")
            await ctx.respond("Failed to retrieve bot information.", ephemeral=True)

    @discord.slash_command(name="ping", description="Check bot latency")
    async def ping(self, ctx):
        """Check bot response time and latency"""
        try:
            await ctx.defer()
            latency = round(self.bot.latency * 1000)

            embed = discord.Embed(
                title="🏓 Pong!",
                description=f"Bot latency: **{latency}ms**",
                color=0x00FF00 if latency < 100 else 0xFFD700 if latency < 300 else 0xFF6B6B,
                timestamp=datetime.now(timezone.utc)
            )

            # Status indicator
            if latency < 100:
                status = " Excellent"
            elif latency < 300:
                status = "🟡 Good"
            else:
                status = " Poor"

            embed.add_field(
                name="📡 Connection Status",
                value=status,
                inline=True
            )

            embed.set_footer(text="Powered by Discord.gg/EmeraldServers")

            await ctx.respond(embed=embed)

        except Exception as e:
            logger.error(f"Failed to ping: {e}")
            await ctx.respond("Failed to check latency.", ephemeral=True)

        @discord.slash_command(name="help", description="Show help information")
    async def help(self, ctx):
        """Display help information and command categories"""
        try:
            await ctx.defer()
            embed = discord.Embed(
                title="❓ Help & Commands",
                description="Complete guide to Emerald's Killfeed Bot",
                color=0x3498DB,
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(
                name="📊 Statistics",
                value="`/stats` - Player statistics
`/leaderboard` - Top players",
                inline=True
            )
            
            embed.add_field(
                name="🔧 Admin",
                value="`/setchannel` - Configure channels
`/status` - Bot status",
                inline=True
            )
            
            embed.add_field(
                name="💰 Economy",
                value="`/balance` - Check credits
`/daily` - Daily rewards",
                inline=True
            )
            
            embed.set_footer(text="Emerald's Killfeed Bot", icon_url=ctx.bot.user.display_avatar.url)
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logger.error(f"Failed to show help: {e}")
            await ctx.respond("Failed to retrieve help information.", ephemeral=True)

    

    def _format_uptime(self) -> str:
        """Format bot uptime in human readable format"""
        try:
            import psutil
            import os

            # Get process uptime
            process = psutil.Process(os.getpid())
            uptime_seconds = process.create_time()
            current_time = datetime.now().timestamp()
            uptime = int(current_time - uptime_seconds)

            hours, remainder = divmod(uptime, 3600)
            minutes, seconds = divmod(remainder, 60)

            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"

        except:
            return "Unknown"

def setup(bot):
    bot.add_cog(Core(bot))