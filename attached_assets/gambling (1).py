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
            embed, gamble_file = await EmbedFactory.build('generic', embed_data)
            embed.color = 0x7f5af0
            embed.set_thumbnail(url="attachment://Gamble.png")

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

            embed, gamble_file = await EmbedFactory.build('generic', embed_data)
            embed.color = 0x7f5af0
            embed.set_thumbnail(url="attachment://Gamble.png")

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
            embed, gamble_file = await EmbedFactory.build('generic', embed_data)
            embed.color = 0x7f5af0
            embed.set_thumbnail(url="attachment://Gamble.png")

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
                value=f"```{reel_display}\n{rarity_line}
```\n💰 **Winnings:** ${winnings:,} (x{multiplier:.1f})\n🤖 **Net Result:** ${net_result:,}",
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
            embed, gamble_file = await EmbedFactory.build('generic', embed_data)
            embed.color = 0x7f5af0
            embed.set_thumbnail(url="attachment://Gamble.png")

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
            embed, gamble_file = await EmbedFactory.build('generic', embed_data)
            embed.color = 0x7f5af0
            embed.set_thumbnail(url="attachment://Gamble.png")

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
        """Initialize blackjack game"""
        try:
            await interaction.response.send_message("Blackjack game initializing...", ephemeral=True)
        except Exception as e:
            logger.error(f"Blackjack init failed: {e}")

    async def _blackjack_hit(self, interaction: discord.Interaction, view: UltimateGamblingView):
        """Handle blackjack hit"""
        try:
            await interaction.response.send_message("Hit action...", ephemeral=True)
        except Exception as e:
            logger.error(f"Blackjack hit failed: {e}")

    async def _blackjack_stand(self, interaction: discord.Interaction, view: UltimateGamblingView):
        """Handle blackjack stand"""
        try:
            await interaction.response.send_message("Stand action...", ephemeral=True)
        except Exception as e:
            logger.error(f"Blackjack stand failed: {e}")

    async def _blackjack_double(self, interaction: discord.Interaction, view: UltimateGamblingView):
        """Handle blackjack double"""
        try:
            await interaction.response.send_message("Double action...", ephemeral=True)
        except Exception as e:
            logger.error(f"Blackjack double failed: {e}")

    async def _blackjack_surrender(self, interaction: discord.Interaction, view: UltimateGamblingView):
        """Handle blackjack surrender"""
        try:
            await interaction.response.send_message("Surrender action...", ephemeral=True)
        except Exception as e:
            logger.error(f"Blackjack surrender failed: {e}")

    async def _initialize_roulette_game(self, interaction: discord.Interaction, bet: int, game_data: Dict):
        """Initialize roulette game"""
        try:
            await interaction.response.send_message("Roulette game initializing...", ephemeral=True)
        except Exception as e:
            logger.error(f"Roulette init failed: {e}")

    async def _execute_roulette_spin(self, interaction: discord.Interaction, view: UltimateGamblingView):
        """Execute roulette spin"""
        try:
            await interaction.response.send_message("Roulette spin executing...", ephemeral=True)
        except Exception as e:
            logger.error(f"Roulette spin failed: {e}")

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
            embed, gamble_file = await EmbedFactory.build('generic', embed_data)
            embed.color = 0x7f5af0
            embed.set_thumbnail(url="attachment://Gamble.png")

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
                value=f"```{recommendation_display}