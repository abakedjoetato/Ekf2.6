
class BetModal(discord.ui.Modal):
    """Modal for bet input"""
    def __init__(self, title="Place Bet"):
        super().__init__(title=title)
        self.bet_amount = discord.ui.InputText(
            label="Bet Amount",
            placeholder="Enter bet amount...",
            max_length=10
        )
        self.add_item(self.bet_amount)
    
    async def callback(self, interaction):
        await interaction.response.defer()
        
"""
Emerald's Killfeed - Advanced Gambling System (PREMIUM)
Single /gamble command with interactive game selection and advanced UX
"""

import discord
from discord.ext import commands
import asyncio
import random
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class GamblingMainView(discord.ui.View):
    """Main gambling interface with changeable bets and game selection"""
    
    def __init__(self, user_id: int, gambling_cog):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.gambling_cog = gambling_cog
        self.current_bet = 100  # Default bet
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your game!", ephemeral=True)
            return False
        return True
        
    async def update_display(self, interaction: discord.Interaction):
        """Update the main gambling display"""
        balance = await self.gambling_cog.get_user_balance(interaction.guild_id, interaction.user.id)
        
        embed = discord.Embed(
            title="🎰 EMERALD CASINO",
            description=f"**Current Bet:** ${self.current_bet:,}\n**Your Balance:** ${balance:,}\n\nChoose your game or adjust your bet:",
            color=0xffd700
        )
        embed.add_field(
            name="🎮 Available Games",
            value="🎰 **Slots** - Match symbols for big wins\n🃏 **Blackjack** - Beat the dealer\n🔴 **Roulette** - Bet on colors or numbers",
            inline=False
        )
        
        # Update bet buttons based on current bet
        self.children[3].disabled = self.current_bet <= 10
        self.children[4].disabled = self.current_bet >= min(50000, balance)
        
        await interaction.edit_original_response(embed=embed, view=self)
    
    @discord.ui.button(label="🎰 Slots", style=discord.ButtonStyle.primary, row=0)
    async def slots_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        result_embed, new_view = await self.gambling_cog.play_slots(interaction, self.current_bet)
        await interaction.edit_original_response(embed=result_embed, view=new_view)
        
    @discord.ui.button(label="🃏 Blackjack", style=discord.ButtonStyle.primary, row=0)
    async def blackjack_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        result_embed, new_view = await self.gambling_cog.play_blackjack(interaction, self.current_bet)
        await interaction.edit_original_response(embed=result_embed, view=new_view)
        
    @discord.ui.button(label="🔴 Roulette", style=discord.ButtonStyle.primary, row=0)
    async def roulette_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        result_embed, new_view = await self.gambling_cog.show_roulette_options(interaction, self.current_bet)
        await interaction.edit_original_response(embed=result_embed, view=new_view)
        
    @discord.ui.button(label="➖ Lower Bet", style=discord.ButtonStyle.secondary, row=1)
    async def lower_bet_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        if self.current_bet > 10:
            if self.current_bet <= 100:
                self.current_bet = max(10, self.current_bet - 10)
            elif self.current_bet <= 1000:
                self.current_bet = max(100, self.current_bet - 100)
            else:
                self.current_bet = max(1000, self.current_bet - 1000)
        await self.update_display(interaction)
        
    @discord.ui.button(label="➕ Raise Bet", style=discord.ButtonStyle.secondary, row=1)
    async def raise_bet_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        balance = await self.gambling_cog.get_user_balance(interaction.guild_id, interaction.user.id)
        max_bet = min(50000, balance)
        
        if self.current_bet < max_bet:
            if self.current_bet < 100:
                self.current_bet = min(max_bet, self.current_bet + 10)
            elif self.current_bet < 1000:
                self.current_bet = min(max_bet, self.current_bet + 100)
            else:
                self.current_bet = min(max_bet, self.current_bet + 1000)
        await self.update_display(interaction)
        
    @discord.ui.button(label="💰 Set Custom Bet", style=discord.ButtonStyle.success, row=1)
    async def custom_bet_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        modal = CustomBetModal(self.gambling_cog, self)
        await interaction.response.send_modal(modal)

class PlayAgainView(discord.ui.View):
    """View for playing again after a game"""
    
    def __init__(self, user_id: int, gambling_cog):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.gambling_cog = gambling_cog
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your game!", ephemeral=True)
            return False
        return True
        
    @discord.ui.button(label="🎲 Play Again", style=discord.ButtonStyle.success, emoji="🎲")
    async def play_again_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Start a new gambling session"""
        await interaction.response.send_modal(BetModal(self.gambling_cog))
        
    @discord.ui.button(label="💰 Check Balance", style=discord.ButtonStyle.secondary, emoji="💰")
    async def balance_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Check current balance"""
        await interaction.response.defer()
        balance = await self.gambling_cog.get_user_balance(interaction.guild_id, interaction.user.id)
        embed = discord.Embed(
            title="💰 Current Balance",
            description=f"**${balance:,}**",
            color=0x00ff00
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

class CustomBetModal(discord.ui.Modal):
    """Modal for setting a custom bet amount"""
    
    def __init__(self, gambling_cog, main_view):
        super().__init__(title="Set Custom Bet Amount")
        self.gambling_cog = gambling_cog
        self.main_view = main_view
        
        self.bet_input = discord.ui.InputText(
            label="Custom Bet Amount",
            placeholder="Enter amount ($10 - $50,000)",
            min_length=2,
            max_length=6
        )
        self.add_item(self.bet_input)
        
    async def callback(self, interaction: discord.Interaction):
        try:
            bet_amount = int(self.bet_input.value.replace('$', '').replace(',', ''))
            
            # Validate bet
            balance = await self.gambling_cog.get_user_balance(interaction.guild_id, interaction.user.id)
            if bet_amount < 10:
                await interaction.response.send_message("Minimum bet is $10", ephemeral=True)
                return
            if bet_amount > 50000:
                await interaction.response.send_message("Maximum bet is $50,000", ephemeral=True)
                return
            if bet_amount > balance:
                await interaction.response.send_message(f"Insufficient balance. You have ${balance:,}", ephemeral=True)
                return
                
            # Update the main view with new bet amount
            self.main_view.current_bet = bet_amount
            await self.main_view.update_display(interaction)
            
        except ValueError:
            await interaction.response.send_message("Please enter a valid number", ephemeral=True)

class Gambling(commands.Cog):
    """Advanced gambling system with premium gating and interactive UX"""
    
    def __init__(self, bot):
        self.bot = bot
        
    async def check_premium_access(self, guild_id: int) -> bool:
        """Check if guild has premium access for gambling features"""
        # Gambling is guild-wide premium feature - requires at least 1 premium server
        try:
            if hasattr(self.bot, 'premium_manager_v2'):
                return await self.bot.premium_manager_v2.has_premium_access(guild_id)
            else:
                # Fallback to old method
                guild_doc = await self.bot.db_manager.get_guild(guild_id)
                if not guild_doc:
                    return False
                
                servers = guild_doc.get('servers', [])
                for server_config in servers:
                    server_id = server_config.get('server_id', server_config.get('_id', 'default'))
                    if await self.bot.db_manager.is_premium_server(guild_id or 0, server_id):
                        return True
                return False
        except Exception as e:
            logger.error(f"Premium check failed for gambling: {e}")
            return False
            
    async def get_user_balance(self, guild_id: int, user_id: int) -> int:
        """Get user's current balance"""
        try:
            wallet = await self.bot.db_manager.get_wallet(guild_id or 0, user_id)
            return wallet.get('balance', 0) if wallet else 0
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return 0
            
    async def update_user_balance(self, guild_id: int, user_id: int, amount: int, description: str) -> bool:
        """Update user balance and log transaction"""
        try:
            current_balance = await self.get_user_balance(guild_id or 0, user_id)
            new_balance = current_balance + amount
            
            if new_balance < 0:
                return False
                
            # Use the correct method signature with transaction_type
            await self.bot.db_manager.update_wallet(guild_id or 0, user_id, amount, 'gambling')
            
            # Log wallet event
            await self.add_wallet_event(guild_id or 0, user_id, amount, 'gambling', description)
            return True
        except Exception as e:
            logger.error(f"Error updating balance: {e}")
            return False
            
    async def add_wallet_event(self, guild_id: int, discord_id: int, amount: int, event_type: str, description: str):
        """Add wallet transaction event for tracking"""
        try:
            event_data = {
                'guild_id': guild_id,
                'discord_id': discord_id,
                'amount': amount,
                'event_type': event_type,
                'description': description,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            await self.bot.db_manager.add_wallet_event(event_data)
        except Exception as e:
            logger.error(f"Error adding wallet event: {e}")
        
    @discord.slash_command(name="gamble", description="Enter the casino with interactive games")
    async def gamble_command(self, ctx: discord.ApplicationContext):
        """Main gambling command with interactive UX"""
        try:
            # Check premium access
            has_access = await self.check_premium_access(ctx.guild_id)
            if not has_access:
                embed = discord.Embed(
                    title="🔒 Premium Required",
                    description="Casino features require premium access",
                    color=0xff0000
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return
                
            # Get user balance
            balance = await self.get_user_balance(ctx.guild_id, ctx.user.id if ctx.user else 0)
            if balance < 10:
                embed = discord.Embed(
                    title="💸 Insufficient Funds",
                    description="You need at least $10 to gamble. Use `/work` to earn money!",
                    color=0xff0000
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return
                
            # Create main gambling interface
            view = GamblingMainView(ctx.user.id if ctx.user else 0, self)
            embed = discord.Embed(
                title="🎰 EMERALD CASINO",
                description=f"**Current Bet:** ${view.current_bet:,}\n**Your Balance:** ${balance:,}\n\nChoose your game or adjust your bet:",
                color=0xffd700
            )
            embed.add_field(
                name="🎮 Available Games",
                value="🎰 **Slots** - Match symbols for big wins\n🃏 **Blackjack** - Beat the dealer\n🔴 **Roulette** - Bet on colors or numbers",
                inline=False
            )
            
            await ctx.respond(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Gamble command error: {e}")
            await ctx.respond("An error occurred", ephemeral=True)
            
    async def play_slots(self, interaction: discord.Interaction, bet_amount: int):
        """Play slots game"""
        # Deduct bet
        success = await self.update_user_balance(interaction.guild_id, interaction.user.id, -bet_amount, f"Slots bet ${bet_amount:,}")
        if not success:
            embed = discord.Embed(title="❌ Insufficient Balance", color=0xff0000)
            return embed, None
            
        # Generate slot result
        symbols = ["🍒", "🍋", "🍊", "🍇", "⭐", "💎", "7️⃣"]
        reels = [random.choice(symbols) for _ in range(3)]
        
        # Calculate payout
        payout = 0
        if reels[0] == reels[1] == reels[2]:  # Three of a kind
            if reels[0] == "💎":
                payout = bet_amount * 10  # Diamond jackpot
            elif reels[0] == "7️⃣":
                payout = bet_amount * 7   # Lucky sevens
            elif reels[0] == "⭐":
                payout = bet_amount * 5   # Stars
            else:
                payout = bet_amount * 3   # Other matches
        elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:  # Two of a kind
            payout = bet_amount  # Return bet
            
        # Update balance if won
        if payout > 0:
            await self.update_user_balance(interaction.guild_id, interaction.user.id, payout, f"Slots win ${payout:,}")
            
        # Create result embed
        profit = payout - bet_amount
        color = 0x00ff00 if profit > 0 else 0xff0000 if profit < 0 else 0xffff00
        
        embed = discord.Embed(
            title="🎰 Slot Machine",
            description=f"{''.join(reels)}\n\n**Bet:** ${bet_amount:,}\n**Payout:** ${payout:,}\n**Profit:** ${profit:+,}",
            color=color
        )
        
        new_balance = await self.get_user_balance(interaction.guild_id, interaction.user.id)
        embed.add_field(name="💰 Balance", value=f"${new_balance:,}", inline=True)
        
        view = PlayAgainView(interaction.user.id, self)
        return embed, view
        
    async def play_blackjack(self, interaction: discord.Interaction, bet_amount: int):
        """Start blackjack game (simplified version)"""
        # Deduct bet
        success = await self.update_user_balance(interaction.guild_id, interaction.user.id, -bet_amount, f"Blackjack bet ${bet_amount:,}")
        if not success:
            embed = discord.Embed(title="❌ Insufficient Balance", color=0xff0000)
            return embed, None
            
        # Simple blackjack simulation
        player_cards = [random.randint(1, 11), random.randint(1, 11)]
        dealer_cards = [random.randint(1, 11), random.randint(1, 11)]
        
        player_total = sum(player_cards)
        dealer_total = sum(dealer_cards)
        
        # Adjust for aces
        if player_total > 21 and 11 in player_cards:
            player_total -= 10
        if dealer_total > 21 and 11 in dealer_cards:
            dealer_total -= 10
            
        # Determine winner
        payout = 0
        if player_total > 21:
            result = "Bust! You lose."
        elif dealer_total > 21:
            result = "Dealer busts! You win!"
            payout = bet_amount * 2
        elif player_total > dealer_total:
            result = "You win!"
            payout = bet_amount * 2
        elif dealer_total > player_total:
            result = "Dealer wins!"
        else:
            result = "Push! Bet returned."
            payout = bet_amount
            
        # Update balance if won
        if payout > 0:
            await self.update_user_balance(interaction.guild_id, interaction.user.id, payout, f"Blackjack win ${payout:,}")
            
        profit = payout - bet_amount
        color = 0x00ff00 if profit > 0 else 0xff0000 if profit < 0 else 0xffff00
        
        embed = discord.Embed(
            title="🃏 Blackjack",
            description=f"**Your cards:** {player_total}\n**Dealer cards:** {dealer_total}\n\n{result}\n\n**Bet:** ${bet_amount:,}\n**Payout:** ${payout:,}\n**Profit:** ${profit:+,}",
            color=color
        )
        
        new_balance = await self.get_user_balance(interaction.guild_id, interaction.user.id)
        embed.add_field(name="💰 Balance", value=f"${new_balance:,}", inline=True)
        
        view = PlayAgainView(interaction.user.id, self)
        return embed, view
        
    async def show_roulette_options(self, interaction: discord.Interaction, bet_amount: int):
        """Show roulette betting options"""
        embed = discord.Embed(
            title="🔴 Roulette",
            description=f"**Bet Amount:** ${bet_amount:,}\n\nChoose your bet type:",
            color=0xff0000
        )
        embed.add_field(name="Color Bets", value="🔴 Red (2x)\n⚫ Black (2x)", inline=True)
        embed.add_field(name="Number Bets", value="🔢 Even (2x)\n🔢 Odd (2x)", inline=True)
        embed.add_field(name="Range Bets", value="📉 Low 1-18 (2x)\n📈 High 19-36 (2x)", inline=True)
        
        # Create roulette view with bet options
        view = RouletteView(interaction.user.id, bet_amount, self)
        return embed, view

class RouletteView(discord.ui.View):
    """Roulette betting interface"""
    
    def __init__(self, user_id: int, bet_amount: int, gambling_cog):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.bet_amount = bet_amount
        self.gambling_cog = gambling_cog
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your game!", ephemeral=True)
            return False
        return True
        
    @discord.ui.button(label="🔴 Red", style=discord.ButtonStyle.danger)
    async def red_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.play_roulette(interaction, "red")
        
    @discord.ui.button(label="⚫ Black", style=discord.ButtonStyle.secondary) 
    async def black_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.play_roulette(interaction, "black")
        
    @discord.ui.button(label="🔢 Even", style=discord.ButtonStyle.primary)
    async def even_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.play_roulette(interaction, "even")
        
    @discord.ui.button(label="🔢 Odd", style=discord.ButtonStyle.primary)
    async def odd_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.play_roulette(interaction, "odd")
        
    async def play_roulette(self, interaction: discord.Interaction, bet_type: str):
        """Play roulette with the selected bet type"""
        await interaction.response.defer()
        
        # Deduct bet
        success = await self.gambling_cog.update_user_balance(interaction.guild_id, interaction.user.id, -self.bet_amount, f"Roulette bet ${self.bet_amount:,}")
        if not success:
            embed = discord.Embed(title="❌ Insufficient Balance", color=0xff0000)
            await interaction.edit_original_response(embed=embed, view=None)
            return
            
        # Spin the wheel
        number = random.randint(0, 36)
        is_red = number in [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
        is_black = number != 0 and not is_red
        is_even = number % 2 == 0 and number != 0
        is_odd = number % 2 == 1
        
        # Check if bet won
        won = False
        if bet_type == "red" and is_red:
            won = True
        elif bet_type == "black" and is_black:
            won = True
        elif bet_type == "even" and is_even:
            won = True
        elif bet_type == "odd" and is_odd:
            won = True
            
        payout = self.bet_amount * 2 if won else 0
        
        # Update balance if won
        if payout > 0:
            await self.gambling_cog.update_user_balance(interaction.guild_id, interaction.user.id, payout, f"Roulette win ${payout:,}")
            
        # Determine color for result
        number_color = "🔴" if is_red else "⚫" if is_black else "🟢"
        profit = payout - self.bet_amount
        embed_color = 0x00ff00 if profit > 0 else 0xff0000
        
        embed = discord.Embed(
            title="🔴 Roulette",
            description=f"**Result:** {number_color} {number}\n**Your bet:** {bet_type.title()}\n**Outcome:** {'WIN!' if won else 'LOSE!'}\n\n**Bet:** ${self.bet_amount:,}\n**Payout:** ${payout:,}\n**Profit:** ${profit:+,}",
            color=embed_color
        )
        
        new_balance = await self.gambling_cog.get_user_balance(interaction.guild_id, interaction.user.id)
        embed.add_field(name="💰 Balance", value=f"${new_balance:,}", inline=True)
        
        view = PlayAgainView(interaction.user.id, self.gambling_cog)
        await interaction.edit_original_response(embed=embed, view=view)

def setup(bot):
    bot.add_cog(Gambling(bot))