"""
Emerald's Killfeed - Modular Gambling System
Refactored gambling system with separated game modules
"""

import discord
from discord.ext import commands
import logging
from bot.gambling.core import GamblingCore
from bot.gambling.slots import SlotsGame
from bot.gambling.blackjack import BlackjackGame
from bot.gambling.roulette import RouletteGame

logger = logging.getLogger(__name__)

class Gambling(commands.Cog):
    """Modular gambling system with premium gating"""
    
    def __init__(self, bot):
        self.bot = bot
        self.core = GamblingCore(bot)
        self.slots = SlotsGame(self.core)
        self.blackjack = BlackjackGame(self.core)
        self.roulette = RouletteGame(self.core)
        
    @discord.slash_command(name="slots", description="Play the slot machine")
    async def slots_command(self, ctx: discord.ApplicationContext, 
                           bet: discord.Option(int, "Bet amount", min_value=10, max_value=50000)):
        """Play slots game"""
        try:
            # Check premium access
            has_access = await self.core.check_premium_access(ctx.guild_id)
            if not has_access:
                embed = discord.Embed(
                    title="🔒 Premium Required",
                    description="Gambling features require premium access",
                    color=0xff0000
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return
                
            await ctx.defer()
            embed = await self.slots.play(ctx, bet)
            await ctx.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Slots command error: {e}")
            await ctx.respond("An error occurred", ephemeral=True)
            
    @discord.slash_command(name="blackjack", description="Start a blackjack game")
    async def blackjack_command(self, ctx: discord.ApplicationContext,
                               bet: discord.Option(int, "Bet amount", min_value=10, max_value=50000)):
        """Start blackjack game"""
        try:
            # Check premium access
            has_access = await self.core.check_premium_access(ctx.guild_id)
            if not has_access:
                embed = discord.Embed(
                    title="🔒 Premium Required",
                    description="Gambling features require premium access",
                    color=0xff0000
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return
                
            await ctx.defer()
            embed = await self.blackjack.start_game(ctx, bet)
            await ctx.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Blackjack command error: {e}")
            await ctx.respond("An error occurred", ephemeral=True)
            
    @discord.slash_command(name="roulette", description="Play roulette")
    async def roulette_command(self, ctx: discord.ApplicationContext,
                              bet: discord.Option(int, "Bet amount", min_value=10, max_value=50000),
                              choice: discord.Option(str, "Bet choice (red/black/even/odd/low/high/0-36)")):
        """Play roulette game"""
        try:
            # Check premium access
            has_access = await self.core.check_premium_access(ctx.guild_id)
            if not has_access:
                embed = discord.Embed(
                    title="🔒 Premium Required", 
                    description="Gambling features require premium access",
                    color=0xff0000
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return
                
            await ctx.defer()
            embed = await self.roulette.play(ctx, bet, choice)
            await ctx.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Roulette command error: {e}")
            await ctx.respond("An error occurred", ephemeral=True)

def setup(bot):
    bot.add_cog(Gambling(bot))