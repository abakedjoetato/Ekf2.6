"""
Emerald's Killfeed - Professional Casino System
Sophisticated UI with modal integration, select menus, and intuitive workflows
Based on professional gambling system design patterns
"""
import discord
import asyncio
import random
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class BetSetupModal(discord.ui.Modal):
    """Professional bet setup modal with validation"""
    
    def __init__(self, game_type: str, max_balance: int, casino_cog):
        super().__init__(title=f"🎰 {game_type.title()} Bet Setup")
        self.game_type = game_type
        self.max_balance = max_balance
        self.casino_cog = casino_cog
        
        # Bet amount input
        self.bet_input = discord.ui.TextInput(
            label="💰 Bet Amount",
            placeholder=f"Enter bet (Max: ${max_balance:,})",
            min_length=1,
            max_length=10,
            style=discord.TextStyle.short
        )
        self.add_item(self.bet_input)
        
        # Game-specific options
        if game_type == "roulette":
            self.choice_input = discord.ui.TextInput(
                label="🎯 Roulette Choice",
                placeholder="red/black/even/odd/low/high or number 0-36",
                min_length=1,
                max_length=20,
                style=discord.TextStyle.short
            )
            self.add_item(self.choice_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Validate bet amount
            bet_str = self.bet_input.value.strip().replace(',', '').replace('$', '')
            
            if not bet_str.isdigit():
                await interaction.response.send_message("❌ Invalid bet amount! Use numbers only.", ephemeral=True)
                return
            
            bet = int(bet_str)
            
            if bet <= 0:
                await interaction.response.send_message("❌ Bet must be positive!", ephemeral=True)
                return
            
            if bet > self.max_balance:
                await interaction.response.send_message(f"❌ Insufficient funds! Max bet: ${self.max_balance:,}", ephemeral=True)
                return
            
            # Prepare game data
            game_data = {"bet": bet}
            
            if self.game_type == "roulette" and hasattr(self, 'choice_input'):
                choice = self.choice_input.value.strip().lower()
                valid_choices = {'red', 'black', 'green', 'even', 'odd', 'low', 'high'}
                is_number = choice.isdigit() and 0 <= int(choice) <= 36
                
                if choice not in valid_choices and not is_number:
                    await interaction.response.send_message("❌ Invalid roulette choice!", ephemeral=True)
                    return
                
                game_data["choice"] = choice
            
            # Initialize the game
            await self.casino_cog._initialize_game_from_modal(interaction, self.game_type, game_data)
            
        except Exception as e:
            logger.error(f"Modal submission error: {e}")
            await interaction.response.send_message("❌ Setup failed. Please try again.", ephemeral=True)

class GameSelectionMenu(discord.ui.Select):
    """Professional game selection dropdown"""
    
    def __init__(self, casino_cog):
        self.casino_cog = casino_cog
        
        options = [
            discord.SelectOption(
                label="🎰 Elite Slots",
                description="Match symbols for multiplied winnings",
                emoji="🎰",
                value="slots"
            ),
            discord.SelectOption(
                label="🎯 Roulette Wheel",
                description="Predict the winning number or color",
                emoji="🎯",
                value="roulette"
            ),
            discord.SelectOption(
                label="🃏 Blackjack",
                description="Beat the dealer to 21",
                emoji="🃏",
                value="blackjack"
            ),
            discord.SelectOption(
                label="🪙 Coin Flip",
                description="Simple heads or tails betting",
                emoji="🪙",
                value="coinflip"
            )
        ]
        
        super().__init__(
            placeholder="🎲 Choose your game experience...",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        await self.casino_cog._handle_game_selection(interaction, self.values[0])

class BetAmountMenu(discord.ui.Select):
    """Smart bet amount selection"""
    
    def __init__(self, balance: int, casino_cog):
        self.balance = balance
        self.casino_cog = casino_cog
        
        # Smart bet suggestions
        suggestions = []
        if balance >= 50:
            suggestions.append(("💰 Conservative", min(50, balance // 20), "Low risk bet"))
        if balance >= 100:
            suggestions.append(("⚡ Moderate", min(100, balance // 10), "Balanced risk bet"))
        if balance >= 500:
            suggestions.append(("🔥 Aggressive", min(500, balance // 5), "High risk bet"))
        if balance >= 1000:
            suggestions.append(("💎 High Roller", min(1000, balance // 3), "Maximum risk bet"))
        
        suggestions.append(("🎯 Custom Amount", 0, "Enter your own bet"))
        
        options = []
        for label, amount, desc in suggestions:
            options.append(discord.SelectOption(
                label=label,
                description=f"{desc} (${amount:,})" if amount > 0 else desc,
                value=str(amount)
            ))
        
        super().__init__(
            placeholder="💰 Select your bet amount...",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        bet = int(self.values[0])
        
        if bet == 0:  # Custom amount
            pending_game = self.casino_cog.pending_games.get(interaction.user.id, {})
            game_type = pending_game.get('game_type', 'slots')
            
            modal = BetSetupModal(game_type, self.balance, self.casino_cog)
            await interaction.response.send_modal(modal)
        else:
            await self.casino_cog._handle_bet_selection(interaction, bet)

class SlotsGame(discord.ui.View):
    """Simple working slots game"""
    
    def __init__(self, bot, guild_id: int, user_id: int, balance: int):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        self.user_id = user_id
        self.balance = balance
        
        # Slot symbols and their values
        self.symbols = ['🍒', '🍋', '🍊', '🍇', '⭐', '💎']
        self.values = {
            '🍒': 2,
            '🍋': 3,
            '🍊': 4,
            '🍇': 5,
            '⭐': 10,
            '💎': 20
        }
    
    def create_embed(self, reels=None, bet=None, win=None, new_balance=None):
        embed = discord.Embed(
            title="🎰 EMERALD SLOTS",
            color=0x00FF7F,
            timestamp=datetime.now(timezone.utc)
        )
        
        if reels:
            slots_display = f"**[ {reels[0]} | {reels[1]} | {reels[2]} ]**"
            embed.add_field(name="Reels", value=slots_display, inline=False)
            
            if win > 0:
                embed.add_field(name="🎉 Winner!", value=f"You won ${win}!", inline=True)
            elif bet:
                embed.add_field(name="Try Again", value=f"Lost ${bet}", inline=True)
        
        current_balance = new_balance if new_balance is not None else self.balance
        embed.add_field(name="💰 Balance", value=f"${current_balance}", inline=True)
        
        embed.add_field(
            name="📋 Payouts",
            value="🍒🍒🍒 = 2x\n🍋🍋🍋 = 3x\n🍊🍊🍊 = 4x\n🍇🍇🍇 = 5x\n⭐⭐⭐ = 10x\n💎💎💎 = 20x",
            inline=False
        )
        
        return embed
    
    @discord.ui.button(label="Bet $10", style=discord.ButtonStyle.green, emoji="🎰")
    async def bet_10(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.play_slots(interaction, 10)
    
    @discord.ui.button(label="Bet $25", style=discord.ButtonStyle.green, emoji="🎰")
    async def bet_25(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.play_slots(interaction, 25)
    
    @discord.ui.button(label="Bet $50", style=discord.ButtonStyle.green, emoji="🎰")
    async def bet_50(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.play_slots(interaction, 50)
    
    @discord.ui.button(label="Bet $100", style=discord.ButtonStyle.green, emoji="🎰")
    async def bet_100(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.play_slots(interaction, 100)
    
    @discord.ui.button(label="Back to Casino", style=discord.ButtonStyle.red, emoji="🏠")
    async def back_to_casino(self, button: discord.ui.Button, interaction: discord.Interaction):
        new_balance = await self.get_current_balance()
        casino_view = CasinoMain(self.bot, self.guild_id, self.user_id, new_balance)
        embed = casino_view.create_main_embed()
        await interaction.response.edit_message(embed=embed, view=casino_view)
    
    async def play_slots(self, interaction: discord.Interaction, bet_amount: int):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your game session.", ephemeral=True)
            return
        
        current_balance = await self.get_current_balance()
        
        if current_balance < bet_amount:
            await interaction.response.send_message(f"Insufficient funds. You need ${bet_amount} but have ${current_balance}.", ephemeral=True)
            return
        
        # Generate random reels
        reels = [random.choice(self.symbols) for _ in range(3)]
        
        # Calculate winnings
        win_amount = 0
        if reels[0] == reels[1] == reels[2]:  # Three of a kind
            multiplier = self.values[reels[0]]
            win_amount = bet_amount * multiplier
        
        # Update balance
        balance_change = win_amount - bet_amount
        success = await self.update_balance(balance_change)
        
        if not success:
            await interaction.response.send_message("Error processing bet. Please try again.", ephemeral=True)
            return
        
        new_balance = current_balance + balance_change
        self.balance = new_balance
        
        embed = self.create_embed(reels, bet_amount, win_amount, new_balance)
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def get_current_balance(self):
        try:
            wallet = await self.bot.db_manager.get_wallet(self.guild_id, self.user_id)
            return wallet.get('balance', 0)
        except:
            return 0
    
    async def update_balance(self, amount):
        try:
            return await self.bot.db_manager.update_wallet(self.guild_id, self.user_id, amount, 'casino_slots')
        except:
            return False

class SimpleCoinFlip(discord.ui.View):
    """Simple coin flip game"""
    
    def __init__(self, bot, guild_id: int, user_id: int, balance: int):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        self.user_id = user_id
        self.balance = balance
    
    def create_embed(self, result=None, bet=None, choice=None, win=None, new_balance=None):
        embed = discord.Embed(
            title="🪙 COIN FLIP",
            color=0xFFD700,
            timestamp=datetime.now(timezone.utc)
        )
        
        if result:
            coin_emoji = "👑" if result == "heads" else "🪙"
            embed.add_field(name="Result", value=f"{coin_emoji} **{result.upper()}**", inline=False)
            
            if choice:
                embed.add_field(name="Your Choice", value=choice.upper(), inline=True)
                
            if win > 0:
                embed.add_field(name="🎉 Winner!", value=f"You won ${win}!", inline=True)
            elif bet:
                embed.add_field(name="Try Again", value=f"Lost ${bet}", inline=True)
        
        current_balance = new_balance if new_balance is not None else self.balance
        embed.add_field(name="💰 Balance", value=f"${current_balance}", inline=True)
        
        embed.add_field(
            name="📋 How to Play",
            value="Choose Heads or Tails\nWin = 2x your bet\nLose = Lose your bet",
            inline=False
        )
        
        return embed
    
    @discord.ui.button(label="Heads - $10", style=discord.ButtonStyle.primary, emoji="👑")
    async def heads_10(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.play_coinflip(interaction, "heads", 10)
    
    @discord.ui.button(label="Tails - $10", style=discord.ButtonStyle.primary, emoji="🪙")
    async def tails_10(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.play_coinflip(interaction, "tails", 10)
    
    @discord.ui.button(label="Heads - $50", style=discord.ButtonStyle.primary, emoji="👑")
    async def heads_50(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.play_coinflip(interaction, "heads", 50)
    
    @discord.ui.button(label="Tails - $50", style=discord.ButtonStyle.primary, emoji="🪙")
    async def tails_50(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.play_coinflip(interaction, "tails", 50)
    
    @discord.ui.button(label="Back to Casino", style=discord.ButtonStyle.red, emoji="🏠", row=1)
    async def back_to_casino(self, button: discord.ui.Button, interaction: discord.Interaction):
        new_balance = await self.get_current_balance()
        casino_view = CasinoMain(self.bot, self.guild_id, self.user_id, new_balance)
        embed = casino_view.create_main_embed()
        await interaction.response.edit_message(embed=embed, view=casino_view)
    
    async def play_coinflip(self, interaction: discord.Interaction, choice: str, bet_amount: int):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your game session.", ephemeral=True)
            return
        
        current_balance = await self.get_current_balance()
        
        if current_balance < bet_amount:
            await interaction.response.send_message(f"Insufficient funds. You need ${bet_amount} but have ${current_balance}.", ephemeral=True)
            return
        
        # Flip the coin
        result = random.choice(["heads", "tails"])
        
        # Calculate winnings
        win_amount = 0
        if choice == result:
            win_amount = bet_amount * 2
        
        # Update balance
        balance_change = win_amount - bet_amount
        success = await self.update_balance(balance_change)
        
        if not success:
            await interaction.response.send_message("Error processing bet. Please try again.", ephemeral=True)
            return
        
        new_balance = current_balance + balance_change
        self.balance = new_balance
        
        embed = self.create_embed(result, bet_amount, choice, win_amount, new_balance)
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def get_current_balance(self):
        try:
            wallet = await self.bot.db_manager.get_wallet(self.guild_id, self.user_id)
            return wallet.get('balance', 0)
        except:
            return 0
    
    async def update_balance(self, amount):
        try:
            return await self.bot.db_manager.update_wallet(self.guild_id, self.user_id, amount, 'casino_coinflip')
        except:
            return False

class CasinoMain(discord.ui.View):
    """Main casino interface with working games"""
    
    def __init__(self, bot, guild_id: int, user_id: int, balance: int):
        super().__init__(timeout=600)
        self.bot = bot
        self.guild_id = guild_id
        self.user_id = user_id
        self.balance = balance
    
    def create_main_embed(self):
        embed = discord.Embed(
            title="🎰 EMERALD CASINO",
            description="Welcome to the casino! Choose your game below.",
            color=0x9932CC,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(
            name="💰 Your Balance",
            value=f"**${self.balance}**",
            inline=True
        )
        
        embed.add_field(
            name="🎮 Available Games",
            value="🎰 **Slots** - Match symbols for big wins\n🪙 **Coin Flip** - Double or nothing",
            inline=False
        )
        
        embed.add_field(
            name="💡 Tips",
            value="• Start with small bets\n• Set limits for yourself\n• Have fun responsibly",
            inline=False
        )
        
        return embed
    
    @discord.ui.button(label="🎰 Play Slots", style=discord.ButtonStyle.green, emoji="🎰")
    async def play_slots(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This casino session belongs to another player.", ephemeral=True)
            return
        
        current_balance = await self.get_current_balance()
        slots_view = SimpleSlots(self.bot, self.guild_id, self.user_id, current_balance)
        embed = slots_view.create_embed()
        await interaction.response.edit_message(embed=embed, view=slots_view)
    
    @discord.ui.button(label="🪙 Coin Flip", style=discord.ButtonStyle.green, emoji="🪙")
    async def play_coinflip(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This casino session belongs to another player.", ephemeral=True)
            return
        
        current_balance = await self.get_current_balance()
        coinflip_view = SimpleCoinFlip(self.bot, self.guild_id, self.user_id, current_balance)
        embed = coinflip_view.create_embed()
        await interaction.response.edit_message(embed=embed, view=coinflip_view)
    
    @discord.ui.button(label="💰 Check Balance", style=discord.ButtonStyle.secondary, emoji="💰")
    async def check_balance(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This casino session belongs to another player.", ephemeral=True)
            return
        
        current_balance = await self.get_current_balance()
        self.balance = current_balance
        embed = self.create_main_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def get_current_balance(self):
        try:
            wallet = await self.bot.db_manager.get_wallet(self.guild_id, self.user_id)
            return wallet.get('balance', 0)
        except:
            return 0

class CasinoRedesign(discord.Cog):
    """Redesigned casino with working games and intuitive interface"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def check_premium_access(self, guild_id: int) -> bool:
        """Check if guild has premium access"""
        try:
            guild_config = await self.bot.db_manager.guild_configs.find_one({'guild_id': guild_id})
            if guild_config:
                if guild_config.get('premium_enabled', False):
                    return True
                
                servers = guild_config.get('servers', [])
                for server in servers:
                    if server.get('premium', False):
                        return True
            
            return False
        except Exception as e:
            logger.error(f"Premium access check error: {e}")
            return False
    
    @discord.slash_command(name="casino", description="Enter the Emerald Casino - Working Games!")
    async def casino(self, ctx: discord.ApplicationContext):
        """Main casino command with working games"""
        try:
            if not ctx.guild:
                await ctx.respond("This command can only be used in a server.", ephemeral=True)
                return
            
            guild_id = ctx.guild.id
            user_id = ctx.user.id
            
            # Check premium access
            if not await self.check_premium_access(guild_id):
                embed = discord.Embed(
                    title="🔒 Premium Access Required",
                    description="The casino requires premium subscription.",
                    color=0xFF6B6B
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return
            
            # Get user balance
            wallet = await self.bot.db_manager.get_wallet(guild_id, user_id)
            balance = wallet.get('balance', 0)
            
            if balance < 10:
                embed = discord.Embed(
                    title="⚠️ Insufficient Funds",
                    description="You need at least $10 to enter the casino. Use `/work` to earn money!",
                    color=0xFFD700
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return
            
            # Create casino interface
            casino_view = CasinoMain(self.bot, guild_id, user_id, balance)
            embed = casino_view.create_main_embed()
            
            await ctx.respond(embed=embed, view=casino_view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Casino error: {e}")
            await ctx.respond("Casino temporarily offline. Please try again.", ephemeral=True)

def setup(bot):
    bot.add_cog(CasinoRedesign(bot))