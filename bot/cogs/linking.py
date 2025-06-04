"""
Emerald's Killfeed - Character Linking System (REFACTORED - PHASE 4)
Links Discord users to game characters for cross-platform statistics
Uses py-cord 2.6.1 syntax with proper error handling
"""

import discord
import logging
from typing import Optional, List
import asyncio

logger = logging.getLogger(__name__)

class Linking(discord.Cog):
    """Character linking system for Discord users"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("Linking cog initialized")

    async def check_premium_access(self, guild_id: int) -> bool:
        """Check if guild has premium access"""
        try:
            premium_data = await self.bot.db_manager.premium_guilds.find_one({"guild_id": guild_id})
            return premium_data is not None and premium_data.get("active", False)
        except Exception as e:
            logger.error(f"Error checking premium access: {e}")
            return False

    @discord.slash_command(name="link", description="Link your Discord account to a game character")
    async def link_character(self, ctx: discord.ApplicationContext, character_name: str):
        """Link Discord user to game character"""
        # Immediate defer to prevent Discord timeout
        try:
            await ctx.defer()
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
            user_id = ctx.user.id
            
            # Clean character name
            character_name = character_name.strip()
            if not character_name:
                await ctx.followup.send("Please provide a valid character name!", ephemeral=True)
                return
            
            # Check if character exists in database
            try:
                character_exists = await asyncio.wait_for(
                    self.bot.db_manager.kill_events.find_one({
                        "guild_id": guild_id,
                        "$or": [
                            {"killer_name": character_name},
                            {"victim_name": character_name}
                        ]
                    }),
                    timeout=3.0
                )
                
                if not character_exists:
                    embed = discord.Embed(
                        title="❌ Character Not Found",
                        description=f"Character '{character_name}' not found in the database.\nMake sure the character has activity on the server.",
                        color=0xff0000
                    )
                    await ctx.followup.send(embed=embed, ephemeral=True)
                    return
                    
            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="⚠️ Database Timeout",
                    description="Database is currently slow. Please try again.",
                    color=0xFFAA00
                )
                await ctx.followup.send(embed=embed, ephemeral=True)
                return
            
            # Create or update linking
            try:
                await asyncio.wait_for(
                    self.bot.db_manager.user_characters.update_one(
                        {"guild_id": guild_id, "user_id": user_id},
                        {
                            "$addToSet": {"character_names": character_name},
                            "$set": {
                                "last_updated": discord.utils.utcnow(),
                                "display_name": ctx.user.display_name
                            }
                        },
                        upsert=True
                    ),
                    timeout=3.0
                )
                
                embed = discord.Embed(
                    title="✅ Character Linked",
                    description=f"Successfully linked character '{character_name}' to your account!",
                    color=0x00ff00
                )
                await ctx.followup.send(embed=embed, ephemeral=True)
                
            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="⚠️ Link Failed",
                    description="Database timeout. Please try again.",
                    color=0xFFAA00
                )
                await ctx.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error in link command: {e}")
            try:
                await ctx.followup.send("An error occurred while linking character.", ephemeral=True)
            except:
                pass

    @discord.slash_command(name="unlink", description="Unlink a character from your Discord account")
    async def unlink_character(self, ctx: discord.ApplicationContext, character_name: str):
        """Unlink character from Discord user"""
        # Immediate defer to prevent Discord timeout
        try:
            await ctx.defer()
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
            user_id = ctx.user.id
            
            # Remove character from user's linked characters
            try:
                result = await asyncio.wait_for(
                    self.bot.db_manager.user_characters.update_one(
                        {"guild_id": guild_id, "user_id": user_id},
                        {"$pull": {"character_names": character_name.strip()}}
                    ),
                    timeout=3.0
                )
                
                if result.modified_count > 0:
                    embed = discord.Embed(
                        title="✅ Character Unlinked",
                        description=f"Successfully unlinked character '{character_name}' from your account!",
                        color=0x00ff00
                    )
                else:
                    embed = discord.Embed(
                        title="❌ Character Not Found",
                        description=f"Character '{character_name}' was not linked to your account.",
                        color=0xff0000
                    )
                    
                await ctx.followup.send(embed=embed, ephemeral=True)
                
            except asyncio.TimeoutError:
                embed = discord.Embed(
                    title="⚠️ Unlink Failed",
                    description="Database timeout. Please try again.",
                    color=0xFFAA00
                )
                await ctx.followup.send(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error in unlink command: {e}")
            try:
                await ctx.followup.send("An error occurred while unlinking character.", ephemeral=True)
            except:
                pass

    @discord.slash_command(name="linked", description="View your linked characters")
    async def view_linked(self, ctx: discord.ApplicationContext):
        """View user's linked characters"""
        # Immediate defer to prevent Discord timeout
        try:
            await ctx.defer()
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
            user_id = ctx.user.id
            
            # Get user's linked characters
            try:
                user_data = await asyncio.wait_for(
                    self.bot.db_manager.user_characters.find_one({
                        "guild_id": guild_id,
                        "user_id": user_id
                    }),
                    timeout=3.0
                )
                
                if not user_data or not user_data.get("character_names"):
                    embed = discord.Embed(
                        title="📋 Linked Characters",
                        description="You haven't linked any characters yet.\nUse `/link <character_name>` to link a character.",
                        color=0x808080
                    )
                else:
                    characters = user_data.get("character_names", [])
                    char_list = "\n".join([f"• {char}" for char in characters])
                    
                    embed = discord.Embed(
                        title="📋 Linked Characters",
                        description=f"**Your linked characters:**\n{char_list}",
                        color=0x00d38a
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
            logger.error(f"Error in linked command: {e}")
            try:
                await ctx.followup.send("An error occurred while retrieving linked characters.", ephemeral=True)
            except:
                pass

def setup(bot):
    """Load the Linking cog"""
    bot.add_cog(Linking(bot))
    logger.info("Linking cog loaded")
