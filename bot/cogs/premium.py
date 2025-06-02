"""
Simple Premium Management
Basic premium subscription handling without overengineering
"""

import discord
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)

class Premium(commands.Cog):
    """Basic premium subscription management"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @discord.slash_command(name="premium", description="Check premium status")
    async def premium_status(self, ctx: discord.ApplicationContext):
        """Check if this server has premium access"""
        try:
            # Simple database query
            guild_doc = await self.bot.db.guilds.find_one({"guild_id": ctx.guild_id})
            has_premium = guild_doc.get("premium", False) if guild_doc else False
            
            embed = discord.Embed(
                title="Premium Status",
                color=discord.Color.gold() if has_premium else discord.Color.red()
            )
            embed.add_field(
                name="Status", 
                value="✅ Premium Active" if has_premium else "❌ Free Tier",
                inline=False
            )
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logger.error(f"Premium check failed: {e}")
            await ctx.respond("Error checking premium status", ephemeral=True)

def setup(bot):
    bot.add_cog(Premium(bot))