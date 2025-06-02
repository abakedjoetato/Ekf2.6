"""
Advanced EmbedFactory - Phase 4: Enhanced Embed System with UI Integration
Preserves existing visual themes while adding py-cord 2.6.1 interactive components
"""

import discord
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
import logging
from pathlib import Path

# Import UI components
from bot.ui import (
    StatsNavigationView, LeaderboardView, CasinoGameView,
    FactionManagementView, AdminControlView
)

logger = logging.getLogger(__name__)

class AdvancedEmbedFactory:
    """
    Enhanced embed generation system maintaining existing theme structure
    Preserves all current styling while adding interactive py-cord 2.6.1 components
    """
    
    # Asset paths (preserved from original system)
    ASSET_PATH = Path("./assets")
    ASSETS = {
        'airdrop': 'Airdrop.png',
        'bounty': 'Bounty.png', 
        'casino': 'Casino.png',
        'connections': 'Connections.png',
        'faction': 'Faction.png',
        'falling': 'Falling.png',
        'gamble': 'Gamble.png',
        'helicrash': 'Helicrash.png',
        'killfeed': 'Killfeed.png',
        'leaderboard': 'Leaderboard.png',
        'mission': 'Mission.png',
        'suicide': 'Suicide.png',
        'trader': 'Trader.png',
        'vehicle': 'Vehicle.png',
        'weaponstats': 'WeaponStats.png',
        'main': 'main.png'
    }
    
    @staticmethod
    async def build_interactive_killfeed_embed(
        kill_data: Dict[str, Any], 
        bot,
        include_view: bool = True
    ) -> Tuple[discord.Embed, Optional[discord.File], Optional[discord.View]]:
        """Enhanced killfeed embed with platform data and interactive elements"""
        try:
            # Build base embed with preserved styling
            embed = discord.Embed(
                title="💀 Kill Event",
                color=0xFF4500,
                timestamp=kill_data.get('timestamp', datetime.now(timezone.utc))
            )
            
            # Killer information with platform icons
            killer = kill_data.get('killer', 'Unknown')
            killer_platform = kill_data.get('killer_platform', 'Unknown')
            platform_emoji = AdvancedEmbedFactory._get_platform_emoji(killer_platform)
            
            # Victim information with platform icons
            victim = kill_data.get('victim', 'Unknown')
            victim_platform = kill_data.get('victim_platform', 'Unknown')
            victim_platform_emoji = AdvancedEmbedFactory._get_platform_emoji(victim_platform)
            
            # Check for suicide normalization (preserved logic)
            is_suicide = kill_data.get('is_suicide', False)
            if is_suicide:
                embed.title = "💀 Suicide Event"
                embed.color = 0x8B0000
                embed.description = f"**{killer}** {platform_emoji} took their own life"
            else:
                embed.description = f"**{killer}** {platform_emoji} eliminated **{victim}** {victim_platform_emoji}"
            
            # Weapon and distance information (preserved formatting)
            weapon = kill_data.get('weapon', 'Unknown')
            distance = kill_data.get('distance', 0)
            
            embed.add_field(
                name="🔫 Weapon",
                value=f"**{weapon}**",
                inline=True
            )
            
            embed.add_field(
                name="📏 Distance",
                value=f"**{distance:.1f}m**" if distance > 0 else "**Unknown**",
                inline=True
            )
            
            # Cross-platform kill detection
            if not is_suicide and killer_platform != victim_platform:
                embed.add_field(
                    name="🌐 Cross-Platform",
                    value=f"**{killer_platform}** vs **{victim_platform}**",
                    inline=True
                )
            
            # Server information
            server_name = kill_data.get('server_name', 'Unknown Server')
            embed.set_footer(
                text=f"Server: {server_name} | Powered by Emerald's Killfeed",
                icon_url="attachment://killfeed.png"
            )
            
            # Preserved asset loading
            asset_file = discord.File(
                AdvancedEmbedFactory.ASSET_PATH / AdvancedEmbedFactory.ASSETS['killfeed'],
                filename="killfeed.png"
            )
            embed.set_thumbnail(url="attachment://killfeed.png")
            
            # Interactive view for detailed stats (optional)
            view = None
            if include_view and not is_suicide:
                # Create view with player stat buttons
                view = KillfeedInteractionView(bot, killer, victim, kill_data)
            
            return embed, asset_file, view
            
        except Exception as e:
            logger.error(f"Killfeed embed creation failed: {e}")
            return AdvancedEmbedFactory._create_error_embed("killfeed"), None, None
    
    @staticmethod
    async def build_interactive_stats_embed(
        player_data: Dict[str, Any],
        bot,
        guild_id: int,
        servers: List[Dict[str, Any]],
        is_premium: bool = False
    ) -> Tuple[discord.Embed, Optional[discord.File], Optional[discord.View]]:
        """Enhanced stats embed with cross-character aggregation and navigation"""
        try:
            player_name = player_data.get('player_name', 'Unknown Player')
            
            # Build base embed with preserved styling
            embed = discord.Embed(
                title=f"📊 Player Statistics - {player_name}",
                color=0x3498DB,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Core statistics (preserved formatting)
            kills = player_data.get('kills', 0)
            deaths = player_data.get('deaths', 0)
            kdr = player_data.get('kdr', 0.0)
            streak = player_data.get('longest_streak', 0)
            
            embed.add_field(
                name="🔥 Combat Stats",
                value=f"• Kills: **{kills:,}**\n• Deaths: **{deaths:,}**\n• K/D Ratio: **{kdr:.2f}**\n• Best Streak: **{streak}**",
                inline=True
            )
            
            # Distance statistics
            total_distance = player_data.get('total_distance', 0)
            best_distance = player_data.get('personal_best_distance', 0)
            
            embed.add_field(
                name="📏 Distance Stats",
                value=f"• Total Distance: **{total_distance:,.0f}m**\n• Longest Kill: **{best_distance:.1f}m**",
                inline=True
            )
            
            # Platform statistics (new feature)
            platform_stats = player_data.get('platform_stats', {})
            if platform_stats and is_premium:
                platform_text = ""
                for platform, stats in platform_stats.items():
                    emoji = AdvancedEmbedFactory._get_platform_emoji(platform)
                    platform_kdr = stats.get('kdr', 0.0)
                    platform_kills = stats.get('kills', 0)
                    platform_text += f"• {emoji} {platform}: **{platform_kills}** kills (**{platform_kdr:.2f}** K/D)\n"
                
                if platform_text:
                    embed.add_field(
                        name="🎮 Platform Performance",
                        value=platform_text.strip(),
                        inline=False
                    )
            
            # Premium vs free distinction
            embed.add_field(
                name="🌟 Status", 
                value="**Premium Features Active**" if is_premium else "**Free Tier** - Upgrade for more features",
                inline=False
            )
            
            # Preserved asset loading
            asset_file = discord.File(
                AdvancedEmbedFactory.ASSET_PATH / AdvancedEmbedFactory.ASSETS['weaponstats'],
                filename="weaponstats.png"
            )
            embed.set_thumbnail(url="attachment://weaponstats.png")
            embed.set_footer(
                text="Use navigation buttons for detailed view | Powered by Emerald's Killfeed"
            )
            
            # Interactive navigation view
            view = StatsNavigationView(bot, player_data, servers)
            
            return embed, asset_file, view
            
        except Exception as e:
            logger.error(f"Stats embed creation failed: {e}")
            return AdvancedEmbedFactory._create_error_embed("stats"), None, None
    
    @staticmethod
    async def build_interactive_leaderboard_embed(
        leaderboard_data: List[Dict[str, Any]],
        bot,
        guild_id: int,
        embed_type: str = "kills",
        server_name: str = None,
        current_page: int = 0
    ) -> Tuple[discord.Embed, Optional[discord.File], Optional[discord.View]]:
        """Enhanced leaderboard with platform filtering and navigation"""
        try:
            # Dynamic title based on type
            type_titles = {
                'kills': '🔥 Kill Leaders',
                'kd': '💀 K/D Masters', 
                'distance': '🎯 Distance Kings',
                'streak': '⚡ Streak Legends',
                'weapons': '🏅 Weapon Masters'
            }
            
            title = type_titles.get(embed_type, '🏆 Leaderboard')
            if server_name:
                title += f" - {server_name}"
            
            embed = discord.Embed(
                title=title,
                color=0xF1C40F,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Build leaderboard content (preserved formatting)
            leaderboard_text = ""
            start_rank = current_page * 10 + 1
            
            for i, player in enumerate(leaderboard_data[current_page*10:(current_page+1)*10]):
                rank = start_rank + i
                name = player.get('player_name', 'Unknown')
                
                # Rank emoji
                rank_emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}."
                
                if embed_type == 'kills':
                    value = player.get('kills', 0)
                    leaderboard_text += f"{rank_emoji} **{name}** - **{value:,}** kills\n"
                elif embed_type == 'kd':
                    kdr = player.get('kdr', 0.0)
                    kills = player.get('kills', 0)
                    leaderboard_text += f"{rank_emoji} **{name}** - **{kdr:.2f}** K/D ({kills:,} kills)\n"
                elif embed_type == 'distance':
                    distance = player.get('personal_best_distance', 0)
                    leaderboard_text += f"{rank_emoji} **{name}** - **{distance:.1f}m**\n"
                elif embed_type == 'streak':
                    streak = player.get('longest_streak', 0)
                    leaderboard_text += f"{rank_emoji} **{name}** - **{streak}** kill streak\n"
            
            embed.description = leaderboard_text if leaderboard_text else "No players found for this leaderboard."
            
            # Page information
            total_pages = (len(leaderboard_data) + 9) // 10
            embed.add_field(
                name="📄 Page Info",
                value=f"Page {current_page + 1} of {total_pages} | Showing ranks {start_rank}-{min(start_rank + 9, len(leaderboard_data))}",
                inline=False
            )
            
            # Preserved asset loading
            asset_file = discord.File(
                AdvancedEmbedFactory.ASSET_PATH / AdvancedEmbedFactory.ASSETS['leaderboard'],
                filename="leaderboard.png"
            )
            embed.set_thumbnail(url="attachment://leaderboard.png")
            embed.set_footer(text="Use filters to customize view | Powered by Emerald's Killfeed")
            
            # Interactive leaderboard view
            view = LeaderboardView(bot, {'data': leaderboard_data, 'type': embed_type}, guild_id)
            
            return embed, asset_file, view
            
        except Exception as e:
            logger.error(f"Leaderboard embed creation failed: {e}")
            return AdvancedEmbedFactory._create_error_embed("leaderboard"), None, None
    
    @staticmethod
    async def build_interactive_faction_embed(
        faction_data: Dict[str, Any],
        bot,
        guild_id: int,
        user_role: str,
        action_type: str = "info"
    ) -> Tuple[discord.Embed, Optional[discord.File], Optional[discord.View]]:
        """Enhanced faction embed with treasury and member management"""
        try:
            faction_name = faction_data.get('name', 'Unknown Faction')
            
            embed = discord.Embed(
                title=f"🏛️ {faction_name}",
                description=faction_data.get('description', 'No description set'),
                color=int(faction_data.get('color', '#3498DB').replace('#', ''), 16),
                timestamp=datetime.now(timezone.utc)
            )
            
            # Member information
            members = faction_data.get('members', [])
            officers = faction_data.get('officers', [])
            leader_id = faction_data.get('leader_id')
            
            embed.add_field(
                name="👥 Members",
                value=f"• Total: **{len(members)}**\n• Officers: **{len(officers)}**\n• Leader: <@{leader_id}>",
                inline=True
            )
            
            # Treasury information
            treasury = faction_data.get('treasury', 0)
            embed.add_field(
                name="💰 Treasury",
                value=f"**{treasury:,}** Credits",
                inline=True
            )
            
            # Performance stats (if available)
            faction_stats = faction_data.get('performance_stats', {})
            if faction_stats:
                total_kills = faction_stats.get('total_kills', 0)
                avg_kdr = faction_stats.get('avg_kdr', 0.0)
                embed.add_field(
                    name="📊 Performance",
                    value=f"• Total Kills: **{total_kills:,}**\n• Avg K/D: **{avg_kdr:.2f}**",
                    inline=True
                )
            
            # User role indicator
            role_text = {
                'leader': '👑 Faction Leader',
                'officer': '⭐ Faction Officer', 
                'member': '👤 Faction Member'
            }.get(user_role, '👀 Observer')
            
            embed.add_field(
                name="📋 Your Role",
                value=role_text,
                inline=False
            )
            
            # Preserved asset loading
            asset_file = discord.File(
                AdvancedEmbedFactory.ASSET_PATH / AdvancedEmbedFactory.ASSETS['faction'],
                filename="faction.png"
            )
            embed.set_thumbnail(url="attachment://faction.png")
            embed.set_footer(text="Use management buttons below | Powered by Emerald's Killfeed")
            
            # Interactive faction management view
            view = FactionManagementView(bot, faction_data, user_role, guild_id)
            
            return embed, asset_file, view
            
        except Exception as e:
            logger.error(f"Faction embed creation failed: {e}")
            return AdvancedEmbedFactory._create_error_embed("faction"), None, None
    
    @staticmethod
    async def build_interactive_casino_embed(
        user_data: Dict[str, Any],
        economy_config: Dict[str, Any],
        bot,
        guild_id: int,
        game_type: str = "main_menu"
    ) -> Tuple[discord.Embed, Optional[discord.File], Optional[discord.View]]:
        """Interactive casino with game selection matrix"""
        try:
            currency_symbol = economy_config.get('currency_symbol', '💎')
            currency_name = economy_config.get('currency_name', 'Credits')
            user_balance = user_data.get('wallet_balance', 0)
            betting_limits = economy_config.get('betting_limits', {})
            
            embed = discord.Embed(
                title="🎰 Emerald's Casino",
                description=f"Welcome to the premium gaming experience!",
                color=0xF39C12,
                timestamp=datetime.now(timezone.utc)
            )
            
            # User balance and limits
            embed.add_field(
                name="💰 Your Balance",
                value=f"**{user_balance:,}** {currency_symbol} {currency_name}",
                inline=True
            )
            
            embed.add_field(
                name="🎯 Betting Limits",
                value=f"Min: **{betting_limits.get('casino_min', 10):,}** {currency_symbol}\nMax: **{betting_limits.get('casino_max', 10000):,}** {currency_symbol}",
                inline=True
            )
            
            # Casino statistics
            casino_stats = user_data.get('casino_stats', {})
            total_wagered = casino_stats.get('total_wagered', 0)
            total_won = casino_stats.get('total_won', 0)
            games_played = casino_stats.get('games_played', 0)
            
            embed.add_field(
                name="📊 Your Casino Stats",
                value=f"• Games Played: **{games_played:,}**\n• Total Wagered: **{total_wagered:,}** {currency_symbol}\n• Total Won: **{total_won:,}** {currency_symbol}",
                inline=False
            )
            
            # Game availability
            embed.add_field(
                name="🎮 Available Games",
                value="🎰 **Slots** - Quick spins and big wins!\n🃏 **Blackjack** - Beat the dealer!\n🎲 **Roulette** - Spin to win!\n🎴 **Poker** - Coming soon!",
                inline=False
            )
            
            # Preserved asset loading
            asset_file = discord.File(
                AdvancedEmbedFactory.ASSET_PATH / AdvancedEmbedFactory.ASSETS['casino'],
                filename="casino.png"
            )
            embed.set_thumbnail(url="attachment://casino.png")
            embed.set_footer(text="Select a game to start playing | Powered by Emerald's Killfeed")
            
            # Interactive casino game view
            view = CasinoGameView(bot, user_balance, betting_limits, currency_symbol)
            
            return embed, asset_file, view
            
        except Exception as e:
            logger.error(f"Casino embed creation failed: {e}")
            return AdvancedEmbedFactory._create_error_embed("casino"), None, None
    
    @staticmethod
    async def build_admin_control_embed(
        admin_data: Dict[str, Any],
        permissions: List[str],
        bot,
        guild_id: int,
        action_type: str = "control_panel"
    ) -> Tuple[discord.Embed, Optional[discord.File], Optional[discord.View]]:
        """Advanced administrative control interface"""
        try:
            embed = discord.Embed(
                title="⚙️ Administrative Control Panel",
                description="Complete server management and oversight tools",
                color=0xE74C3C,
                timestamp=datetime.now(timezone.utc)
            )
            
            # System status overview
            guild_stats = admin_data.get('guild_stats', {})
            embed.add_field(
                name="📊 Guild Overview",
                value=f"• Total Players: **{guild_stats.get('total_players', 0):,}**\n• Active Factions: **{guild_stats.get('active_factions', 0)}**\n• Premium Servers: **{guild_stats.get('premium_servers', 0)}**",
                inline=True
            )
            
            # Economic overview
            economy_stats = admin_data.get('economy_stats', {})
            embed.add_field(
                name="💰 Economy Status",
                value=f"• Total Currency: **{economy_stats.get('total_currency', 0):,}**\n• Daily Transactions: **{economy_stats.get('daily_transactions', 0)}**\n• Casino Activity: **{economy_stats.get('casino_games', 0)}** games",
                inline=True
            )
            
            # Available permissions
            perm_text = ""
            for perm in permissions[:5]:  # Show first 5 permissions
                perm_text += f"• {perm}\n"
            if len(permissions) > 5:
                perm_text += f"• ...and {len(permissions) - 5} more"
            
            embed.add_field(
                name="🔐 Your Permissions",
                value=perm_text if perm_text else "• Administrator Access",
                inline=False
            )
            
            # Quick actions available
            embed.add_field(
                name="⚡ Quick Actions",
                value="🔗 **Player Linking** - Manage character links\n💰 **Currency Control** - Balance management\n🏛️ **Faction Control** - Administrative faction tools\n⚙️ **System Config** - Economy and server settings",
                inline=False
            )
            
            # Preserved asset loading
            asset_file = discord.File(
                AdvancedEmbedFactory.ASSET_PATH / AdvancedEmbedFactory.ASSETS['main'],
                filename="main.png"
            )
            embed.set_thumbnail(url="attachment://main.png")
            embed.set_footer(text="Select a control category below | Administrative Access Required")
            
            # Interactive admin control view
            view = AdminControlView(bot, permissions, guild_id)
            
            return embed, asset_file, view
            
        except Exception as e:
            logger.error(f"Admin control embed creation failed: {e}")
            return AdvancedEmbedFactory._create_error_embed("admin"), None, None
    
    # Utility methods
    @staticmethod
    def _get_platform_emoji(platform: str) -> str:
        """Get emoji for gaming platform"""
        platform_emojis = {
            'PC': '💻',
            'Xbox': '🎮', 
            'PS5': '🕹️',
            'PlayStation': '🕹️',
            'Unknown': '❓'
        }
        return platform_emojis.get(platform, '❓')
    
    @staticmethod
    def _create_error_embed(embed_type: str) -> discord.Embed:
        """Create error embed for failed operations"""
        embed = discord.Embed(
            title="❌ Error",
            description=f"Failed to load {embed_type} information. Please try again later.",
            color=0xFF0000
        )
        return embed
    
    # Preserved legacy methods for backward compatibility
    @staticmethod
    async def build_killfeed_embed(kill_data: Dict[str, Any]) -> Tuple[discord.Embed, discord.File]:
        """Legacy killfeed embed without UI components"""
        embed, file, _ = await AdvancedEmbedFactory.build_interactive_killfeed_embed(
            kill_data, None, include_view=False
        )
        return embed, file
    
    @staticmethod
    async def build_stats_embed(player_data: Dict[str, Any], is_premium: bool = False) -> Tuple[discord.Embed, discord.File]:
        """Legacy stats embed without UI components"""
        embed, file, _ = await AdvancedEmbedFactory.build_interactive_stats_embed(
            player_data, None, 0, [], is_premium
        )
        return embed, file
    
    @staticmethod
    async def build_leaderboard_embed(leaderboard_data: List[Dict], embed_type: str, server_name: str = None) -> Tuple[discord.Embed, discord.File]:
        """Legacy leaderboard embed without UI components"""
        embed, file, _ = await AdvancedEmbedFactory.build_interactive_leaderboard_embed(
            leaderboard_data, None, 0, embed_type, server_name
        )
        return embed, file

class KillfeedInteractionView(discord.View):
    """Quick interaction view for killfeed embeds"""
    
    def __init__(self, bot, killer: str, victim: str, kill_data: Dict[str, Any]):
        super().__init__(timeout=300)
        self.bot = bot
        self.killer = killer
        self.victim = victim
        self.kill_data = kill_data
        
        # Quick stats buttons
        killer_stats_btn = discord.ui.Button(
            label=f"📊 {killer} Stats",
            style=discord.ButtonStyle.secondary,
            emoji="🔥"
        )
        killer_stats_btn.callback = self._killer_stats_callback
        self.add_item(killer_stats_btn)
        
        victim_stats_btn = discord.ui.Button(
            label=f"📊 {victim} Stats", 
            style=discord.ButtonStyle.secondary,
            emoji="💀"
        )
        victim_stats_btn.callback = self._victim_stats_callback
        self.add_item(victim_stats_btn)
        
        weapon_stats_btn = discord.ui.Button(
            label="🔫 Weapon Info",
            style=discord.ButtonStyle.grey
        )
        weapon_stats_btn.callback = self._weapon_stats_callback
        self.add_item(weapon_stats_btn)
    
    async def _killer_stats_callback(self, interaction: discord.Interaction):
        """Show killer statistics"""
        await interaction.response.send_message(
            f"📊 Detailed statistics for **{self.killer}** coming soon!", ephemeral=True
        )
    
    async def _victim_stats_callback(self, interaction: discord.Interaction):
        """Show victim statistics"""
        await interaction.response.send_message(
            f"📊 Detailed statistics for **{self.victim}** coming soon!", ephemeral=True
        )
    
    async def _weapon_stats_callback(self, interaction: discord.Interaction):
        """Show weapon information"""
        weapon = self.kill_data.get('weapon', 'Unknown')
        await interaction.response.send_message(
            f"🔫 Detailed information for **{weapon}** coming soon!", ephemeral=True
        )