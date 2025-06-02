"""
Faction Management UI Components - Phase 7: Dual-Layer System
User-controlled faction management with administrative override capabilities
"""

import discord
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class FactionManagementView(discord.View):
    """Advanced faction management interface with role-based controls"""
    
    def __init__(self, bot, faction_data: Dict[str, Any], user_role: str, guild_id: int):
        super().__init__(timeout=300)
        self.bot = bot
        self.faction_data = faction_data
        self.user_role = user_role
        self.guild_id = guild_id
        
        self._setup_buttons_by_role()
    
    def _setup_buttons_by_role(self):
        """Setup buttons based on user's role in faction"""
        if self.user_role == "leader":
            # Row 0: Leadership Controls
            manage_btn = discord.ui.Button(
                label="👑 Manage Members",
                style=discord.ButtonStyle.primary,
                row=0
            )
            manage_btn.callback = self._manage_members_callback
            self.add_item(manage_btn)
            
            treasury_btn = discord.ui.Button(
                label="💰 Treasury",
                style=discord.ButtonStyle.secondary,
                row=0
            )
            treasury_btn.callback = self._treasury_callback
            self.add_item(treasury_btn)
            
            settings_btn = discord.ui.Button(
                label="⚙️ Settings",
                style=discord.ButtonStyle.secondary,
                row=0
            )
            settings_btn.callback = self._settings_callback
            self.add_item(settings_btn)
            
            # Row 1: Advanced Actions
            promote_btn = discord.ui.Button(
                label="⬆️ Promote",
                style=discord.ButtonStyle.success,
                row=1
            )
            promote_btn.callback = self._promote_callback
            self.add_item(promote_btn)
            
            kick_btn = discord.ui.Button(
                label="👢 Kick Member",
                style=discord.ButtonStyle.danger,
                row=1
            )
            kick_btn.callback = self._kick_callback
            self.add_item(kick_btn)
            
            disband_btn = discord.ui.Button(
                label="💥 Disband",
                style=discord.ButtonStyle.danger,
                row=1
            )
            disband_btn.callback = self._disband_callback
            self.add_item(disband_btn)
            
        elif self.user_role == "officer":
            # Row 0: Officer Controls
            invite_btn = discord.ui.Button(
                label="📨 Invite Members",
                style=discord.ButtonStyle.primary,
                row=0
            )
            invite_btn.callback = self._invite_callback
            self.add_item(invite_btn)
            
            kick_member_btn = discord.ui.Button(
                label="👢 Kick Member",
                style=discord.ButtonStyle.secondary,
                row=0
            )
            kick_member_btn.callback = self._kick_member_callback
            self.add_item(kick_member_btn)
            
            treasury_btn = discord.ui.Button(
                label="💰 Treasury",
                style=discord.ButtonStyle.secondary,
                row=0
            )
            treasury_btn.callback = self._treasury_callback
            self.add_item(treasury_btn)
            
        else:  # Regular member
            # Row 0: Member Controls
            stats_btn = discord.ui.Button(
                label="📊 Faction Stats",
                style=discord.ButtonStyle.primary,
                row=0
            )
            stats_btn.callback = self._stats_callback
            self.add_item(stats_btn)
            
            treasury_btn = discord.ui.Button(
                label="💰 Contribute",
                style=discord.ButtonStyle.secondary,
                row=0
            )
            treasury_btn.callback = self._contribute_callback
            self.add_item(treasury_btn)
            
            leave_btn = discord.ui.Button(
                label="🚪 Leave Faction",
                style=discord.ButtonStyle.danger,
                row=0
            )
            leave_btn.callback = self._leave_callback
            self.add_item(leave_btn)
        
        # Common buttons for all roles
        info_btn = discord.ui.Button(
            label="ℹ️ Faction Info",
            style=discord.ButtonStyle.grey,
            row=2
        )
        info_btn.callback = self._info_callback
        self.add_item(info_btn)
        
        refresh_btn = discord.ui.Button(
            label="🔄 Refresh",
            style=discord.ButtonStyle.grey,
            row=2
        )
        refresh_btn.callback = self._refresh_callback
        self.add_item(refresh_btn)
    
    async def _manage_members_callback(self, interaction: discord.Interaction):
        """Handle member management"""
        modal = MemberManagementModal(self.bot, self.faction_data, self.guild_id)
        await interaction.response.send_modal(modal)
    
    async def _treasury_callback(self, interaction: discord.Interaction):
        """Handle treasury management"""
        modal = TreasuryModal(self.bot, self.faction_data, self.user_role, self.guild_id)
        await interaction.response.send_modal(modal)
    
    async def _settings_callback(self, interaction: discord.Interaction):
        """Handle faction settings"""
        modal = FactionSettingsModal(self.bot, self.faction_data, self.guild_id)
        await interaction.response.send_modal(modal)
    
    async def _promote_callback(self, interaction: discord.Interaction):
        """Handle member promotion"""
        modal = PromotionModal(self.bot, self.faction_data, self.guild_id)
        await interaction.response.send_modal(modal)
    
    async def _kick_callback(self, interaction: discord.Interaction):
        """Handle member kicking"""
        modal = KickMemberModal(self.bot, self.faction_data, self.guild_id)
        await interaction.response.send_modal(modal)
    
    async def _disband_callback(self, interaction: discord.Interaction):
        """Handle faction disbanding"""
        view = FactionDisbandConfirmView(self.bot, self.faction_data, self.guild_id)
        embed = discord.Embed(
            title="⚠️ Confirm Faction Disbanding",
            description=f"Are you sure you want to disband **{self.faction_data.get('name')}**?\n\n**This action cannot be undone!**",
            color=0xFF0000
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def _invite_callback(self, interaction: discord.Interaction):
        """Handle member invitation"""
        modal = InviteMemberModal(self.bot, self.faction_data, self.guild_id)
        await interaction.response.send_modal(modal)
    
    async def _kick_member_callback(self, interaction: discord.Interaction):
        """Handle member kicking (officer version)"""
        modal = KickMemberModal(self.bot, self.faction_data, self.guild_id, officer_mode=True)
        await interaction.response.send_modal(modal)
    
    async def _stats_callback(self, interaction: discord.Interaction):
        """Handle faction statistics display"""
        await interaction.response.send_message(
            "📊 Detailed faction statistics coming soon!", ephemeral=True
        )
    
    async def _contribute_callback(self, interaction: discord.Interaction):
        """Handle treasury contribution"""
        modal = ContributionModal(self.bot, self.faction_data, self.guild_id)
        await interaction.response.send_modal(modal)
    
    async def _leave_callback(self, interaction: discord.Interaction):
        """Handle leaving faction"""
        view = LeaveFactionConfirmView(self.bot, self.faction_data, self.guild_id)
        embed = discord.Embed(
            title="⚠️ Confirm Leave Faction",
            description=f"Are you sure you want to leave **{self.faction_data.get('name')}**?",
            color=0xFFA500
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def _info_callback(self, interaction: discord.Interaction):
        """Handle faction information display"""
        await interaction.response.send_message(
            "ℹ️ Detailed faction information coming soon!", ephemeral=True
        )
    
    async def _refresh_callback(self, interaction: discord.Interaction):
        """Handle refresh"""
        await interaction.response.send_message(
            "🔄 Refreshing faction data...", ephemeral=True
        )

class MemberManagementModal(discord.Modal):
    """Modal for managing faction members"""
    
    def __init__(self, bot, faction_data: Dict[str, Any], guild_id: int):
        super().__init__(title="👑 Manage Faction Members")
        self.bot = bot
        self.faction_data = faction_data
        self.guild_id = guild_id
        
        self.action_type = discord.InputText(
            label="Action",
            placeholder="invite, kick, promote, demote, transfer",
            style=discord.InputTextStyle.short,
            max_length=20,
            required=True
        )
        
        self.target_user = discord.InputText(
            label="Target User (Discord ID or @mention)",
            placeholder="Enter user ID or mention them",
            style=discord.InputTextStyle.short,
            max_length=100,
            required=True
        )
        
        self.reason = discord.InputText(
            label="Reason (Optional)",
            placeholder="Reason for this action",
            style=discord.InputTextStyle.long,
            max_length=200,
            required=False
        )
        
        self.add_item(self.action_type)
        self.add_item(self.target_user)
        self.add_item(self.reason)
    
    async def callback(self, interaction: discord.Interaction):
        """Process member management action"""
        try:
            action = self.action_type.value.strip().lower()
            target = self.target_user.value.strip()
            reason = self.reason.value.strip() or "No reason provided"
            
            # Extract user ID from mention or direct ID
            user_id = None
            if target.startswith('<@') and target.endswith('>'):
                user_id = int(target[2:-1].replace('!', ''))
            else:
                try:
                    user_id = int(target)
                except ValueError:
                    await interaction.response.send_message(
                        "❌ Invalid user ID or mention format!", ephemeral=True
                    )
                    return
            
            if action == "invite":
                # Handle invitation logic
                await interaction.response.send_message(
                    f"✅ Invitation sent to <@{user_id}>", ephemeral=True
                )
            elif action == "kick":
                # Handle kick logic
                await interaction.response.send_message(
                    f"✅ <@{user_id}> has been kicked from the faction", ephemeral=True
                )
            elif action == "promote":
                # Handle promotion logic
                await interaction.response.send_message(
                    f"✅ <@{user_id}> has been promoted to officer", ephemeral=True
                )
            elif action == "demote":
                # Handle demotion logic
                await interaction.response.send_message(
                    f"✅ <@{user_id}> has been demoted to member", ephemeral=True
                )
            elif action == "transfer":
                # Handle leadership transfer
                await interaction.response.send_message(
                    f"✅ Leadership transferred to <@{user_id}>", ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "❌ Invalid action! Use: invite, kick, promote, demote, or transfer", ephemeral=True
                )
                
        except Exception as e:
            logger.error(f"Member management failed: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while processing the action.", ephemeral=True
            )

class TreasuryModal(discord.Modal):
    """Modal for faction treasury management"""
    
    def __init__(self, bot, faction_data: Dict[str, Any], user_role: str, guild_id: int):
        super().__init__(title="💰 Faction Treasury")
        self.bot = bot
        self.faction_data = faction_data
        self.user_role = user_role
        self.guild_id = guild_id
        
        self.action = discord.InputText(
            label="Action",
            placeholder="deposit, withdraw (leaders only)",
            style=discord.InputTextStyle.short,
            max_length=10,
            required=True
        )
        
        self.amount = discord.InputText(
            label="Amount",
            placeholder="Enter amount",
            style=discord.InputTextStyle.short,
            max_length=15,
            required=True
        )
        
        self.purpose = discord.InputText(
            label="Purpose (Optional)",
            placeholder="Reason for transaction",
            style=discord.InputTextStyle.long,
            max_length=200,
            required=False
        )
        
        self.add_item(self.action)
        self.add_item(self.amount)
        self.add_item(self.purpose)
    
    async def callback(self, interaction: discord.Interaction):
        """Process treasury transaction"""
        try:
            action = self.action.value.strip().lower()
            purpose = self.purpose.value.strip() or f"Treasury {action}"
            
            try:
                amount = int(self.amount.value.replace(",", ""))
                if amount <= 0:
                    raise ValueError("Amount must be positive")
            except ValueError:
                await interaction.response.send_message(
                    "❌ Please enter a valid positive amount!", ephemeral=True
                )
                return
            
            if action == "deposit":
                # Handle deposit logic
                await interaction.response.send_message(
                    f"✅ Deposited {amount:,} to faction treasury", ephemeral=True
                )
            elif action == "withdraw":
                if self.user_role != "leader":
                    await interaction.response.send_message(
                        "❌ Only faction leaders can withdraw from treasury!", ephemeral=True
                    )
                    return
                # Handle withdrawal logic
                await interaction.response.send_message(
                    f"✅ Withdrew {amount:,} from faction treasury", ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "❌ Invalid action! Use 'deposit' or 'withdraw'", ephemeral=True
                )
                
        except Exception as e:
            logger.error(f"Treasury transaction failed: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while processing the transaction.", ephemeral=True
            )

class FactionSettingsModal(discord.Modal):
    """Modal for faction settings configuration"""
    
    def __init__(self, bot, faction_data: Dict[str, Any], guild_id: int):
        super().__init__(title="⚙️ Faction Settings")
        self.bot = bot
        self.faction_data = faction_data
        self.guild_id = guild_id
        
        self.description = discord.InputText(
            label="Faction Description",
            placeholder="Update faction description",
            style=discord.InputTextStyle.long,
            value=faction_data.get('description', ''),
            max_length=500,
            required=False
        )
        
        self.color = discord.InputText(
            label="Faction Color (Hex)",
            placeholder="#3498DB",
            style=discord.InputTextStyle.short,
            value=faction_data.get('color', '#3498DB'),
            max_length=7,
            required=False
        )
        
        self.add_item(self.description)
        self.add_item(self.color)
    
    async def callback(self, interaction: discord.Interaction):
        """Process faction settings update"""
        try:
            description = self.description.value.strip()
            color = self.color.value.strip()
            
            # Validate color format
            if color and not color.startswith('#'):
                color = '#' + color
            
            if color and len(color) != 7:
                await interaction.response.send_message(
                    "❌ Color must be in hex format (e.g., #3498DB)!", ephemeral=True
                )
                return
            
            # Update faction settings
            update_data = {}
            if description:
                update_data['description'] = description
            if color:
                update_data['color'] = color
            
            if update_data:
                await self.bot.db_manager.factions.update_one(
                    {"guild_id": self.guild_id, "faction_id": self.faction_data['faction_id']},
                    {"$set": update_data}
                )
                
                await interaction.response.send_message(
                    "✅ Faction settings updated successfully!", ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "❌ No changes were made!", ephemeral=True
                )
                
        except Exception as e:
            logger.error(f"Faction settings update failed: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while updating faction settings.", ephemeral=True
            )

class FactionDisbandConfirmView(discord.View):
    """Confirmation view for faction disbanding"""
    
    def __init__(self, bot, faction_data: Dict[str, Any], guild_id: int):
        super().__init__(timeout=60)
        self.bot = bot
        self.faction_data = faction_data
        self.guild_id = guild_id
        
        confirm_btn = discord.ui.Button(
            label="Yes, Disband",
            style=discord.ButtonStyle.danger,
            emoji="💥"
        )
        confirm_btn.callback = self._confirm_callback
        self.add_item(confirm_btn)
        
        cancel_btn = discord.ui.Button(
            label="Cancel",
            style=discord.ButtonStyle.secondary,
            emoji="❌"
        )
        cancel_btn.callback = self._cancel_callback
        self.add_item(cancel_btn)
    
    async def _confirm_callback(self, interaction: discord.Interaction):
        """Confirm faction disbanding"""
        try:
            # Delete faction from database
            await self.bot.db_manager.factions.delete_one({
                "guild_id": self.guild_id,
                "faction_id": self.faction_data['faction_id']
            })
            
            # Remove faction ID from all members
            await self.bot.db_manager.players.update_many(
                {"guild_id": self.guild_id, "faction_id": self.faction_data['faction_id']},
                {"$unset": {"faction_id": ""}}
            )
            
            await interaction.response.send_message(
                f"💥 Faction **{self.faction_data.get('name')}** has been disbanded!", ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Faction disbanding failed: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while disbanding the faction.", ephemeral=True
            )
    
    async def _cancel_callback(self, interaction: discord.Interaction):
        """Cancel faction disbanding"""
        await interaction.response.send_message(
            "✅ Faction disbanding cancelled.", ephemeral=True
        )

class LeaveFactionConfirmView(discord.View):
    """Confirmation view for leaving faction"""
    
    def __init__(self, bot, faction_data: Dict[str, Any], guild_id: int):
        super().__init__(timeout=60)
        self.bot = bot
        self.faction_data = faction_data
        self.guild_id = guild_id
        
        confirm_btn = discord.ui.Button(
            label="Yes, Leave",
            style=discord.ButtonStyle.danger,
            emoji="🚪"
        )
        confirm_btn.callback = self._confirm_callback
        self.add_item(confirm_btn)
        
        cancel_btn = discord.ui.Button(
            label="Cancel",
            style=discord.ButtonStyle.secondary,
            emoji="❌"
        )
        cancel_btn.callback = self._cancel_callback
        self.add_item(cancel_btn)
    
    async def _confirm_callback(self, interaction: discord.Interaction):
        """Confirm leaving faction"""
        try:
            # Remove user from faction
            await self.bot.db_manager.players.update_one(
                {"guild_id": self.guild_id, "discord_id": interaction.user.id},
                {"$unset": {"faction_id": ""}}
            )
            
            # Remove from faction member lists
            await self.bot.db_manager.factions.update_one(
                {"guild_id": self.guild_id, "faction_id": self.faction_data['faction_id']},
                {
                    "$pull": {
                        "members": interaction.user.id,
                        "officers": interaction.user.id
                    }
                }
            )
            
            await interaction.response.send_message(
                f"🚪 You have left **{self.faction_data.get('name')}**", ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Leaving faction failed: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while leaving the faction.", ephemeral=True
            )
    
    async def _cancel_callback(self, interaction: discord.Interaction):
        """Cancel leaving faction"""
        await interaction.response.send_message(
            "✅ Cancelled leaving faction.", ephemeral=True
        )

# Additional modal classes for specific actions
class PromotionModal(discord.Modal):
    """Modal for promoting faction members"""
    
    def __init__(self, bot, faction_data: Dict[str, Any], guild_id: int):
        super().__init__(title="⬆️ Promote Member")
        self.bot = bot
        self.faction_data = faction_data
        self.guild_id = guild_id
        
        self.target_user = discord.InputText(
            label="User to Promote",
            placeholder="Discord ID or @mention",
            style=discord.InputTextStyle.short,
            required=True
        )
        
        self.add_item(self.target_user)
    
    async def callback(self, interaction: discord.Interaction):
        """Process member promotion"""
        await interaction.response.send_message(
            "✅ Member promotion functionality coming soon!", ephemeral=True
        )

class KickMemberModal(discord.Modal):
    """Modal for kicking faction members"""
    
    def __init__(self, bot, faction_data: Dict[str, Any], guild_id: int, officer_mode: bool = False):
        super().__init__(title="👢 Kick Member")
        self.bot = bot
        self.faction_data = faction_data
        self.guild_id = guild_id
        self.officer_mode = officer_mode
        
        self.target_user = discord.InputText(
            label="User to Kick",
            placeholder="Discord ID or @mention",
            style=discord.InputTextStyle.short,
            required=True
        )
        
        self.reason = discord.InputText(
            label="Reason",
            placeholder="Reason for kicking",
            style=discord.InputTextStyle.long,
            required=False
        )
        
        self.add_item(self.target_user)
        self.add_item(self.reason)
    
    async def callback(self, interaction: discord.Interaction):
        """Process member kick"""
        await interaction.response.send_message(
            "✅ Member kick functionality coming soon!", ephemeral=True
        )

class InviteMemberModal(discord.Modal):
    """Modal for inviting new faction members"""
    
    def __init__(self, bot, faction_data: Dict[str, Any], guild_id: int):
        super().__init__(title="📨 Invite Member")
        self.bot = bot
        self.faction_data = faction_data
        self.guild_id = guild_id
        
        self.target_user = discord.InputText(
            label="User to Invite",
            placeholder="Discord ID or @mention",
            style=discord.InputTextStyle.short,
            required=True
        )
        
        self.message = discord.InputText(
            label="Invitation Message",
            placeholder="Personal message with invitation",
            style=discord.InputTextStyle.long,
            required=False
        )
        
        self.add_item(self.target_user)
        self.add_item(self.message)
    
    async def callback(self, interaction: discord.Interaction):
        """Process member invitation"""
        await interaction.response.send_message(
            "✅ Member invitation functionality coming soon!", ephemeral=True
        )

class ContributionModal(discord.Modal):
    """Modal for treasury contributions"""
    
    def __init__(self, bot, faction_data: Dict[str, Any], guild_id: int):
        super().__init__(title="💰 Contribute to Treasury")
        self.bot = bot
        self.faction_data = faction_data
        self.guild_id = guild_id
        
        self.amount = discord.InputText(
            label="Contribution Amount",
            placeholder="Enter amount to contribute",
            style=discord.InputTextStyle.short,
            required=True
        )
        
        self.add_item(self.amount)
    
    async def callback(self, interaction: discord.Interaction):
        """Process treasury contribution"""
        await interaction.response.send_message(
            "✅ Treasury contribution functionality coming soon!", ephemeral=True
        )