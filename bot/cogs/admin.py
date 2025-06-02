"""
Simple Admin Commands
Basic server administration without complexity
"""

import discord
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)

class Admin(commands.Cog):
    """Basic admin commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @discord.slash_command(name="ping", description="Check bot latency")
    async def ping(self, ctx: discord.ApplicationContext):
        """Simple ping command"""
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Latency: {latency}ms",
            color=discord.Color.green()
        )
        await ctx.respond(embed=embed)
    
    @discord.slash_command(name="info", description="Bot information")
    async def info(self, ctx: discord.ApplicationContext):
        """Display bot info"""
        embed = discord.Embed(
            title="Bot Information",
            color=discord.Color.blue()
        )
        embed.add_field(name="Guilds", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="Users", value=len(self.bot.users), inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        
        await ctx.respond(embed=embed)
    
    @discord.slash_command(name="give", description="Give coins to a user")
    @commands.has_permissions(administrator=True)
    async def give_coins(self, ctx: discord.ApplicationContext, user: discord.Member, amount: int):
        """Give coins to a user (admin only)"""
        try:
            if amount <= 0:
                await ctx.respond("Amount must be positive", ephemeral=True)
                return
            
            # Update user's balance
            await self.bot.db.users.update_one(
                {"user_id": user.id, "guild_id": ctx.guild_id},
                {"$inc": {"balance": amount}},
                upsert=True
            )
            
            embed = discord.Embed(
                title="💰 Coins Given",
                description=f"Gave {amount} coins to {user.mention}",
                color=discord.Color.green()
            )
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logger.error(f"Give coins error: {e}")
            await ctx.respond("Error giving coins", ephemeral=True)

def setup(bot):
    bot.add_cog(Admin(bot))