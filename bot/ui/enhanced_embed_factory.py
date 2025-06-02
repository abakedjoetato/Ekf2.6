"""
Enhanced Embed Factory - Consistent UI Components
Standardized embed creation with server context and branding
"""

import discord
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

class EnhancedEmbedFactory:
    """
    Enhanced embed factory with server context and consistent branding
    """
    
    # Brand colors
    COLORS = {
        'primary': 0x3498DB,      # Blue
        'success': 0x00FF00,      # Green
        'warning': 0xFFAA00,      # Orange
        'error': 0xFF0000,        # Red
        'info': 0x9B59B6,         # Purple
        'premium': 0xFFD700,      # Gold
        'server': 0x2ECC71,       # Emerald green
        'stats': 0x1ABC9C,        # Turquoise
        'faction': 0xE74C3C,      # Red
        'casino': 0x8E44AD        # Purple
    }
    
    @classmethod
    def create_killfeed_embed(cls, kill_data: Dict[str, Any], server_name: str = None) -> discord.Embed:
        """Create killfeed embed with server context"""
        embed = discord.Embed(
            title="💀 Kill Event",
            color=cls.COLORS['error'],
            timestamp=kill_data.get('timestamp', datetime.now(timezone.utc))
        )
        
        # Killer information
        killer = kill_data.get('killer', 'Unknown')
        victim = kill_data.get('victim', 'Unknown')
        weapon = kill_data.get('weapon', 'Unknown')
        distance = kill_data.get('distance', 0)
        
        embed.add_field(
            name="🔫 Killer",
            value=f"**{killer}**",
            inline=True
        )
        
        embed.add_field(
            name="☠️ Victim", 
            value=f"**{victim}**",
            inline=True
        )
        
        embed.add_field(
            name="⚔️ Weapon",
            value=f"**{weapon}**",
            inline=True
        )
        
        embed.add_field(
            name="📏 Distance",
            value=f"**{distance}m**",
            inline=True
        )
        
        # Server context
        if server_name:
            embed.add_field(
                name="🌐 Server",
                value=f"**{server_name}**",
                inline=True
            )
        
        # Special indicators
        if distance >= 500:
            embed.add_field(
                name="🎯 Special",
                value="**Long Range Kill**",
                inline=True
            )
        
        if kill_data.get('headshot'):
            embed.add_field(
                name="🎯 Special",
                value="**Headshot**",
                inline=True
            )
        
        return embed
    
    @classmethod
    def create_server_status_embed(cls, server_config: Dict[str, Any], status_data: Dict[str, Any] = None) -> discord.Embed:
        """Create server status embed"""
        status = server_config.get('connection_status', 'unknown')
        status_colors = {
            'connected': cls.COLORS['success'],
            'failed': cls.COLORS['error'],
            'pending': cls.COLORS['warning'],
            'unknown': cls.COLORS['info']
        }
        
        embed = discord.Embed(
            title=f"🌐 Server Status - {server_config.get('name', 'Unknown')}",
            color=status_colors.get(status, cls.COLORS['info']),
            timestamp=datetime.now(timezone.utc)
        )
        
        # Connection information
        status_icons = {
            'connected': '🟢 Connected',
            'failed': '🔴 Failed',
            'pending': '🟡 Pending',
            'unknown': '⚪ Unknown'
        }
        
        embed.add_field(
            name="Status",
            value=status_icons.get(status, '⚪ Unknown'),
            inline=True
        )
        
        embed.add_field(
            name="Host",
            value=f"`{server_config.get('host', 'unknown')}:{server_config.get('port', 22)}`",
            inline=True
        )
        
        embed.add_field(
            name="Server ID",
            value=f"`{server_config.get('_id', 'unknown')}`",
            inline=True
        )
        
        # Add status data if provided
        if status_data:
            if 'player_count' in status_data:
                embed.add_field(
                    name="👥 Players",
                    value=f"**{status_data['player_count']}** online",
                    inline=True
                )
            
            if 'last_activity' in status_data:
                embed.add_field(
                    name="📅 Last Activity",
                    value=f"<t:{int(status_data['last_activity'].timestamp())}:R>",
                    inline=True
                )
        
        return embed
    
    @classmethod
    def create_player_stats_embed(cls, player_name: str, stats: Dict[str, Any], server_name: str = None) -> discord.Embed:
        """Create comprehensive player statistics embed"""
        embed = discord.Embed(
            title=f"📊 Player Statistics - {player_name}",
            color=cls.COLORS['stats'],
            timestamp=datetime.now(timezone.utc)
        )
        
        # Server context
        if server_name:
            embed.add_field(name="🌐 Server", value=server_name, inline=True)
        else:
            embed.add_field(name="📊 Data Scope", value="All Servers", inline=True)
        
        # Basic combat stats
        kills = stats.get('kills', 0)
        deaths = stats.get('deaths', 0)
        kd_ratio = round(kills / deaths, 2) if deaths > 0 else kills
        
        embed.add_field(name="🔫 Kills", value=f"**{kills:,}**", inline=True)
        embed.add_field(name="💀 Deaths", value=f"**{deaths:,}**", inline=True)
        embed.add_field(name="📈 K/D Ratio", value=f"**{kd_ratio}**", inline=True)
        
        # Additional stats if available
        if 'headshots' in stats:
            headshot_rate = round((stats['headshots'] / kills) * 100, 1) if kills > 0 else 0
            embed.add_field(name="🎯 Headshot Rate", value=f"**{headshot_rate}%**", inline=True)
        
        if 'average_distance' in stats:
            embed.add_field(name="📏 Avg Distance", value=f"**{stats['average_distance']:.1f}m**", inline=True)
        
        # Rivalry information
        rivalries = stats.get('rivalries', {})
        if rivalries.get('nemesis'):
            nemesis = rivalries['nemesis']
            embed.add_field(
                name="⚔️ Nemesis",
                value=f"**{nemesis['player']}**\nRecord: {nemesis['our_kills']}-{nemesis['their_kills']}",
                inline=True
            )
        
        if rivalries.get('prey'):
            prey = rivalries['prey']
            embed.add_field(
                name="🎯 Prey",
                value=f"**{prey['player']}**\nRecord: {prey['our_kills']}-{prey['their_kills']}",
                inline=True
            )
        
        # Performance badges
        badges = []
        if kd_ratio >= 2.0:
            badges.append("🔥 Elite Fighter")
        if stats.get('headshots', 0) / max(kills, 1) >= 0.5:
            badges.append("🎯 Sharpshooter")
        if stats.get('average_distance', 0) >= 300:
            badges.append("🔭 Long Range")
        
        if badges:
            embed.add_field(
                name="🏆 Performance Badges",
                value=" • ".join(badges),
                inline=False
            )
        
        return embed
    
    @classmethod
    def create_leaderboard_embed(cls, leaderboard_type: str, entries: List[Dict[str, Any]], 
                                server_name: str = None, page: int = 1, total_pages: int = 1) -> discord.Embed:
        """Create leaderboard embed with pagination"""
        title_map = {
            'kills': '🔫 Kill Leaderboard',
            'kd': '📈 K/D Leaderboard', 
            'distance': '📏 Distance Leaderboard',
            'headshots': '🎯 Headshot Leaderboard'
        }
        
        title = title_map.get(leaderboard_type, f'🏆 {leaderboard_type.title()} Leaderboard')
        if server_name:
            title += f" - {server_name}"
        
        embed = discord.Embed(
            title=title,
            color=cls.COLORS['primary'],
            timestamp=datetime.now(timezone.utc)
        )
        
        # Add pagination info
        if total_pages > 1:
            embed.set_footer(text=f"Page {page}/{total_pages}")
        
        # Medal emojis
        medals = ["🥇", "🥈", "🥉"]
        
        leaderboard_text = ""
        for i, entry in enumerate(entries[:10]):  # Top 10
            rank = (page - 1) * 10 + i + 1
            medal = medals[i] if i < 3 and page == 1 else f"**#{rank}**"
            
            player_name = entry.get('player_name', 'Unknown')
            value = entry.get(leaderboard_type, 0)
            
            if leaderboard_type == 'kd':
                value_str = f"{value:.2f}"
            elif leaderboard_type == 'distance':
                value_str = f"{value:.1f}m"
            else:
                value_str = f"{value:,}"
            
            leaderboard_text += f"{medal} **{player_name}** - {value_str}\n"
        
        embed.description = leaderboard_text
        
        return embed
    
    @classmethod
    def create_channel_config_embed(cls, guild_name: str, config_data: Dict[str, Any]) -> discord.Embed:
        """Create channel configuration display embed"""
        embed = discord.Embed(
            title=f"📋 Channel Configuration - {guild_name}",
            color=cls.COLORS['info'],
            timestamp=datetime.now(timezone.utc)
        )
        
        # Default channels
        defaults = config_data.get('default_channels', {})
        if defaults:
            default_text = ""
            for channel_type, channel_id in defaults.items():
                default_text += f"• **{channel_type.title()}**: <#{channel_id}>\n"
            
            embed.add_field(
                name="🌐 Guild Defaults",
                value=default_text or "None configured",
                inline=False
            )
        
        # Server-specific configurations
        server_configs = config_data.get('server_channels', {})
        if server_configs:
            for server_id, channels in server_configs.items():
                if channels and any(k != 'last_updated' for k in channels.keys()):
                    server_text = ""
                    for channel_type, channel_id in channels.items():
                        if channel_type != 'last_updated':
                            server_text += f"• **{channel_type.title()}**: <#{channel_id}>\n"
                    
                    if server_text:
                        embed.add_field(
                            name=f"🎯 {server_id}",
                            value=server_text,
                            inline=True
                        )
        
        # Legend
        embed.add_field(
            name="📝 Priority",
            value="Server-specific channels override guild defaults",
            inline=False
        )
        
        return embed
    
    @classmethod
    def create_error_embed(cls, title: str, description: str, error_details: str = None) -> discord.Embed:
        """Create standardized error embed"""
        embed = discord.Embed(
            title=f"❌ {title}",
            description=description,
            color=cls.COLORS['error'],
            timestamp=datetime.now(timezone.utc)
        )
        
        if error_details:
            embed.add_field(
                name="Error Details",
                value=f"```{error_details[:1000]}```",
                inline=False
            )
        
        return embed
    
    @classmethod
    def create_success_embed(cls, title: str, description: str, details: str = None) -> discord.Embed:
        """Create standardized success embed"""
        embed = discord.Embed(
            title=f"✅ {title}",
            description=description,
            color=cls.COLORS['success'],
            timestamp=datetime.now(timezone.utc)
        )
        
        if details:
            embed.add_field(
                name="Details",
                value=details,
                inline=False
            )
        
        return embed
    
    @classmethod
    def create_progress_embed(cls, title: str, progress: int, total: int, details: str = None) -> discord.Embed:
        """Create progress tracking embed"""
        percentage = round((progress / total) * 100, 1) if total > 0 else 0
        
        embed = discord.Embed(
            title=f"🔄 {title}",
            color=cls.COLORS['info'],
            timestamp=datetime.now(timezone.utc)
        )
        
        # Progress bar
        bar_length = 20
        filled_length = int(bar_length * progress / total) if total > 0 else 0
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        embed.add_field(
            name="Progress",
            value=f"`{bar}` {percentage}%\n{progress:,}/{total:,} items",
            inline=False
        )
        
        if details:
            embed.add_field(
                name="Current Status",
                value=details,
                inline=False
            )
        
        return embed