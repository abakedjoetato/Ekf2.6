"""
Embed Factory - Standardized embed creation for Emerald's Killfeed
Consistent styling and branding across all bot responses
"""

import discord
from typing import Optional, List, Dict, Any
from datetime import datetime

class EmbedFactory:
    """Factory class for creating standardized Discord embeds"""
    
    # Brand colors
    PRIMARY_COLOR = 0x2ECC71    # Emerald green
    SUCCESS_COLOR = 0x27AE60    # Success green
    WARNING_COLOR = 0xF39C12    # Warning orange
    ERROR_COLOR = 0xE74C3C      # Error red
    INFO_COLOR = 0x3498DB       # Info blue
    PREMIUM_COLOR = 0x9B59B6    # Premium purple
    
    @classmethod
    def create_embed(cls, title: str, description: str = None, color: int = None) -> discord.Embed:
        """Create a basic embed with standard formatting"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=color or cls.PRIMARY_COLOR,
            timestamp=datetime.utcnow()
        )
        
        embed.set_footer(
            text="Emerald's Killfeed",
            icon_url="https://cdn.discordapp.com/attachments/placeholder/emerald_icon.png"
        )
        
        return embed
    
    @classmethod
    def create_success_embed(cls, title: str, description: str = None) -> discord.Embed:
        """Create a success embed with green color"""
        return cls.create_embed(title, description, cls.SUCCESS_COLOR)
    
    @classmethod
    def create_error_embed(cls, title: str, description: str = None) -> discord.Embed:
        """Create an error embed with red color"""
        return cls.create_embed(title, description, cls.ERROR_COLOR)
    
    @classmethod
    def create_warning_embed(cls, title: str, description: str = None) -> discord.Embed:
        """Create a warning embed with orange color"""
        return cls.create_embed(title, description, cls.WARNING_COLOR)
    
    @classmethod
    def create_info_embed(cls, title: str, description: str = None) -> discord.Embed:
        """Create an info embed with blue color"""
        return cls.create_embed(title, description, cls.INFO_COLOR)
    
    @classmethod
    def create_premium_embed(cls, title: str, description: str = None) -> discord.Embed:
        """Create a premium embed with purple color and special formatting"""
        embed = cls.create_embed(title, description, cls.PREMIUM_COLOR)
        embed.set_author(name="💎 Premium Feature")
        return embed
    
    @classmethod
    def create_leaderboard_embed(cls, title: str, entries: List[Dict[str, Any]], 
                                category: str = "Kills") -> discord.Embed:
        """Create a formatted leaderboard embed"""
        embed = cls.create_embed(title, color=cls.PRIMARY_COLOR)
        
        if not entries:
            embed.add_field(
                name="No Data Available",
                value="No leaderboard data found for this category.",
                inline=False
            )
            return embed
        
        # Format leaderboard entries
        leaderboard_text = []
        medals = ["🥇", "🥈", "🥉"]
        
        for i, entry in enumerate(entries[:10]):  # Top 10
            rank_icon = medals[i] if i < 3 else f"{i+1}."
            player_name = entry.get('player_name', 'Unknown')
            value = entry.get('value', 0)
            
            if category.lower() in ['kills', 'deaths']:
                formatted_value = f"{value:,}"
            elif category.lower() == 'kdr':
                formatted_value = f"{value:.2f}"
            elif category.lower() == 'distance':
                formatted_value = f"{value:,}m"
            else:
                formatted_value = str(value)
            
            leaderboard_text.append(f"{rank_icon} **{player_name}** - {formatted_value}")
        
        embed.add_field(
            name=f"Top {category}",
            value="\n".join(leaderboard_text),
            inline=False
        )
        
        return embed
    
    @classmethod
    def create_kill_embed(cls, kill_data: Dict[str, Any]) -> discord.Embed:
        """Create a formatted kill notification embed"""
        killer = kill_data.get('killer', 'Unknown')
        victim = kill_data.get('victim', 'Unknown')
        weapon = kill_data.get('weapon', 'Unknown')
        distance = kill_data.get('distance', 0)
        
        title = f"💀 {killer} eliminated {victim}"
        
        embed = cls.create_embed(title, color=cls.ERROR_COLOR)
        
        embed.add_field(name="Weapon", value=weapon, inline=True)
        embed.add_field(name="Distance", value=f"{distance:,}m", inline=True)
        
        # Add additional data if available
        if 'faction_killer' in kill_data and 'faction_victim' in kill_data:
            embed.add_field(
                name="Faction War",
                value=f"{kill_data['faction_killer']} vs {kill_data['faction_victim']}",
                inline=False
            )
        
        return embed
    
    @classmethod
    def create_economy_embed(cls, user_name: str, balance: int, 
                           transaction_type: str = None, amount: int = None) -> discord.Embed:
        """Create an economy-related embed"""
        title = f"💰 {user_name}'s Wallet"
        
        embed = cls.create_embed(title, color=cls.SUCCESS_COLOR)
        embed.add_field(name="Balance", value=f"${balance:,}", inline=True)
        
        if transaction_type and amount:
            embed.add_field(
                name="Recent Transaction",
                value=f"{transaction_type}: ${amount:,}",
                inline=True
            )
        
        return embed
    
    @classmethod
    def create_faction_embed(cls, faction_data: Dict[str, Any]) -> discord.Embed:
        """Create a faction information embed"""
        faction_name = faction_data.get('name', 'Unknown Faction')
        title = f"⚔️ {faction_name}"
        
        embed = cls.create_embed(title, color=cls.WARNING_COLOR)
        
        # Basic faction info
        embed.add_field(
            name="Leader",
            value=faction_data.get('leader', 'Unknown'),
            inline=True
        )
        embed.add_field(
            name="Members",
            value=str(faction_data.get('member_count', 0)),
            inline=True
        )
        embed.add_field(
            name="Founded",
            value=faction_data.get('created_date', 'Unknown'),
            inline=True
        )
        
        # Statistics
        stats = faction_data.get('stats', {})
        embed.add_field(
            name="Total Kills",
            value=f"{stats.get('kills', 0):,}",
            inline=True
        )
        embed.add_field(
            name="Total Deaths",
            value=f"{stats.get('deaths', 0):,}",
            inline=True
        )
        
        kdr = stats.get('kills', 0) / max(stats.get('deaths', 1), 1)
        embed.add_field(
            name="K/D Ratio",
            value=f"{kdr:.2f}",
            inline=True
        )
        
        # Description if available
        if 'description' in faction_data:
            embed.add_field(
                name="Description",
                value=faction_data['description'],
                inline=False
            )
        
        return embed
    
    @classmethod
    def create_casino_embed(cls, game_type: str, result: str, 
                          bet_amount: int, payout: int = 0) -> discord.Embed:
        """Create a casino game result embed"""
        title = f"🎰 {game_type} Results"
        
        if payout > bet_amount:
            color = cls.SUCCESS_COLOR
            outcome = "🎉 You won!"
        elif payout == bet_amount:
            color = cls.WARNING_COLOR
            outcome = "🤝 Push!"
        else:
            color = cls.ERROR_COLOR
            outcome = "💸 You lost!"
        
        embed = cls.create_embed(title, color=color)
        
        embed.add_field(name="Outcome", value=outcome, inline=True)
        embed.add_field(name="Bet Amount", value=f"${bet_amount:,}", inline=True)
        embed.add_field(name="Payout", value=f"${payout:,}", inline=True)
        embed.add_field(name="Result", value=result, inline=False)
        
        return embed
    
    @classmethod
    def create_server_status_embed(cls, server_data: Dict[str, Any]) -> discord.Embed:
        """Create a server status embed"""
        server_name = server_data.get('name', 'Unknown Server')
        title = f"🖥️ {server_name} Status"
        
        status = server_data.get('status', 'Unknown')
        if status.lower() == 'online':
            color = cls.SUCCESS_COLOR
            status_icon = "🟢"
        elif status.lower() == 'offline':
            color = cls.ERROR_COLOR
            status_icon = "🔴"
        else:
            color = cls.WARNING_COLOR
            status_icon = "🟡"
        
        embed = cls.create_embed(title, color=color)
        
        embed.add_field(
            name="Status",
            value=f"{status_icon} {status.title()}",
            inline=True
        )
        embed.add_field(
            name="Players",
            value=f"{server_data.get('players', 0)}/{server_data.get('max_players', 0)}",
            inline=True
        )
        embed.add_field(
            name="Map",
            value=server_data.get('map', 'Unknown'),
            inline=True
        )
        
        if 'ip' in server_data:
            embed.add_field(
                name="Connection",
                value=f"`{server_data['ip']}`",
                inline=False
            )
        
        return embed
    
    @classmethod
    def create_help_embed(cls, command_groups: Dict[str, List[str]]) -> discord.Embed:
        """Create a help command embed"""
        embed = cls.create_embed(
            "📚 Emerald's Killfeed Commands",
            "Complete command reference for all bot features",
            cls.INFO_COLOR
        )
        
        for category, commands in command_groups.items():
            command_list = "\n".join([f"`/{cmd}`" for cmd in commands])
            embed.add_field(
                name=f"{category} Commands",
                value=command_list,
                inline=True
            )
        
        embed.add_field(
            name="Support",
            value="Need help? Join our support server or contact an administrator.",
            inline=False
        )
        
        return embed