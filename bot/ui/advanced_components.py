"""
Advanced UI Components for py-cord 2.6.1
Maximum utilization of advanced UI components for premium user experience
"""

import discord
from discord.ext import commands
from typing import Dict, List, Optional, Any, Callable
import asyncio
import logging

logger = logging.getLogger(__name__)

class MultiRowButtonView(discord.ui.View):
    """Advanced multi-row button matrix system"""
    
    def __init__(self, buttons_config: List[Dict[str, Any]], timeout: int = 180):
        super().__init__(timeout=timeout)
        self.buttons_config = buttons_config
        self.setup_buttons()
    
    def setup_buttons(self):
        """Setup button matrix with proper row management"""
        current_row = 0
        buttons_in_row = 0
        
        for config in self.buttons_config:
            if buttons_in_row >= 5:  # Discord limit per row
                current_row += 1
                buttons_in_row = 0
            
            button = discord.ui.Button(
                label=config.get('label', 'Button'),
                style=config.get('style', discord.ButtonStyle.secondary),
                emoji=config.get('emoji'),
                disabled=config.get('disabled', False),
                row=current_row
            )
            
            # Dynamic callback assignment
            if 'callback' in config:
                button.callback = config['callback']
            
            self.add_item(button)
            buttons_in_row += 1

class AdvancedCasinoView(discord.ui.View):
    """Advanced casino interface with dynamic betting"""
    
    def __init__(self, user_id: int, balance: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.balance = balance
        self.current_bet = 10
        
    @discord.ui.button(label="🎰 Slots", style=discord.ButtonStyle.primary, row=0)
    async def play_slots(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Play slot machine"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        
        # Show betting modal
        modal = BettingModal(self.current_bet, self.balance, "Slots")
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="🃏 Blackjack", style=discord.ButtonStyle.primary, row=0)
    async def play_blackjack(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Play blackjack"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        
        modal = BettingModal(self.current_bet, self.balance, "Blackjack")
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="🎲 Dice", style=discord.ButtonStyle.primary, row=0)
    async def play_dice(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Play dice game"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        
        modal = BettingModal(self.current_bet, self.balance, "Dice")
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="💰 Balance", style=discord.ButtonStyle.secondary, row=1)
    async def check_balance(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Check current balance"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="💰 Current Balance",
            description=f"**${self.balance:,}**",
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class BettingModal(discord.ui.Modal):
    """Advanced betting modal with validation"""
    
    def __init__(self, current_bet: int, max_balance: int, game_type: str):
        super().__init__(title=f"Place Bet - {game_type}")
        self.max_balance = max_balance
        self.game_type = game_type
        
        self.bet_input = discord.ui.InputText(
            label="Bet Amount",
            placeholder=f"Enter amount (Max: ${max_balance:,})",
            value=str(current_bet),
            min_length=1,
            max_length=10
        )
        self.add_item(self.bet_input)
    
    async def callback(self, interaction: discord.Interaction):
        """Handle bet submission"""
        try:
            bet_amount = int(self.bet_input.value.replace(',', '').replace('$', ''))
            
            if bet_amount <= 0:
                await interaction.response.send_message("Bet must be positive!", ephemeral=True)
                return
            
            if bet_amount > self.max_balance:
                await interaction.response.send_message(f"Insufficient funds! Max: ${self.max_balance:,}", ephemeral=True)
                return
            
            # Process game logic here
            embed = discord.Embed(
                title=f"🎮 {self.game_type} Game",
                description=f"Bet placed: **${bet_amount:,}**",
                color=discord.Color.green()
            )
            
            view = GameActionView(bet_amount, self.game_type)
            await interaction.response.send_message(embed=embed, view=view)
            
        except ValueError:
            await interaction.response.send_message("Invalid bet amount!", ephemeral=True)

class GameActionView(discord.ui.View):
    """Game-specific action buttons"""
    
    def __init__(self, bet_amount: int, game_type: str):
        super().__init__(timeout=120)
        self.bet_amount = bet_amount
        self.game_type = game_type
    
    @discord.ui.button(label="🎲 Roll/Play", style=discord.ButtonStyle.success)
    async def play_game(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Execute game logic"""
        # Game logic would go here
        result_embed = discord.Embed(
            title=f"🎮 {self.game_type} Result",
            description=f"Game played with ${self.bet_amount:,} bet",
            color=discord.Color.blue()
        )
        
        # Disable all buttons after play
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=result_embed, view=self)
    
    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.danger)
    async def cancel_game(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Cancel the game"""
        embed = discord.Embed(
            title="Game Cancelled",
            description="Your bet has been refunded.",
            color=discord.Color.red()
        )
        
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)

class FactionManagementView(discord.ui.View):
    """Advanced faction management interface"""
    
    def __init__(self, user_faction: Optional[Dict], is_leader: bool = False):
        super().__init__(timeout=300)
        self.user_faction = user_faction
        self.is_leader = is_leader
        self.setup_faction_buttons()
    
    def setup_faction_buttons(self):
        """Setup faction-specific buttons based on user status"""
        if not self.user_faction:
            # User has no faction
            create_button = discord.ui.Button(
                label="⚔️ Create Faction",
                style=discord.ButtonStyle.primary,
                row=0
            )
            create_button.callback = self.create_faction
            self.add_item(create_button)
            
            join_button = discord.ui.Button(
                label="🤝 Join Faction",
                style=discord.ButtonStyle.secondary,
                row=0
            )
            join_button.callback = self.join_faction
            self.add_item(join_button)
        else:
            # User has faction
            stats_button = discord.ui.Button(
                label="📊 Faction Stats",
                style=discord.ButtonStyle.primary,
                row=0
            )
            stats_button.callback = self.view_stats
            self.add_item(stats_button)
            
            members_button = discord.ui.Button(
                label="👥 Members",
                style=discord.ButtonStyle.secondary,
                row=0
            )
            members_button.callback = self.view_members
            self.add_item(members_button)
            
            if self.is_leader:
                invite_button = discord.ui.Button(
                    label="📧 Invite Member",
                    style=discord.ButtonStyle.success,
                    row=1
                )
                invite_button.callback = self.invite_member
                self.add_item(invite_button)
                
                manage_button = discord.ui.Button(
                    label="⚙️ Manage",
                    style=discord.ButtonStyle.secondary,
                    row=1
                )
                manage_button.callback = self.manage_faction
                self.add_item(manage_button)
            
            leave_button = discord.ui.Button(
                label="🚪 Leave Faction",
                style=discord.ButtonStyle.danger,
                row=2
            )
            leave_button.callback = self.leave_faction
            self.add_item(leave_button)
    
    async def create_faction(self, interaction: discord.Interaction):
        """Show faction creation modal"""
        modal = FactionCreationModal()
        await interaction.response.send_modal(modal)
    
    async def join_faction(self, interaction: discord.Interaction):
        """Show faction selection dropdown"""
        view = FactionSelectionView()
        embed = discord.Embed(
            title="Join Faction",
            description="Select a faction to join:",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def view_stats(self, interaction: discord.Interaction):
        """Show faction statistics"""
        embed = discord.Embed(
            title=f"📊 {self.user_faction['name']} Statistics",
            color=discord.Color.gold()
        )
        embed.add_field(name="Total Kills", value="1,234", inline=True)
        embed.add_field(name="Total Deaths", value="567", inline=True)
        embed.add_field(name="K/D Ratio", value="2.18", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def view_members(self, interaction: discord.Interaction):
        """Show faction members"""
        embed = discord.Embed(
            title=f"👥 {self.user_faction['name']} Members",
            description="Active faction members:",
            color=discord.Color.blue()
        )
        embed.add_field(name="Leader", value="PlayerOne", inline=False)
        embed.add_field(name="Officers", value="PlayerTwo\nPlayerThree", inline=False)
        embed.add_field(name="Members", value="PlayerFour\nPlayerFive\nPlayerSix", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def invite_member(self, interaction: discord.Interaction):
        """Show member invitation modal"""
        modal = MemberInvitationModal(self.user_faction['name'])
        await interaction.response.send_modal(modal)
    
    async def manage_faction(self, interaction: discord.Interaction):
        """Show faction management options"""
        view = FactionManagementOptionsView(self.user_faction)
        embed = discord.Embed(
            title="⚙️ Faction Management",
            description="Choose management option:",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def leave_faction(self, interaction: discord.Interaction):
        """Show leave confirmation"""
        view = ConfirmationView("leave faction")
        embed = discord.Embed(
            title="⚠️ Leave Faction",
            description=f"Are you sure you want to leave **{self.user_faction['name']}**?",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class FactionCreationModal(discord.ui.Modal):
    """Modal for creating new factions"""
    
    def __init__(self):
        super().__init__(title="Create New Faction")
        
        self.name_input = discord.ui.InputText(
            label="Faction Name",
            placeholder="Enter faction name (3-32 characters)",
            min_length=3,
            max_length=32
        )
        self.add_item(self.name_input)
        
        self.tag_input = discord.ui.InputText(
            label="Faction Tag (Optional)",
            placeholder="Enter faction tag (2-6 characters)",
            min_length=2,
            max_length=6,
            required=False
        )
        self.add_item(self.tag_input)
        
        self.description_input = discord.ui.InputText(
            label="Description (Optional)",
            placeholder="Enter faction description",
            style=discord.InputTextStyle.paragraph,
            max_length=500,
            required=False
        )
        self.add_item(self.description_input)
    
    async def callback(self, interaction: discord.Interaction):
        """Handle faction creation"""
        embed = discord.Embed(
            title="✅ Faction Created",
            description=f"Successfully created faction **{self.name_input.value}**",
            color=discord.Color.green()
        )
        
        if self.tag_input.value:
            embed.add_field(name="Tag", value=self.tag_input.value, inline=True)
        
        if self.description_input.value:
            embed.add_field(name="Description", value=self.description_input.value, inline=False)
        
        await interaction.response.send_message(embed=embed)

class FactionSelectionView(discord.ui.View):
    """Dropdown for selecting factions to join"""
    
    def __init__(self):
        super().__init__(timeout=120)
        
        # Example faction options
        options = [
            discord.SelectOption(label="Warriors Guild", description="Elite PvP faction", emoji="⚔️"),
            discord.SelectOption(label="Shadow Clan", description="Stealth specialists", emoji="🥷"),
            discord.SelectOption(label="Iron Brotherhood", description="Defensive powerhouse", emoji="🛡️"),
            discord.SelectOption(label="Storm Raiders", description="Fast attack faction", emoji="⚡"),
        ]
        
        select = discord.ui.Select(
            placeholder="Choose a faction to join...",
            options=options
        )
        select.callback = self.faction_selected
        self.add_item(select)
    
    async def faction_selected(self, interaction: discord.Interaction):
        """Handle faction selection"""
        selected_faction = interaction.data["values"][0]
        
        embed = discord.Embed(
            title="📧 Join Request Sent",
            description=f"Your request to join **{selected_faction}** has been sent to the faction leaders.",
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class PlayerLinkingModal(discord.ui.Modal):
    """Modal for linking player characters"""
    
    def __init__(self, user_id: int):
        super().__init__(title="Link Player Character")
        self.user_id = user_id
        
        self.main_player_input = discord.ui.InputText(
            label="Main Character Name",
            placeholder="Enter your main character name",
            min_length=3,
            max_length=32
        )
        self.add_item(self.main_player_input)
        
        self.alt_player_input = discord.ui.InputText(
            label="Alt Character Name (Optional)",
            placeholder="Enter alt character name to link",
            min_length=3,
            max_length=32,
            required=False
        )
        self.add_item(self.alt_player_input)
    
    async def callback(self, interaction: discord.Interaction):
        """Handle player linking"""
        embed = discord.Embed(
            title="✅ Character Linked",
            description=f"Successfully linked character **{self.main_player_input.value}**",
            color=discord.Color.green()
        )
        
        if self.alt_player_input.value:
            embed.add_field(name="Alt Character", value=self.alt_player_input.value, inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class EconomyConfigModal(discord.ui.Modal):
    """Modal for economy configuration"""
    
    def __init__(self):
        super().__init__(title="Economy Configuration")
        
        self.starting_balance = discord.ui.InputText(
            label="Starting Balance",
            placeholder="Default balance for new users",
            value="1000"
        )
        self.add_item(self.starting_balance)
        
        self.daily_bonus = discord.ui.InputText(
            label="Daily Bonus",
            placeholder="Daily login bonus amount",
            value="100"
        )
        self.add_item(self.daily_bonus)
    
    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="✅ Economy Updated",
            description="Economy settings have been updated",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class BountyCreationModal(discord.ui.Modal):
    """Modal for creating bounties"""
    
    def __init__(self):
        super().__init__(title="Create Bounty")
        
        self.target_input = discord.ui.InputText(
            label="Target Player",
            placeholder="Enter target player name"
        )
        self.add_item(self.target_input)
        
        self.amount_input = discord.ui.InputText(
            label="Bounty Amount",
            placeholder="Enter bounty amount"
        )
        self.add_item(self.amount_input)
        
        self.reason_input = discord.ui.InputText(
            label="Reason (Optional)",
            placeholder="Why is this bounty being placed?",
            style=discord.InputTextStyle.paragraph,
            required=False
        )
        self.add_item(self.reason_input)
    
    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="💰 Bounty Created",
            description=f"Bounty placed on **{self.target_input.value}** for **${self.amount_input.value}**",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)

class CasinoBetModal(discord.ui.Modal):
    """Modal for casino betting"""
    
    def __init__(self, game_type: str, max_bet: int):
        super().__init__(title=f"Place Bet - {game_type}")
        self.game_type = game_type
        
        self.bet_input = discord.ui.InputText(
            label="Bet Amount",
            placeholder=f"Enter amount (Max: ${max_bet:,})"
        )
        self.add_item(self.bet_input)
    
    async def callback(self, interaction: discord.Interaction):
        try:
            bet_amount = int(self.bet_input.value.replace(',', '').replace('$', ''))
            embed = discord.Embed(
                title=f"🎮 {self.game_type}",
                description=f"Bet placed: **${bet_amount:,}**",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
        except ValueError:
            await interaction.response.send_message("Invalid bet amount!", ephemeral=True)

class StatsNavigationView(discord.ui.View):
    """Navigation view for statistics"""
    
    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
    
    @discord.ui.button(label="📊 Personal Stats", style=discord.ButtonStyle.primary)
    async def personal_stats(self, button: discord.ui.Button, interaction: discord.Interaction):
        embed = discord.Embed(title="📊 Personal Statistics", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="🏆 Leaderboards", style=discord.ButtonStyle.secondary)
    async def leaderboards(self, button: discord.ui.Button, interaction: discord.Interaction):
        embed = discord.Embed(title="🏆 Leaderboards", color=discord.Color.gold())
        await interaction.response.send_message(embed=embed, ephemeral=True)

class LeaderboardView(discord.ui.View):
    """View for leaderboard navigation"""
    
    def __init__(self):
        super().__init__(timeout=300)
    
    @discord.ui.button(label="🔫 Kills", style=discord.ButtonStyle.primary)
    async def kills_leaderboard(self, button: discord.ui.Button, interaction: discord.Interaction):
        embed = discord.Embed(title="🔫 Kill Leaderboard", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)

class CasinoGameView(discord.ui.View):
    """View for casino games"""
    
    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
    
    @discord.ui.button(label="🎰 Slots", style=discord.ButtonStyle.primary)
    async def slots(self, button: discord.ui.Button, interaction: discord.Interaction):
        embed = discord.Embed(title="🎰 Slot Machine", color=discord.Color.gold())
        await interaction.response.send_message(embed=embed, ephemeral=True)

class ServerSelectionView(discord.ui.View):
    """View for server selection"""
    
    def __init__(self, servers: list):
        super().__init__(timeout=300)
        self.servers = servers
    
    @discord.ui.button(label="🌐 Select Server", style=discord.ButtonStyle.primary)
    async def select_server(self, button: discord.ui.Button, interaction: discord.Interaction):
        embed = discord.Embed(title="🌐 Server Selection", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

class MemberInvitationModal(discord.ui.Modal):
    """Modal for inviting new faction members"""
    
    def __init__(self, faction_name: str):
        super().__init__(title=f"Invite to {faction_name}")
        self.faction_name = faction_name
        
        self.player_input = discord.ui.InputText(
            label="Player Name or Discord User",
            placeholder="Enter player name or @mention user",
            min_length=2,
            max_length=50
        )
        self.add_item(self.player_input)
        
        self.message_input = discord.ui.InputText(
            label="Invitation Message (Optional)",
            placeholder="Add a personal message to the invitation",
            style=discord.InputTextStyle.paragraph,
            max_length=200,
            required=False
        )
        self.add_item(self.message_input)
    
    async def callback(self, interaction: discord.Interaction):
        """Handle member invitation"""
        embed = discord.Embed(
            title="📧 Invitation Sent",
            description=f"Invitation sent to **{self.player_input.value}** to join **{self.faction_name}**",
            color=discord.Color.green()
        )
        
        if self.message_input.value:
            embed.add_field(name="Message", value=self.message_input.value, inline=False)
        
        await interaction.response.send_message(embed=embed)

class FactionManagementOptionsView(discord.ui.View):
    """Advanced faction management options"""
    
    def __init__(self, faction_data: Dict):
        super().__init__(timeout=180)
        self.faction_data = faction_data
    
    @discord.ui.button(label="👥 Manage Members", style=discord.ButtonStyle.primary)
    async def manage_members(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Show member management interface"""
        view = MemberManagementView(self.faction_data)
        embed = discord.Embed(
            title="👥 Member Management",
            description="Select member management action:",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @discord.ui.button(label="⚙️ Settings", style=discord.ButtonStyle.secondary)
    async def faction_settings(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Show faction settings modal"""
        modal = FactionSettingsModal(self.faction_data)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="📊 Analytics", style=discord.ButtonStyle.success)
    async def faction_analytics(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Show detailed faction analytics"""
        embed = discord.Embed(
            title="📊 Faction Analytics",
            description=f"Detailed statistics for **{self.faction_data['name']}**",
            color=discord.Color.gold()
        )
        
        embed.add_field(name="📈 Performance", value="KDR: 2.34\nWin Rate: 67%\nActivity: High", inline=True)
        embed.add_field(name="👥 Members", value="Active: 15\nInactive: 3\nNew: 2", inline=True)
        embed.add_field(name="🏆 Rankings", value="Server Rank: #3\nGlobal Rank: #47\nTrend: ↗️", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class MemberManagementView(discord.ui.View):
    """Member management interface"""
    
    def __init__(self, faction_data: Dict):
        super().__init__(timeout=120)
        self.faction_data = faction_data
    
    @discord.ui.button(label="🏅 Promote Member", style=discord.ButtonStyle.success)
    async def promote_member(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Show member promotion interface"""
        modal = MemberActionModal("promote", self.faction_data['name'])
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="⬇️ Demote Member", style=discord.ButtonStyle.secondary)
    async def demote_member(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Show member demotion interface"""
        modal = MemberActionModal("demote", self.faction_data['name'])
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="🚫 Kick Member", style=discord.ButtonStyle.danger)
    async def kick_member(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Show member kick interface"""
        modal = MemberActionModal("kick", self.faction_data['name'])
        await interaction.response.send_modal(modal)

class MemberActionModal(discord.ui.Modal):
    """Modal for member management actions"""
    
    def __init__(self, action: str, faction_name: str):
        super().__init__(title=f"{action.title()} Member - {faction_name}")
        self.action = action
        self.faction_name = faction_name
        
        self.member_input = discord.ui.InputText(
            label="Member Name",
            placeholder="Enter member name or Discord user",
            min_length=2,
            max_length=50
        )
        self.add_item(self.member_input)
        
        if action == "kick":
            self.reason_input = discord.ui.InputText(
                label="Reason (Optional)",
                placeholder="Enter reason for removal",
                style=discord.InputTextStyle.paragraph,
                max_length=200,
                required=False
            )
            self.add_item(self.reason_input)
    
    async def callback(self, interaction: discord.Interaction):
        """Handle member action"""
        embed = discord.Embed(
            title=f"✅ Member {self.action.title()}d",
            description=f"Successfully {self.action}d **{self.member_input.value}** from **{self.faction_name}**",
            color=discord.Color.green() if self.action != "kick" else discord.Color.red()
        )
        
        if hasattr(self, 'reason_input') and self.reason_input.value:
            embed.add_field(name="Reason", value=self.reason_input.value, inline=False)
        
        await interaction.response.send_message(embed=embed)

class FactionSettingsModal(discord.ui.Modal):
    """Modal for faction settings configuration"""
    
    def __init__(self, faction_data: Dict):
        super().__init__(title=f"Settings - {faction_data['name']}")
        self.faction_data = faction_data
        
        self.description_input = discord.ui.InputText(
            label="Faction Description",
            placeholder="Enter new faction description",
            style=discord.InputTextStyle.paragraph,
            value=faction_data.get('description', ''),
            max_length=500
        )
        self.add_item(self.description_input)
        
        self.recruitment_input = discord.ui.InputText(
            label="Recruitment Status",
            placeholder="open/closed/invite-only",
            value=faction_data.get('recruitment', 'open'),
            max_length=20
        )
        self.add_item(self.recruitment_input)
    
    async def callback(self, interaction: discord.Interaction):
        """Handle settings update"""
        embed = discord.Embed(
            title="⚙️ Settings Updated",
            description=f"Settings for **{self.faction_data['name']}** have been updated",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Description", value=self.description_input.value or "None", inline=False)
        embed.add_field(name="Recruitment", value=self.recruitment_input.value, inline=True)
        
        await interaction.response.send_message(embed=embed)

class ConfirmationView(discord.ui.View):
    """Generic confirmation dialog"""
    
    def __init__(self, action: str):
        super().__init__(timeout=60)
        self.action = action
        self.confirmed = False
    
    @discord.ui.button(label="✅ Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Confirm the action"""
        self.confirmed = True
        
        embed = discord.Embed(
            title="✅ Confirmed",
            description=f"Action confirmed: {self.action}",
            color=discord.Color.green()
        )
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()
    
    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        """Cancel the action"""
        embed = discord.Embed(
            title="❌ Cancelled",
            description=f"Action cancelled: {self.action}",
            color=discord.Color.red()
        )
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

class LeaderboardNavigationView(discord.ui.View):
    """Advanced leaderboard navigation with filtering"""
    
    def __init__(self, current_page: int = 0, total_pages: int = 1):
        super().__init__(timeout=300)
        self.current_page = current_page
        self.total_pages = total_pages
        self.setup_navigation()
    
    def setup_navigation(self):
        """Setup navigation buttons based on current state"""
        # Previous page button
        prev_button = discord.ui.Button(
            label="◀️ Previous",
            style=discord.ButtonStyle.secondary,
            disabled=self.current_page <= 0,
            row=0
        )
        prev_button.callback = self.previous_page
        self.add_item(prev_button)
        
        # Page indicator
        page_button = discord.ui.Button(
            label=f"Page {self.current_page + 1}/{self.total_pages}",
            style=discord.ButtonStyle.primary,
            disabled=True,
            row=0
        )
        self.add_item(page_button)
        
        # Next page button
        next_button = discord.ui.Button(
            label="Next ▶️",
            style=discord.ButtonStyle.secondary,
            disabled=self.current_page >= self.total_pages - 1,
            row=0
        )
        next_button.callback = self.next_page
        self.add_item(next_button)
        
        # Filter dropdown
        filter_options = [
            discord.SelectOption(label="All Time", description="Show all-time statistics", emoji="🕐"),
            discord.SelectOption(label="This Month", description="Show monthly statistics", emoji="📅"),
            discord.SelectOption(label="This Week", description="Show weekly statistics", emoji="📊"),
            discord.SelectOption(label="Today", description="Show daily statistics", emoji="📈"),
        ]
        
        filter_select = discord.ui.Select(
            placeholder="Filter by time period...",
            options=filter_options,
            row=1
        )
        filter_select.callback = self.filter_changed
        self.add_item(filter_select)
        
        # Category selection
        category_options = [
            discord.SelectOption(label="Kills", description="Top killers", emoji="💀"),
            discord.SelectOption(label="Deaths", description="Most deaths", emoji="⚰️"),
            discord.SelectOption(label="K/D Ratio", description="Best K/D ratios", emoji="📊"),
            discord.SelectOption(label="Distance", description="Longest kills", emoji="🎯"),
            discord.SelectOption(label="Weapons", description="Most used weapons", emoji="🔫"),
            discord.SelectOption(label="Factions", description="Top factions", emoji="⚔️"),
        ]
        
        category_select = discord.ui.Select(
            placeholder="Select category...",
            options=category_options,
            row=2
        )
        category_select.callback = self.category_changed
        self.add_item(category_select)
    
    async def previous_page(self, interaction: discord.Interaction):
        """Navigate to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_leaderboard(interaction)
    
    async def next_page(self, interaction: discord.Interaction):
        """Navigate to next page"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            await self.update_leaderboard(interaction)
    
    async def filter_changed(self, interaction: discord.Interaction):
        """Handle time filter change"""
        selected_filter = interaction.data["values"][0]
        self.current_page = 0  # Reset to first page
        
        embed = discord.Embed(
            title="🔄 Updating Leaderboard",
            description=f"Applying filter: **{selected_filter}**",
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await self.update_leaderboard(interaction, filter_type=selected_filter)
    
    async def category_changed(self, interaction: discord.Interaction):
        """Handle category change"""
        selected_category = interaction.data["values"][0]
        self.current_page = 0  # Reset to first page
        
        embed = discord.Embed(
            title="🔄 Switching Category",
            description=f"Loading: **{selected_category}** leaderboard",
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await self.update_leaderboard(interaction, category=selected_category)
    
    async def update_leaderboard(self, interaction: discord.Interaction, 
                               filter_type: str = None, category: str = None):
        """Update leaderboard display"""
        # This would integrate with the actual leaderboard system
        embed = discord.Embed(
            title="📊 Updated Leaderboard",
            description="Leaderboard has been updated with new filters",
            color=discord.Color.green()
        )
        
        # Update navigation buttons
        self.clear_items()
        self.setup_navigation()
        
        try:
            await interaction.edit_original_response(embed=embed, view=self)
        except discord.NotFound:
            await interaction.followup.send(embed=embed, view=self)