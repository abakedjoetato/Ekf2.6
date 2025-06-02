#!/usr/bin/env python3
"""
Casino System Cog - Guild-isolated economy with interactive games
"""

import discord
from discord.ext import commands
import logging
import random
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class Casino(commands.Cog):
    """Casino games with guild-isolated economy"""
    
    def __init__(self, bot):
        self.bot = bot
        
    async def get_wallet(self, guild_id: int, user_id: int) -> Dict[str, Any]:
        """Get user's wallet for this guild"""
        wallet = await self.bot.db.economy.find_one({
            "guild_id": guild_id,
            "user_id": user_id
        })
        
        if not wallet:
            # Create new wallet
            wallet = {
                "guild_id": guild_id,
                "user_id": user_id,
                "balance": 1000,  # Starting balance
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            await self.bot.db.economy.insert_one(wallet)
            
        return wallet
    
    async def update_balance(self, guild_id: int, user_id: int, amount: int) -> bool:
        """Update user's balance"""
        try:
            result = await self.bot.db.economy.update_one(
                {"guild_id": guild_id, "user_id": user_id},
                {
                    "$inc": {"balance": amount},
                    "$set": {"updated_at": datetime.now()}
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating balance: {e}")
            return False
    
    @discord.slash_command(name="casino_balance", description="Check your casino balance")
    async def casino_balance(self, ctx: discord.ApplicationContext):
        """Check user's casino balance"""
        try:
            guild_id = ctx.guild.id if ctx.guild else None
            if not guild_id:
                await ctx.respond("❌ This command can only be used in a server.", ephemeral=True)
                return
            
            wallet = await self.get_wallet(guild_id, ctx.author.id)
            
            embed = discord.Embed(
                title="💰 Casino Balance",
                description=f"**Balance:** {wallet['balance']:,} coins",
                color=discord.Color.gold()
            )
            
            embed.set_footer(text=f"Guild: {ctx.guild.name}")
            await ctx.respond(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in casino balance: {e}")
            await ctx.respond("❌ An error occurred while checking your balance.", ephemeral=True)
    
    @discord.slash_command(name="casino_slots", description="Play the slot machine")
    async def casino_slots(
        self,
        ctx: discord.ApplicationContext,
        bet: discord.Option(int, description="Amount to bet (minimum 10)", min_value=10)
    ):
        """Play slot machine"""
        try:
            guild_id = ctx.guild.id if ctx.guild else None
            if not guild_id:
                await ctx.respond("❌ This command can only be used in a server.", ephemeral=True)
                return
            
            wallet = await self.get_wallet(guild_id, ctx.author.id)
            
            if wallet['balance'] < bet:
                await ctx.respond(f"❌ Insufficient balance. You have {wallet['balance']:,} coins.", ephemeral=True)
                return
            
            # Slot symbols
            symbols = ["🍒", "🍋", "🍊", "🍇", "⭐", "💎"]
            
            # Spin the slots
            result = [random.choice(symbols) for _ in range(3)]
            
            # Calculate winnings
            winnings = 0
            if result[0] == result[1] == result[2]:
                if result[0] == "💎":
                    winnings = bet * 10  # Jackpot
                elif result[0] == "⭐":
                    winnings = bet * 5
                else:
                    winnings = bet * 3
            elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
                winnings = bet  # Break even
            
            # Update balance
            net_change = winnings - bet
            await self.update_balance(guild_id, ctx.author.id, net_change)
            
            # Create result embed
            if winnings > bet:
                color = discord.Color.green()
                title = "🎰 WINNER!"
            elif winnings == bet:
                color = discord.Color.yellow()
                title = "🎰 Break Even"
            else:
                color = discord.Color.red()
                title = "🎰 Better Luck Next Time"
            
            embed = discord.Embed(title=title, color=color)
            embed.add_field(name="Result", value=" ".join(result), inline=False)
            embed.add_field(name="Bet", value=f"{bet:,} coins", inline=True)
            embed.add_field(name="Won", value=f"{winnings:,} coins", inline=True)
            embed.add_field(name="Net", value=f"{net_change:+,} coins", inline=True)
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in casino slots: {e}")
            await ctx.respond("❌ An error occurred while playing slots.", ephemeral=True)
    
    @casino_group.command(name="blackjack", description="Play blackjack")
    async def casino_blackjack(
        self,
        ctx: discord.ApplicationContext,
        bet: discord.Option(int, description="Amount to bet (minimum 10)", min_value=10)
    ):
        """Play blackjack"""
        try:
            guild_id = ctx.guild.id if ctx.guild else None
            if not guild_id:
                await ctx.respond("❌ This command can only be used in a server.", ephemeral=True)
                return
            
            wallet = await self.get_wallet(guild_id, ctx.author.id)
            
            if wallet['balance'] < bet:
                await ctx.respond(f"❌ Insufficient balance. You have {wallet['balance']:,} coins.", ephemeral=True)
                return
            
            # Simple blackjack simulation
            player_cards = [random.randint(1, 11), random.randint(1, 11)]
            dealer_cards = [random.randint(1, 11), random.randint(1, 11)]
            
            player_total = sum(player_cards)
            dealer_total = sum(dealer_cards)
            
            # Determine winner
            winnings = 0
            if player_total == 21:
                winnings = bet * 2  # Blackjack
                result_text = "🎉 Blackjack! You win!"
                color = discord.Color.green()
            elif player_total > 21:
                winnings = 0  # Bust
                result_text = "💥 Bust! You lose!"
                color = discord.Color.red()
            elif dealer_total > 21:
                winnings = bet * 2  # Dealer bust
                result_text = "🎉 Dealer bust! You win!"
                color = discord.Color.green()
            elif player_total > dealer_total:
                winnings = bet * 2  # Player wins
                result_text = "🎉 You win!"
                color = discord.Color.green()
            elif player_total < dealer_total:
                winnings = 0  # Player loses
                result_text = "😔 You lose!"
                color = discord.Color.red()
            else:
                winnings = bet  # Tie
                result_text = "🤝 It's a tie!"
                color = discord.Color.yellow()
            
            # Update balance
            net_change = winnings - bet
            await self.update_balance(guild_id, ctx.author.id, net_change)
            
            embed = discord.Embed(title="🃏 Blackjack", description=result_text, color=color)
            embed.add_field(name="Your Cards", value=f"{player_cards} = {player_total}", inline=True)
            embed.add_field(name="Dealer Cards", value=f"{dealer_cards} = {dealer_total}", inline=True)
            embed.add_field(name="Net Change", value=f"{net_change:+,} coins", inline=False)
            
            await ctx.respond(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in casino blackjack: {e}")
            await ctx.respond("❌ An error occurred while playing blackjack.", ephemeral=True)

def setup(bot):
    bot.add_cog(Casino(bot))