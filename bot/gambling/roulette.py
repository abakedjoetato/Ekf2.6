"""
Roulette Game Implementation
European roulette with comprehensive betting options
"""

import random
import logging
from typing import Dict, List, Tuple, Optional
import discord
from .core import GamblingCore, BetValidation, GameSession

logger = logging.getLogger(__name__)

class RouletteGame:
    """European roulette implementation"""
    
    # European roulette numbers (0-36)
    RED_NUMBERS = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
    BLACK_NUMBERS = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]
    
    def __init__(self, gambling_core: GamblingCore):
        self.core = gambling_core
        
    def spin_wheel(self) -> int:
        """Spin the roulette wheel"""
        return random.randint(0, 36)
        
    def get_number_color(self, number: int) -> str:
        """Get color of number"""
        if number == 0:
            return "green"
        elif number in self.RED_NUMBERS:
            return "red"
        else:
            return "black"
            
    def calculate_payout(self, bet_type: str, bet_value: str, winning_number: int, bet_amount: int) -> Tuple[int, str]:
        """Calculate payout based on bet type and winning number"""
        winning_color = self.get_number_color(winning_number)
        
        # Straight number bet
        if bet_type == "number":
            try:
                bet_number = int(bet_value)
                if bet_number == winning_number:
                    return bet_amount * 35, f"Straight number {winning_number} wins!"
            except ValueError:
                pass
                
        # Color bets
        elif bet_type == "color":
            if bet_value.lower() == winning_color and winning_number != 0:
                return bet_amount * 2, f"{winning_color.title()} wins!"
                
        # Even/Odd bets
        elif bet_type == "parity":
            if winning_number != 0:
                is_even = winning_number % 2 == 0
                if (bet_value.lower() == "even" and is_even) or (bet_value.lower() == "odd" and not is_even):
                    return bet_amount * 2, f"{bet_value.title()} wins!"
                    
        # High/Low bets
        elif bet_type == "range":
            if winning_number != 0:
                if (bet_value.lower() == "low" and 1 <= winning_number <= 18) or \
                   (bet_value.lower() == "high" and 19 <= winning_number <= 36):
                    return bet_amount * 2, f"{bet_value.title()} wins!"
                    
        return 0, f"Number {winning_number} ({winning_color}) - No win"
        
    def parse_bet(self, bet_input: str) -> Tuple[str, str]:
        """Parse bet input string"""
        bet_input = bet_input.lower().strip()
        
        # Number bet
        if bet_input.isdigit():
            number = int(bet_input)
            if 0 <= number <= 36:
                return "number", bet_input
                
        # Color bets
        elif bet_input in ["red", "black"]:
            return "color", bet_input
            
        # Parity bets
        elif bet_input in ["even", "odd"]:
            return "parity", bet_input
            
        # Range bets
        elif bet_input in ["low", "high"]:
            return "range", bet_input
            
        return "invalid", ""
        
    async def play(self, ctx: discord.ApplicationContext, bet_amount: int, bet_choice: str) -> discord.Embed:
        """Play roulette game"""
        try:
            # Validate bet amount
            balance = await self.core.get_user_balance(ctx.guild.id, ctx.user.id)
            valid, error_msg = BetValidation.validate_bet_amount(bet_amount, balance)
            
            if not valid:
                embed = discord.Embed(
                    title="❌ Invalid Bet",
                    description=error_msg,
                    color=0xff0000
                )
                return embed
                
            # Parse bet choice
            bet_type, bet_value = self.parse_bet(bet_choice)
            
            if bet_type == "invalid":
                embed = discord.Embed(
                    title="❌ Invalid Bet Choice",
                    description="Valid options: red/black, even/odd, low/high, or number 0-36",
                    color=0xff0000
                )
                return embed
                
            # Deduct bet amount
            success = await self.core.update_user_balance(
                ctx.guild.id, ctx.user.id, -bet_amount, f"Roulette bet: ${bet_amount:,} on {bet_choice}"
            )
            
            if not success:
                embed = discord.Embed(
                    title="❌ Transaction Failed",
                    description="Unable to process bet",
                    color=0xff0000
                )
                return embed
                
            # Spin wheel
            winning_number = self.spin_wheel()
            payout, result_desc = self.calculate_payout(bet_type, bet_value, winning_number, bet_amount)
            
            # Process winnings
            if payout > 0:
                await self.core.update_user_balance(
                    ctx.guild.id, ctx.user.id, payout, f"Roulette win: ${payout:,}"
                )
                
            # Get updated balance
            new_balance = await self.core.get_user_balance(ctx.guild.id, ctx.user.id)
            net_change = payout - bet_amount
            
            # Create result embed
            color = self.get_number_color(winning_number)
            embed_color = 0xff0000 if color == "red" else 0x000000 if color == "black" else 0x00ff00
            
            embed = discord.Embed(
                title="🎡 EMERALD ROULETTE",
                description=f"**Winning Number: {winning_number} ({color.upper()})**\n\n{result_desc}",
                color=embed_color
            )
            
            embed.add_field(
                name="🎯 Your Bet",
                value=f"**Choice:** {bet_choice.title()}\n**Amount:** ${bet_amount:,}",
                inline=True
            )
            
            embed.add_field(
                name="💰 Results",
                value=f"**Payout:** ${payout:,}\n**Net:** ${net_change:+,}",
                inline=True
            )
            
            embed.add_field(
                name="💳 Balance",
                value=f"${new_balance:,}",
                inline=False
            )
            
            return embed
            
        except Exception as e:
            logger.error(f"Roulette game error: {e}")
            embed = discord.Embed(
                title="❌ Game Error",
                description="An error occurred during the game",
                color=0xff0000
            )
            return embed