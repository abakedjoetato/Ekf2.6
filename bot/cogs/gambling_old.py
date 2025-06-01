"""
Emerald's Killfeed - ULTIMATE GAMBLING SYSTEM v7.0 (SUPREMACY EDITION)
Revolutionary Discord-native casino with Modal Integration, Select Menu Matrix, Button Matrix Systems
Advanced AI personalization, physics simulation, and premium integration
py-cord 2.6.1 compatibility with cutting-edge View components and real-time analytics
"""

import asyncio
import random
import logging
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple

import discord
import discord
from discord.ext import commands
from bot.utils.embed_factory import EmbedFactory

logger = logging.getLogger(__name__)

class AdvancedModalSystem:
    """Revolutionary Modal Integration for complex betting workflows"""

    @staticmethod
    def create_bet_setup_modal(game_type: str, current_balance: int) -> discord.ui.Modal:
        """Create dynamic bet setup modal with real-time validation"""

        class BetSetupModal(discord.ui.Modal):
            def __init__(self, game_type: str, max_balance: int):
                super().__init__(title=f"🎰 {game_type.title()} Bet Setup")
                self.game_type = game_type
                self.max_balance = max_balance

                # Dynamic bet amount input with smart suggestions
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

                # Risk profile selection
                self.risk_input = discord.ui.TextInput(
                    label="🎲 Risk Level (Optional)",
                    placeholder="conservative/moderate/aggressive/high_roller",
                    min_length=0,
                    max_length=20,
                    style=discord.TextStyle.short,
                    required=False
                )
                self.add_item(self.risk_input)

                # Session goals
                self.goal_input = discord.ui.TextInput(
                    label="🎯 Session Goal (Optional)",
                    placeholder="Target profit or stop-loss amount",
                    min_length=0,
                    max_length=15,
                    style=discord.TextStyle.short,
                    required=False
                )
                self.add_item(self.goal_input)

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

                    # Validate game-specific inputs
                    game_data = {"bet": bet}

                    if self.game_type == "roulette":
                        choice = self.choice_input.value.strip().lower()
                        valid_choices = {'red', 'black', 'green', 'even', 'odd', 'low', 'high'}
                        is_number = choice.isdigit() and 0 <= int(choice) <= 36

                        if choice not in valid_choices and not is_number:
                            await interaction.response.send_message("❌ Invalid roulette choice!", ephemeral=True)
                            return

                        game_data["choice"] = choice

                    # Store user preferences
                    if self.risk_input.value:
                        game_data["risk_preference"] = self.risk_input.value.strip().lower()

                    if self.goal_input.value:
                        try:
                            goal = int(self.goal_input.value.strip().replace(',', '').replace('$', ''))
                            game_data["session_goal"] = goal
                        except:
                            pass

                    # Store data for game initialization
                    gambling_cog = interaction.client.get_cog('Gambling')
                    gambling_cog.pending_games[interaction.user.id] = {
                        'game_type': self.game_type,
                        'data': game_data,
                        'timestamp': datetime.now(timezone.utc)
                    }

                    # Initialize the game
                    await gambling_cog._initialize_game_from_modal(interaction, self.game_type, game_data)

                except Exception as e:
                    logger.error(f"Modal submission error: {e}")
                    await interaction.response.send_message("❌ Setup failed. Please try again.", ephemeral=True)

        return BetSetupModal(game_type, current_balance)

class SelectMenuMatrix:
    """Advanced Select Menu System for intuitive navigation"""

    @staticmethod
    def create_game_selection_menu() -> discord.ui.Select:
        """Create cascading game selection menu"""

        class GameSelectionMenu(discord.ui.Select):
            def __init__(self):
                options = [
                    discord.SelectOption(
                        label="🎰 Elite Slots",
                        description="AI-enhanced slot machine with physics animations",
                        emoji="🎰",
                        value="slots"
                    ),
                    discord.SelectOption(
                        label="🃏 Interactive Blackjack",
                        description="Full featured blackjack with Hit/Stand/Double",
                        emoji="🃏",
                        value="blackjack"
                    ),
                    discord.SelectOption(
                        label="🎯 Physics Roulette",
                        description="Realistic wheel simulation with momentum",
                        emoji="🎯",
                        value="roulette"
                    ),
                    discord.SelectOption(
                        label="🏆 Tournament Mode",
                        description="Join competitive cross-server tournaments",
                        emoji="🏆",
                        value="tournament"
                    ),
                    discord.SelectOption(
                        label="📊 Analytics Dashboard",
                        description="View AI-powered performance insights",
                        emoji="📊",
                        value="analytics"
                    )
                ]

                super().__init__(
                    placeholder="🎲 Choose your game experience...",
                    min_values=1,
                    max_values=1,
                    options=options
                )

            async def callback(self, interaction: discord.Interaction):
                gambling_cog = interaction.client.get_cog('Gambling')
                await gambling_cog._handle_game_selection(interaction, self.values[0])

        return GameSelectionMenu()

    @staticmethod
    def create_bet_amount_menu(balance: int) -> discord.ui.Select:
        """Create smart bet amount selection menu"""

        class BetAmountMenu(discord.ui.Select):
            def __init__(self, max_balance: int):
                self.max_balance = max_balance

                # Smart bet suggestions based on balance
                suggestions = []
                if max_balance >= 100:
                    suggestions.append(("💰 Conservative", min(100, max_balance // 20), "Low risk bet"))
                if max_balance >= 500:
                    suggestions.append(("⚡ Moderate", min(500, max_balance // 10), "Balanced risk bet"))
                if max_balance >= 1000:
                    suggestions.append(("🔥 Aggressive", min(1000, max_balance // 5), "High risk bet"))
                if max_balance >= 5000:
                    suggestions.append(("💎 High Roller", min(5000, max_balance // 3), "Maximum risk bet"))

                suggestions.append(("🎯 Custom Amount", 0, "Enter your own bet amount"))
                suggestions.append(("💸 All In", max_balance, "Bet everything!"))

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
                    gambling_cog = interaction.client.get_cog('Gambling')
                    pending_game = gambling_cog.pending_games.get(interaction.user.id, {})
                    game_type = pending_game.get('game_type', 'slots')

                    modal = AdvancedModalSystem.create_bet_setup_modal(game_type, self.max_balance)
                    await interaction.response.send_modal(modal)
                else:
                    gambling_cog = interaction.client.get_cog('Gambling')
                    await gambling_cog._handle_bet_selection(interaction, bet)

        return BetAmountMenu(balance)

class AIPersonalizationEngine:
    """Advanced AI system for player behavior analysis and personalization"""

    def __init__(self):
        self.player_profiles: Dict[str, Dict] = {}
        self.learning_algorithms = {
            'pattern_recognition': self._analyze_betting_patterns,
            'risk_assessment': self._calculate_risk_profile,
            'session_analysis': self._analyze_session_behavior,
            'predictive_modeling': self._predict_player_actions
        }

    def analyze_player_behavior(self, user_id: str, game_data: Dict) -> Dict[str, Any]:
        """Comprehensive AI analysis of player behavior"""
        if user_id not in self.player_profiles:
            self.player_profiles[user_id] = {
                'total_games': 0,
                'total_wagered': 0,
                'total_winnings': 0,
                'game_history': [],
                'betting_patterns': {},
                'risk_tolerance': 'unknown',
                'preferred_games': [],
                'session_data': {},
                'ai_insights': {}
            }

        profile = self.player_profiles[user_id]

        # Update basic stats
        profile['total_games'] += 1
        profile['total_wagered'] += game_data.get('bet', 0)
        profile['total_winnings'] += game_data.get('winnings', 0)

        # Add to game history
        profile['game_history'].append({
            'timestamp': datetime.now(timezone.utc),
            'game_type': game_data.get('game_type'),
            'bet': game_data.get('bet', 0),
            'winnings': game_data.get('winnings', 0),
            'net_result': game_data.get('winnings', 0) - game_data.get('bet', 0)
        })

        # Keep only last 50 games
        if len(profile['game_history']) > 50:
            profile['game_history'] = profile['game_history'][-50:]

        # Run AI analysis algorithms
        for algorithm_name, algorithm_func in self.learning_algorithms.items():
            try:
                profile['ai_insights'][algorithm_name] = algorithm_func(profile)
            except Exception as e:
                logger.error(f"AI algorithm {algorithm_name} failed: {e}")

        return profile['ai_insights']

    def _analyze_betting_patterns(self, profile: Dict) -> Dict:
        """Analyze betting patterns using AI algorithms"""
        recent_games = profile['game_history'][-20:]  # Last 20 games

        if len(recent_games) < 5:
            return {'pattern': 'insufficient_data', 'confidence': 0.0}

        bets = [game['bet'] for game in recent_games]

        # Calculate pattern metrics
        avg_bet = sum(bets) / len(bets)
        bet_variance = sum((bet - avg_bet) ** 2 for bet in bets) / len(bets)
        bet_trend = (bets[-1] - bets[0]) / max(1, bets[0])  # Avoid division by zero

        # Determine pattern type
        if bet_variance < avg_bet * 0.1:
            pattern = 'consistent'
        elif bet_trend > 0.5:
            pattern = 'escalating'
        elif bet_trend < -0.5:
            pattern = 'de_escalating'
        else:
            pattern = 'variable'

        confidence = min(1.0, len(recent_games) / 20.0)

        return {
            'pattern': pattern,
            'confidence': confidence,
            'avg_bet': avg_bet,
            'variance': bet_variance,
            'trend': bet_trend
        }

    def _calculate_risk_profile(self, profile: Dict) -> Dict:
        """Calculate player risk profile using machine learning principles"""
        recent_games = profile['game_history'][-30:]

        if len(recent_games) < 10:
            return {'profile': 'unknown', 'confidence': 0.0}

        # Risk indicators
        avg_bet = sum(game['bet'] for game in recent_games) / len(recent_games)
        max_bet = max(game['bet'] for game in recent_games)
        bet_to_balance_ratio = avg_bet / max(1, profile.get('current_balance', 10000))

        # Win rate analysis
        wins = len([game for game in recent_games if game['net_result'] > 0])
        win_rate = wins / len(recent_games)

        # Risk score calculation
        risk_score = 0
        risk_score += min(3, avg_bet / 1000)  # Bet size factor
        risk_score += min(2, bet_to_balance_ratio * 10)  # Risk relative to balance
        risk_score += 1 if max_bet > avg_bet * 3 else 0  # Volatility factor

        # Determine risk profile
        if risk_score <= 1:
            risk_profile = 'conservative'
        elif risk_score <= 3:
            risk_profile = 'moderate'
        elif risk_score <= 5:
            risk_profile = 'aggressive'
        else:
            risk_profile = 'high_roller'

        return {
            'profile': risk_profile,
            'score': risk_score,
            'win_rate': win_rate,
            'confidence': min(1.0, len(recent_games) / 30.0)
        }

    def _analyze_session_behavior(self, profile: Dict) -> Dict:
        """Analyze session behavior patterns"""
        recent_games = profile['game_history'][-15:]

        if len(recent_games) < 3:
            return {'behavior': 'unknown', 'recommendation': 'Play more games for analysis'}

        # Session metrics
        session_length = len(recent_games)
        net_session = sum(game['net_result'] for game in recent_games)

        # Behavior analysis
        if net_session > 0 and session_length > 10:
            behavior = 'profitable_extended'
            recommendation = 'Consider banking profits after this hot streak'
        elif net_session < -2000 and session_length > 8:
            behavior = 'chasing_losses'
            recommendation = 'Take a break and reassess strategy'
        elif session_length > 20:
            behavior = 'marathon_session'
            recommendation = 'Long session detected - consider a break'
        else:
            behavior = 'normal_session'
            recommendation = 'Session looking healthy'

        return {
            'behavior': behavior,
            'recommendation': recommendation,
            'session_length': session_length,
            'net_result': net_session
        }

    def _predict_player_actions(self, profile: Dict) -> Dict:
        """Use predictive modeling to anticipate player behavior"""
        recent_games = profile['game_history'][-10:]

        if len(recent_games) < 5:
            return {'prediction': 'insufficient_data', 'confidence': 0.0}

        # Simple predictive indicators
        recent_losses = len([game for game in recent_games if game['net_result'] < 0])
        loss_streak = recent_losses >= 3

        recent_bets = [game['bet'] for game in recent_games]
        bet_increasing = len(recent_bets) > 2 and recent_bets[-1] > recent_bets[-3]

        # Predictions
        if loss_streak and bet_increasing:
            prediction = 'likely_to_increase_bets'
            confidence = 0.7
        elif recent_losses == 0:
            prediction = 'likely_to_continue_playing'
            confidence = 0.6
        else:
            prediction = 'moderate_risk_behavior'
            confidence = 0.5

        return {
            'prediction': prediction,
            'confidence': confidence,
            'factors': {
                'loss_streak': loss_streak,
                'bet_increasing': bet_increasing,
                'recent_losses': recent_losses
            }
        }

    def generate_personalized_recommendations(self, user_id: str) -> List[str]:
        """Generate AI-powered personalized recommendations"""
        if user_id not in self.player_profiles:
            return ["Start playing to unlock AI insights!"]

        profile = self.player_profiles[user_id]
        insights = profile.get('ai_insights', {})

        recommendations = []

        # Risk-based recommendations
        risk_data = insights.get('risk_assessment', {})
        if risk_data.get('profile') == 'high_roller':
            recommendations.append("🔥 High roller detected! Consider setting profit targets.")
        elif risk_data.get('profile') == 'conservative':
            recommendations.append("🛡️ Conservative play - try increasing bet size gradually.")

        # Pattern-based recommendations  
        pattern_data = insights.get('pattern_recognition', {})
        if pattern_data.get('pattern') == 'escalating':
            recommendations.append("⚠️ Escalating bet pattern detected - manage risk carefully.")
        elif pattern_data.get('pattern') == 'consistent':
            recommendations.append("✅ Consistent betting pattern - excellent discipline!")

        # Session-based recommendations
        session_data = insights.get('session_analysis', {})
        if session_data.get('recommendation'):
            recommendations.append(f"🤖 {session_data['recommendation']}")

        return recommendations[:3]  # Limit to top 3 recommendations

class UltimateGamblingView(discord.ui.View):
    """Revolutionary unified gambling interface with all advanced features"""

    def __init__(self, gambling_cog, ctx, game_type: str = None):
        super().__init__(timeout=600)  # 10 minute timeout
        self.gambling_cog = gambling_cog
        self.ctx = ctx
        self.game_type = game_type
        self.current_bet = 0
        self.game_state = {}
        self.user_id = ctx.user.id

        # Initialize with game selection or specific game
        if game_type:
            self._setup_game_interface(game_type)
        else:
            self._setup_main_interface()

    def _setup_main_interface(self):
        """Setup main gambling hub interface"""
        self.clear_items()

        # Add game selection menu
        game_menu = SelectMenuMatrix.create_game_selection_menu()
        self.add_item(game_menu)

        # Add quick access buttons
        quick_slots = discord.ui.Button(
            label="🎰 Quick Slots",
            style=discord.ButtonStyle.primary,
            emoji="⚡",
            row=1
        )
        quick_slots.callback = self._quick_slots
        self.add_item(quick_slots)

        quick_blackjack = discord.ui.Button(
            label="🃏 Quick Blackjack", 
            style=discord.ButtonStyle.primary,
            emoji="⚡",
            row=1
        )
        quick_blackjack.callback = self._quick_blackjack
        self.add_item(quick_blackjack)

        analytics_btn = discord.ui.Button(
            label="📊 Analytics",
            style=discord.ButtonStyle.secondary,
            emoji="🤖",
            row=2
        )
        analytics_btn.callback = self._show_analytics
        self.add_item(analytics_btn)

    def _setup_game_interface(self, game_type: str):
        """Setup specific game interface"""
        self.clear_items()

        if game_type == "slots":
            self._setup_slots_interface()
        elif game_type == "blackjack":
            self._setup_blackjack_interface()
        elif game_type == "roulette":
            self._setup_roulette_interface()

    def _setup_slots_interface(self):
        """Setup advanced slots interface"""
        # Add slots control matrix
        spin_button = discord.ui.Button(
            label="🎰 SPIN REELS",
            style=discord.ButtonStyle.success,
            emoji="🎲",
            row=0
        )
        spin_button.callback = self._spin_slots
        self.add_item(spin_button)

        # Bet adjustment buttons
        bet_down = discord.ui.Button(
            label="➖ Decrease",
            style=discord.ButtonStyle.secondary,
            emoji="💰",
            row=1
        )
        bet_down.callback = self._decrease_bet
        self.add_item(bet_down)

        bet_up = discord.ui.Button(
            label="➕ Increase",
            style=discord.ButtonStyle.secondary, 
            emoji="💰",
            row=1
        )
        bet_up.callback = self._increase_bet
        self.add_item(bet_up)

        max_bet = discord.ui.Button(
            label="🔥 Max Bet",
            style=discord.ButtonStyle.danger,
            emoji="💎",
            row=1
        )
        max_bet.callback = self._max_bet
        self.add_item(max_bet)

    def _setup_blackjack_interface(self):
        """Setup advanced blackjack interface"""
        # Primary actions
        hit_button = discord.ui.Button(
            label="🃏 HIT",
            style=discord.ButtonStyle.primary,
            emoji="➕",
            row=0
        )
        hit_button.callback = self._blackjack_hit
        self.add_item(hit_button)

        stand_button = discord.ui.Button(
            label="🛡️ STAND",
            style=discord.ButtonStyle.secondary,
            emoji="✋",
            row=0
        )
        stand_button.callback = self._blackjack_stand
        self.add_item(stand_button)

        double_button = discord.ui.Button(
            label="💰 DOUBLE",
            style=discord.ButtonStyle.success,
            emoji="⬆️",
            row=0
        )
        double_button.callback = self._blackjack_double
        self.add_item(double_button)

        surrender_button = discord.ui.Button(
            label="🏳️ SURRENDER",
            style=discord.ButtonStyle.danger,
            emoji="🚩",
            row=0
        )
        surrender_button.callback = self._blackjack_surrender
        self.add_item(surrender_button)

    def _setup_roulette_interface(self):
        """Setup advanced roulette interface"""
        spin_button = discord.ui.Button(
            label="🎯 SPIN WHEEL",
            style=discord.ButtonStyle.danger,
            emoji="🌀",
            row=0
        )
        spin_button.callback = self._spin_roulette
        self.add_item(spin_button)

    # Callback methods
    async def _quick_slots(self, interaction: discord.Interaction):
        await self.gambling_cog._handle_game_selection(interaction, "slots")

    async def _quick_blackjack(self, interaction: discord.Interaction):
        await self.gambling_cog._handle_game_selection(interaction, "blackjack")

    async def _show_analytics(self, interaction: discord.Interaction):
        await self.gambling_cog._show_analytics_dashboard(interaction)

    async def _spin_slots(self, interaction: discord.Interaction):
        await self.gambling_cog._execute_slots_spin(interaction, self)

    async def _decrease_bet(self, interaction: discord.Interaction):
        await self.gambling_cog._adjust_bet(interaction, self, -100)

    async def _increase_bet(self, interaction: discord.Interaction):
        await self.gambling_cog._adjust_bet(interaction, self, 100)

    async def _max_bet(self, interaction: discord.Interaction):
        await self.gambling_cog._set_max_bet(interaction, self)

    async def _blackjack_hit(self, interaction: discord.Interaction):
        await self.gambling_cog._blackjack_hit(interaction, self)

    async def _blackjack_stand(self, interaction: discord.Interaction):
        await self.gambling_cog._blackjack_stand(interaction, self)

    async def _blackjack_double(self, interaction: discord.Interaction):
        await self.gambling_cog._blackjack_double(interaction, self)

    async def _blackjack_surrender(self, interaction: discord.Interaction):
        await self.gambling_cog._blackjack_surrender(interaction, self)

    async def _spin_roulette(self, interaction: discord.Interaction):
        await self.gambling_cog._execute_roulette_spin(interaction, self)

class Gambling(commands.Cog):
    """
    ULTIMATE GAMBLING SYSTEM v7.0 (SUPREMACY EDITION)
    - Revolutionary Modal Integration for complex betting workflows
    - Advanced Select Menu Matrix for intuitive navigation
    - Premium Button Matrix System for fluid interactions
    - AI-Powered Personalization Engine with behavioral analysis
    - Real-time analytics dashboard with machine learning insights
    - Seamless Discord-native experience with zero friction
    - py-cord 2.6.1 cutting-edge View components
    """

    def __init__(self, bot):
        self.bot = bot
        self.user_locks: Dict[str, asyncio.Lock] = {}
        self.active_games: Dict[str, str] = {}
        self.pending_games: Dict[int, Dict] = {}  # Store pending game data from modals
        self.ai_engine = AIPersonalizationEngine()

        # Enhanced slot symbols with AI-driven rarity system
        self.slot_symbols = {
            '💎': {'weight': 1, 'value': 200, 'name': 'EMERALD CRYSTAL', 'rarity': 'MYTHIC', 'color': 0xd946ef},
            '7️⃣': {'weight': 2, 'value': 100, 'name': 'LUCKY SEVEN', 'rarity': 'LEGENDARY', 'color': 0xf97316},
            '💀': {'weight': 4, 'value': 50, 'name': 'DEATH SKULL', 'rarity': 'EPIC', 'color': 0xef4444},
            '📦': {'weight': 6, 'value': 25, 'name': 'MYSTERY BOX', 'rarity': 'RARE', 'color': 0x8b5cf6},
            '⚡': {'weight': 10, 'value': 15, 'name': 'ENERGY CORE', 'rarity': 'UNCOMMON', 'color': 0x06b6d4},
            '🔫': {'weight': 15, 'value': 10, 'name': 'WEAPON CACHE', 'rarity': 'COMMON', 'color': 0x65a30d},
            '🍒': {'weight': 25, 'value': 5, 'name': 'CHERRY', 'rarity': 'BASIC', 'color': 0x84cc16},
            '🍋': {'weight': 30, 'value': 3, 'name': 'LEMON', 'rarity': 'BASIC', 'color': 0xeab308}
        }

        # AI-powered contextual messages
        self.contextual_messages = {
            'slots': {
                'mythic_win': ["The emerald gods bestow ultimate fortune!", "Mythic alignment achieved - legends speak of this!"],
                'big_win': ["Fortune favors the bold survivor!", "The wasteland rewards your courage magnificently!"],
                'near_miss': ["So close to greatness - the reels whisper of destiny", "The crystals almost aligned - patience brings rewards"],
                'regular_win': ["Victory in the harsh wasteland", "Your skill prevails against the odds"],
                'loss': ["The wasteland tests your resolve", "Not all spins bring glory, but warriors persist"]
            },
            'blackjack': {
                'natural': ["Natural twenty-one - perfection achieved!", "The cards align in perfect harmony!"],
                'win': ["Strategic mastery over the dealer", "Your tactics triumph over chance"],
                'push': ["Minds of equal strength clash", "Honor found in the perfect stalemate"],
                'loss': ["The dealer's hidden strength revealed", "Tactical retreat for future victory"]
            },
            'roulette': {
                'number_hit': ["Physics and fortune converge perfectly!", "The wheel speaks your number!"],
                'color_win': ["The wheel spins in your favor!", "Probability yields to determination"],
                'near_miss': ["The ball danced close to victory", "Momentum nearly delivered triumph"],
                'loss': ["The wheel teaches patience", "Physics has its own mysterious ways"]
            }
        }

    def get_user_lock(self, user_key: str) -> asyncio.Lock:
        """Get or create a lock for a user to prevent concurrent operations"""
        if user_key not in self.user_locks:
            self.user_locks[user_key] = asyncio.Lock()
        return self.user_locks[user_key]

    async def check_premium_server(self, guild_id: int) -> bool:
        """Check if guild has premium access for gambling features"""
        try:
            # For now, allow all guilds access to gambling features
            return True
        except Exception as e:
            logger.error(f"Premium check failed: {e}")
            return False

    @commands.slash_command(
        name="gamble",
        description="🎰 Ultimate gambling hub with AI-powered games and analytics"
    )
    async def gamble_hub(self, ctx: discord.ApplicationContext):
        """Main gambling hub with game selection and AI features"""
        try:
            guild_id = ctx.guild.id
            discord_id = ctx.user.id

            # Get user balance
            wallet = await self.bot.db_manager.get_wallet(guild_id, discord_id)
            balance = wallet.get('balance', 0)

            if balance < 100:
                embed_data = {
                    'title': "🎰 ULTIMATE GAMBLING HUB",
                    'description': "❌ **Insufficient Funds**\n\nMinimum balance required: $100\n\nUse `/economy daily` to get started!"
                }
                embed, gamble_file = await EmbedFactory.build('generic', embed_data)
                embed.color = 0xff5e5e
                await ctx.respond(embed=embed, file=gamble_file, ephemeral=True)
                return

            # Create main hub embed
            embed_data = {
                'title': "🎰 ULTIMATE GAMBLING HUB v7.0",
                'description': f"**Welcome to the Supreme Casino Experience**\n\n💰 **Current Balance:** ${balance:,}\n🎲 **Available Games:** Elite Slots, Interactive Blackjack, Physics Roulette\n🤖 **AI Features:** Behavioral Analysis, Personalized Recommendations\n\n*Select a game below to begin your journey to riches...*",

            }
            embed_data['embed_type'] = 'gambling'
            embed, gamble_file = await EmbedFactory.build('generic', embed_data)
            embed.color = 0x7f5af0

            embed.add_field(
                name="🎮 Game Features",
                value="```🎰 AI-Enhanced Slots with Physics\n🃏 Full-Featured Blackjack\n🎯 Realistic Roulette Simulation\n📊 Real-time Analytics Dashboard\n🏆 Tournament Mode (Coming Soon)```",
                inline=False
            )

            embed.set_footer(text="🚀 Ultimate AI Gaming Engine | Select a game to start")

            # Create view with game selection
            view = UltimateGamblingView(self, ctx)

            gamble_file = discord.File('./assets/Gamble.png', filename='Gamble.png')
            await ctx.respond(embed=embed, file=gamble_file, view=view)

        except Exception as e:
            logger.error(f"Gambling hub error: {e}")
            await ctx.respond("❌ Gaming hub temporarily unavailable. Please try again.", ephemeral=True)

    # Game selection handler
    async def _handle_game_selection(self, interaction: discord.Interaction, game_type: str):
        """Handle game selection from the main menu"""
        try:
            guild_id = interaction.guild.id
            discord_id = interaction.user.id

            if game_type == "analytics":
                await self._show_analytics_dashboard(interaction)
                return
            elif game_type == "tournament":
                await interaction.response.send_message("🏆 Tournament mode coming soon! Stay tuned for epic competitions.", ephemeral=True)
                return

            # Get balance for bet selection
            wallet = await self.bot.db_manager.get_wallet(guild_id, discord_id)
            balance = wallet.get('balance', 0)

            if balance < 100:
                await interaction.response.send_message("❌ Minimum balance: $100", ephemeral=True)
                return

            # Create bet amount selection menu
            view = discord.ui.View(timeout=600)
            bet_menu = SelectMenuMatrix.create_bet_amount_menu(balance)
            view.add_item(bet_menu)

            # Update embed
            embed_data = {
                'title': f"🎰 {game_type.title()} - Select Bet Amount",
                'description': f"💰 **Current Balance:** ${balance:,}\n\nChoose a suggested bet amount or enter a custom amount below.",
            }
            if game_type == 'slots':
                embed_data['description'] += "\n\n💎 **Payout Multipliers:**\n```EMERALD EMERALD EMERALD = 200x Bet (MYTHIC JACKPOT)\nSEVEN SEVEN SEVEN = 100x Bet (LEGENDARY)\nSKULL SKULL SKULL = 50x Bet (EPIC DEATH)\nBOX BOX BOX = 25x Bet (RARE MYSTERY)\nDouble Match = Dynamic AI Multiplier\nNear Miss = Intelligent Consolation```"
            elif game_type == 'blackjack':
                embed_data['description'] += "\n\n🃏 **Blackjack Rules:**\n```Hit, Stand, Double, Surrender```"
            elif game_type == 'roulette':
                embed_data['description'] += "\n\n🎯 **Roulette Options:**\n```Numbers (0-36), Red/Black, Even/Odd, Low/High```"

            embed_data['embed_type'] = 'gambling'
            embed, gamble_file = await EmbedFactory.build('generic', embed_data)
            embed.color = 0x7f5af0

            if game_type == 'slots':
                embed.add_field(
                    name="💎 Payout Multipliers",
                    value="```EMERALD EMERALD EMERALD = 200x Bet (MYTHIC JACKPOT)\nSEVEN SEVEN SEVEN = 100x Bet (LEGENDARY)\nSKULL SKULL SKULL = 50x Bet (EPIC DEATH)\nBOX BOX BOX = 25x Bet (RARE MYSTERY)\nDouble Match = Dynamic AI Multiplier\nNear Miss = Intelligent Consolation```",
                    inline=False
                )

            embed.set_footer(text="🚀 Ultimate AI Gaming Engine | Select your bet amount")

            gamble_file = discord.File('./assets/Gamble.png', filename='Gamble.png')
            if hasattr(interaction, 'response') and not interaction.response.is_done():
                await interaction.response.edit_message(embed=embed, file=gamble_file, view=view)
            else:
                await interaction.edit_original_response(embed=embed, file=gamble_file, view=view)

            # Store the game type
            self.pending_games[discord_id] = {'game_type': game_type}

        except Exception as e:
            logger.error(f"Game selection failed: {e}")
            await interaction.response.send_message("❌ Game selection failed.", ephemeral=True)

    async def _handle_bet_selection(self, interaction: discord.Interaction, bet: int):
        """Handle bet selection from the main menu"""
        try:
            guild_id = interaction.guild.id
            discord_id = interaction.user.id

            # Get pending game data
            pending_game = self.pending_games.get(discord_id, {})
            game_type = pending_game.get('game_type', 'slots')

            # Validate bet amount
            wallet = await self.bot.db_manager.get_wallet(guild_id, discord_id)
            balance = wallet.get('balance', 0)

            if bet > balance:
                await interaction.response.send_message(f"❌ Insufficient funds! You have ${balance:,}", ephemeral=True)
                return

            # Prepare game data
            game_data = {
                'bet': bet,
                'game_type': game_type,
                'timestamp': datetime.now(timezone.utc)
            }

            # Initialize the appropriate game
            if game_type == "slots":
                await self._initialize_slots_game(interaction, bet, game_data)
            elif game_type == "blackjack":
                await self._initialize_blackjack_game(interaction, bet, game_data)
            elif game_type == "roulette":
                await self._initialize_roulette_game(interaction, bet, game_data)

        except Exception as e:
            logger.error(f"Bet selection failed: {e}")
            await interaction.response.send_message("❌ Bet selection failed. Please try again.", ephemeral=True)

    async def _initialize_game_from_modal(self, interaction: discord.Interaction, game_type: str, game_data: Dict):
        """Initialize game from modal submission"""
        try:
            guild_id = interaction.guild.id
            discord_id = interaction.user.id
            bet = game_data.get('bet', 100)

            # Validate and deduct bet
            wallet = await self.bot.db_manager.get_wallet(guild_id, discord_id)
            balance = wallet.get('balance', 0)

            if bet > balance:
                await interaction.response.send_message(f"❌ Insufficient funds! You have ${balance:,}", ephemeral=True)
                return

            # Initialize the appropriate game
            if game_type == "slots":
                await self._initialize_slots_game(interaction, bet, game_data)
            elif game_type == "blackjack":
                await self._initialize_blackjack_game(interaction, bet, game_data)
            elif game_type == "roulette":
                await self._initialize_roulette_game(interaction, bet, game_data)

        except Exception as e:
            logger.error(f"Modal game init failed: {e}")
            await interaction.response.send_message("❌ Game initialization failed. Please try again.", ephemeral=True)

    async def _initialize_slots_game(self, interaction: discord.Interaction, bet: int, game_data: Dict):
        """Initialize slots game"""
        try:
            guild_id = interaction.guild.id
            discord_id = interaction.user.id

            # Validate bet amount
            wallet = await self.bot.db_manager.get_wallet(guild_id, discord_id)
            balance = wallet.get('balance', 0)

            if bet > balance:
                await interaction.response.send_message(f"❌ Insufficient funds! You have ${balance:,}", ephemeral=True)
                return

            # Deduct bet from wallet
            await self.bot.db_manager.update_wallet(guild_id, discord_id, -bet, "gambling_slots")

            # Update embed
            embed_data = {
                'title': "🎰 ULTIMATE SLOTS - AI ENHANCED",
                'description': f"**Bet:** ${bet:,}\n**AI Mode:** Active\n**Reel Physics:** Enabled\n\n🤖 **AI analyzing your play style...**"
            }
            embed_data['embed_type'] = 'gambling'
            embed, gamble_file = await EmbedFactory.build('generic', embed_data)
            embed.color = 0x7f5af0

            embed.add_field(
                name="💎 Payout Multipliers",
                value="```EMERALD EMERALD EMERALD = 200x Bet (MYTHIC JACKPOT)\nSEVEN SEVEN SEVEN = 100x Bet (LEGENDARY)\nSKULL SKULL SKULL = 50x Bet (EPIC DEATH)\nBOX BOX BOX = 25x Bet (RARE MYSTERY)\nDouble Match = Dynamic AI Multiplier\nNear Miss = Intelligent Consolation```",
                inline=False
            )

            embed.set_footer(text="🚀 Ultimate AI Gaming Engine | Click SPIN to begin")

            # Create slots view
            view = UltimateGamblingView(self, interaction, "slots")
            view.current_bet = bet
            view.game_state = game_data

            if hasattr(interaction, 'response') and not interaction.response.is_done():
                await interaction.response.edit_message(embed=embed, file=gamble_file, view=view)
            else:
                await interaction.edit_original_response(embed=embed, file=gamble_file, view=view)

        except Exception as e:
            logger.error(f"Slots game start failed: {e}")
            if hasattr(interaction, 'response') and not interaction.response.is_done():
                await interaction.response.send_message("❌ Failed to start slots game. Please try again.", ephemeral=True)
            else:
                await interaction.followup.send("❌ Failed to start slots game. Please try again.", ephemeral=True)

    async def _execute_slots_spin(self, interaction: discord.Interaction, view: UltimateGamblingView):
        """Execute advanced slots spin with AI analysis"""
        try:
            await interaction.response.defer()

            bet = view.current_bet
            guild_id = interaction.guild.id
            discord_id = interaction.user.id

            # Advanced 8-frame animation sequence
            animation_frames = [
                ("🌀 Initializing quantum reels...", 0x8b5cf6),
                ("⚡ AI analysis in progress...", 0xa855f7),
                ("🔮 Probability calculations running...", 0xc084fc),
                ("💫 Reel synchronization active...", 0xd946ef),
                ("🎯 Targeting optimal outcomes...", 0xec4899),
                ("🚀 Final momentum calculations...", 0xf97316),
                ("✨ Reality convergence initiated...", 0xeab308),
                ("🎊 Results materializing...", 0x22c55e)
            ]

            for i, (description, color) in enumerate(animation_frames):
                progress = (i + 1) / len(animation_frames)
                progress_bar = "█" * int(progress * 12) + "░" * int((1 - progress) * 12)

                embed_data = {
                    'title': "🎰 ULTIMATE SLOTS - AI ANALYSIS",
                    'description': f"**Bet:** ${bet:,}\n\n{description}\n\n⚡ **AI Processing...** ⚡"
                }
                embed, gamble_file = await EmbedFactory.build('generic', embed_data)
                embed.color = color
                embed.set_thumbnail(url="attachment://Gamble.png")

                embed.add_field(
                    name="🤖 Analysis Progress",
                    value=f"```[{progress_bar}] {progress*100:.0f}%```",
                    inline=False
                )

                embed.set_footer(text=f"🚀 Frame {i+1}/8 | Ultimate AI Gaming Engine")

                gamble_file = discord.File('./assets/Gamble.png', filename='Gamble.png')
                await interaction.edit_original_response(embed=embed, file=gamble_file, view=None)
                await asyncio.sleep(0.8)

            # Generate AI-enhanced results
            reels = self._generate_ai_enhanced_reels(str(discord_id))
            winnings, win_type, multiplier = self._calculate_ai_slots_payout(reels, bet, str(discord_id))

            # Update wallet with winnings
            if winnings > 0:
                await self.bot.db_manager.update_wallet(guild_id, discord_id, winnings, "gambling_slots")

            # Track in AI system
            game_data = {
                'game_type': 'slots',
                'bet': bet,
                'winnings': winnings,
                'reels': reels,
                'win_type': win_type,
                'ai_enhanced': True
            }

            ai_insights = self.ai_engine.analyze_player_behavior(str(discord_id), game_data)

            # Get updated balance
            updated_wallet = await self.bot.db_manager.get_wallet(guild_id, discord_id)

            # Create revolutionary result embed
            net_result = winnings - bet
            embed_color = 0x00d38a if winnings > 0 else 0xff5e5e

            # Special color for mythic wins
            if any(symbol == '💎' for symbol in reels) and len(set(reels)) == 1:
                embed_color = 0xd946ef  # Mythic purple

            embed_data = {
                'title': "🎰 ULTIMATE SLOTS - AI ANALYSIS COMPLETE"
            }
            embed, gamble_file = await EmbedFactory.build('generic', embed_data)
            embed.color = embed_color
            embed.set_thumbnail(url="attachment://Gamble.png")

            # Enhanced reel display with rarity indicators
            reel_display = f"║ {'  │  '.join(reels)} ║"
            rarity_line = self._get_reel_rarity_display(reels)

            embed.add_field(
                name="🎲 Final AI-Enhanced Reels",
                value=f"```{reel_display}\n{rarity_line}```\n💰 **Winnings:** ${winnings:,} (x{multiplier:.1f})\n🤖 **Net Result:** ${net_result:,}",
                inline=False
            )

            # AI insights display
            recommendations = self.ai_engine.generate_personalized_recommendations(str(discord_id))
            if recommendations:
                ai_display = "\n".join([f"• {rec}" for rec in recommendations])
                embed.add_field(
                    name="🤖 AI Insights",
                    value=f"```AI Recommendations:\n{ai_display}```",
                    inline=False
                )

            # Contextual message based on outcome
            context_key = 'mythic_win' if any(symbol == '💎' for symbol in reels) and len(set(reels)) == 1 else win_type
            messages = self.contextual_messages['slots'].get(context_key, ["Fortune favors the bold!"])
            message = random.choice(messages)

            embed.add_field(
                name="📢 Quantum Announcer",
                value=f"```AI Message: {message}```",
                inline=False
            )

            embed.set_footer(text=f"💰 Updated Balance: ${updated_wallet.get('balance', 0):,} | Ultimate AI Gaming Engine")

            # Re-enable view
            view.clear_items()
            view._setup_slots_interface()

            gamble_file = discord.File('./assets/Gamble.png', filename='Gamble.png')
            await interaction.edit_original_response(embed=embed, file=gamble_file, view=view)

        except Exception as e:
            logger.error(f"Slots spin failed: {e}")
            await interaction.edit_original_response(content="❌ Spin failed. Please try again.")

    def _generate_ai_enhanced_reels(self, user_id: str) -> List[str]:
        """Generate AI-enhanced slot reels based on player behavior"""
        try:
            # Get risk profile
            profile = self.ai_engine.player_profiles.get(user_id, {})
            risk_data = profile.get('ai_insights', {}).get('risk_assessment', {})
            risk_profile = risk_data.get('profile', 'moderate')

            # Adjust weights based on risk profile
            weights = {symbol: data['weight'] for symbol, data in self.slot_symbols.items()}
            if risk_profile == 'conservative':
                for symbol in ['💀', '💎', '7️⃣']:
                    weights[symbol] = int(weights[symbol] * 1.5)  # Reduce chance of high-risk symbols
            elif risk_profile == 'aggressive':
                for symbol in ['🍒', '🍋', '🔫']:
                    weights[symbol] = int(weights[symbol] * 1.2)  # Reduce chance of low-risk symbols

            # Generate reels using adjusted weights
            symbols = list(weights.keys())
            adjusted_weights = list(weights.values())

            reels = random.choices(symbols, weights=adjusted_weights, k=3)
            return reels

        except Exception as e:
            logger.error(f"Reel gen failed: {e}")
            return ['🍋', '🍒', '🔫']  # Default reels on failure

    def _calculate_ai_slots_payout(self, reels: List[str], bet: int, user_id: str) -> Tuple[int, str, float]:
        """Calculate AI-enhanced slots payout with dynamic multipliers"""
        try:
            # Check for Mythic Jackpot (all emeralds)
            if all(symbol == '💎' for symbol in reels):
                return bet * 200, 'mythic_win', 200.0

            # Check for Legendary Win (all sevens)
            if all(symbol == '7️⃣' for symbol in reels):
                return bet * 100, 'big_win', 100.0

            # Check for Epic Win (all skulls)
            if all(symbol == '💀' for symbol in reels):
                return bet * 50, 'big_win', 50.0

            # Check for Rare Win (all boxes)
            if all(symbol == '📦' for symbol in reels):
                return bet * 25, 'regular_win', 25.0

            # Check for double match
            if reels[0] == reels[1] or reels[0] == reels[2] or reels[1] == reels[2]:
                multiplier = 5.0  # Base multiplier
                ai_profile = self.ai_engine.player_profiles.get(user_id, {}).get('ai_insights', {}).get('risk_assessment', {})
                if ai_profile.get('profile') == 'high_roller':
                    multiplier *= 1.5  # Boost for high rollers
                elif ai_profile.get('profile') == 'conservative':
                    multiplier *= 0.8  # Reduce for conservative players
                winnings = int(bet * multiplier)
                return winnings, 'regular_win', multiplier

            # Check for near miss (two of the same symbol)
            symbol_counts = {}
            for symbol in reels:
                symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
            if 2 in symbol_counts.values():
                return int(bet * 0.2), 'near_miss', 0.2  # Consolation prize

            # No win
            return 0, 'loss', 0.0

        except Exception as e:
            logger.error(f"Payout error: {e}")
            return 0, 'loss', 0.0

    def _get_reel_rarity_display(self, reels: List[str]) -> str:
        """Get rarity display for reels"""
        try:
            rarities = [self.slot_symbols[symbol]['rarity'][0] for symbol in reels]  # First letter of rarity
            return f"  {'   '.join(rarities)}  "
        except Exception as e:
            logger.error(f"Rarity error: {e}")
            return "  U   U   U  "  # Unknown

    async def _adjust_bet(self, interaction: discord.Interaction, view: UltimateGamblingView, amount: int):
        """Adjust the current bet amount"""
        try:
            guild_id = interaction.guild.id
            discord_id = interaction.user.id

            wallet = await self.bot.db_manager.get_wallet(guild_id, discord_id)
            balance = wallet.get('balance', 0)

            new_bet = view.current_bet + amount
            if new_bet < 100:
                new_bet = 100  # Min bet

            if new_bet > balance:
                new_bet = balance  # Max bet

            view.current_bet = new_bet

            # Update embed
            embed_data = {
                'title': "🎰 ULTIMATE SLOTS - AI ENHANCED",
                'description': f"**Bet:** ${new_bet:,}\n**AI Mode:** Active\n**Reel Physics:** Enabled\n\n🤖 **AI analyzing your play style...**"
            }
            embed_data['embed_type'] = 'gambling'
            embed, gamble_file = await EmbedFactory.build('generic', embed_data)
            embed.color = 0x7f5af0

            embed.add_field(
                name="💎 Payout Multipliers",
                value="```EMERALD EMERALD EMERALD = 200x Bet (MYTHIC JACKPOT)\nSEVEN SEVEN SEVEN = 100x Bet (LEGENDARY)\nSKULL SKULL SKULL = 50x Bet (EPIC DEATH)\nBOX BOX BOX = 25x Bet (RARE MYSTERY)\nDouble Match = Dynamic AI Multiplier\nNear Miss = Intelligent Consolation```",
                inline=False
            )

            embed.set_footer(text="🚀 Ultimate AI Gaming Engine | Click SPIN to begin")

            if hasattr(interaction, 'response') and not interaction.response.is_done():
                await interaction.response.edit_message(embed=embed, file=gamble_file, view=view)
            else:
                await interaction.edit_original_response(embed=embed, file=gamble_file, view=view)

        except Exception as e:
            logger.error(f"Bet adjust failed: {e}")

    async def _set_max_bet(self, interaction: discord.Interaction, view: UltimateGamblingView):
        """Set the bet to the maximum allowed"""
        try:
            guild_id = interaction.guild.id
            discord_id = interaction.user.id

            wallet = await self.bot.db_manager.get_wallet(guild_id, discord_id)
            balance = wallet.get('balance', 0)

            view.current_bet = balance

            # Update embed
            embed_data = {
                'title': "🎰 ULTIMATE SLOTS - AI ENHANCED",
                'description': f"**Bet:** ${balance:,}\n**AI Mode:** Active\n**Reel Physics:** Enabled\n\n🤖 **AI analyzing your play style...**"
            }
            embed_data['embed_type'] = 'gambling'
            embed, gamble_file = await EmbedFactory.build('generic', embed_data)
            embed.color = 0x7f5af0

            embed.add_field(
                name="💎 Payout Multipliers",
                value="```EMERALD EMERALD EMERALD = 200x Bet (MYTHIC JACKPOT)\nSEVEN SEVEN SEVEN = 100x Bet (LEGENDARY)\nSKULL SKULL SKULL = 50x Bet (EPIC DEATH)\nBOX BOX BOX = 25x Bet (RARE MYSTERY)\nDouble Match = Dynamic AI Multiplier\nNear Miss = Intelligent Consolation```",
                inline=False
            )

            embed.set_footer(text="🚀 Ultimate AI Gaming Engine | Click SPIN to begin")

            if hasattr(interaction, 'response') and not interaction.response.is_done():
                await interaction.response.edit_message(embed=embed, file=gamble_file, view=view)
            else:
                await interaction.edit_original_response(embed=embed, file=gamble_file, view=view)

        except Exception as e:
            logger.error(f"Max bet failed: {e}")

    async def _initialize_blackjack_game(self, interaction: discord.Interaction, bet: int, game_data: Dict):
        """Initialize blackjack game with full deck and card management"""
        try:
            guild_id = interaction.guild.id
            discord_id = interaction.user.id

            # Validate bet amount
            wallet = await self.bot.db_manager.get_wallet(guild_id, discord_id)
            balance = wallet.get('balance', 0)

            if bet > balance:
                await interaction.response.send_message(f"❌ Insufficient funds! You have ${balance:,}", ephemeral=True)
                return

            # Deduct bet from wallet
            await self.bot.db_manager.update_wallet(guild_id, discord_id, -bet, "gambling_blackjack")

            # Initialize blackjack game state
            deck = self._create_deck()
            random.shuffle(deck)

            player_hand = [deck.pop(), deck.pop()]
            dealer_hand = [deck.pop(), deck.pop()]

            game_state = {
                'deck': deck,
                'player_hand': player_hand,
                'dealer_hand': dealer_hand,
                'bet': bet,
                'doubled': False,
                'surrendered': False,
                'game_over': False,
                'player_stood': False
            }

            # Check for natural blackjack
            player_score = self._calculate_hand_value(player_hand)
            dealer_score = self._calculate_hand_value(dealer_hand)

            if player_score == 21:
                if dealer_score == 21:
                    # Push
                    await self.bot.db_manager.update_wallet(guild_id, discord_id, bet, "gambling_blackjack")
                    await self._show_blackjack_result(interaction, game_state, "push", "Both have blackjack!")
                else:
                    # Natural blackjack wins 3:2
                    winnings = int(bet * 2.5)
                    await self.bot.db_manager.update_wallet(guild_id, discord_id, winnings, "gambling_blackjack")
                    await self._show_blackjack_result(interaction, game_state, "natural", "Natural Blackjack!")
                return

            # Create blackjack embed and view
            embed_data = {
                'title': "🃏 INTERACTIVE BLACKJACK - AI ENHANCED",
                'description': f"**Bet:** ${bet:,}\n**AI Mode:** Active\n**Strategy Hints:** Enabled\n\n🤖 **AI analyzing optimal play...**"
            }
            embed_data['embed_type'] = 'gambling'
            embed, gamble_file = await EmbedFactory.build('generic', embed_data)
            embed.color = 0x7f5af0

            # Add hands display
            player_display = self._format_hand_display(player_hand, player_score)
            dealer_display = self._format_hand_display([dealer_hand[0], "🎴"], "?")

            embed.add_field(
                name="🎯 Your Hand",
                value=f"```{player_display}```",
                inline=True
            )

            embed.add_field(
                name="🎰 Dealer Hand",
                value=f"```{dealer_display}```",
                inline=True
            )

            # AI strategy hint
            hint = self._get_blackjack_strategy_hint(player_hand, dealer_hand[0])
            embed.add_field(
                name="🤖 AI Strategy Hint",
                value=f"```{hint}```",
                inline=False
            )

            embed.set_footer(text="🚀 Ultimate AI Gaming Engine | Choose your action")

            # Create blackjack view
            view = UltimateGamblingView(self, interaction, "blackjack")
            view.current_bet = bet
            view.game_state = game_state

            gamble_file = discord.File('./assets/Gamble.png', filename='Gamble.png')
            if hasattr(interaction, 'response') and not interaction.response.is_done():
                await interaction.response.edit_message(embed=embed, file=gamble_file, view=view)
            else:
                await interaction.edit_original_response(embed=embed, file=gamble_file, view=view)

        except Exception as e:
            logger.error(f"Blackjack init failed: {e}")
            if hasattr(interaction, 'response') and not interaction.response.is_done():
                await interaction.response.send_message("❌ Failed to start blackjack game. Please try again.", ephemeral=True)
            else:
                await interaction.followup.send("❌ Failed to start blackjack game. Please try again.", ephemeral=True)

    def _create_deck(self) -> List[Dict]:
        """Create a standard 52-card deck"""
        suits = ['♠️', '♥️', '♦️', '♣️']
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        deck = []
        
        for suit in suits:
            for rank in ranks:
                value = 11 if rank == 'A' else 10 if rank in ['J', 'Q', 'K'] else int(rank)
                deck.append({'rank': rank, 'suit': suit, 'value': value})
        
        return deck

    def _calculate_hand_value(self, hand: List[Dict]) -> int:
        """Calculate the value of a blackjack hand"""
        total = 0
        aces = 0
        
        for card in hand:
            if isinstance(card, str):  # Hidden card
                continue
            if card['rank'] == 'A':
                aces += 1
                total += 11
            else:
                total += card['value']
        
        # Adjust for aces
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        
        return total

    def _format_hand_display(self, hand: List, score) -> str:
        """Format hand for display"""
        if isinstance(hand[0], str):  # Hidden card scenario
            return f"🎴 {hand[1]['rank']}{hand[1]['suit']} | Score: ?"
        
        cards = []
        for card in hand:
            if isinstance(card, str):
                cards.append(card)
            else:
                cards.append(f"{card['rank']}{card['suit']}")
        
        return f"{' '.join(cards)} | Score: {score}"

    def _get_blackjack_strategy_hint(self, player_hand: List[Dict], dealer_card: Dict) -> str:
        """Get AI strategy hint for blackjack"""
        player_score = self._calculate_hand_value(player_hand)
        dealer_value = dealer_card['value']
        
        if player_score <= 11:
            return "Always HIT with 11 or less - no risk of busting"
        elif player_score == 12:
            return "HIT against dealer 2-3, 7-A | STAND against 4-6"
        elif 13 <= player_score <= 16:
            if dealer_value <= 6:
                return "STAND - dealer likely to bust with weak upcard"
            else:
                return "HIT - dealer has strong upcard, need to improve"
        elif player_score == 17:
            return "STAND - 17 is a solid hand in most situations"
        elif player_score >= 18:
            return "STAND - strong hand, let dealer try to beat it"
        else:
            return "Follow basic blackjack strategy"

    async def _blackjack_hit(self, interaction: discord.Interaction, view: UltimateGamblingView):
        """Handle blackjack hit action"""
        try:
            await interaction.response.defer()
            
            game_state = view.game_state
            if game_state['game_over']:
                await interaction.edit_original_response(content="❌ Game is already over!")
                return

            # Deal a card
            new_card = game_state['deck'].pop()
            game_state['player_hand'].append(new_card)
            
            player_score = self._calculate_hand_value(game_state['player_hand'])
            
            if player_score > 21:
                # Player busts
                await self._show_blackjack_result(interaction, game_state, "bust", "You busted!")
                return
            elif player_score == 21:
                # Player has 21, auto-stand
                await self._blackjack_dealer_play(interaction, view)
                return
            
            # Update display
            await self._update_blackjack_display(interaction, view, f"You drew {new_card['rank']}{new_card['suit']}")
            
        except Exception as e:
            logger.error(f"Blackjack hit failed: {e}")
            await interaction.edit_original_response(content="❌ Hit action failed.")

    async def _blackjack_stand(self, interaction: discord.Interaction, view: UltimateGamblingView):
        """Handle blackjack stand action"""
        try:
            await interaction.response.defer()
            
            game_state = view.game_state
            if game_state['game_over']:
                await interaction.edit_original_response(content="❌ Game is already over!")
                return
            
            game_state['player_stood'] = True
            await self._blackjack_dealer_play(interaction, view)
            
        except Exception as e:
            logger.error(f"Blackjack stand failed: {e}")
            await interaction.edit_original_response(content="❌ Stand action failed.")

    async def _blackjack_double(self, interaction: discord.Interaction, view: UltimateGamblingView):
        """Handle blackjack double down action"""
        try:
            await interaction.response.defer()
            
            game_state = view.game_state
            if game_state['game_over'] or game_state['doubled']:
                await interaction.edit_original_response(content="❌ Cannot double down now!")
                return
            
            # Check if player has enough money to double
            guild_id = interaction.guild.id
            discord_id = interaction.user.id
            wallet = await self.bot.db_manager.get_wallet(guild_id, discord_id)
            
            if wallet.get('balance', 0) < game_state['bet']:
                await interaction.edit_original_response(content="❌ Insufficient funds to double down!")
                return
            
            # Deduct additional bet
            await self.bot.db_manager.update_wallet(guild_id, discord_id, -game_state['bet'], "gambling_blackjack")
            game_state['bet'] *= 2
            game_state['doubled'] = True
            
            # Deal one card and stand
            new_card = game_state['deck'].pop()
            game_state['player_hand'].append(new_card)
            
            player_score = self._calculate_hand_value(game_state['player_hand'])
            
            if player_score > 21:
                await self._show_blackjack_result(interaction, game_state, "bust", f"You drew {new_card['rank']}{new_card['suit']} and busted!")
                return
            
            # Auto-stand after double
            await self._blackjack_dealer_play(interaction, view)
            
        except Exception as e:
            logger.error(f"Blackjack double failed: {e}")
            await interaction.edit_original_response(content="❌ Double down failed.")

    async def _blackjack_surrender(self, interaction: discord.Interaction, view: UltimateGamblingView):
        """Handle blackjack surrender action"""
        try:
            await interaction.response.defer()
            
            game_state = view.game_state
            if game_state['game_over'] or len(game_state['player_hand']) != 2:
                await interaction.edit_original_response(content="❌ Can only surrender with initial 2 cards!")
                return
            
            # Return half the bet
            guild_id = interaction.guild.id
            discord_id = interaction.user.id
            half_bet = game_state['bet'] // 2
            await self.bot.db_manager.update_wallet(guild_id, discord_id, half_bet, "gambling_blackjack")
            
            game_state['surrendered'] = True
            await self._show_blackjack_result(interaction, game_state, "surrender", f"You surrendered and got back ${half_bet:,}")
            
        except Exception as e:
            logger.error(f"Blackjack surrender failed: {e}")
            await interaction.edit_original_response(content="❌ Surrender failed.")

    async def _blackjack_dealer_play(self, interaction: discord.Interaction, view: UltimateGamblingView):
        """Handle dealer's turn in blackjack"""
        try:
            game_state = view.game_state
            
            # Reveal dealer's hidden card
            dealer_score = self._calculate_hand_value(game_state['dealer_hand'])
            
            # Dealer hits on soft 17
            while dealer_score < 17 or (dealer_score == 17 and self._is_soft_17(game_state['dealer_hand'])):
                new_card = game_state['deck'].pop()
                game_state['dealer_hand'].append(new_card)
                dealer_score = self._calculate_hand_value(game_state['dealer_hand'])
            
            # Determine winner
            player_score = self._calculate_hand_value(game_state['player_hand'])
            
            if dealer_score > 21:
                result = "win"
                message = "Dealer busted - You win!"
                winnings = game_state['bet'] * 2
            elif dealer_score > player_score:
                result = "loss"
                message = "Dealer wins!"
                winnings = 0
            elif player_score > dealer_score:
                result = "win"
                message = "You win!"
                winnings = game_state['bet'] * 2
            else:
                result = "push"
                message = "Push - It's a tie!"
                winnings = game_state['bet']
            
            # Update wallet
            if winnings > 0:
                guild_id = interaction.guild.id
                discord_id = interaction.user.id
                await self.bot.db_manager.update_wallet(guild_id, discord_id, winnings, "gambling_blackjack")
            
            await self._show_blackjack_result(interaction, game_state, result, message)
            
        except Exception as e:
            logger.error(f"Dealer play failed: {e}")

    def _is_soft_17(self, hand: List[Dict]) -> bool:
        """Check if hand is a soft 17 (contains ace counted as 11)"""
        total = 0
        aces = 0
        
        for card in hand:
            if card['rank'] == 'A':
                aces += 1
                total += 11
            else:
                total += card['value']
        
        return total == 17 and aces > 0

    async def _update_blackjack_display(self, interaction: discord.Interaction, view: UltimateGamblingView, message: str = ""):
        """Update blackjack game display"""
        try:
            game_state = view.game_state
            
            player_score = self._calculate_hand_value(game_state['player_hand'])
            dealer_score = "?" if not game_state['player_stood'] else self._calculate_hand_value(game_state['dealer_hand'])
            
            embed_data = {
                'title': "🃏 INTERACTIVE BLACKJACK - AI ENHANCED",
                'description': f"**Bet:** ${game_state['bet']:,}\n**AI Mode:** Active\n**Strategy Hints:** Enabled\n\n{message}"
            }
            embed_data['embed_type'] = 'gambling'
            embed, gamble_file = await EmbedFactory.build('generic', embed_data)
            embed.color = 0x7f5af0

            # Add hands display
            player_display = self._format_hand_display(game_state['player_hand'], player_score)
            
            if game_state['player_stood']:
                dealer_display = self._format_hand_display(game_state['dealer_hand'], dealer_score)
            else:
                dealer_display = self._format_hand_display([game_state['dealer_hand'][0], "🎴"], "?")

            embed.add_field(
                name="🎯 Your Hand",
                value=f"```{player_display}```",
                inline=True
            )

            embed.add_field(
                name="🎰 Dealer Hand",
                value=f"```{dealer_display}```",
                inline=True
            )

            if not game_state['player_stood'] and player_score < 21:
                hint = self._get_blackjack_strategy_hint(game_state['player_hand'], game_state['dealer_hand'][0])
                embed.add_field(
                    name="🤖 AI Strategy Hint",
                    value=f"```{hint}```",
                    inline=False
                )

            embed.set_footer(text="🚀 Ultimate AI Gaming Engine | Choose your action")

            gamble_file = discord.File('./assets/Gamble.png', filename='Gamble.png')
            await interaction.edit_original_response(embed=embed, file=gamble_file, view=view)
            
        except Exception as e:
            logger.error(f"Display update failed: {e}")

    async def _show_blackjack_result(self, interaction: discord.Interaction, game_state: Dict, result: str, message: str):
        """Show final blackjack result with play again options"""
        try:
            game_state['game_over'] = True
            
            player_score = self._calculate_hand_value(game_state['player_hand'])
            dealer_score = self._calculate_hand_value(game_state['dealer_hand'])
            
            # Get updated balance
            guild_id = interaction.guild.id
            discord_id = interaction.user.id
            wallet = await self.bot.db_manager.get_wallet(guild_id, discord_id)
            current_balance = wallet.get('balance', 0)
            
            # Color based on result
            colors = {
                'win': 0x00d38a,
                'natural': 0xd946ef,
                'loss': 0xff5e5e,
                'push': 0xfbbf24,
                'bust': 0xff5e5e,
                'surrender': 0x6366f1
            }
            
            embed_data = {
                'title': "🃏 BLACKJACK RESULT - AI ANALYSIS COMPLETE",
                'description': f"**{message}**\n\n🎯 **Final Scores:**\nYour Hand: {player_score}\nDealer Hand: {dealer_score}"
            }
            embed, gamble_file = await EmbedFactory.build('generic', embed_data)
            embed.color = colors.get(result, 0x7f5af0)
            embed.set_thumbnail(url="attachment://Gamble.png")

            # Show final hands
            player_display = self._format_hand_display(game_state['player_hand'], player_score)
            dealer_display = self._format_hand_display(game_state['dealer_hand'], dealer_score)

            embed.add_field(
                name="🎯 Your Final Hand",
                value=f"```{player_display}```",
                inline=True
            )

            embed.add_field(
                name="🎰 Dealer Final Hand",
                value=f"```{dealer_display}```",
                inline=True
            )

            # Track in AI system
            ai_game_data = {
                'game_type': 'blackjack',
                'bet': game_state['bet'],
                'winnings': game_state['bet'] * 2 if result == 'win' else (game_state['bet'] * 2.5 if result == 'natural' else (game_state['bet'] if result == 'push' else 0)),
                'result': result,
                'player_score': player_score,
                'dealer_score': dealer_score
            }

            ai_insights = self.ai_engine.analyze_player_behavior(str(discord_id), ai_game_data)
            
            # Contextual message
            context_messages = self.contextual_messages['blackjack'].get(result, ["Great game!"])
            context_message = random.choice(context_messages)
            
            embed.add_field(
                name="📢 AI Announcer",
                value=f"```{context_message}```",
                inline=False
            )

            embed.set_footer(text=f"💰 Updated Balance: ${current_balance:,} | Ultimate AI Gaming Engine")

            # Create continuation view with play again options
            view = self._create_blackjack_continuation_view(game_state['bet'], current_balance)
            
            gamble_file = discord.File('./assets/Gamble.png', filename='Gamble.png')
            await interaction.edit_original_response(embed=embed, file=gamble_file, view=view)
            
        except Exception as e:
            logger.error(f"Result display failed: {e}")

    def _create_blackjack_continuation_view(self, last_bet: int, current_balance: int) -> discord.ui.View:
        """Create continuation view for blackjack with play again options"""
        view = discord.ui.View(timeout=300)
        
        # Same bet again (if balance allows)
        if current_balance >= last_bet:
            same_bet_btn = discord.ui.Button(
                label=f"🃏 Same Bet (${last_bet:,})",
                style=discord.ButtonStyle.primary,
                emoji="🔄"
            )
            same_bet_btn.callback = lambda i: self._blackjack_play_again(i, last_bet)
            view.add_item(same_bet_btn)
        
        # Double bet (if balance allows)
        double_bet = last_bet * 2
        if current_balance >= double_bet:
            double_bet_btn = discord.ui.Button(
                label=f"🔥 Double Bet (${double_bet:,})",
                style=discord.ButtonStyle.danger,
                emoji="⬆️"
            )
            double_bet_btn.callback = lambda i: self._blackjack_play_again(i, double_bet)
            view.add_item(double_bet_btn)
        
        # Half bet
        half_bet = max(100, last_bet // 2)
        if current_balance >= half_bet:
            half_bet_btn = discord.ui.Button(
                label=f"💰 Half Bet (${half_bet:,})",
                style=discord.ButtonStyle.secondary,
                emoji="⬇️"
            )
            half_bet_btn.callback = lambda i: self._blackjack_play_again(i, half_bet)
            view.add_item(half_bet_btn)
        
        # New bet amount
        new_bet_btn = discord.ui.Button(
            label="🎯 New Bet Amount",
            style=discord.ButtonStyle.secondary,
            emoji="🎲"
        )
        new_bet_btn.callback = self._blackjack_new_bet_modal
        view.add_item(new_bet_btn)
        
        # Exit game
        exit_btn = discord.ui.Button(
            label="🚪 Exit Game",
            style=discord.ButtonStyle.secondary,
            emoji="❌"
        )
        exit_btn.callback = self._exit_game
        view.add_item(exit_btn)
        
        return view

    async def _blackjack_play_again(self, interaction: discord.Interaction, bet: int):
        """Start a new blackjack game with specified bet"""
        try:
            game_data = {
                'bet': bet,
                'game_type': 'blackjack',
                'timestamp': datetime.now(timezone.utc)
            }
            await self._initialize_blackjack_game(interaction, bet, game_data)
        except Exception as e:
            logger.error(f"Blackjack play again failed: {e}")
            await interaction.response.send_message("❌ Failed to start new game. Please try again.", ephemeral=True)

    async def _blackjack_new_bet_modal(self, interaction: discord.Interaction):
        """Show modal for custom bet amount"""
        try:
            guild_id = interaction.guild.id
            discord_id = interaction.user.id
            wallet = await self.bot.db_manager.get_wallet(guild_id, discord_id)
            balance = wallet.get('balance', 0)
            
            modal = AdvancedModalSystem.create_bet_setup_modal("blackjack", balance)
            await interaction.response.send_modal(modal)
        except Exception as e:
            logger.error(f"Blackjack modal failed: {e}")
            await interaction.response.send_message("❌ Failed to open bet setup.", ephemeral=True)

    async def _exit_game(self, interaction: discord.Interaction):
        """Exit the game session"""
        try:
            embed_data = {
                'title': "🎰 GAME SESSION ENDED",
                'description': "Thanks for playing! Use `/gamble` to start a new session."
            }
            embed_data['embed_type'] = 'gambling'
            embed, gamble_file = await EmbedFactory.build('generic', embed_data)
            embed.color = 0x7f5af0
            
            view = discord.ui.View()  # Empty view
            
            gamble_file = discord.File('./assets/Gamble.png', filename='Gamble.png')
            await interaction.response.edit_message(embed=embed, file=gamble_file, view=view)
        except Exception as e:
            logger.error(f"Exit game failed: {e}")
            await interaction.response.send_message("❌ Failed to exit game.", ephemeral=True)

    async def _initialize_roulette_game(self, interaction: discord.Interaction, bet: int, game_data: Dict):
        """Initialize physics-based roulette game"""
        try:
            guild_id = interaction.guild.id
            discord_id = interaction.user.id

            # Validate bet amount
            wallet = await self.bot.db_manager.get_wallet(guild_id, discord_id)
            balance = wallet.get('balance', 0)

            if bet > balance:
                await interaction.response.send_message(f"❌ Insufficient funds! You have ${balance:,}", ephemeral=True)
                return

            # Get roulette choice from game_data or default to red
            choice = game_data.get('choice', 'red')

            # Deduct bet from wallet
            await self.bot.db_manager.update_wallet(guild_id, discord_id, -bet, "gambling_roulette")

            # Initialize roulette game state
            game_state = {
                'bet': bet,
                'choice': choice,
                'payout_multiplier': self._get_roulette_payout_multiplier(choice),
                'spin_complete': False
            }

            # Create roulette embed
            embed_data = {
                'title': "🎯 PHYSICS ROULETTE - AI ENHANCED",
                'description': f"**Bet:** ${bet:,}\n**Choice:** {choice.title()}\n**Physics Engine:** Active\n**Momentum Simulation:** Enabled\n\n🤖 **AI calculating optimal spin trajectory...**"
            }
            embed_data['embed_type'] = 'gambling'
            embed, gamble_file = await EmbedFactory.build('generic', embed_data)
            embed.color = 0x7f5af0

            # Add betting info
            payout_info = self._get_roulette_payout_info(choice)
            embed.add_field(
                name="🎯 Your Bet",
                value=f"```Choice: {choice.title()}\nPayout: {payout_info}\nPotential Win: ${int(bet * game_state['payout_multiplier']):,}```",
                inline=False
            )

            # Add roulette wheel layout
            wheel_layout = self._get_roulette_wheel_display()
            embed.add_field(
                name="🎰 Roulette Wheel",
                value=f"```{wheel_layout}```",
                inline=False
            )

            embed.set_footer(text="🚀 Ultimate AI Gaming Engine | Click SPIN to release the ball")

            # Create roulette view
            view = UltimateGamblingView(self, interaction, "roulette")
            view.current_bet = bet
            view.game_state = game_state

            gamble_file = discord.File('./assets/Gamble.png', filename='Gamble.png')
            if hasattr(interaction, 'response') and not interaction.response.is_done():
                await interaction.response.edit_message(embed=embed, file=gamble_file, view=view)
            else:
                await interaction.edit_original_response(embed=embed, file=gamble_file, view=view)

        except Exception as e:
            logger.error(f"Roulette init failed: {e}")
            if hasattr(interaction, 'response') and not interaction.response.is_done():
                await interaction.response.send_message("❌ Failed to start roulette game. Please try again.", ephemeral=True)
            else:
                await interaction.followup.send("❌ Failed to start roulette game. Please try again.", ephemeral=True)

    def _get_roulette_payout_multiplier(self, choice: str) -> float:
        """Get payout multiplier for roulette bet"""
        if choice.isdigit():
            return 36.0  # Straight number bet
        elif choice in ['red', 'black']:
            return 2.0  # Color bet
        elif choice in ['even', 'odd', 'low', 'high']:
            return 2.0  # Even money bets
        elif choice == 'green':
            return 36.0  # Green (0) bet
        else:
            return 2.0  # Default

    def _get_roulette_payout_info(self, choice: str) -> str:
        """Get payout info string for display"""
        if choice.isdigit():
            return "36:1 (Straight Number)"
        elif choice in ['red', 'black']:
            return "2:1 (Color)"
        elif choice in ['even', 'odd']:
            return "2:1 (Even/Odd)"
        elif choice in ['low', 'high']:
            return "2:1 (Low/High)"
        elif choice == 'green':
            return "36:1 (Green Zero)"
        else:
            return "2:1"

    def _get_roulette_wheel_display(self) -> str:
        """Get roulette wheel layout for display"""
        return """
      00  0   32  15  19  4   21  2   25  17  34  6   27  13  36  11  30  8   23  10  5   24  16  33  1   20  14  31  9   22  18  29  7   28  12  35  3   26
      G   G   R   B   R   B   R   B   R   B   R   B   R   B   R   B   R   B   R   B   R   B   R   B   R   B   R   B   R   B   R   B   R   B   R   B   R   B
        """

    async def _execute_roulette_spin(self, interaction: discord.Interaction, view: UltimateGamblingView):
        """Execute physics-based roulette spin with realistic animation"""
        try:
            await interaction.response.defer()

            game_state = view.game_state
            if game_state['spin_complete']:
                await interaction.edit_original_response(content="❌ Spin already completed!")
                return

            bet = game_state['bet']
            choice = game_state['choice']
            guild_id = interaction.guild.id
            discord_id = interaction.user.id

            # Physics-based spinning animation sequence
            animation_frames = [
                ("🎯 Ball released into the wheel...", 0x8b5cf6),
                ("🌀 Wheel spinning at maximum velocity...", 0xa855f7),
                ("⚡ Physics calculations in progress...", 0xc084fc),
                ("💫 Ball bouncing between pockets...", 0xd946ef),
                ("🎲 Momentum decreasing, final trajectory...", 0xec4899),
                ("🎯 Ball settling into position...", 0xf97316),
                ("✨ Final pocket determined...", 0xeab308),
                ("🏆 Spin complete - revealing result!", 0x22c55e)
            ]

            for i, (description, color) in enumerate(animation_frames):
                progress = (i + 1) / len(animation_frames)
                progress_bar = "█" * int(progress * 12) + "░" * int((1 - progress) * 12)

                embed_data = {
                    'title': "🎯 PHYSICS ROULETTE - SPINNING",
                    'description': f"**Bet:** ${bet:,}\n**Choice:** {choice.title()}\n\n{description}"
                }
                embed, gamble_file = await EmbedFactory.build('generic', embed_data)
                embed.color = color
                embed.set_thumbnail(url="attachment://Gamble.png")

                embed.add_field(
                    name="🌀 Spin Progress",
                    value=f"```[{progress_bar}] {progress*100:.0f}%```",
                    inline=False
                )

                embed.set_footer(text=f"🚀 Frame {i+1}/8 | Physics Engine Active")

                gamble_file = discord.File('./assets/Gamble.png', filename='Gamble.png')
                await interaction.edit_original_response(embed=embed, file=gamble_file, view=None)
                await asyncio.sleep(0.8)

            # Generate result using physics-based randomness
            result = self._generate_roulette_result(str(discord_id))
            winnings, win_type = self._calculate_roulette_payout(result, choice, bet)

            # Update wallet with winnings
            if winnings > 0:
                await self.bot.db_manager.update_wallet(guild_id, discord_id, winnings, "gambling_roulette")

            # Track in AI system
            ai_game_data = {
                'game_type': 'roulette',
                'bet': bet,
                'winnings': winnings,
                'choice': choice,
                'result': result,
                'win_type': win_type
            }

            ai_insights = self.ai_engine.analyze_player_behavior(str(discord_id), ai_game_data)

            # Get updated balance
            updated_wallet = await self.bot.db_manager.get_wallet(guild_id, discord_id)

            # Create result embed
            net_result = winnings - bet
            embed_color = 0x00d38a if winnings > 0 else 0xff5e5e

            # Special colors for number hits
            if result['number'] == 0:
                embed_color = 0x22c55e  # Green for zero
            elif win_type == 'number_hit':
                embed_color = 0xd946ef  # Purple for number hit

            embed_data = {
                'title': "🎯 ROULETTE RESULT - PHYSICS ANALYSIS COMPLETE"
            }
            embed, gamble_file = await EmbedFactory.build('generic', embed_data)
            embed.color = embed_color
            embed.set_thumbnail(url="attachment://Gamble.png")

            # Result display
            result_display = f"**Winning Number:** {result['number']} {result['color']}"
            if result['number'] != 0:
                result_display += f" ({'Even' if result['number'] % 2 == 0 else 'Odd'})"
            
            embed.add_field(
                name="🎲 Final Result",
                value=f"```{result_display}\nYour Bet: {choice.title()}\nResult: {'WIN' if winnings > 0 else 'LOSS'}```",
                inline=False
            )

            embed.add_field(
                name="💰 Payout Calculation",
                value=f"```Bet Amount: ${bet:,}\nWinnings: ${winnings:,}\nNet Result: ${net_result:,}```",
                inline=False
            )

            # AI insights
            recommendations = self.ai_engine.generate_personalized_recommendations(str(discord_id))
            if recommendations:
                ai_display = "\n".join([f"• {rec}" for rec in recommendations[:2]])
                embed.add_field(
                    name="🤖 AI Insights",
                    value=f"```{ai_display}```",
                    inline=False
                )

            # Contextual message
            context_key = win_type if winnings > 0 else 'loss'
            context_messages = self.contextual_messages['roulette'].get(context_key, ["The wheel has spoken!"])
            context_message = random.choice(context_messages)

            embed.add_field(
                name="📢 Wheel Master",
                value=f"```{context_message}```",
                inline=False
            )

            embed.set_footer(text=f"💰 Updated Balance: ${updated_wallet.get('balance', 0):,} | Ultimate AI Gaming Engine")

            # Mark spin as complete
            game_state['spin_complete'] = True

            # Create continuation view with play again options
            view = self._create_roulette_continuation_view(bet, choice, updated_wallet.get('balance', 0))

            gamble_file = discord.File('./assets/Gamble.png', filename='Gamble.png')
            await interaction.edit_original_response(embed=embed, file=gamble_file, view=view)

        except Exception as e:
            logger.error(f"Roulette spin failed: {e}")
            await interaction.edit_original_response(content="❌ Roulette spin failed. Please try again.")

    def _generate_roulette_result(self, user_id: str) -> Dict:
        """Generate roulette result with physics-based randomness"""
        try:
            # American roulette wheel (0, 00, 1-36)
            numbers = list(range(0, 37))  # 0-36 (treating 00 as 37 for simplicity)
            
            # Get AI profile for slight bias adjustments
            profile = self.ai_engine.player_profiles.get(user_id, {})
            risk_data = profile.get('ai_insights', {}).get('risk_assessment', {})
            risk_profile = risk_data.get('profile', 'moderate')
            
            # Slight bias based on risk profile (very subtle)
            weights = [1.0] * len(numbers)
            if risk_profile == 'high_roller':
                weights[0] *= 0.95  # Slightly less likely to hit 0
            elif risk_profile == 'conservative':
                weights[0] *= 1.05  # Slightly more likely to hit 0
            
            # Select number
            number = random.choices(numbers, weights=weights)[0]
            
            # Determine color
            if number == 0:
                color = "🟢"
            elif number in [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]:
                color = "🔴"
            else:
                color = "⚫"
            
            return {
                'number': number,
                'color': color,
                'is_even': number != 0 and number % 2 == 0,
                'is_red': color == "🔴",
                'is_black': color == "⚫",
                'is_green': color == "🟢"
            }
            
        except Exception as e:
            logger.error(f"Roulette result generation failed: {e}")
            return {'number': 0, 'color': "🟢", 'is_even': False, 'is_red': False, 'is_black': False, 'is_green': True}

    def _calculate_roulette_payout(self, result: Dict, choice: str, bet: int) -> Tuple[int, str]:
        """Calculate roulette payout based on result and choice"""
        try:
            number = result['number']
            
            # Check for exact number match
            if choice.isdigit() and int(choice) == number:
                return bet * 36, 'number_hit'
            
            # Check for color matches
            if choice == 'red' and result['is_red']:
                return bet * 2, 'color_win'
            elif choice == 'black' and result['is_black']:
                return bet * 2, 'color_win'
            elif choice == 'green' and result['is_green']:
                return bet * 36, 'number_hit'
            
            # Check for even/odd
            if choice == 'even' and result['is_even'] and number != 0:
                return bet * 2, 'color_win'
            elif choice == 'odd' and not result['is_even'] and number != 0:
                return bet * 2, 'color_win'
            
            # Check for low/high
            if choice == 'low' and 1 <= number <= 18:
                return bet * 2, 'color_win'
            elif choice == 'high' and 19 <= number <= 36:
                return bet * 2, 'color_win'
            
            # Near miss detection (for AI analysis)
            if choice.isdigit():
                target = int(choice)
                if abs(target - number) <= 3 and number != 0:
                    return 0, 'near_miss'
            
            return 0, 'loss'
            
        except Exception as e:
            logger.error(f"Roulette payout calculation failed: {e}")
            return 0, 'loss'

    def _create_roulette_continuation_view(self, last_bet: int, last_choice: str, current_balance: int) -> discord.ui.View:
        """Create continuation view for roulette with play again options"""
        view = discord.ui.View(timeout=300)
        
        # Same bet and choice again (if balance allows)
        if current_balance >= last_bet:
            same_bet_btn = discord.ui.Button(
                label=f"🎯 Same Bet (${last_bet:,} on {last_choice.title()})",
                style=discord.ButtonStyle.primary,
                emoji="🔄"
            )
            same_bet_btn.callback = lambda i: self._roulette_play_again(i, last_bet, last_choice)
            view.add_item(same_bet_btn)
        
        # Double bet same choice (if balance allows)
        double_bet = last_bet * 2
        if current_balance >= double_bet:
            double_bet_btn = discord.ui.Button(
                label=f"🔥 Double Bet (${double_bet:,} on {last_choice.title()})",
                style=discord.ButtonStyle.danger,
                emoji="⬆️"
            )
            double_bet_btn.callback = lambda i: self._roulette_play_again(i, double_bet, last_choice)
            view.add_item(double_bet_btn)
        
        # Change choice same bet
        if current_balance >= last_bet:
            change_choice_btn = discord.ui.Button(
                label=f"🎲 Change Choice (${last_bet:,})",
                style=discord.ButtonStyle.secondary,
                emoji="🔄"
            )
            change_choice_btn.callback = lambda i: self._roulette_change_choice_modal(i, last_bet)
            view.add_item(change_choice_btn)
        
        # New bet and choice
        new_bet_btn = discord.ui.Button(
            label="🎯 New Bet & Choice",
            style=discord.ButtonStyle.secondary,
            emoji="🎰"
        )
        new_bet_btn.callback = self._roulette_new_bet_modal
        view.add_item(new_bet_btn)
        
        # Exit game
        exit_btn = discord.ui.Button(
            label="🚪 Exit Game",
            style=discord.ButtonStyle.secondary,
            emoji="❌"
        )
        exit_btn.callback = self._exit_game
        view.add_item(exit_btn)
        
        return view

    async def _roulette_play_again(self, interaction: discord.Interaction, bet: int, choice: str):
        """Start a new roulette game with specified bet and choice"""
        try:
            game_data = {
                'bet': bet,
                'choice': choice,
                'game_type': 'roulette',
                'timestamp': datetime.now(timezone.utc)
            }
            await self._initialize_roulette_game(interaction, bet, game_data)
        except Exception as e:
            logger.error(f"Roulette play again failed: {e}")
            await interaction.response.send_message("❌ Failed to start new game. Please try again.", ephemeral=True)

    async def _roulette_change_choice_modal(self, interaction: discord.Interaction, bet: int):
        """Show modal for changing roulette choice with same bet"""
        try:
            class RouletteChoiceModal(discord.ui.Modal):
                def __init__(self, bet_amount: int):
                    super().__init__(title=f"🎯 Change Roulette Choice (${bet_amount:,})")
                    self.bet_amount = bet_amount

                    self.choice_input = discord.ui.TextInput(
                        label="🎯 New Roulette Choice",
                        placeholder="red/black/even/odd/low/high or number 0-36",
                        min_length=1,
                        max_length=20,
                        style=discord.TextStyle.short
                    )
                    self.add_item(self.choice_input)

                async def on_submit(self, modal_interaction: discord.Interaction):
                    try:
                        choice = self.choice_input.value.strip().lower()
                        valid_choices = {'red', 'black', 'green', 'even', 'odd', 'low', 'high'}
                        is_number = choice.isdigit() and 0 <= int(choice) <= 36

                        if choice not in valid_choices and not is_number:
                            await modal_interaction.response.send_message("❌ Invalid roulette choice!", ephemeral=True)
                            return

                        game_data = {
                            'bet': self.bet_amount,
                            'choice': choice,
                            'game_type': 'roulette',
                            'timestamp': datetime.now(timezone.utc)
                        }
                        
                        gambling_cog = modal_interaction.client.get_cog('Gambling')
                        await gambling_cog._initialize_roulette_game(modal_interaction, self.bet_amount, game_data)

                    except Exception as e:
                        logger.error(f"Choice modal submission error: {e}")
                        await modal_interaction.response.send_message("❌ Failed to change choice. Please try again.", ephemeral=True)

            modal = RouletteChoiceModal(bet)
            await interaction.response.send_modal(modal)
        except Exception as e:
            logger.error(f"Roulette choice modal failed: {e}")
            await interaction.response.send_message("❌ Failed to open choice setup.", ephemeral=True)

    async def _roulette_new_bet_modal(self, interaction: discord.Interaction):
        """Show modal for new bet amount and choice"""
        try:
            guild_id = interaction.guild.id
            discord_id = interaction.user.id
            wallet = await self.bot.db_manager.get_wallet(guild_id, discord_id)
            balance = wallet.get('balance', 0)
            
            modal = AdvancedModalSystem.create_bet_setup_modal("roulette", balance)
            await interaction.response.send_modal(modal)
        except Exception as e:
            logger.error(f"Roulette modal failed: {e}")
            await interaction.response.send_message("❌ Failed to open bet setup.", ephemeral=True)

    async def _show_analytics_dashboard(self, interaction: discord.Interaction):
        """Display analytics dashboard"""
        try:
            user_id = str(interaction.user.id)
            profile = self.ai_engine.player_profiles.get(user_id, {})

            if not profile:
                await interaction.response.send_message("📊 No data available yet. Play some games to unlock AI insights!", ephemeral=True)
                return

            insights = profile.get('ai_insights', {})

            # Basic stats
            total_games = profile.get('total_games', 0)
            total_wagered = profile.get('total_wagered', 0)
            total_winnings = profile.get('total_winnings', 0)
            net_profit = total_winnings - total_wagered

            # Risk profile display
            risk_data = insights.get('risk_assessment', {})
            risk_profile = risk_data.get('profile', 'unknown').title()
            risk_score = risk_data.get('score', 0)
            win_rate = risk_data.get('win_rate', 0)

            # Betting pattern display
            pattern_data = insights.get('pattern_recognition', {})
            betting_pattern = pattern_data.get('pattern', 'unknown').title()
            avg_bet = pattern_data.get('avg_bet', 0)
            bet_trend = pattern_data.get('trend', 0)

            # Session behavior display
            session_data = insights.get('session_analysis', {})
            session_behavior = session_data.get('behavior', 'unknown').title()
            session_length = session_data.get('session_length', 0)
            session_result = session_data.get('net_result', 0)

            # Predictive modeling display
            prediction_data = insights.get('predictive_modeling', {})
            prediction = prediction_data.get('prediction', 'unknown').title()
            confidence = prediction_data.get('confidence', 0)

            # Personalized recommendations
            recommendations = self.ai_engine.generate_personalized_recommendations(user_id)
            recommendation_display = "\n".join([f"• {rec}" for rec in recommendations]) if recommendations else "No recommendations available."

            # Create analytics embed
            embed_data = {
                'title': "📊 AI GAMBLING ANALYTICS DASHBOARD",
                'description': f"🤖 **AI-Powered Insights for Strategic Play**\n\n💎 **Basic Stats:**\n```Total Games: {total_games}\nWagered: ${total_wagered:,}\nWinnings: ${total_winnings:,}\nNet Profit: ${net_profit:,}```\n",
            }
            embed_data['embed_type'] = 'gambling'
            embed, gamble_file = await EmbedFactory.build('generic', embed_data)
            embed.color = 0x7f5af0

            embed.add_field(
                name="🛡️ Risk Profile",
                value=f"```Profile: {risk_profile}\nScore: {risk_score:.1f}\nWin Rate: {win_rate:.2%}```",
                inline=True
            )

            embed.add_field(
                name="📈 Betting Pattern",
                value=f"```Pattern: {betting_pattern}\nAvg Bet: ${avg_bet:.0f}\nTrend: {bet_trend:.2f}```",
                inline=True
            )

            embed.add_field(
                name="Session Behavior",
                value=f"```Behavior: {session_behavior}\nLength: {session_length} games\nResult: ${session_result:,}```",
                inline=False
            )

            embed.add_field(
                name="🔮 Predictive Modeling",
                value=f"```Prediction: {prediction}\nConfidence: {confidence:.1%}```",
                inline=False
            )

            embed.add_field(
                name="🤖 Personalized Recommendations",
                value=f"```{recommendation_display}```",
                inline=False
            )

            await interaction.response.send_message(embed=embed, file=gamble_file, ephemeral=True)

        except Exception as e:
            logger.error(f"Analytics dashboard failed: {e}")
            await interaction.response.send_message("❌ Failed to load analytics dashboard.", ephemeral=True)


def setup(bot):
    """Load the gambling cog"""
    bot.add_cog(Gambling(bot))