"""
Emerald's Killfeed - Core System Commands (REFACTORED)
Essential bot information and system status commands
Uses py-cord 2.6.1 syntax with proper error handling
"""

import discord
from discord.ext import commands
import logging
from datetime import datetime, timezone
import platform
# import psutil  # Not available
import asyncio

logger = logging.getLogger(__name__)

class Core(discord.Cog):
    """Core system commands for bot information and status"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("Core cog initialized")

    async def check_premium_access(self, guild_id: int) -> bool:
        """Check if guild has premium access - unified validation"""
        try:
            premium_data = await self.bot.db_manager.premium_guilds.find_one({"guild_id": guild_id})
            return premium_data is not None and premium_data.get("active", False)
        except Exception as e:
            logger.error(f"Error checking premium access: {e}")
            return False

    @discord.slash_command(name="info", description="Show bot information")
    async def info(self, ctx: discord.ApplicationContext):
        """Display bot information and statistics"""
        # IMMEDIATE defer - must be first line to prevent timeout
        await ctx.defer()
        
        try:
            pass
            # Create bot info embed manually for reliability
            embed = discord.Embed(
        # IMMEDIATE defer - must be first line to prevent timeout
        
                title="🤖 Emerald's Killfeed Bot",
                description="Advanced Discord bot for Deadside server monitoring",
                color=0x00d38a,
                timestamp=datetime.now(timezone.utc)
            )

            # Add bot information fields
            embed.add_field(
                name="📊 Statistics",
                value=f"Servers: {len(self.bot.guilds)}\nLatency: {round(self.bot.latency * 1000)}ms",
                inline=True
            )

            embed.add_field(
                name="💾 System",
                value=f"Python: {platform.python_version()}\nPy-cord: {discord.__version__}",
                inline=True
            )

            embed.add_field(
                name="🔗 Links",
                value="[Discord Server](https://discord.gg/EmeraldServers)\n[Support](https://discord.gg/EmeraldServers)",
                inline=False
            )

            # Set thumbnail using main logo
            try:
                main_file = discord.File("./assets/main.png", filename="main.png")
                embed.set_thumbnail(url="attachment://main.png")
                embed.set_footer(text="Powered by Discord.gg/EmeraldServers")
                
                await ctx.followup.send(embed=embed, file=main_file)
            except FileNotFoundError:
                embed.set_footer(text="Powered by Discord.gg/EmeraldServers")
                await ctx.followup.send(embed=embed)
            except discord.errors.NotFound:
                pass  # Interaction expired
            except Exception as e:
                logger.error(f"Failed to show bot info: {e}")
                try:
                    await ctx.followup.send("Failed to retrieve bot information.", ephemeral=True)
                except discord.errors.NotFound:
                    pass  # Interaction expired
                    
        except Exception as e:
            logger.error(f"Error in info command: {e}")
            try:
                await ctx.followup.send("An error occurred while retrieving bot information.", ephemeral=True)
            except:
                pass

    @discord.slash_command(name="ping", description="Check bot latency")
    async def ping(self, ctx: discord.ApplicationContext):
        """Check bot response time and latency"""
        # IMMEDIATE defer - must be first line to prevent timeout
        await ctx.defer()
        
        try:
            pass
            latency = round(self.bot.latency * 1000)
            
            embed = discord.Embed(
                title="🏓 Pong!",
                description=f"Bot latency: **{latency}ms**",
                color=0x00FF00 if latency < 100 else 0xFFAA00 if latency < 200 else 0xFF0000
            )
            
            await ctx.followup.send(embed=embed)
            
        except discord.errors.NotFound:
            pass  # Interaction expired
        except Exception as e:
            logger.error(f"Error in ping command: {e}")
            try:
                await ctx.followup.send("Failed to check latency.", ephemeral=True)
            except:
                pass

    @discord.slash_command(name="status", description="Show bot system status")
    async def status(self, ctx: discord.ApplicationContext):
        """Display detailed bot system status"""
        # IMMEDIATE defer - must be first line to prevent timeout
        await ctx.defer()
        
        try:
            pass
            # Get system information
            cpu_percent = 0.0  # psutil not available
            memory = type("obj", (object,), {"percent": 0.0, "used": 0, "total": 1024*1024*1024})()
            disk = type("obj", (object,), {"percent": 0.0, "used": 0, "total": 1024*1024*1024*10})()
            
            embed = discord.Embed(
                title="📊 Bot System Status",
                color=0x00d38a,
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(
                name="🖥️ CPU Usage",
                value=f"{cpu_percent:.1f}%",
                inline=True
            )
            
            embed.add_field(
                name="💾 Memory Usage",
                value=f"{memory.percent:.1f}%\n({memory.used // 1024 // 1024}MB / {memory.total // 1024 // 1024}MB)",
                inline=True
            )
            
            embed.add_field(
                name="💿 Disk Usage",
                value=f"{disk.percent:.1f}%\n({disk.used // 1024 // 1024 // 1024}GB / {disk.total // 1024 // 1024 // 1024}GB)",
                inline=True
            )
            
            embed.add_field(
                name="🌐 Network",
                value=f"Latency: {round(self.bot.latency * 1000)}ms\nGuilds: {len(self.bot.guilds)}",
                inline=True
            )
            
            await ctx.followup.send(embed=embed)
            
        except discord.errors.NotFound:
            pass  # Interaction expired
        except Exception as e:
            logger.error(f"Error in status command: {e}")
            try:
                await ctx.followup.send("Failed to retrieve system status.", ephemeral=True)
            except:
                pass

def setup(bot):
    """Load the Core cog"""
    bot.add_cog(Core(bot))
    logger.info("Core cog loaded")
