"""
Emerald's Killfeed - Advanced Gambling System (PREMIUM)
Top-tier casino experience with sophisticated UX and game mechanics
"""

import discord
from discord.ext import commands
import asyncio
import random
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
import math

logger = logging.getLogger(__name__)

class AdvancedGamblingView(discord.ui.View):
    """Ultra-sophisticated gambling interface with real-time updates"""
    
    def __init__(self, user_id: int, gambling_cog):
        super().__init__(timeout=600)  # 10 minute timeout
        self.user_id = user_id
        self.gambling_cog = gambling_cog
        self.current_bet = 100
        self.balance = 0
        self.bet_history = []
        self.quick_bets = [50, 100, 500, 1000, 5000]
        self.current_game = None
        self.wins_streak = 0
        self.total_session_profit = 0
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("🎰 This casino session belongs to someone else!", ephemeral=True)
            return False
        return True
        
    async def refresh_balance(self, guild_id: int):
        """Refresh user balance and update display"""
        self.balance = await self.gambling_cog.get_user_balance(guild_id, self.user_id)
        
    async def update_main_display(self, interaction: discord.Interaction):
        """Update the sophisticated main casino display"""
        await self.refresh_balance(interaction.guild_id)
        
        # Calculate session stats
        session_time = len(self.bet_history)
        avg_bet = sum(self.bet_history) / len(self.bet_history) if self.bet_history else 0
        
        embed = discord.Embed(
            title="🎰 EMERALD PREMIUM CASINO",
            color=0xffd700
        )
        
        # Main stats section
        embed.add_field(
            name="💰 Account Status",
            value=f"**Balance:** ${self.balance:,}\n**Current Bet:** ${self.current_bet:,}\n**Session P&L:** ${self.total_session_profit:+,}",
            inline=True
        )
        
        # Session stats
        embed.add_field(
            name="📊 Session Stats",
            value=f"**Win Streak:** {self.wins_streak}\n**Games Played:** {session_time}\n**Avg Bet:** ${avg_bet:,.0f}",
            inline=True
        )
        
        # Game status
        game_status = f"**Active Game:** {self.current_game or 'None'}\n**Status:** Ready to Play"
        embed.add_field(
            name="🎮 Gaming Status",
            value=game_status,
            inline=True
        )
        
        # Quick bet buttons status
        embed.add_field(
            name="⚡ Quick Bet Options",
            value=" • ".join([f"${bet:,}" for bet in self.quick_bets]),
            inline=False
        )
        
        # Update button states
        self.update_button_states()
        
        await interaction.edit_original_response(embed=embed, view=self)
    
    def update_button_states(self):
        """Update button enabled/disabled states based on balance"""
        # Update quick bet buttons
        for i, quick_bet in enumerate(self.quick_bets):
            if i < len(self.children) - 8:  # Account for game buttons
                self.children[i].disabled = quick_bet > self.balance
                
        # Update bet adjustment buttons
        lower_btn = next((btn for btn in self.children if hasattr(btn, 'custom_id') and btn.custom_id == 'lower_bet'), None)
        raise_btn = next((btn for btn in self.children if hasattr(btn, 'custom_id') and btn.custom_id == 'raise_bet'), None)
        
        if lower_btn:
            lower_btn.disabled = self.current_bet <= 10
        if raise_btn:
            raise_btn.disabled = self.current_bet >= min(50000, self.balance)
    
    # Quick bet buttons (row 0)
    @discord.ui.button(label="$50", style=discord.ButtonStyle.secondary, row=0)
    async def quick_bet_50(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self._set_quick_bet(interaction, 50)
        
    @discord.ui.button(label="$100", style=discord.ButtonStyle.secondary, row=0)
    async def quick_bet_100(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self._set_quick_bet(interaction, 100)
        
    @discord.ui.button(label="$500", style=discord.ButtonStyle.secondary, row=0)
    async def quick_bet_500(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self._set_quick_bet(interaction, 500)
        
    @discord.ui.button(label="$1K", style=discord.ButtonStyle.secondary, row=0)
    async def quick_bet_1k(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self._set_quick_bet(interaction, 1000)
        
    @discord.ui.button(label="$5K", style=discord.ButtonStyle.secondary, row=0)
    async def quick_bet_5k(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self._set_quick_bet(interaction, 5000)
    
    # Game selection buttons (row 1)
    @discord.ui.button(label="🎰 SLOTS", style=discord.ButtonStyle.primary, row=1)
    async def advanced_slots(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        self.current_game = "Slots"
        result_embed, profit = await self.gambling_cog.play_advanced_slots(interaction, self.current_bet)
        await self._process_game_result(interaction, profit, result_embed)
        
    @discord.ui.button(label="🃏 BLACKJACK", style=discord.ButtonStyle.primary, row=1)
    async def advanced_blackjack(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        self.current_game = "Blackjack"
        result_embed, profit = await self.gambling_cog.play_advanced_blackjack(interaction, self.current_bet)
        await self._process_game_result(interaction, profit, result_embed)
        
    @discord.ui.button(label="🎲 ROULETTE", style=discord.ButtonStyle.primary, row=1)
    async def advanced_roulette(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        self.current_game = "Roulette"
        view = AdvancedRouletteView(self.user_id, self.current_bet, self.gambling_cog, self)
        await view.show_roulette_interface(interaction)
        
    @discord.ui.button(label="🎯 CRASH", style=discord.ButtonStyle.primary, row=1)
    async def crash_game(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        self.current_game = "Crash"
        view = CrashGameView(self.user_id, self.current_bet, self.gambling_cog, self)
        await view.start_crash_game(interaction)
    
    # Bet adjustment buttons (row 2)
    @discord.ui.button(label="➖ Lower", style=discord.ButtonStyle.secondary, row=2, custom_id="lower_bet")
    async def lower_bet(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        if self.current_bet > 10:
            if self.current_bet <= 100:
                self.current_bet = max(10, self.current_bet - 10)
            elif self.current_bet <= 1000:
                self.current_bet = max(100, self.current_bet - 100)
            else:
                self.current_bet = max(1000, self.current_bet - 1000)
        await self.update_main_display(interaction)
        
    @discord.ui.button(label="➕ Raise", style=discord.ButtonStyle.secondary, row=2, custom_id="raise_bet")
    async def raise_bet(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        max_bet = min(50000, self.balance)
        if self.current_bet < max_bet:
            if self.current_bet < 100:
                self.current_bet = min(max_bet, self.current_bet + 10)
            elif self.current_bet < 1000:
                self.current_bet = min(max_bet, self.current_bet + 100)
            else:
                self.current_bet = min(max_bet, self.current_bet + 1000)
        await self.update_main_display(interaction)
        
    @discord.ui.button(label="💎 Max Bet", style=discord.ButtonStyle.success, row=2)
    async def max_bet(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        self.current_bet = min(50000, self.balance)
        await self.update_main_display(interaction)
        
    @discord.ui.button(label="📋 Custom", style=discord.ButtonStyle.success, row=2)
    async def custom_bet(self, button: discord.ui.Button, interaction: discord.Interaction):
        modal = AdvancedBetModal(self.gambling_cog, self)
        await interaction.response.send_modal(modal)
        
    @discord.ui.button(label="📊 Stats", style=discord.ButtonStyle.secondary, row=2)
    async def detailed_stats(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self._show_detailed_stats(interaction)
    
    async def _set_quick_bet(self, interaction: discord.Interaction, amount: int):
        """Set bet to quick bet amount"""
        await interaction.response.defer()
        if amount <= self.balance:
            self.current_bet = amount
            await self.update_main_display(interaction)
        else:
            await interaction.followup.send(f"Insufficient balance for ${amount:,} bet", ephemeral=True)
    
    async def _process_game_result(self, interaction: discord.Interaction, profit: int, result_embed: discord.Embed):
        """Process game result and update session stats"""
        self.bet_history.append(self.current_bet)
        self.total_session_profit += profit
        
        if profit > 0:
            self.wins_streak += 1
        else:
            self.wins_streak = 0
            
        # Create enhanced result with session context
        result_embed.add_field(
            name="🏆 Session Impact",
            value=f"**Streak:** {self.wins_streak} wins\n**Session P&L:** ${self.total_session_profit:+,}",
            inline=True
        )
        
        # Add play again view
        view = PlayAgainAdvancedView(self.user_id, self.gambling_cog, self)
        await interaction.edit_original_response(embed=result_embed, view=view)
    
    async def _show_detailed_stats(self, interaction: discord.Interaction):
        """Show comprehensive gambling statistics"""
        await interaction.response.defer(ephemeral=True)
        
        # Get historical data
        stats = await self.gambling_cog.get_gambling_stats(interaction.guild_id, interaction.user.id)
        
        embed = discord.Embed(
            title="📊 Advanced Gambling Statistics",
            color=0x00ff00
        )
        
        embed.add_field(
            name="💰 Financial Overview",
            value=f"**Current Balance:** ${self.balance:,}\n**Total Wagered:** ${stats.get('total_wagered', 0):,}\n**Total Won:** ${stats.get('total_won', 0):,}\n**Net Profit:** ${stats.get('net_profit', 0):+,}",
            inline=True
        )
        
        embed.add_field(
            name="🎮 Game Statistics",
            value=f"**Games Played:** {stats.get('total_games', 0)}\n**Win Rate:** {stats.get('win_rate', 0):.1f}%\n**Best Streak:** {stats.get('best_streak', 0)}\n**Favorite Game:** {stats.get('favorite_game', 'None')}",
            inline=True
        )
        
        embed.add_field(
            name="📈 Session Data",
            value=f"**Current Session:** {len(self.bet_history)} games\n**Session Profit:** ${self.total_session_profit:+,}\n**Current Streak:** {self.wins_streak}",
            inline=True
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)

class AdvancedRouletteView(discord.ui.View):
    """Sophisticated roulette interface with multiple bet types"""
    
    def __init__(self, user_id: int, bet_amount: int, gambling_cog, main_view):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.bet_amount = bet_amount
        self.gambling_cog = gambling_cog
        self.main_view = main_view
        
    async def show_roulette_interface(self, interaction: discord.Interaction):
        """Display advanced roulette betting interface"""
        embed = discord.Embed(
            title="🎲 PREMIUM ROULETTE",
            description=f"**Bet Amount:** ${self.bet_amount:,}\n\nSelect your betting strategy:",
            color=0xff0000
        )
        
        embed.add_field(
            name="🎯 Single Bets",
            value="• **Red/Black** - 1:1 payout\n• **Even/Odd** - 1:1 payout\n• **High/Low** - 1:1 payout",
            inline=True
        )
        
        embed.add_field(
            name="💎 Premium Bets",
            value="• **Dozens** - 2:1 payout\n• **Columns** - 2:1 payout\n• **Number** - 35:1 payout",
            inline=True
        )
        
        await interaction.edit_original_response(embed=embed, view=self)
    
    # Color bets
    @discord.ui.button(label="🔴 Red", style=discord.ButtonStyle.danger, row=0)
    async def bet_red(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self._play_roulette(interaction, "red")
        
    @discord.ui.button(label="⚫ Black", style=discord.ButtonStyle.secondary, row=0)
    async def bet_black(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self._play_roulette(interaction, "black")
        
    @discord.ui.button(label="🔢 Even", style=discord.ButtonStyle.primary, row=0)
    async def bet_even(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self._play_roulette(interaction, "even")
        
    @discord.ui.button(label="🔢 Odd", style=discord.ButtonStyle.primary, row=0)
    async def bet_odd(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self._play_roulette(interaction, "odd")
    
    # Premium bets
    @discord.ui.button(label="📉 Low (1-18)", style=discord.ButtonStyle.success, row=1)
    async def bet_low(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self._play_roulette(interaction, "low")
        
    @discord.ui.button(label="📈 High (19-36)", style=discord.ButtonStyle.success, row=1)
    async def bet_high(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self._play_roulette(interaction, "high")
        
    @discord.ui.button(label="🎯 Lucky Number", style=discord.ButtonStyle.success, row=1)
    async def bet_number(self, button: discord.ui.Button, interaction: discord.Interaction):
        modal = NumberBetModal(self)
        await interaction.response.send_modal(modal)
        
    @discord.ui.button(label="🔙 Back to Casino", style=discord.ButtonStyle.secondary, row=2)
    async def back_to_main(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.main_view.update_main_display(interaction)
    
    async def _play_roulette(self, interaction: discord.Interaction, bet_type: str):
        """Execute roulette game with advanced mechanics"""
        await interaction.response.defer()
        
        result_embed, profit = await self.gambling_cog.play_advanced_roulette(
            interaction, self.bet_amount, bet_type
        )
        
        await self.main_view._process_game_result(interaction, profit, result_embed)

class CrashGameView(discord.ui.View):
    """Innovative crash game with real-time multiplier"""
    
    def __init__(self, user_id: int, bet_amount: int, gambling_cog, main_view):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.bet_amount = bet_amount
        self.gambling_cog = gambling_cog
        self.main_view = main_view
        self.multiplier = 1.0
        self.crashed = False
        self.cashed_out = False
        
    async def start_crash_game(self, interaction: discord.Interaction):
        """Start the crash game with real-time updates"""
        embed = discord.Embed(
            title="🚀 CRASH GAME",
            description=f"**Bet:** ${self.bet_amount:,}\n**Multiplier:** {self.multiplier:.2f}x\n\n🚀 Rocket is climbing! Cash out before it crashes!",
            color=0x00ff00
        )
        
        await interaction.edit_original_response(embed=embed, view=self)
        
        # Start the crash sequence
        asyncio.create_task(self._run_crash_sequence(interaction))
    
    @discord.ui.button(label="💰 CASH OUT", style=discord.ButtonStyle.success, row=0)
    async def cash_out(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not self.crashed and not self.cashed_out:
            self.cashed_out = True
            await self._process_cash_out(interaction)
    
    async def _run_crash_sequence(self, interaction: discord.Interaction):
        """Run the crash game sequence"""
        crash_point = random.uniform(1.1, 10.0)
        
        while self.multiplier < crash_point and not self.cashed_out:
            await asyncio.sleep(1)
            self.multiplier += random.uniform(0.1, 0.5)
            
            if not self.cashed_out:
                embed = discord.Embed(
                    title="🚀 CRASH GAME",
                    description=f"**Bet:** ${self.bet_amount:,}\n**Multiplier:** {self.multiplier:.2f}x\n**Potential Win:** ${int(self.bet_amount * self.multiplier):,}\n\n🚀 Rocket climbing! Cash out before it crashes!",
                    color=0x00ff00
                )
                try:
                    await interaction.edit_original_response(embed=embed, view=self)
                except:
                    break
        
        if not self.cashed_out:
            self.crashed = True
            await self._process_crash(interaction, crash_point)
    
    async def _process_cash_out(self, interaction: discord.Interaction):
        """Process successful cash out"""
        await interaction.response.defer()
        payout = int(self.bet_amount * self.multiplier)
        profit = payout - self.bet_amount
        
        # Update balance
        await self.gambling_cog.update_user_balance(
            interaction.guild_id, interaction.user.id, profit, 
            f"Crash game win at {self.multiplier:.2f}x"
        )
        
        embed = discord.Embed(
            title="💰 CASHED OUT!",
            description=f"**Multiplier:** {self.multiplier:.2f}x\n**Payout:** ${payout:,}\n**Profit:** ${profit:+,}",
            color=0x00ff00
        )
        
        await self.main_view._process_game_result(interaction, profit, embed)
    
    async def _process_crash(self, interaction: discord.Interaction, crash_point: float):
        """Process game crash"""
        profit = -self.bet_amount
        
        await self.gambling_cog.update_user_balance(
            interaction.guild_id, interaction.user.id, profit,
            f"Crash game loss at {crash_point:.2f}x"
        )
        
        embed = discord.Embed(
            title="💥 CRASHED!",
            description=f"**Crash Point:** {crash_point:.2f}x\n**Your Multiplier:** {self.multiplier:.2f}x\n**Loss:** ${self.bet_amount:,}",
            color=0xff0000
        )
        
        try:
            await self.main_view._process_game_result(interaction, profit, embed)
        except:
            pass

class PlayAgainAdvancedView(discord.ui.View):
    """Enhanced play again interface with quick options"""
    
    def __init__(self, user_id: int, gambling_cog, main_view):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.gambling_cog = gambling_cog
        self.main_view = main_view
    
    @discord.ui.button(label="🎰 Play Same Game", style=discord.ButtonStyle.primary, row=0)
    async def play_same_game(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        # Logic to replay the same game type
        await self.main_view.update_main_display(interaction)
    
    @discord.ui.button(label="🎲 Different Game", style=discord.ButtonStyle.secondary, row=0)
    async def choose_different_game(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.main_view.update_main_display(interaction)
    
    @discord.ui.button(label="💰 Check Balance", style=discord.ButtonStyle.success, row=0)
    async def quick_balance(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        balance = await self.gambling_cog.get_user_balance(interaction.guild_id, interaction.user.id)
        await interaction.followup.send(f"💰 Current Balance: ${balance:,}", ephemeral=True)

class AdvancedBetModal(discord.ui.Modal):
    """Sophisticated bet input modal with validation"""
    
    def __init__(self, gambling_cog, main_view):
        super().__init__(title="💎 Premium Bet Configuration")
        self.gambling_cog = gambling_cog
        self.main_view = main_view
        
        self.bet_input = discord.ui.InputText(
            label="Bet Amount",
            placeholder="Enter amount ($10 - $50,000)",
            min_length=2,
            max_length=8
        )
        self.add_item(self.bet_input)
        
    async def callback(self, interaction: discord.Interaction):
        try:
            # Parse bet amount
            bet_str = self.bet_input.value.replace('$', '').replace(',', '').replace('k', '000').replace('K', '000')
            bet_amount = int(float(bet_str))
            
            # Validate bet
            balance = await self.gambling_cog.get_user_balance(interaction.guild_id, interaction.user.id)
            if bet_amount < 10:
                await interaction.response.send_message("❌ Minimum bet is $10", ephemeral=True)
                return
            if bet_amount > 50000:
                await interaction.response.send_message("❌ Maximum bet is $50,000", ephemeral=True)
                return
            if bet_amount > balance:
                await interaction.response.send_message(f"❌ Insufficient balance. You have ${balance:,}", ephemeral=True)
                return
                
            # Update bet amount
            self.main_view.current_bet = bet_amount
            await self.main_view.update_main_display(interaction)
            
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid number", ephemeral=True)

class NumberBetModal(discord.ui.Modal):
    """Modal for number betting in roulette"""
    
    def __init__(self, roulette_view):
        super().__init__(title="🎯 Lucky Number Bet")
        self.roulette_view = roulette_view
        
        self.number_input = discord.ui.InputText(
            label="Lucky Number (0-36)",
            placeholder="Enter a number from 0 to 36",
            min_length=1,
            max_length=2
        )
        self.add_item(self.number_input)
        
    async def callback(self, interaction: discord.Interaction):
        try:
            number = int(self.number_input.value)
            if 0 <= number <= 36:
                await self.roulette_view._play_roulette(interaction, f"number_{number}")
            else:
                await interaction.response.send_message("❌ Number must be between 0 and 36", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid number", ephemeral=True)

class AdvancedGambling(commands.Cog):
    """Ultra-sophisticated gambling system with premium features"""
    
    def __init__(self, bot):
        self.bot = bot
        
    async def check_premium_access(self, guild_id: int) -> bool:
        """Check if guild has premium access for gambling features"""
        try:
            guild_doc = await self.bot.db_manager.get_guild(guild_id)
            if not guild_doc:
                return False
            
            # Check if any server in the guild has premium access
            servers = guild_doc.get('servers', [])
            for server_config in servers:
                server_id = server_config.get('server_id', server_config.get('_id', 'default'))
                if await self.bot.db_manager.is_premium_server(guild_id, server_id):
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Premium check failed: {e}")
            return False
            
    async def get_user_balance(self, guild_id: int, user_id: int) -> int:
        """Get user's current balance"""
        try:
            wallet = await self.bot.db_manager.get_wallet(guild_id, user_id)
            return wallet.get('balance', 0) if wallet else 0
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return 0
            
    async def update_user_balance(self, guild_id: int, user_id: int, amount: int, description: str) -> bool:
        """Update user balance with proper transaction logging"""
        try:
            current_balance = await self.get_user_balance(guild_id, user_id)
            new_balance = current_balance + amount
            
            if new_balance < 0:
                return False
                
            # Use correct method signature
            await self.bot.db_manager.update_wallet(guild_id, user_id, amount, 'gambling')
            
            # Log transaction
            await self.add_wallet_event(guild_id, user_id, amount, 'gambling', description)
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
    
    async def get_gambling_stats(self, guild_id: int, user_id: int) -> Dict[str, Any]:
        """Get comprehensive gambling statistics for a user"""
        try:
            # This would fetch from a gambling_stats collection
            # For now, return basic stats
            return {
                'total_wagered': 0,
                'total_won': 0,
                'net_profit': 0,
                'total_games': 0,
                'win_rate': 0.0,
                'best_streak': 0,
                'favorite_game': 'Slots'
            }
        except Exception as e:
            logger.error(f"Error getting gambling stats: {e}")
            return {}
        
    @discord.slash_command(name="casino", description="Enter the premium casino experience")
    async def casino_command(self, ctx: discord.ApplicationContext):
        """Ultra-premium gambling command with sophisticated interface"""
        try:
            # Check premium access
            has_access = await self.check_premium_access(ctx.guild_id)
            if not has_access:
                embed = discord.Embed(
                    title="🔒 Premium Casino Access Required",
                    description="The premium casino requires an active premium subscription.\n\nContact server administrators for access.",
                    color=0xff0000
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return
                
            # Check balance
            balance = await self.get_user_balance(ctx.guild_id, ctx.user.id)
            if balance < 10:
                embed = discord.Embed(
                    title="💸 Insufficient Casino Funds",
                    description="Minimum balance of $10 required for casino access.\n\nUse `/work` or other commands to earn money first.",
                    color=0xff0000
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return
                
            # Create premium casino interface
            view = AdvancedGamblingView(ctx.user.id, self)
            await view.refresh_balance(ctx.guild_id)
            
            embed = discord.Embed(
                title="🎰 EMERALD PREMIUM CASINO",
                description="Welcome to the most sophisticated gambling experience.",
                color=0xffd700
            )
            
            embed.add_field(
                name="💰 Account Status",
                value=f"**Balance:** ${balance:,}\n**Current Bet:** ${view.current_bet:,}\n**Status:** Ready to Play",
                inline=True
            )
            
            embed.add_field(
                name="🎮 Available Games",
                value="🎰 **Slots** - Advanced reels\n🃏 **Blackjack** - Professional tables\n🎲 **Roulette** - European style\n🚀 **Crash** - High-risk multiplier",
                inline=True
            )
            
            embed.add_field(
                name="⚡ Features",
                value="• Real-time balance updates\n• Session tracking\n• Win streak bonuses\n• Quick bet options",
                inline=True
            )
            
            await ctx.respond(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Casino command error: {e}")
            await ctx.respond("❌ Casino temporarily unavailable", ephemeral=True)
    
    async def play_advanced_slots(self, interaction: discord.Interaction, bet_amount: int) -> Tuple[discord.Embed, int]:
        """Play advanced slots with sophisticated mechanics"""
        # Deduct bet
        success = await self.update_user_balance(interaction.guild_id, interaction.user.id, -bet_amount, f"Slots bet ${bet_amount:,}")
        if not success:
            embed = discord.Embed(title="❌ Insufficient Balance", color=0xff0000)
            return embed, -bet_amount
            
        # Advanced slot symbols with varying rarities
        symbols = {
            '🍒': {'weight': 30, 'value': 2},
            '🍋': {'weight': 25, 'value': 3},
            '🍊': {'weight': 20, 'value': 4},
            '🍇': {'weight': 15, 'value': 5},
            '🔔': {'weight': 8, 'value': 8},
            '⭐': {'weight': 5, 'value': 12},
            '💎': {'weight': 3, 'value': 25},
            '🎰': {'weight': 1, 'value': 50}
        }
        
        # Generate weighted reels
        symbol_pool = []
        for symbol, data in symbols.items():
            symbol_pool.extend([symbol] * data['weight'])
            
        reels = [random.choice(symbol_pool) for _ in range(5)]  # 5-reel slots
        
        # Calculate sophisticated payout
        payout = 0
        win_description = ""
        
        # Check for wins
        unique_symbols = set(reels)
        if len(unique_symbols) == 1:  # All same
            symbol = reels[0]
            multiplier = symbols[symbol]['value'] * 2  # Bonus for 5 of a kind
            payout = bet_amount * multiplier
            win_description = f"🎊 JACKPOT! Five {symbol} - {multiplier}x multiplier!"
        elif len(unique_symbols) == 2:  # Four of a kind
            for symbol in unique_symbols:
                count = reels.count(symbol)
                if count >= 4:
                    multiplier = symbols[symbol]['value']
                    payout = bet_amount * multiplier
                    win_description = f"🎉 Four {symbol} - {multiplier}x multiplier!"
                    break
        elif len(unique_symbols) == 3:  # Three of a kind
            for symbol in unique_symbols:
                count = reels.count(symbol)
                if count >= 3:
                    multiplier = symbols[symbol]['value'] // 2
                    payout = int(bet_amount * multiplier)
                    win_description = f"✨ Three {symbol} - {multiplier}x multiplier!"
                    break
        
        # Apply payout
        if payout > 0:
            await self.update_user_balance(interaction.guild_id, interaction.user.id, payout, f"Slots win ${payout:,}")
            
        profit = payout - bet_amount
        color = 0x00ff00 if profit > 0 else 0xff0000 if profit < 0 else 0xffff00
        
        embed = discord.Embed(
            title="🎰 PREMIUM SLOTS",
            description=f"{'  '.join(reels)}\n\n{win_description or 'No winning combination'}",
            color=color
        )
        
        embed.add_field(
            name="💰 Results",
            value=f"**Bet:** ${bet_amount:,}\n**Payout:** ${payout:,}\n**Profit:** ${profit:+,}",
            inline=True
        )
        
        new_balance = await self.get_user_balance(interaction.guild_id, interaction.user.id)
        embed.add_field(
            name="💳 Balance",
            value=f"${new_balance:,}",
            inline=True
        )
        
        return embed, profit
    
    async def play_advanced_blackjack(self, interaction: discord.Interaction, bet_amount: int) -> Tuple[discord.Embed, int]:
        """Play sophisticated blackjack with proper mechanics"""
        # Deduct bet
        success = await self.update_user_balance(interaction.guild_id, interaction.user.id, -bet_amount, f"Blackjack bet ${bet_amount:,}")
        if not success:
            embed = discord.Embed(title="❌ Insufficient Balance", color=0xff0000)
            return embed, -bet_amount
        
        # Advanced blackjack logic
        def card_value(card):
            if card in ['J', 'Q', 'K']:
                return 10
            elif card == 'A':
                return 11
            else:
                return int(card)
        
        def hand_value(hand):
            value = sum(card_value(card) for card in hand)
            aces = hand.count('A')
            while value > 21 and aces > 0:
                value -= 10
                aces -= 1
            return value
        
        # Create deck
        cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'] * 4
        random.shuffle(cards)
        
        # Deal cards
        player_hand = [cards.pop(), cards.pop()]
        dealer_hand = [cards.pop(), cards.pop()]
        
        player_value = hand_value(player_hand)
        dealer_value = hand_value(dealer_hand)
        
        # Player logic (simplified AI decision)
        while player_value < 17:
            if random.random() < 0.6:  # Hit 60% of time when under 17
                player_hand.append(cards.pop())
                player_value = hand_value(player_hand)
            else:
                break
        
        # Dealer logic
        while dealer_value < 17:
            dealer_hand.append(cards.pop())
            dealer_value = hand_value(dealer_hand)
        
        # Determine winner
        payout = 0
        result = ""
        
        if player_value > 21:
            result = "💥 BUST! You went over 21"
        elif dealer_value > 21:
            result = "🎉 DEALER BUST! You win!"
            payout = bet_amount * 2
        elif player_value == 21 and len(player_hand) == 2:
            result = "🎊 BLACKJACK! Perfect 21!"
            payout = int(bet_amount * 2.5)
        elif player_value > dealer_value:
            result = "🎉 YOU WIN! Beat the dealer!"
            payout = bet_amount * 2
        elif dealer_value > player_value:
            result = "😞 DEALER WINS! Better luck next time"
        else:
            result = "🤝 PUSH! It's a tie"
            payout = bet_amount
        
        # Apply payout
        if payout > 0:
            await self.update_user_balance(interaction.guild_id, interaction.user.id, payout, f"Blackjack win ${payout:,}")
        
        profit = payout - bet_amount
        color = 0x00ff00 if profit > 0 else 0xff0000 if profit < 0 else 0xffff00
        
        embed = discord.Embed(
            title="🃏 PREMIUM BLACKJACK",
            description=f"**Your Hand:** {' '.join(player_hand)} = {player_value}\n**Dealer Hand:** {' '.join(dealer_hand)} = {dealer_value}\n\n{result}",
            color=color
        )
        
        embed.add_field(
            name="💰 Results",
            value=f"**Bet:** ${bet_amount:,}\n**Payout:** ${payout:,}\n**Profit:** ${profit:+,}",
            inline=True
        )
        
        new_balance = await self.get_user_balance(interaction.guild_id, interaction.user.id)
        embed.add_field(
            name="💳 Balance",
            value=f"${new_balance:,}",
            inline=True
        )
        
        return embed, profit
    
    async def play_advanced_roulette(self, interaction: discord.Interaction, bet_amount: int, bet_type: str) -> Tuple[discord.Embed, int]:
        """Play sophisticated roulette with multiple bet types"""
        # Deduct bet
        success = await self.update_user_balance(interaction.guild_id, interaction.user.id, -bet_amount, f"Roulette bet ${bet_amount:,}")
        if not success:
            embed = discord.Embed(title="❌ Insufficient Balance", color=0xff0000)
            return embed, -bet_amount
        
        # Spin the wheel
        number = random.randint(0, 36)
        
        # Define number properties
        red_numbers = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
        is_red = number in red_numbers
        is_black = number != 0 and not is_red
        is_even = number % 2 == 0 and number != 0
        is_odd = number % 2 == 1
        is_low = 1 <= number <= 18
        is_high = 19 <= number <= 36
        
        # Determine color symbol
        if number == 0:
            color_symbol = "🟢"
        elif is_red:
            color_symbol = "🔴"
        else:
            color_symbol = "⚫"
        
        # Calculate payout based on bet type
        payout = 0
        win = False
        
        if bet_type == "red" and is_red:
            win = True
            payout = bet_amount * 2
        elif bet_type == "black" and is_black:
            win = True
            payout = bet_amount * 2
        elif bet_type == "even" and is_even:
            win = True
            payout = bet_amount * 2
        elif bet_type == "odd" and is_odd:
            win = True
            payout = bet_amount * 2
        elif bet_type == "low" and is_low:
            win = True
            payout = bet_amount * 2
        elif bet_type == "high" and is_high:
            win = True
            payout = bet_amount * 2
        elif bet_type.startswith("number_"):
            bet_number = int(bet_type.split("_")[1])
            if number == bet_number:
                win = True
                payout = bet_amount * 36  # 35:1 payout plus original bet
        
        # Apply payout
        if payout > 0:
            await self.update_user_balance(interaction.guild_id, interaction.user.id, payout, f"Roulette win ${payout:,}")
        
        profit = payout - bet_amount
        color = 0x00ff00 if profit > 0 else 0xff0000
        
        result_text = "🎉 WINNER!" if win else "💔 No luck this time"
        
        embed = discord.Embed(
            title="🎲 PREMIUM ROULETTE",
            description=f"**Winning Number:** {color_symbol} {number}\n**Your Bet:** {bet_type.replace('_', ' ').title()}\n**Result:** {result_text}",
            color=color
        )
        
        embed.add_field(
            name="💰 Results",
            value=f"**Bet:** ${bet_amount:,}\n**Payout:** ${payout:,}\n**Profit:** ${profit:+,}",
            inline=True
        )
        
        new_balance = await self.get_user_balance(interaction.guild_id, interaction.user.id)
        embed.add_field(
            name="💳 Balance",
            value=f"${new_balance:,}",
            inline=True
        )
        
        return embed, profit

def setup(bot):
    bot.add_cog(AdvancedGambling(bot))