"""
Advanced py-cord 2.6.1 UI Components - Phase 2: Interactive System
Complete modal forms, button matrices, and select menus for premium user experience
"""

import discord
from discord.ext import commands
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)

# ===== MODAL FORMS =====

class PlayerLinkingModal(discord.Modal):
    """Advanced character linking with validation and main/alt selection"""
    
    def __init__(self, bot, guild_id: int, existing_characters: List[str] = None):
        super().__init__(title="🔗 Link Gaming Character")
        self.bot = bot
        self.guild_id = guild_id
        self.existing_characters = existing_characters or []
        
        self.character_name = discord.InputText(
            label="Character Name",
            placeholder="Enter your exact in-game character name...",
            style=discord.InputTextStyle.short,
            max_length=50,
            required=True
        )
        
        self.character_type = discord.InputText(
            label="Character Type",
            placeholder="Type 'main' for main character or 'alt' for alternate",
            style=discord.InputTextStyle.short,
            value="main" if not self.existing_characters else "alt",
            max_length=10,
            required=True
        )
        
        self.add_item(self.character_name)
        self.add_item(self.character_type)
    
    async def callback(self, interaction: discord.Interaction):
        """Process character linking with validation"""
        try:
            character_name = self.character_name.value.strip()
            char_type = self.character_type.value.strip().lower()
            
            # Validation
            if not character_name:
                await interaction.response.send_message(
                    "❌ Character name cannot be empty!", ephemeral=True
                )
                return
            
            if char_type not in ["main", "alt"]:
                await interaction.response.send_message(
                    "❌ Character type must be 'main' or 'alt'!", ephemeral=True
                )
                return
            
            if character_name in self.existing_characters:
                await interaction.response.send_message(
                    "❌ This character is already linked to your account!", ephemeral=True
                )
                return
            
            # Link character
            is_main = char_type == "main"
            success = await self.bot.db_manager.link_character_to_player(
                self.guild_id, interaction.user.id, character_name, is_main
            )
            
            if success:
                embed = discord.Embed(
                    title="✅ Character Linked Successfully",
                    description=f"**{character_name}** has been linked as your {'main' if is_main else 'alt'} character.",
                    color=0x00FF00,
                    timestamp=datetime.now(timezone.utc)
                )
                
                embed.add_field(
                    name="Character Info",
                    value=f"• Name: **{character_name}**\n• Type: **{char_type.title()}**\n• Linked by: {interaction.user.mention}",
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(
                    "❌ Failed to link character. Please try again later.", ephemeral=True
                )
                
        except Exception as e:
            logger.error(f"Character linking failed: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while linking your character.", ephemeral=True
            )

class FactionCreationModal(discord.Modal):
    """Advanced faction creation with customization options"""
    
    def __init__(self, bot, guild_id: int):
        super().__init__(title="🏛️ Create New Faction")
        self.bot = bot
        self.guild_id = guild_id
        
        self.faction_name = discord.InputText(
            label="Faction Name",
            placeholder="Enter a unique faction name...",
            style=discord.InputTextStyle.short,
            max_length=32,
            required=True
        )
        
        self.faction_description = discord.InputText(
            label="Faction Description",
            placeholder="Describe your faction's purpose and goals...",
            style=discord.InputTextStyle.long,
            max_length=500,
            required=False
        )
        
        self.add_item(self.faction_name)
        self.add_item(self.faction_description)
    
    async def callback(self, interaction: discord.Interaction):
        """Process faction creation"""
        try:
            faction_name = self.faction_name.value.strip()
            description = self.faction_description.value.strip() or f"The {faction_name} faction"
            
            # Validation
            if not faction_name:
                await interaction.response.send_message(
                    "❌ Faction name cannot be empty!", ephemeral=True
                )
                return
            
            if len(faction_name) < 3:
                await interaction.response.send_message(
                    "❌ Faction name must be at least 3 characters long!", ephemeral=True
                )
                return
            
            # Check if faction name already exists
            existing_faction = await self.bot.db_manager.factions.find_one({
                "guild_id": self.guild_id,
                "name": {"$regex": f"^{faction_name}$", "$options": "i"}
            })
            
            if existing_faction:
                await interaction.response.send_message(
                    "❌ A faction with this name already exists!", ephemeral=True
                )
                return
            
            # Create faction
            faction_id = await self.bot.db_manager.create_faction(
                self.guild_id, faction_name, interaction.user.id, description
            )
            
            if faction_id:
                embed = discord.Embed(
                    title="🏛️ Faction Created Successfully",
                    description=f"**{faction_name}** has been established!",
                    color=0x3498DB,
                    timestamp=datetime.now(timezone.utc)
                )
                
                embed.add_field(
                    name="Faction Details",
                    value=f"• Name: **{faction_name}**\n• Leader: {interaction.user.mention}\n• Members: **1**\n• Treasury: **0 Credits**",
                    inline=False
                )
                
                embed.add_field(
                    name="Description",
                    value=description,
                    inline=False
                )
                
                embed.set_footer(text=f"Faction ID: {faction_id}")
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(
                    "❌ Failed to create faction. Please try again later.", ephemeral=True
                )
                
        except Exception as e:
            logger.error(f"Faction creation failed: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while creating your faction.", ephemeral=True
            )

class EconomyConfigModal(discord.Modal):
    """Advanced economy configuration for administrators"""
    
    def __init__(self, bot, guild_id: int, current_config: Dict[str, Any]):
        super().__init__(title="💰 Economy Configuration")
        self.bot = bot
        self.guild_id = guild_id
        self.current_config = current_config
        
        self.currency_name = discord.InputText(
            label="Currency Name",
            placeholder="e.g., Credits, Gold, Points",
            style=discord.InputTextStyle.short,
            value=current_config.get('currency_name', 'Credits'),
            max_length=20,
            required=True
        )
        
        self.currency_symbol = discord.InputText(
            label="Currency Symbol/Emoji",
            placeholder="e.g., 💎, $, €, ⚡",
            style=discord.InputTextStyle.short,
            value=current_config.get('currency_symbol', '💎'),
            max_length=10,
            required=True
        )
        
        self.base_kill_reward = discord.InputText(
            label="Base Kill Reward",
            placeholder="Amount earned per kill (e.g., 100)",
            style=discord.InputTextStyle.short,
            value=str(current_config.get('kill_rewards', {}).get('base_kill', 100)),
            max_length=10,
            required=True
        )
        
        self.casino_max_bet = discord.InputText(
            label="Maximum Casino Bet",
            placeholder="Maximum amount for casino games",
            style=discord.InputTextStyle.short,
            value=str(current_config.get('betting_limits', {}).get('casino_max', 10000)),
            max_length=10,
            required=True
        )
        
        self.add_item(self.currency_name)
        self.add_item(self.currency_symbol)
        self.add_item(self.base_kill_reward)
        self.add_item(self.casino_max_bet)
    
    async def callback(self, interaction: discord.Interaction):
        """Process economy configuration update"""
        try:
            # Validate inputs
            try:
                base_kill = int(self.base_kill_reward.value)
                max_bet = int(self.casino_max_bet.value)
                
                if base_kill < 0 or max_bet < 0:
                    raise ValueError("Values must be positive")
                    
            except ValueError:
                await interaction.response.send_message(
                    "❌ Kill reward and casino max bet must be positive numbers!", ephemeral=True
                )
                return
            
            # Update configuration
            update_data = {
                "$set": {
                    "currency_name": self.currency_name.value.strip(),
                    "currency_symbol": self.currency_symbol.value.strip(),
                    "kill_rewards.base_kill": base_kill,
                    "betting_limits.casino_max": max_bet
                }
            }
            
            result = await self.bot.db_manager.economy_config.update_one(
                {"guild_id": self.guild_id},
                update_data,
                upsert=True
            )
            
            if result:
                embed = discord.Embed(
                    title="✅ Economy Configuration Updated",
                    description="Your server's economy settings have been updated successfully!",
                    color=0x00FF00,
                    timestamp=datetime.now(timezone.utc)
                )
                
                embed.add_field(
                    name="Updated Settings",
                    value=f"• Currency: **{self.currency_name.value}** {self.currency_symbol.value}\n• Kill Reward: **{base_kill:,}**\n• Max Casino Bet: **{max_bet:,}**",
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(
                    "❌ Failed to update economy configuration.", ephemeral=True
                )
                
        except Exception as e:
            logger.error(f"Economy config update failed: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while updating the economy configuration.", ephemeral=True
            )

class BountyCreationModal(discord.Modal):
    """Advanced bounty creation with threat assessment"""
    
    def __init__(self, bot, guild_id: int, max_bounty: int, currency_symbol: str):
        super().__init__(title="🎯 Create Bounty Contract")
        self.bot = bot
        self.guild_id = guild_id
        self.max_bounty = max_bounty
        self.currency_symbol = currency_symbol
        
        self.target_player = discord.InputText(
            label="Target Player Name",
            placeholder="Enter the exact player name...",
            style=discord.InputTextStyle.short,
            max_length=50,
            required=True
        )
        
        self.bounty_amount = discord.InputText(
            label="Bounty Amount",
            placeholder=f"Amount (1 - {max_bounty:,})",
            style=discord.InputTextStyle.short,
            max_length=15,
            required=True
        )
        
        self.bounty_reason = discord.InputText(
            label="Bounty Reason (Optional)",
            placeholder="Why is this bounty being placed?",
            style=discord.InputTextStyle.long,
            max_length=200,
            required=False
        )
        
        self.add_item(self.target_player)
        self.add_item(self.bounty_amount)
        self.add_item(self.bounty_reason)
    
    async def callback(self, interaction: discord.Interaction):
        """Process bounty creation"""
        try:
            target_name = self.target_player.value.strip()
            reason = self.bounty_reason.value.strip() or "No reason specified"
            
            # Validate bounty amount
            try:
                amount = int(self.bounty_amount.value.replace(",", ""))
                if amount <= 0 or amount > self.max_bounty:
                    raise ValueError("Invalid amount")
            except ValueError:
                await interaction.response.send_message(
                    f"❌ Bounty amount must be between 1 and {self.max_bounty:,}!", ephemeral=True
                )
                return
            
            # Check if target exists in database
            target_stats = await self.bot.db_manager.pvp_data.find_one({
                "guild_id": self.guild_id,
                "player_name": target_name
            })
            
            if not target_stats:
                await interaction.response.send_message(
                    f"❌ Player '{target_name}' not found in database!", ephemeral=True
                )
                return
            
            # Check user's balance
            user_data = await self.bot.db_manager.players.find_one({
                "guild_id": self.guild_id,
                "discord_id": interaction.user.id
            })
            
            current_balance = user_data.get("wallet_balance", 0) if user_data else 0
            if current_balance < amount:
                await interaction.response.send_message(
                    f"❌ Insufficient funds! You have {current_balance:,} {self.currency_symbol}, need {amount:,} {self.currency_symbol}",
                    ephemeral=True
                )
                return
            
            # Create bounty
            bounty_doc = {
                "guild_id": self.guild_id,
                "target_player": target_name,
                "creator_id": interaction.user.id,
                "amount": amount,
                "reason": reason,
                "status": "active",
                "created_at": datetime.now(timezone.utc),
                "expires_at": datetime.now(timezone.utc).replace(hour=23, minute=59, second=59) + timedelta(days=7)
            }
            
            await self.bot.db_manager.bounties.insert_one(bounty_doc)
            
            # Deduct amount from creator's balance
            await self.bot.db_manager.update_player_balance(
                self.guild_id, interaction.user.id, -amount, f"Bounty placed on {target_name}"
            )
            
            embed = discord.Embed(
                title="🎯 Bounty Contract Created",
                description=f"A bounty has been placed on **{target_name}**!",
                color=0xFF4500,
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(
                name="Contract Details",
                value=f"• Target: **{target_name}**\n• Reward: **{amount:,}** {self.currency_symbol}\n• Posted by: {interaction.user.mention}",
                inline=False
            )
            
            embed.add_field(
                name="Reason",
                value=reason,
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Bounty creation failed: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while creating the bounty.", ephemeral=True
            )

class CasinoBetModal(discord.Modal):
    """Casino betting modal with game-specific options"""
    
    def __init__(self, game_type: str, max_bet: int, currency_symbol: str):
        super().__init__(title=f"🎰 {game_type.title()} - Place Bet")
        self.game_type = game_type
        self.max_bet = max_bet
        self.currency_symbol = currency_symbol
        
        self.bet_amount = discord.InputText(
            label="Bet Amount",
            placeholder=f"Enter amount (1 - {max_bet:,})",
            style=discord.InputTextStyle.short,
            max_length=15,
            required=True
        )
        
        self.add_item(self.bet_amount)
        
        if game_type == "roulette":
            self.bet_type = discord.InputText(
                label="Bet Type",
                placeholder="red, black, even, odd, or specific number (0-36)",
                style=discord.InputTextStyle.short,
                max_length=10,
                required=True
            )
            self.add_item(self.bet_type)
    
    async def callback(self, interaction: discord.Interaction):
        """Process casino bet - this will be handled by the casino cog"""
        # This modal's callback will be overridden by the casino system
        pass

# ===== BUTTON MATRICES =====

class StatsNavigationView(discord.View):
    """Advanced statistics navigation with comprehensive button matrix"""
    
    def __init__(self, bot, player_data: Dict[str, Any], servers: List[Dict], current_server_idx: int = 0):
        super().__init__(timeout=300)
        self.bot = bot
        self.player_data = player_data
        self.servers = servers
        self.current_server_idx = current_server_idx
        self.current_view = "overview"
        
        # Initialize navigation buttons
        self._setup_navigation_buttons()
        self._setup_view_buttons()
        self._setup_server_buttons()
    
    def _setup_navigation_buttons(self):
        """Setup main navigation buttons"""
        # Row 0: View Selection
        overview_btn = discord.ui.Button(
            label="📊 Overview", 
            style=discord.ButtonStyle.primary if self.current_view == "overview" else discord.ButtonStyle.secondary,
            row=0
        )
        overview_btn.callback = self._create_view_callback("overview")
        self.add_item(overview_btn)
        
        weapons_btn = discord.ui.Button(
            label="🔫 Weapons", 
            style=discord.ButtonStyle.primary if self.current_view == "weapons" else discord.ButtonStyle.secondary,
            row=0
        )
        weapons_btn.callback = self._create_view_callback("weapons")
        self.add_item(weapons_btn)
        
        platforms_btn = discord.ui.Button(
            label="🎮 Platforms", 
            style=discord.ButtonStyle.primary if self.current_view == "platforms" else discord.ButtonStyle.secondary,
            row=0
        )
        platforms_btn.callback = self._create_view_callback("platforms")
        self.add_item(platforms_btn)
        
        achievements_btn = discord.ui.Button(
            label="🏆 Achievements", 
            style=discord.ButtonStyle.primary if self.current_view == "achievements" else discord.ButtonStyle.secondary,
            row=0
        )
        achievements_btn.callback = self._create_view_callback("achievements")
        self.add_item(achievements_btn)
    
    def _setup_view_buttons(self):
        """Setup view-specific action buttons"""
        # Row 1: Actions
        compare_btn = discord.ui.Button(
            label="⚔️ Compare",
            style=discord.ButtonStyle.secondary,
            row=1
        )
        compare_btn.callback = self._compare_callback
        self.add_item(compare_btn)
        
        refresh_btn = discord.ui.Button(
            label="🔄 Refresh",
            style=discord.ButtonStyle.secondary,
            row=1
        )
        refresh_btn.callback = self._refresh_callback
        self.add_item(refresh_btn)
        
        export_btn = discord.ui.Button(
            label="📊 Export",
            style=discord.ButtonStyle.secondary,
            row=1
        )
        export_btn.callback = self._export_callback
        self.add_item(export_btn)
    
    def _setup_server_buttons(self):
        """Setup server navigation buttons"""
        if len(self.servers) > 1:
            # Row 2: Server Navigation
            prev_btn = discord.ui.Button(
                label="◀️ Previous Server",
                style=discord.ButtonStyle.grey,
                row=2,
                disabled=self.current_server_idx == 0
            )
            prev_btn.callback = self._prev_server_callback
            self.add_item(prev_btn)
            
            current_server = self.servers[self.current_server_idx]
            server_btn = discord.ui.Button(
                label=f"🖥️ {current_server.get('name', 'Unknown')}",
                style=discord.ButtonStyle.success,
                row=2,
                disabled=True
            )
            self.add_item(server_btn)
            
            next_btn = discord.ui.Button(
                label="▶️ Next Server",
                style=discord.ButtonStyle.grey,
                row=2,
                disabled=self.current_server_idx >= len(self.servers) - 1
            )
            next_btn.callback = self._next_server_callback
            self.add_item(next_btn)
    
    def _create_view_callback(self, view_name: str):
        """Create callback for view change"""
        async def callback(interaction: discord.Interaction):
            self.current_view = view_name
            await self._update_display(interaction)
        return callback
    
    async def _compare_callback(self, interaction: discord.Interaction):
        """Handle compare button"""
        await interaction.response.send_message(
            "🔍 Player comparison feature coming soon!", ephemeral=True
        )
    
    async def _refresh_callback(self, interaction: discord.Interaction):
        """Handle refresh button"""
        await interaction.response.send_message(
            "🔄 Refreshing player statistics...", ephemeral=True
        )
    
    async def _export_callback(self, interaction: discord.Interaction):
        """Handle export button"""
        await interaction.response.send_message(
            "📊 Statistics export feature coming soon!", ephemeral=True
        )
    
    async def _prev_server_callback(self, interaction: discord.Interaction):
        """Handle previous server button"""
        if self.current_server_idx > 0:
            self.current_server_idx -= 1
            await self._update_display(interaction)
    
    async def _next_server_callback(self, interaction: discord.Interaction):
        """Handle next server button"""
        if self.current_server_idx < len(self.servers) - 1:
            self.current_server_idx += 1
            await self._update_display(interaction)
    
    async def _update_display(self, interaction: discord.Interaction):
        """Update the statistics display"""
        # This will be implemented with the embed factory integration
        await interaction.response.defer()

class LeaderboardView(discord.View):
    """Advanced leaderboard with filtering and navigation"""
    
    def __init__(self, bot, leaderboard_data: Dict[str, Any], guild_id: int):
        super().__init__(timeout=300)
        self.bot = bot
        self.leaderboard_data = leaderboard_data
        self.guild_id = guild_id
        self.current_type = "kills"
        self.current_platform = "all"
        self.current_page = 0
        self.page_size = 10
        
        self._setup_leaderboard_controls()
    
    def _setup_leaderboard_controls(self):
        """Setup leaderboard control elements"""
        # Type selection (Row 0)
        type_select = discord.ui.Select(
            placeholder="Choose leaderboard type...",
            options=[
                discord.SelectOption(label="🔥 Kill Leaders", value="kills", emoji="🔥"),
                discord.SelectOption(label="💀 K/D Masters", value="kd", emoji="💀"),
                discord.SelectOption(label="🎯 Distance Kings", value="distance", emoji="🎯"),
                discord.SelectOption(label="⚡ Streak Legends", value="streak", emoji="⚡"),
                discord.SelectOption(label="🏅 Weapon Masters", value="weapons", emoji="🏅")
            ],
            row=0
        )
        type_select.callback = self._type_select_callback
        self.add_item(type_select)
        
        # Platform filter (Row 1)
        platform_select = discord.ui.Select(
            placeholder="Filter by platform...",
            options=[
                discord.SelectOption(label="🖥️ All Platforms", value="all", emoji="🖥️"),
                discord.SelectOption(label="💻 PC Only", value="PC", emoji="💻"),
                discord.SelectOption(label="🎮 Xbox Only", value="Xbox", emoji="🎮"),
                discord.SelectOption(label="🕹️ PS5 Only", value="PS5", emoji="🕹️")
            ],
            row=1
        )
        platform_select.callback = self._platform_select_callback
        self.add_item(platform_select)
        
        # Navigation buttons (Row 2)
        prev_btn = discord.ui.Button(
            label="◀️ Previous",
            style=discord.ButtonStyle.grey,
            row=2,
            disabled=self.current_page == 0
        )
        prev_btn.callback = self._prev_page_callback
        self.add_item(prev_btn)
        
        refresh_btn = discord.ui.Button(
            label="🔄 Refresh",
            style=discord.ButtonStyle.primary,
            row=2
        )
        refresh_btn.callback = self._refresh_callback
        self.add_item(refresh_btn)
        
        next_btn = discord.ui.Button(
            label="▶️ Next",
            style=discord.ButtonStyle.grey,
            row=2
        )
        next_btn.callback = self._next_page_callback
        self.add_item(next_btn)
    
    async def _type_select_callback(self, interaction: discord.Interaction):
        """Handle leaderboard type selection"""
        self.current_type = interaction.data["values"][0]
        self.current_page = 0
        await self._update_leaderboard(interaction)
    
    async def _platform_select_callback(self, interaction: discord.Interaction):
        """Handle platform filter selection"""
        self.current_platform = interaction.data["values"][0]
        self.current_page = 0
        await self._update_leaderboard(interaction)
    
    async def _prev_page_callback(self, interaction: discord.Interaction):
        """Handle previous page button"""
        if self.current_page > 0:
            self.current_page -= 1
            await self._update_leaderboard(interaction)
    
    async def _next_page_callback(self, interaction: discord.Interaction):
        """Handle next page button"""
        self.current_page += 1
        await self._update_leaderboard(interaction)
    
    async def _refresh_callback(self, interaction: discord.Interaction):
        """Handle refresh button"""
        await self._update_leaderboard(interaction)
    
    async def _update_leaderboard(self, interaction: discord.Interaction):
        """Update leaderboard display"""
        # This will be implemented with the embed factory integration
        await interaction.response.defer()

class CasinoGameView(discord.View):
    """Advanced casino interface with game selection matrix"""
    
    def __init__(self, bot, user_balance: int, betting_limits: Dict[str, int], currency_symbol: str):
        super().__init__(timeout=300)
        self.bot = bot
        self.user_balance = user_balance
        self.betting_limits = betting_limits
        self.currency_symbol = currency_symbol
        
        self._setup_game_buttons()
        self._setup_info_buttons()
    
    def _setup_game_buttons(self):
        """Setup casino game buttons"""
        # Row 0: Main Games
        slots_btn = discord.ui.Button(
            label="🎰 Slots",
            style=discord.ButtonStyle.primary,
            emoji="🎰",
            row=0
        )
        slots_btn.callback = self._create_game_callback("slots")
        self.add_item(slots_btn)
        
        blackjack_btn = discord.ui.Button(
            label="🃏 Blackjack",
            style=discord.ButtonStyle.primary,
            emoji="🃏",
            row=0
        )
        blackjack_btn.callback = self._create_game_callback("blackjack")
        self.add_item(blackjack_btn)
        
        roulette_btn = discord.ui.Button(
            label="🎲 Roulette",
            style=discord.ButtonStyle.primary,
            emoji="🎲",
            row=0
        )
        roulette_btn.callback = self._create_game_callback("roulette")
        self.add_item(roulette_btn)
        
        poker_btn = discord.ui.Button(
            label="🎴 Poker",
            style=discord.ButtonStyle.primary,
            emoji="🎴",
            row=0,
            disabled=True  # Coming soon
        )
        self.add_item(poker_btn)
    
    def _setup_info_buttons(self):
        """Setup information and utility buttons"""
        # Row 1: Info & Utils
        balance_btn = discord.ui.Button(
            label="💰 Balance",
            style=discord.ButtonStyle.secondary,
            emoji="💰",
            row=1
        )
        balance_btn.callback = self._balance_callback
        self.add_item(balance_btn)
        
        leaderboard_btn = discord.ui.Button(
            label="🏆 Leaderboard",
            style=discord.ButtonStyle.secondary,
            emoji="🏆",
            row=1
        )
        leaderboard_btn.callback = self._leaderboard_callback
        self.add_item(leaderboard_btn)
        
        rules_btn = discord.ui.Button(
            label="📖 Rules",
            style=discord.ButtonStyle.secondary,
            emoji="📖",
            row=1
        )
        rules_btn.callback = self._rules_callback
        self.add_item(rules_btn)
        
        stats_btn = discord.ui.Button(
            label="📊 My Stats",
            style=discord.ButtonStyle.secondary,
            emoji="📊",
            row=1
        )
        stats_btn.callback = self._stats_callback
        self.add_item(stats_btn)
    
    def _create_game_callback(self, game_type: str):
        """Create callback for game selection"""
        async def callback(interaction: discord.Interaction):
            modal = CasinoBetModal(game_type, self.betting_limits['casino_max'], self.currency_symbol)
            await interaction.response.send_modal(modal)
        return callback
    
    async def _balance_callback(self, interaction: discord.Interaction):
        """Handle balance button"""
        embed = discord.Embed(
            title="💰 Your Casino Balance",
            description=f"Current balance: **{self.user_balance:,}** {self.currency_symbol}",
            color=0x00FF00
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def _leaderboard_callback(self, interaction: discord.Interaction):
        """Handle leaderboard button"""
        await interaction.response.send_message(
            "🏆 Casino leaderboard feature coming soon!", ephemeral=True
        )
    
    async def _rules_callback(self, interaction: discord.Interaction):
        """Handle rules button"""
        await interaction.response.send_message(
            "📖 Casino rules and game guides coming soon!", ephemeral=True
        )
    
    async def _stats_callback(self, interaction: discord.Interaction):
        """Handle stats button"""
        await interaction.response.send_message(
            "📊 Personal casino statistics coming soon!", ephemeral=True
        )

# ===== ADVANCED SELECT MENUS =====

class ServerSelectionView(discord.View):
    """Dynamic server selection with search capability"""
    
    def __init__(self, servers: List[Dict[str, Any]], callback_function: Callable):
        super().__init__(timeout=300)
        self.servers = servers
        self.callback_function = callback_function
        self.current_page = 0
        self.page_size = 20  # Discord limit is 25, leave room for navigation
        
        self._setup_server_select()
        self._setup_navigation()
    
    def _setup_server_select(self):
        """Setup server selection dropdown"""
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.servers))
        current_servers = self.servers[start_idx:end_idx]
        
        if current_servers:
            options = []
            for server in current_servers:
                premium_status = "Premium" if server.get('premium_status') else "Free"
                options.append(discord.SelectOption(
                    label=server['name'],
                    value=server['server_id'],
                    description=f"Host: {server['host']} | Status: {premium_status}",
                    emoji="🌟" if server.get('premium_status') else "🖥️"
                ))
            
            server_select = discord.ui.Select(
                placeholder="Choose a server...",
                options=options,
                row=0
            )
            server_select.callback = self._server_select_callback
            self.add_item(server_select)
    
    def _setup_navigation(self):
        """Setup pagination navigation"""
        total_pages = (len(self.servers) + self.page_size - 1) // self.page_size
        
        if total_pages > 1:
            # Navigation buttons
            prev_btn = discord.ui.Button(
                label="◀️ Previous",
                style=discord.ButtonStyle.grey,
                row=1,
                disabled=self.current_page == 0
            )
            prev_btn.callback = self._prev_page_callback
            self.add_item(prev_btn)
            
            page_btn = discord.ui.Button(
                label=f"Page {self.current_page + 1}/{total_pages}",
                style=discord.ButtonStyle.secondary,
                row=1,
                disabled=True
            )
            self.add_item(page_btn)
            
            next_btn = discord.ui.Button(
                label="▶️ Next",
                style=discord.ButtonStyle.grey,
                row=1,
                disabled=self.current_page >= total_pages - 1
            )
            next_btn.callback = self._next_page_callback
            self.add_item(next_btn)
    
    async def _server_select_callback(self, interaction: discord.Interaction):
        """Handle server selection"""
        selected_server_id = interaction.data["values"][0]
        await self.callback_function(interaction, selected_server_id)
    
    async def _prev_page_callback(self, interaction: discord.Interaction):
        """Handle previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            await self._update_page(interaction)
    
    async def _next_page_callback(self, interaction: discord.Interaction):
        """Handle next page"""
        total_pages = (len(self.servers) + self.page_size - 1) // self.page_size
        if self.current_page < total_pages - 1:
            self.current_page += 1
            await self._update_page(interaction)
    
    async def _update_page(self, interaction: discord.Interaction):
        """Update the page display"""
        # Recreate the view with new page
        new_view = ServerSelectionView(self.servers, self.callback_function)
        new_view.current_page = self.current_page
        await interaction.response.edit_message(view=new_view)