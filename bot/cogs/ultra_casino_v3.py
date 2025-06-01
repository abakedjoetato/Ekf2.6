"""
Emerald's Killfeed - Ultra-Advanced Casino System V3
Complete redesign with sophisticated aesthetics, advanced features, and proper py-cord 2.6.1 syntax
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
        'primary': 0x1E90FF,    # Deep Sky Blue
        'success': 0x32CD32,   # Lime Green
        'warning': 0xFFD700,   # Gold
        'danger': 0xFF4500,    # Orange Red
        'jackpot': 0xFF1493,   # Deep Pink
        'luxury': 0x9932CC,    # Dark Orchid
        'elite': 0x00CED1      # Dark Turquoise
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
        'dice': '🎲',
        'spade': '♠️',
        'heart': '♥️',
        'diamond_suit': '♦️',
        'club': '♣️'
    }

class AdvancedCasinoMenu(discord.ui.View):
    """Ultra-sophisticated casino menu with advanced features"""
    
    def __init__(self, bot, guild_id: int, user_id: int, balance: int, stats: GameStats):
        super().__init__(timeout=900)  # 15 minute timeout
        self.bot = bot
        self.guild_id = guild_id
        self.user_id = user_id
        self.balance = balance
        self.stats = stats
        self.current_bet = 100
        self.auto_mode = False
        
    def create_main_embed(self) -> discord.Embed:
        """Create sophisticated main casino embed"""
        embed = discord.Embed(
            title=f"{CasinoTheme.EMOJIS['crown']} EMERALD ELITE CASINO {CasinoTheme.EMOJIS['crown']}",
            description=f"*Welcome to the most exclusive gaming experience*",
            color=CasinoTheme.COLORS['luxury'],
            timestamp=datetime.now(timezone.utc)
        )
        
        # Player status with advanced formatting
        embed.add_field(
            name=f"{CasinoTheme.EMOJIS['diamond']} Player Status",
            value=f"**Balance:** ${self.balance:,}\n"
                  f"**Current Bet:** ${self.current_bet:,}\n"
                  f"**VIP Level:** {self.get_vip_level()}",
            inline=True
        )
        
        # Advanced statistics
        embed.add_field(
            name=f"{CasinoTheme.EMOJIS['trophy']} Statistics",
            value=f"**Games Played:** {self.stats.games_played:,}\n"
                  f"**Total Wagered:** ${self.stats.total_bet:,}\n"
                  f"**Net Profit:** ${self.stats.total_won - self.stats.total_bet:,}",
            inline=True
        )
        
        # Streak information
        embed.add_field(
            name=f"{CasinoTheme.EMOJIS['fire']} Streaks",
            value=f"**Current:** {self.stats.current_streak}\n"
                  f"**Best:** {self.stats.best_streak}\n"
                  f"**Biggest Win:** ${self.stats.biggest_win:,}",
            inline=True
        )
        
        embed.set_footer(text="Select a premium game below • Emerald Elite Gaming")
        embed.set_thumbnail(url="attachment://casino.png")
        
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
    
    # Row 1: Premium Games
    @discord.ui.button(
        label="QUANTUM SLOTS",
        style=discord.ButtonStyle.primary,
        emoji=CasinoTheme.EMOJIS['lightning'],
        row=0
    )
    async def quantum_slots(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Advanced quantum-themed slots with multiplier mechanics"""
        if not await self.validate_interaction(interaction):
            return
        
        modal = QuantumSlotsModal(self.bot, self.guild_id, self.user_id, self.balance)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(
        label="NEURAL BLACKJACK",
        style=discord.ButtonStyle.primary,
        emoji=CasinoTheme.EMOJIS['spade'],
        row=0
    )
    async def neural_blackjack(self, button: discord.ui.Button, interaction: discord.Interaction):
        """AI-enhanced blackjack with advanced strategy options"""
        if not await self.validate_interaction(interaction):
            return
        
        modal = NeuralBlackjackModal(self.bot, self.guild_id, self.user_id, self.balance)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(
        label="PLATINUM ROULETTE",
        style=discord.ButtonStyle.primary,
        emoji=CasinoTheme.EMOJIS['gem'],
        row=0
    )
    async def platinum_roulette(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Premium roulette with advanced betting patterns"""
        if not await self.validate_interaction(interaction):
            return
        
        modal = PlatinumRouletteModal(self.bot, self.guild_id, self.user_id, self.balance)
        await interaction.response.send_modal(modal)
    
    # Row 2: Exclusive Games
    @discord.ui.button(
        label="DIAMOND CRASH",
        style=discord.ButtonStyle.secondary,
        emoji=CasinoTheme.EMOJIS['diamond'],
        row=1
    )
    async def diamond_crash(self, button: discord.ui.Button, interaction: discord.Interaction):
        """High-stakes crash game with real-time multipliers"""
        if not await self.validate_interaction(interaction):
            return
        
        modal = DiamondCrashModal(self.bot, self.guild_id, self.user_id, self.balance)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(
        label="ELITE POKER",
        style=discord.ButtonStyle.secondary,
        emoji=CasinoTheme.EMOJIS['crown'],
        row=1
    )
    async def elite_poker(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Premium poker with advanced hand analysis"""
        if not await self.validate_interaction(interaction):
            return
        
        view = ElitePokerView(self.bot, self.guild_id, self.user_id, self.balance)
        embed = view.create_poker_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(
        label="FORTUNE WHEEL",
        style=discord.ButtonStyle.secondary,
        emoji=CasinoTheme.EMOJIS['coin'],
        row=1
    )
    async def fortune_wheel(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Luxury fortune wheel with progressive jackpots"""
        if not await self.validate_interaction(interaction):
            return
        
        view = FortuneWheelView(self.bot, self.guild_id, self.user_id, self.balance)
        embed = view.create_wheel_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    # Row 3: Settings and Controls
    @discord.ui.button(
        label="BET SETTINGS",
        style=discord.ButtonStyle.secondary,
        emoji="⚙️",
        row=2
    )
    async def bet_settings(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Advanced betting configuration"""
        if not await self.validate_interaction(interaction):
            return
        
        modal = BetSettingsModal(self.current_bet, self.auto_mode)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(
        label="STATISTICS",
        style=discord.ButtonStyle.secondary,
        emoji="📊",
        row=2
    )
    async def detailed_stats(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Show detailed gaming statistics"""
        if not await self.validate_interaction(interaction):
            return
        
        embed = self.create_stats_embed()
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(
        label="REFRESH",
        style=discord.ButtonStyle.success,
        emoji="🔄",
        row=2
    )
    async def refresh_menu(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Refresh the casino menu with updated balance"""
        if not await self.validate_interaction(interaction):
            return
        
        # Update balance from database
        self.balance = await self.get_current_balance()
        embed = self.create_main_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def validate_interaction(self, interaction: discord.Interaction) -> bool:
        """Validate user interaction permissions"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This casino session belongs to another player.",
                ephemeral=True
            )
            return False
        return True
    
    async def get_current_balance(self) -> int:
        """Get current user balance from database"""
        try:
            wallet = await self.bot.db_manager.user_wallets.find_one({
                'guild_id': self.guild_id,
                'discord_id': self.user_id
            })
            return wallet.get('balance', 0) if wallet else 0
        except Exception:
            return self.balance
    
    def create_stats_embed(self) -> discord.Embed:
        """Create detailed statistics embed"""
        embed = discord.Embed(
            title=f"{CasinoTheme.EMOJIS['trophy']} Detailed Gaming Statistics",
            color=CasinoTheme.COLORS['elite'],
            timestamp=datetime.now(timezone.utc)
        )
        
        # Performance metrics
        win_rate = (self.stats.total_won / max(self.stats.total_bet, 1)) * 100
        profit_loss = self.stats.total_won - self.stats.total_bet
        
        embed.add_field(
            name="Performance Metrics",
            value=f"**Win Rate:** {win_rate:.1f}%\n"
                  f"**Profit/Loss:** ${profit_loss:,}\n"
                  f"**Average Bet:** ${self.stats.total_bet // max(self.stats.games_played, 1):,}",
            inline=True
        )
        
        embed.add_field(
            name="Achievement Progress",
            value=f"**VIP Level:** {self.get_vip_level()}\n"
                  f"**Next Tier:** ${max(0, self.get_next_tier_requirement() - self.stats.total_bet):,}\n"
                  f"**Completion:** {min(100, (self.stats.total_bet / self.get_next_tier_requirement()) * 100):.1f}%",
            inline=True
        )
        
        return embed
    
    def get_next_tier_requirement(self) -> int:
        """Get the betting requirement for the next VIP tier"""
        current_bet = self.stats.total_bet
        tiers = [100000, 250000, 500000, 1000000, 2500000]
        
        for tier in tiers:
            if current_bet < tier:
                return tier
        return 5000000  # Ultimate tier

class QuantumSlotsModal(discord.ui.Modal):
    """Advanced quantum-themed slots configuration"""
    
    def __init__(self, bot, guild_id: int, user_id: int, balance: int):
        super().__init__(title=f"{CasinoTheme.EMOJIS['lightning']} QUANTUM SLOTS CONFIGURATION")
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
        
        self.auto_spin = discord.ui.InputText(
            label="Auto-Spin Count (1-100, optional)",
            placeholder="Leave empty for single spin",
            required=False,
            max_length=3
        )
        self.add_item(self.auto_spin)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Process quantum slots configuration and execute game"""
        try:
            bet_value = str(self.bet_amount.value or '0')
            bet = int(bet_value.replace('$', '').replace(',', ''))
            
            level_value = str(self.quantum_level.value or '1')
            level = max(1, min(10, int(level_value)))
            
            auto_spins = 1
            if self.auto_spin.value:
                auto_spins = max(1, min(100, int(str(self.auto_spin.value))))
            
            if bet < 100 or bet > 50000:
                await interaction.response.send_message(
                    f"{CasinoTheme.EMOJIS['warning']} **Invalid quantum energy level**\nRange: $100 - $50,000",
                    ephemeral=True
                )
                return
            
            total_bet = bet * auto_spins
            if total_bet > self.balance:
                await interaction.response.send_message(
                    f"{CasinoTheme.EMOJIS['warning']} **Insufficient quantum energy**\nRequired: ${total_bet:,} | Available: ${self.balance:,}",
                    ephemeral=True
                )
                return
            
            # Execute quantum slots game
            game = QuantumSlotsGame(self.bot, self.guild_id, self.user_id, bet, level, auto_spins)
            result_embed = await game.play()
            
            await interaction.response.send_message(embed=result_embed, ephemeral=True)
            
        except ValueError:
            await interaction.response.send_message(
                f"{CasinoTheme.EMOJIS['warning']} **Invalid quantum parameters**\nPlease enter valid numbers.",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Quantum slots error: {e}")
            await interaction.response.send_message(
                f"{CasinoTheme.EMOJIS['warning']} **Quantum entanglement failed**\nPlease try again.",
                ephemeral=True
            )

class QuantumSlotsGame:
    """Advanced quantum slots game engine"""
    
    QUANTUM_SYMBOLS = [
        ('💎', 'Diamond', 50),    # Ultra rare
        ('👑', 'Crown', 25),      # Super rare
        ('⭐', 'Star', 15),       # Rare
        ('🔥', 'Fire', 10),       # Uncommon
        ('⚡', 'Lightning', 8),   # Uncommon
        ('💠', 'Gem', 5),        # Common
        ('🪙', 'Coin', 3),       # Common
        ('🎲', 'Dice', 2)        # Very common
    ]
    
    def __init__(self, bot, guild_id: int, user_id: int, bet: int, level: int, spins: int):
        self.bot = bot
        self.guild_id = guild_id
        self.user_id = user_id
        self.bet = bet
        self.level = level
        self.spins = spins
        self.total_winnings = 0
        self.results = []
    
    async def play(self) -> discord.Embed:
        """Execute the quantum slots game"""
        for spin in range(self.spins):
            result = await self.single_spin()
            self.results.append(result)
        
        return self.create_result_embed()
    
    async def single_spin(self) -> Dict[str, Any]:
        """Execute a single quantum spin"""
        # Quantum volatility affects symbol probabilities
        volatility_multiplier = 1 + (self.level - 1) * 0.15
        
        # Generate 5 reels with quantum entanglement
        reels = []
        for i in range(5):
            symbols = []
            for j in range(3):  # 3 symbols per reel
                symbol = self.get_quantum_symbol(volatility_multiplier)
                symbols.append(symbol)
            reels.append(symbols)
        
        # Calculate winnings
        winnings = self.calculate_winnings(reels)
        self.total_winnings += winnings
        
        # Update database
        net_change = winnings - self.bet
        if net_change != 0:
            await self.update_balance(net_change)
        
        return {
            'reels': reels,
            'winnings': winnings,
            'multiplier': self.get_win_multiplier(reels)
        }
    
    def get_quantum_symbol(self, volatility: float) -> Tuple[str, str, int]:
        """Get a quantum-influenced symbol"""
        # Adjust probabilities based on quantum level
        adjusted_weights = []
        for symbol, name, base_weight in self.QUANTUM_SYMBOLS:
            # Higher volatility increases chance of rare symbols
            if base_weight >= 15:  # Rare symbols
                weight = base_weight * volatility
            else:  # Common symbols
                weight = base_weight / volatility
            adjusted_weights.append(weight)
        
        return random.choices(self.QUANTUM_SYMBOLS, weights=adjusted_weights)[0]
    
    def calculate_winnings(self, reels: List[List[Tuple[str, str, int]]]) -> int:
        """Calculate winnings from reel configuration"""
        winnings = 0
        
        # Check horizontal lines (3 rows)
        for row in range(3):
            line = [reels[col][row] for col in range(5)]
            winnings += self.check_line_winnings(line)
        
        # Check diagonal lines
        diagonal1 = [reels[i][i] for i in range(min(5, 3))]
        diagonal2 = [reels[i][2-i] for i in range(min(5, 3))]
        
        winnings += self.check_line_winnings(diagonal1)
        winnings += self.check_line_winnings(diagonal2)
        
        # Quantum bonus for mixed rare symbols
        winnings += self.calculate_quantum_bonus(reels)
        
        return winnings
    
    def check_line_winnings(self, line: List[Tuple[str, str, int]]) -> int:
        """Check winnings for a single line"""
        if len(line) < 3:
            return 0
        
        # Count consecutive matching symbols from left
        first_symbol = line[0]
        count = 1
        
        for i in range(1, len(line)):
            if line[i][0] == first_symbol[0]:  # Same emoji
                count += 1
            else:
                break
        
        if count >= 3:
            base_payout = first_symbol[2]  # Symbol value
            multiplier = count - 2  # 3=1x, 4=2x, 5=3x
            return int(self.bet * base_payout * multiplier * 0.1)
        
        return 0
    
    def calculate_quantum_bonus(self, reels: List[List[Tuple[str, str, int]]]) -> int:
        """Calculate quantum entanglement bonus"""
        # Count unique rare symbols (value >= 15)
        rare_symbols = set()
        for reel in reels:
            for symbol in reel:
                if symbol[2] >= 15:
                    rare_symbols.add(symbol[0])
        
        if len(rare_symbols) >= 3:
            bonus_multiplier = len(rare_symbols) * 0.5
            return int(self.bet * bonus_multiplier)
        
        return 0
    
    def get_win_multiplier(self, reels: List[List[Tuple[str, str, int]]]) -> float:
        """Get the total win multiplier for this spin"""
        if self.results:
            return self.results[-1]['winnings'] / max(self.bet, 1)
        return 0.0
    
    async def update_balance(self, amount: int):
        """Update user balance in database"""
        try:
            await self.bot.db_manager.user_wallets.update_one(
                {'guild_id': self.guild_id, 'discord_id': self.user_id},
                {'$inc': {'balance': amount}},
                upsert=True
            )
            
            # Log transaction
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
    
    def create_result_embed(self) -> discord.Embed:
        """Create sophisticated result embed"""
        total_bet = self.bet * self.spins
        net_profit = self.total_winnings - total_bet
        
        color = CasinoTheme.COLORS['success'] if net_profit > 0 else CasinoTheme.COLORS['danger']
        if net_profit > self.bet * 10:  # Big win
            color = CasinoTheme.COLORS['jackpot']
        
        embed = discord.Embed(
            title=f"{CasinoTheme.EMOJIS['lightning']} QUANTUM SLOTS RESULTS",
            description=f"*Quantum Level {self.level} • {self.spins} Spin{'s' if self.spins > 1 else ''}*",
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Show last spin results if multiple spins
        if self.results:
            last_result = self.results[-1]
            reel_display = self.format_reels(last_result['reels'])
            embed.add_field(
                name="Final Quantum State",
                value=reel_display,
                inline=False
            )
        
        # Financial summary
        embed.add_field(
            name=f"{CasinoTheme.EMOJIS['coin']} Financial Results",
            value=f"**Total Bet:** ${total_bet:,}\n"
                  f"**Total Won:** ${self.total_winnings:,}\n"
                  f"**Net Profit:** ${net_profit:,}",
            inline=True
        )
        
        # Performance metrics
        win_rate = (sum(1 for r in self.results if r['winnings'] > 0) / len(self.results)) * 100
        avg_multiplier = sum(r['multiplier'] for r in self.results) / len(self.results)
        
        embed.add_field(
            name=f"{CasinoTheme.EMOJIS['trophy']} Performance",
            value=f"**Win Rate:** {win_rate:.1f}%\n"
                  f"**Avg Multiplier:** {avg_multiplier:.2f}x\n"
                  f"**Best Spin:** ${max((r['winnings'] for r in self.results), default=0):,}",
            inline=True
        )
        
        embed.set_footer(text="Quantum entanglement complete • Play again for more energy")
        
        return embed
    
    def format_reels(self, reels: List[List[Tuple[str, str, int]]]) -> str:
        """Format reels for display"""
        lines = []
        for row in range(3):
            line = " | ".join(reels[col][row][0] for col in range(5))
            lines.append(f"`{line}`")
        return "\n".join(lines)

class UltraCasinoV3(discord.Cog):
    """Ultra-Advanced Casino System V3 with py-cord 2.6.1 compatibility"""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_sessions = {}
    
    async def check_premium_access(self, guild_id: int) -> bool:
        """Check if guild has premium access for casino features"""
        try:
            guild_config = await self.bot.db_manager.guild_configs.find_one({'guild_id': guild_id})
            return guild_config.get('premium_enabled', False) if guild_config else False
        except Exception:
            return False
    
    async def get_user_stats(self, guild_id: int, user_id: int) -> GameStats:
        """Get user gaming statistics"""
        try:
            # Get wallet events for this user
            events = await self.bot.db_manager.wallet_events.find({
                'guild_id': guild_id,
                'discord_id': user_id,
                'event_type': {'$in': ['quantum_slots', 'neural_blackjack', 'platinum_roulette', 'diamond_crash', 'elite_poker', 'fortune_wheel']}
            }).to_list(length=1000)
            
            stats = GameStats()
            current_streak = 0
            
            for event in events:
                amount = event.get('amount', 0)
                if amount > 0:  # Win
                    stats.total_won += amount
                    current_streak += 1
                    if amount > stats.biggest_win:
                        stats.biggest_win = amount
                else:  # Loss
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
        """Main casino command with ultra-advanced features"""
        try:
            guild_id = ctx.guild.id if ctx.guild else 0
            user_id = ctx.user.id if ctx.user else 0
            
            # Check premium access
            if not await self.check_premium_access(guild_id):
                embed = discord.Embed(
                    title=f"{CasinoTheme.EMOJIS['crown']} Premium Access Required",
                    description="The Ultra-Advanced Casino requires premium subscription for access to exclusive gaming features.",
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
            
            # Create ultra-advanced casino menu
            view = AdvancedCasinoMenu(self.bot, guild_id, user_id, balance, stats)
            embed = view.create_main_embed()
            
            # Add casino file attachment
            try:
                casino_file = discord.File("./assets/casino.png", filename="casino.png")
                await ctx.respond(embed=embed, view=view, file=casino_file, ephemeral=True)
            except FileNotFoundError:
                await ctx.respond(embed=embed, view=view, ephemeral=True)
            
            # Track active session
            self.active_sessions[user_id] = {
                'guild_id': guild_id,
                'start_time': datetime.now(timezone.utc),
                'games_played': 0
            }
            
        except Exception as e:
            logger.error(f"Ultra casino error: {e}")
            await ctx.respond("Casino systems are temporarily offline. Please try again.", ephemeral=True)

def setup(bot):
    bot.add_cog(UltraCasinoV3(bot))