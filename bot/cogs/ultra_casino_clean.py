"""
Emerald's Killfeed - Ultra-Advanced Casino System V3 (Clean)
Complete redesign with sophisticated aesthetics and proper py-cord 2.6.1 syntax
"""
import discord
import asyncio
import random
import math
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class GameStats:
    """Advanced game statistics tracking"""
    total_bet: int = 0
    total_won: int = 0
    games_played: int = 0
    biggest_win: int = 0
    current_streak: int = 0
    best_streak: int = 0

class CasinoTheme:
    """Advanced casino theming system"""
    
    COLORS = {
        'primary': 0x1E90FF,
        'success': 0x32CD32,
        'warning': 0xFFD700,
        'danger': 0xFF4500,
        'jackpot': 0xFF1493,
        'luxury': 0x9932CC,
        'elite': 0x00CED1
    }
    
    EMOJIS = {
        'diamond': '💎',
        'crown': '👑',
        'star': '⭐',
        'fire': '🔥',
        'lightning': '⚡',
        'gem': '💠',
        'trophy': '🏆',
        'coin': '🪙',
        'spade': '♠️'
    }

class QuantumSlotsModal(discord.ui.Modal):
    """Advanced quantum-themed slots configuration"""
    
    def __init__(self, bot, guild_id: int, user_id: int, balance: int):
        super().__init__(title=f"{CasinoTheme.EMOJIS['lightning']} QUANTUM SLOTS")
        self.bot = bot
        self.guild_id = guild_id
        self.user_id = user_id
        self.balance = balance
        
        self.bet_amount = discord.ui.InputText(
            label="Quantum Energy Investment ($100 - $50,000)",
            placeholder="Enter your bet amount...",
            required=True,
            max_length=8
        )
        self.add_item(self.bet_amount)
        
        self.quantum_level = discord.ui.InputText(
            label="Quantum Entanglement Level (1-10)",
            placeholder="Higher levels = more volatile outcomes",
            required=True,
            max_length=2
        )
        self.add_item(self.quantum_level)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Process quantum slots configuration"""
        try:
            bet_value = str(self.bet_amount.value or '0')
            bet = int(bet_value.replace('$', '').replace(',', ''))
            
            level_value = str(self.quantum_level.value or '1')
            level = max(1, min(10, int(level_value)))
            
            if bet < 100 or bet > 50000:
                await interaction.response.send_message(
                    f"{CasinoTheme.EMOJIS['warning']} Invalid quantum energy level. Range: $100 - $50,000",
                    ephemeral=True
                )
                return
            
            if bet > self.balance:
                await interaction.response.send_message(
                    f"{CasinoTheme.EMOJIS['warning']} Insufficient quantum energy. Required: ${bet:,} | Available: ${self.balance:,}",
                    ephemeral=True
                )
                return
            
            # Execute quantum slots game
            game = QuantumSlotsGame(self.bot, self.guild_id, self.user_id, bet, level)
            result_embed = await game.play()
            
            await interaction.response.send_message(embed=result_embed, ephemeral=True)
            
        except ValueError:
            await interaction.response.send_message(
                f"{CasinoTheme.EMOJIS['warning']} Invalid quantum parameters. Please enter valid numbers.",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Quantum slots error: {e}")
            await interaction.response.send_message(
                f"{CasinoTheme.EMOJIS['warning']} Quantum entanglement failed. Please try again.",
                ephemeral=True
            )

class QuantumSlotsGame:
    """Advanced quantum slots game engine"""
    
    QUANTUM_SYMBOLS = [
        ('💎', 'Diamond', 50),
        ('👑', 'Crown', 25),
        ('⭐', 'Star', 15),
        ('🔥', 'Fire', 10),
        ('⚡', 'Lightning', 8),
        ('💠', 'Gem', 5),
        ('🪙', 'Coin', 3),
        ('🎲', 'Dice', 2)
    ]
    
    def __init__(self, bot, guild_id: int, user_id: int, bet: int, level: int):
        self.bot = bot
        self.guild_id = guild_id
        self.user_id = user_id
        self.bet = bet
        self.level = level
        self.total_winnings = 0
    
    async def play(self) -> discord.Embed:
        """Execute the quantum slots game"""
        # Quantum volatility affects symbol probabilities
        volatility_multiplier = 1 + (self.level - 1) * 0.15
        
        # Generate 5 reels with quantum entanglement
        reels = []
        for i in range(5):
            symbols = []
            for j in range(3):
                symbol = self.get_quantum_symbol(volatility_multiplier)
                symbols.append(symbol)
            reels.append(symbols)
        
        # Calculate winnings
        winnings = self.calculate_winnings(reels)
        self.total_winnings = winnings
        
        # Update database
        net_change = winnings - self.bet
        if net_change != 0:
            await self.update_balance(net_change)
        
        return self.create_result_embed(reels)
    
    def get_quantum_symbol(self, volatility: float) -> Tuple[str, str, int]:
        """Get a quantum-influenced symbol"""
        adjusted_weights = []
        for symbol, name, base_weight in self.QUANTUM_SYMBOLS:
            if base_weight >= 15:
                weight = base_weight * volatility
            else:
                weight = base_weight / volatility
            adjusted_weights.append(weight)
        
        return random.choices(self.QUANTUM_SYMBOLS, weights=adjusted_weights)[0]
    
    def calculate_winnings(self, reels: List[List[Tuple[str, str, int]]]) -> int:
        """Calculate winnings from reel configuration"""
        winnings = 0
        
        # Check horizontal lines
        for row in range(3):
            line = [reels[col][row] for col in range(5)]
            winnings += self.check_line_winnings(line)
        
        # Quantum bonus for mixed rare symbols
        rare_symbols = set()
        for reel in reels:
            for symbol in reel:
                if symbol[2] >= 15:
                    rare_symbols.add(symbol[0])
        
        if len(rare_symbols) >= 3:
            bonus_multiplier = len(rare_symbols) * 0.5
            winnings += int(self.bet * bonus_multiplier)
        
        return winnings
    
    def check_line_winnings(self, line: List[Tuple[str, str, int]]) -> int:
        """Check winnings for a single line"""
        if len(line) < 3:
            return 0
        
        first_symbol = line[0]
        count = 1
        
        for i in range(1, len(line)):
            if line[i][0] == first_symbol[0]:
                count += 1
            else:
                break
        
        if count >= 3:
            base_payout = first_symbol[2]
            multiplier = count - 2
            return int(self.bet * base_payout * multiplier * 0.1)
        
        return 0
    
    async def update_balance(self, amount: int):
        """Update user balance in database"""
        try:
            await self.bot.db_manager.user_wallets.update_one(
                {'guild_id': self.guild_id, 'discord_id': self.user_id},
                {'$inc': {'balance': amount}},
                upsert=True
            )
            
            await self.bot.db_manager.wallet_events.insert_one({
                'guild_id': self.guild_id,
                'discord_id': self.user_id,
                'amount': amount,
                'event_type': 'quantum_slots',
                'description': f"Quantum Slots - Level {self.level}",
                'timestamp': datetime.now(timezone.utc)
            })
        except Exception as e:
            logger.error(f"Balance update error: {e}")
    
    def create_result_embed(self, reels: List[List[Tuple[str, str, int]]]) -> discord.Embed:
        """Create sophisticated result embed"""
        net_profit = self.total_winnings - self.bet
        
        color = CasinoTheme.COLORS['success'] if net_profit > 0 else CasinoTheme.COLORS['danger']
        if net_profit > self.bet * 10:
            color = CasinoTheme.COLORS['jackpot']
        
        embed = discord.Embed(
            title=f"{CasinoTheme.EMOJIS['lightning']} QUANTUM SLOTS RESULTS",
            description=f"*Quantum Level {self.level}*",
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Show quantum state
        reel_display = self.format_reels(reels)
        embed.add_field(
            name="Quantum State",
            value=reel_display,
            inline=False
        )
        
        # Financial results
        embed.add_field(
            name=f"{CasinoTheme.EMOJIS['coin']} Results",
            value=f"**Bet:** ${self.bet:,}\n**Won:** ${self.total_winnings:,}\n**Profit:** ${net_profit:,}",
            inline=True
        )
        
        return embed
    
    def format_reels(self, reels: List[List[Tuple[str, str, int]]]) -> str:
        """Format reels for display"""
        lines = []
        for row in range(3):
            line = " | ".join(reels[col][row][0] for col in range(5))
            lines.append(f"`{line}`")
        return "\n".join(lines)

class AdvancedCasinoMenu(discord.ui.View):
    """Ultra-sophisticated casino menu"""
    
    def __init__(self, bot, guild_id: int, user_id: int, balance: int, stats: GameStats):
        super().__init__(timeout=900)
        self.bot = bot
        self.guild_id = guild_id
        self.user_id = user_id
        self.balance = balance
        self.stats = stats
    
    def create_main_embed(self) -> discord.Embed:
        """Create sophisticated main casino embed"""
        embed = discord.Embed(
            title=f"{CasinoTheme.EMOJIS['crown']} EMERALD ELITE CASINO {CasinoTheme.EMOJIS['crown']}",
            description="*Welcome to the most exclusive gaming experience*",
            color=CasinoTheme.COLORS['luxury'],
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(
            name=f"{CasinoTheme.EMOJIS['diamond']} Player Status",
            value=f"**Balance:** ${self.balance:,}\n**VIP Level:** {self.get_vip_level()}",
            inline=True
        )
        
        embed.add_field(
            name=f"{CasinoTheme.EMOJIS['trophy']} Statistics",
            value=f"**Games:** {self.stats.games_played:,}\n**Total Wagered:** ${self.stats.total_bet:,}",
            inline=True
        )
        
        embed.set_footer(text="Select a premium game below • Emerald Elite Gaming")
        
        return embed
    
    def get_vip_level(self) -> str:
        """Calculate VIP level based on total wagered"""
        total_wagered = self.stats.total_bet
        if total_wagered >= 1000000:
            return f"{CasinoTheme.EMOJIS['crown']} Diamond Elite"
        elif total_wagered >= 500000:
            return f"{CasinoTheme.EMOJIS['gem']} Platinum"
        elif total_wagered >= 250000:
            return f"{CasinoTheme.EMOJIS['star']} Gold"
        elif total_wagered >= 100000:
            return f"{CasinoTheme.EMOJIS['trophy']} Silver"
        else:
            return "Bronze"
    
    @discord.ui.button(
        label="QUANTUM SLOTS",
        style=discord.ButtonStyle.primary,
        emoji=CasinoTheme.EMOJIS['lightning'],
        row=0
    )
    async def quantum_slots(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Advanced quantum-themed slots"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This casino session belongs to another player.",
                ephemeral=True
            )
            return
        
        modal = QuantumSlotsModal(self.bot, self.guild_id, self.user_id, self.balance)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(
        label="COMING SOON",
        style=discord.ButtonStyle.secondary,
        emoji="🎯",
        row=0,
        disabled=True
    )
    async def coming_soon_1(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Placeholder for future games"""
        pass
    
    @discord.ui.button(
        label="COMING SOON",
        style=discord.ButtonStyle.secondary,
        emoji="🎲",
        row=0,
        disabled=True
    )
    async def coming_soon_2(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Placeholder for future games"""
        pass
    
    @discord.ui.button(
        label="REFRESH",
        style=discord.ButtonStyle.success,
        emoji="🔄",
        row=1
    )
    async def refresh_menu(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Refresh the casino menu"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This casino session belongs to another player.",
                ephemeral=True
            )
            return
        
        # Update balance from database
        try:
            wallet = await self.bot.db_manager.user_wallets.find_one({
                'guild_id': self.guild_id,
                'discord_id': self.user_id
            })
            self.balance = wallet.get('balance', 0) if wallet else 0
        except Exception:
            pass
        
        embed = self.create_main_embed()
        await interaction.response.edit_message(embed=embed, view=self)

class UltraCasinoV3Clean(discord.Cog):
    """Ultra-Advanced Casino System V3 with py-cord 2.6.1 compatibility"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def check_premium_access(self, guild_id: int) -> bool:
        """Check if guild has premium access based on active premium servers"""
        try:
            # Method 1: Check guild config for premium servers
            guild_config = await self.bot.db_manager.guild_configs.find_one({'guild_id': guild_id})
            if guild_config:
                # Check for premium_enabled flag (manual override)
                if guild_config.get('premium_enabled', False):
                    return True
                
                # Check for servers with premium status
                servers = guild_config.get('servers', [])
                for server in servers:
                    if server.get('premium', False):
                        return True
            
            # Method 2: Check if guild has any servers (basic access)
            guild_doc = await self.bot.db_manager.get_guild(guild_id)
            if guild_doc and guild_doc.get('servers'):
                # If guild has configured servers, grant access
                return True
            
            return False
        except Exception as e:
            logger.error(f"Premium access check error: {e}")
            return False
    
    async def get_user_stats(self, guild_id: int, user_id: int) -> GameStats:
        """Get user gaming statistics"""
        try:
            events = await self.bot.db_manager.wallet_events.find({
                'guild_id': guild_id,
                'discord_id': user_id,
                'event_type': {'$in': ['quantum_slots']}
            }).to_list(length=1000)
            
            stats = GameStats()
            current_streak = 0
            
            for event in events:
                amount = event.get('amount', 0)
                if amount > 0:
                    stats.total_won += amount
                    current_streak += 1
                    if amount > stats.biggest_win:
                        stats.biggest_win = amount
                else:
                    stats.total_bet += abs(amount)
                    if current_streak > stats.best_streak:
                        stats.best_streak = current_streak
                    current_streak = 0
                
                stats.games_played += 1
            
            stats.current_streak = current_streak
            return stats
        except Exception:
            return GameStats()
    
    async def get_user_balance(self, guild_id: int, user_id: int) -> int:
        """Get user's current balance"""
        try:
            wallet = await self.bot.db_manager.user_wallets.find_one({
                'guild_id': guild_id,
                'discord_id': user_id
            })
            return wallet.get('balance', 0) if wallet else 0
        except Exception:
            return 0
    
    @discord.slash_command(name="casino", description="Enter the Ultra-Advanced Emerald Elite Casino")
    async def ultra_casino(self, ctx: discord.ApplicationContext):
        """Main casino command"""
        try:
            if not ctx.guild:
                await ctx.respond("This command can only be used in a server.", ephemeral=True)
                return
            
            guild_id = ctx.guild.id
            user_id = ctx.user.id
            
            # Check premium access
            if not await self.check_premium_access(guild_id):
                embed = discord.Embed(
                    title=f"{CasinoTheme.EMOJIS['crown']} Premium Access Required",
                    description="The Ultra-Advanced Casino requires premium subscription.",
                    color=CasinoTheme.COLORS['luxury']
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return
            
            # Get user data
            balance = await self.get_user_balance(guild_id, user_id)
            stats = await self.get_user_stats(guild_id, user_id)
            
            if balance < 100:
                embed = discord.Embed(
                    title=f"{CasinoTheme.EMOJIS['warning']} Insufficient Credits",
                    description="You need at least $100 to enter the casino. Use `/work` to earn credits!",
                    color=CasinoTheme.COLORS['warning']
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return
            
            # Create casino menu
            view = AdvancedCasinoMenu(self.bot, guild_id, user_id, balance, stats)
            embed = view.create_main_embed()
            
            await ctx.respond(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Ultra casino error: {e}")
            await ctx.respond("Casino systems are temporarily offline. Please try again.", ephemeral=True)

def setup(bot):
    bot.add_cog(UltraCasinoV3Clean(bot))