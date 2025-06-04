"""
Emerald's Killfeed - Admin Channel Configuration (REFACTORED - PHASE 4)
Discord channel configuration for server events and notifications
Uses py-cord 2.6.1 syntax with proper error handling
"""

import discord
import logging
from typing import Optional
import asyncio

logger = logging.getLogger(__name__)

class AdminChannels(discord.Cog):
    """Admin channel configuration for event notifications"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("AdminChannels cog initialized")

    async def check_premium_access(self, guild_id: int) -> bool:
        """Check if guild has premium access"""
        try:
            premium_data = await self.bot.db_manager.premium_guilds.find_one({"guild_id": guild_id})
            return premium_data is not None and premium_data.get("active", False)
        except Exception as e:
            logger.error(f"Error checking premium access: {e}")
            return False

    @discord.slash_command(name="setup_killfeed", description="Configure killfeed channel")
    @discord.default_permissions(administrator=True)
    async def setup_killfeed(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        """Setup killfeed channel for death notifications"""
        # Immediate defer to prevent Discord timeout
        await ctx.defer()
        except Exception as e:
            logger.error(f"Failed to defer interaction: {e}")
            return
            
        try:
            if not ctx.guild:
                await ctx.followup.send("This command can only be used in a server!", ephemeral=True)
                return
                
            guild_id = ctx.guild.id
            
            # Update channel configuration
            try:
                await asyncio.wait_for(
                    self.bot.db_manager.channel_configs.update_one(
                        {"guild_id": guild_id},
                        {
                            "$set": {
                                "killfeed_channel_id": channel.id,
                                "last_updated": discord.utils.utcnow()
                            }
                        },
                        upsert=True
                    ),
                    timeout=3.0
                )
                
                embed = discord.Embed(
                    title="✅ Killfeed Channel Configured",
                    description=f"Killfeed notifications will now be sent to {channel.mention}",
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
            logger.error(f"Error in setup_killfeed command: {e}")
            try:
                await ctx.followup.send("An error occurred while configuring killfeed channel.", ephemeral=True)
            except:
                pass

    @discord.slash_command(name="setup_events", description="Configure event notifications channel")
    @discord.default_permissions(administrator=True)
    async def setup_events(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        """Setup events channel for mission/helicrash notifications"""
        # Immediate defer to prevent Discord timeout
        try:
        except discord.errors.NotFound:
            return
        except Exception as e:
            logger.error(f"Failed to defer interaction: {e}")
            return
            
        try:
            if not ctx.guild:
                await ctx.followup.send("This command can only be used in a server!", ephemeral=True)
                return
                
            guild_id = ctx.guild.id
            
            # Update channel configuration
            try:
                await asyncio.wait_for(
                    self.bot.db_manager.channel_configs.update_one(
                        {"guild_id": guild_id},
                        {
                            "$set": {
                                "events_channel_id": channel.id,
                                "last_updated": discord.utils.utcnow()
                            }
                        },
                        upsert=True
                    ),
                    timeout=3.0
                )
                
                embed = discord.Embed(
                    title="✅ Events Channel Configured",
                    description=f"Event notifications will now be sent to {channel.mention}",
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
            logger.error(f"Error in setup_events command: {e}")
            try:
                await ctx.followup.send("An error occurred while configuring events channel.", ephemeral=True)
            except:
                pass

    @discord.slash_command(name="view_config", description="View current channel configuration")
    @discord.default_permissions(administrator=True)
    async def view_config(self, ctx: discord.ApplicationContext):
        """View current channel configuration"""
        # Immediate defer to prevent Discord timeout
        await ctx.defer()
        except Exception as e:
            logger.error(f"Failed to defer interaction: {e}")
            return
            
        try:
            if not ctx.guild:
                await ctx.followup.send("This command can only be used in a server!", ephemeral=True)
                return
                
            guild_id = ctx.guild.id
            
            # Get channel configuration
            try:
                config = await asyncio.wait_for(
                    self.bot.db_manager.channel_configs.find_one({"guild_id": guild_id}),
                    timeout=3.0
                )
                
                embed = discord.Embed(
                    title="🔧 Channel Configuration",
                    color=0x00d38a
                )
                
                if config:
                    killfeed_channel = ctx.guild.get_channel(config.get("killfeed_channel_id"))
                    events_channel = ctx.guild.get_channel(config.get("events_channel_id"))
                    
                    embed.add_field(
                        name="Killfeed Channel",
                        value=killfeed_channel.mention if killfeed_channel else "Not configured",
                        inline=False
                    )
                    
                    embed.add_field(
                        name="Events Channel",
                        value=events_channel.mention if events_channel else "Not configured",
                        inline=False
                    )
                else:
                    embed.description = "No channels have been configured yet."
                    
                await ctx.followup.send(embed=embed, ephemeral=True)
                
            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="⚠️ Database Timeout",
                    description="Database is currently slow. Please try again.",
                    color=0xFFAA00
                )
                await ctx.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error in view_config command: {e}")
            try:
                await ctx.followup.send("An error occurred while retrieving configuration.", ephemeral=True)
            except:
                pass

def setup(bot):
    """Load the AdminChannels cog"""
    bot.add_cog(AdminChannels(bot))
    logger.info("AdminChannels cog loaded")
