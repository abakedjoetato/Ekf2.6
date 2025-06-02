"""
Simple Casino System
Basic gambling commands without overengineering
"""

import discord
from discord.ext import commands
import random
import logging

logger = logging.getLogger(__name__)

class Casino(commands.Cog):
    """Basic casino games"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @discord.slash_command(name="flip", description="Flip a coin")
    async def coinflip(self, ctx: discord.ApplicationContext, bet: int = 10):
        """Simple coinflip game"""
        try:
            if bet < 1:
                await ctx.respond("Minimum bet is 1 coin!", ephemeral=True)
                return
                
            # Get user's current balance
            user_doc = await self.bot.db.users.find_one({
                "user_id": ctx.author.id,
                "guild_id": ctx.guild_id
            })
            
            balance = user_doc.get("balance", 100) if user_doc else 100
            
            if bet > balance:
                await ctx.respond(f"You don't have enough coins! Balance: {balance}", ephemeral=True)
                return
            
            # Flip the coin
            player_wins = random.choice([True, False])
            result = "Heads" if player_wins else "Tails"
            
            # Update balance
            new_balance = balance + bet if player_wins else balance - bet
            
            await self.bot.db.users.update_one(
                {"user_id": ctx.author.id, "guild_id": ctx.guild_id},
                {"$set": {"balance": new_balance}},
                upsert=True
            )
            
            embed = discord.Embed(
                title="🪙 Coinflip",
                color=discord.Color.green() if player_wins else discord.Color.red()
            )
            embed.add_field(name="Result", value=result, inline=True)
            embed.add_field(name="Outcome", value="You win!" if player_wins else "You lose!", inline=True)
            embed.add_field(name="Balance", value=f"{new_balance} coins", inline=True)
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logger.error(f"Coinflip error: {e}")
            await ctx.respond("Error processing coinflip", ephemeral=True)
    
    @discord.slash_command(name="balance", description="Check your coin balance")
    async def balance(self, ctx: discord.ApplicationContext):
        """Check user's balance"""
        try:
            user_doc = await self.bot.db.users.find_one({
                "user_id": ctx.author.id,
                "guild_id": ctx.guild_id
            })
            
            balance = user_doc.get("balance", 100) if user_doc else 100
            
            embed = discord.Embed(
                title="💰 Your Balance",
                description=f"**{balance}** coins",
                color=discord.Color.blue()
            )
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logger.error(f"Balance check error: {e}")
            await ctx.respond("Error checking balance", ephemeral=True)

def setup(bot):
    bot.add_cog(Casino(bot))