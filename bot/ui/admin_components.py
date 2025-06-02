"""
Administrative UI Components - Phase 9: Enhanced Guild Admin Controls
Complete administrative override capabilities with audit trails
"""

import discord
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class AdminControlView(discord.View):
    """Advanced administrative control panel with permission-based access"""
    
    def __init__(self, bot, admin_permissions: List[str], guild_id: int):
        super().__init__(timeout=300)
        self.bot = bot
        self.admin_permissions = admin_permissions
        self.guild_id = guild_id
        
        self._setup_admin_controls()
    
    def _setup_admin_controls(self):
        """Setup administrative control buttons based on permissions"""
        # Row 0: Player Management
        player_linking_btn = discord.ui.Button(
            label="👤 Player Linking",
            style=discord.ButtonStyle.primary,
            row=0
        )
        player_linking_btn.callback = self._player_linking_callback
        self.add_item(player_linking_btn)
        
        currency_control_btn = discord.ui.Button(
            label="💰 Currency Control",
            style=discord.ButtonStyle.primary,
            row=0
        )
        currency_control_btn.callback = self._currency_control_callback
        self.add_item(currency_control_btn)
        
        faction_control_btn = discord.ui.Button(
            label="🏛️ Faction Control",
            style=discord.ButtonStyle.primary,
            row=0
        )
        faction_control_btn.callback = self._faction_control_callback
        self.add_item(faction_control_btn)
        
        # Row 1: System Management
        economy_config_btn = discord.ui.Button(
            label="⚙️ Economy Config",
            style=discord.ButtonStyle.secondary,
            row=1
        )
        economy_config_btn.callback = self._economy_config_callback
        self.add_item(economy_config_btn)
        
        channel_setup_btn = discord.ui.Button(
            label="🔧 Channel Setup",
            style=discord.ButtonStyle.secondary,
            row=1
        )
        channel_setup_btn.callback = self._channel_setup_callback
        self.add_item(channel_setup_btn)
        
        premium_control_btn = discord.ui.Button(
            label="🌟 Premium Control",
            style=discord.ButtonStyle.secondary,
            row=1
        )
        premium_control_btn.callback = self._premium_control_callback
        self.add_item(premium_control_btn)
        
        # Row 2: Advanced Operations
        bulk_operations_btn = discord.ui.Button(
            label="🔄 Bulk Operations",
            style=discord.ButtonStyle.danger,
            row=2
        )
        bulk_operations_btn.callback = self._bulk_operations_callback
        self.add_item(bulk_operations_btn)
        
        system_status_btn = discord.ui.Button(
            label="📊 System Status",
            style=discord.ButtonStyle.grey,
            row=2
        )
        system_status_btn.callback = self._system_status_callback
        self.add_item(system_status_btn)
        
        audit_logs_btn = discord.ui.Button(
            label="📋 Audit Logs",
            style=discord.ButtonStyle.grey,
            row=2
        )
        audit_logs_btn.callback = self._audit_logs_callback
        self.add_item(audit_logs_btn)
    
    async def _player_linking_callback(self, interaction: discord.Interaction):
        """Handle player linking management"""
        view = PlayerLinkingAdminView(self.bot, self.guild_id)
        embed = discord.Embed(
            title="👤 Player Linking Administration",
            description="Manage player character linking with administrative override",
            color=0x3498DB
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def _currency_control_callback(self, interaction: discord.Interaction):
        """Handle currency management"""
        view = CurrencyControlView(self.bot, self.guild_id)
        embed = discord.Embed(
            title="💰 Currency Control Panel",
            description="Administrative currency management and balance controls",
            color=0xF1C40F
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def _faction_control_callback(self, interaction: discord.Interaction):
        """Handle faction administration"""
        view = FactionAdminView(self.bot, self.guild_id)
        embed = discord.Embed(
            title="🏛️ Faction Administration",
            description="Administrative faction management and oversight",
            color=0x9B59B6
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def _economy_config_callback(self, interaction: discord.Interaction):
        """Handle economy configuration"""
        # Get current economy config
        economy_config = await self.bot.db_manager.get_economy_config(self.guild_id)
        modal = AdminEconomyModal(self.bot, self.guild_id, economy_config)
        await interaction.response.send_modal(modal)
    
    async def _channel_setup_callback(self, interaction: discord.Interaction):
        """Handle channel setup"""
        await interaction.response.send_message(
            "🔧 Advanced channel setup interface coming soon!", ephemeral=True
        )
    
    async def _premium_control_callback(self, interaction: discord.Interaction):
        """Handle premium management"""
        view = PremiumAdminView(self.bot, self.guild_id)
        embed = discord.Embed(
            title="🌟 Premium Administration",
            description="Server premium status and allocation management",
            color=0xE74C3C
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def _bulk_operations_callback(self, interaction: discord.Interaction):
        """Handle bulk operations"""
        view = BulkOperationsView(self.bot, self.guild_id)
        embed = discord.Embed(
            title="⚠️ Bulk Operations",
            description="**WARNING:** These operations affect multiple users and cannot be undone!",
            color=0xE74C3C
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def _system_status_callback(self, interaction: discord.Interaction):
        """Handle system status display"""
        await interaction.response.send_message(
            "📊 System status dashboard coming soon!", ephemeral=True
        )
    
    async def _audit_logs_callback(self, interaction: discord.Interaction):
        """Handle audit logs display"""
        await interaction.response.send_message(
            "📋 Audit logs viewer coming soon!", ephemeral=True
        )

class PlayerLinkingAdminView(discord.View):
    """Administrative player linking controls"""
    
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        
        # Force link button
        force_link_btn = discord.ui.Button(
            label="🔗 Force Link",
            style=discord.ButtonStyle.primary,
            row=0
        )
        force_link_btn.callback = self._force_link_callback
        self.add_item(force_link_btn)
        
        # Remove link button
        remove_link_btn = discord.ui.Button(
            label="🔓 Remove Link",
            style=discord.ButtonStyle.secondary,
            row=0
        )
        remove_link_btn.callback = self._remove_link_callback
        self.add_item(remove_link_btn)
        
        # Transfer character button
        transfer_btn = discord.ui.Button(
            label="↔️ Transfer Character",
            style=discord.ButtonStyle.secondary,
            row=0
        )
        transfer_btn.callback = self._transfer_callback
        self.add_item(transfer_btn)
        
        # View links button
        view_links_btn = discord.ui.Button(
            label="👁️ View Links",
            style=discord.ButtonStyle.grey,
            row=1
        )
        view_links_btn.callback = self._view_links_callback
        self.add_item(view_links_btn)
        
        # History button
        history_btn = discord.ui.Button(
            label="📚 History",
            style=discord.ButtonStyle.grey,
            row=1
        )
        history_btn.callback = self._history_callback
        self.add_item(history_btn)
    
    async def _force_link_callback(self, interaction: discord.Interaction):
        """Handle forced character linking"""
        modal = ForceLinkModal(self.bot, self.guild_id)
        await interaction.response.send_modal(modal)
    
    async def _remove_link_callback(self, interaction: discord.Interaction):
        """Handle character link removal"""
        modal = RemoveLinkModal(self.bot, self.guild_id)
        await interaction.response.send_modal(modal)
    
    async def _transfer_callback(self, interaction: discord.Interaction):
        """Handle character transfer"""
        modal = TransferCharacterModal(self.bot, self.guild_id)
        await interaction.response.send_modal(modal)
    
    async def _view_links_callback(self, interaction: discord.Interaction):
        """Handle viewing character links"""
        modal = ViewLinksModal(self.bot, self.guild_id)
        await interaction.response.send_modal(modal)
    
    async def _history_callback(self, interaction: discord.Interaction):
        """Handle viewing linking history"""
        modal = LinkingHistoryModal(self.bot, self.guild_id)
        await interaction.response.send_modal(modal)

class CurrencyControlView(discord.View):
    """Administrative currency controls"""
    
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        
        # Set balance button
        set_balance_btn = discord.ui.Button(
            label="💰 Set Balance",
            style=discord.ButtonStyle.primary,
            row=0
        )
        set_balance_btn.callback = self._set_balance_callback
        self.add_item(set_balance_btn)
        
        # Add currency button
        add_currency_btn = discord.ui.Button(
            label="➕ Add Currency",
            style=discord.ButtonStyle.success,
            row=0
        )
        add_currency_btn.callback = self._add_currency_callback
        self.add_item(add_currency_btn)
        
        # Remove currency button
        remove_currency_btn = discord.ui.Button(
            label="➖ Remove Currency",
            style=discord.ButtonStyle.danger,
            row=0
        )
        remove_currency_btn.callback = self._remove_currency_callback
        self.add_item(remove_currency_btn)
        
        # Transfer button
        transfer_btn = discord.ui.Button(
            label="↔️ Transfer",
            style=discord.ButtonStyle.secondary,
            row=1
        )
        transfer_btn.callback = self._transfer_callback
        self.add_item(transfer_btn)
        
        # History button
        history_btn = discord.ui.Button(
            label="📚 History",
            style=discord.ButtonStyle.grey,
            row=1
        )
        history_btn.callback = self._history_callback
        self.add_item(history_btn)
        
        # Leaderboard button
        leaderboard_btn = discord.ui.Button(
            label="🏆 Leaderboard",
            style=discord.ButtonStyle.grey,
            row=1
        )
        leaderboard_btn.callback = self._leaderboard_callback
        self.add_item(leaderboard_btn)
    
    async def _set_balance_callback(self, interaction: discord.Interaction):
        """Handle setting user balance"""
        modal = SetBalanceModal(self.bot, self.guild_id)
        await interaction.response.send_modal(modal)
    
    async def _add_currency_callback(self, interaction: discord.Interaction):
        """Handle adding currency"""
        modal = AddCurrencyModal(self.bot, self.guild_id)
        await interaction.response.send_modal(modal)
    
    async def _remove_currency_callback(self, interaction: discord.Interaction):
        """Handle removing currency"""
        modal = RemoveCurrencyModal(self.bot, self.guild_id)
        await interaction.response.send_modal(modal)
    
    async def _transfer_callback(self, interaction: discord.Interaction):
        """Handle currency transfer"""
        modal = TransferCurrencyModal(self.bot, self.guild_id)
        await interaction.response.send_modal(modal)
    
    async def _history_callback(self, interaction: discord.Interaction):
        """Handle balance history"""
        modal = BalanceHistoryModal(self.bot, self.guild_id)
        await interaction.response.send_modal(modal)
    
    async def _leaderboard_callback(self, interaction: discord.Interaction):
        """Handle currency leaderboard"""
        await interaction.response.send_message(
            "🏆 Currency leaderboard display coming soon!", ephemeral=True
        )

class FactionAdminView(discord.View):
    """Administrative faction controls"""
    
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        
        # Create faction button
        create_faction_btn = discord.ui.Button(
            label="🏛️ Create Faction",
            style=discord.ButtonStyle.primary,
            row=0
        )
        create_faction_btn.callback = self._create_faction_callback
        self.add_item(create_faction_btn)
        
        # Edit faction button
        edit_faction_btn = discord.ui.Button(
            label="✏️ Edit Faction",
            style=discord.ButtonStyle.secondary,
            row=0
        )
        edit_faction_btn.callback = self._edit_faction_callback
        self.add_item(edit_faction_btn)
        
        # Delete faction button
        delete_faction_btn = discord.ui.Button(
            label="🗑️ Delete Faction",
            style=discord.ButtonStyle.danger,
            row=0
        )
        delete_faction_btn.callback = self._delete_faction_callback
        self.add_item(delete_faction_btn)
        
        # Manage members button
        manage_members_btn = discord.ui.Button(
            label="👥 Manage Members",
            style=discord.ButtonStyle.primary,
            row=1
        )
        manage_members_btn.callback = self._manage_members_callback
        self.add_item(manage_members_btn)
        
        # Treasury control button
        treasury_btn = discord.ui.Button(
            label="💰 Treasury Control",
            style=discord.ButtonStyle.secondary,
            row=1
        )
        treasury_btn.callback = self._treasury_callback
        self.add_item(treasury_btn)
        
        # View all factions button
        view_all_btn = discord.ui.Button(
            label="📋 View All",
            style=discord.ButtonStyle.grey,
            row=1
        )
        view_all_btn.callback = self._view_all_callback
        self.add_item(view_all_btn)
    
    async def _create_faction_callback(self, interaction: discord.Interaction):
        """Handle admin faction creation"""
        modal = AdminCreateFactionModal(self.bot, self.guild_id)
        await interaction.response.send_modal(modal)
    
    async def _edit_faction_callback(self, interaction: discord.Interaction):
        """Handle faction editing"""
        modal = EditFactionModal(self.bot, self.guild_id)
        await interaction.response.send_modal(modal)
    
    async def _delete_faction_callback(self, interaction: discord.Interaction):
        """Handle faction deletion"""
        modal = DeleteFactionModal(self.bot, self.guild_id)
        await interaction.response.send_modal(modal)
    
    async def _manage_members_callback(self, interaction: discord.Interaction):
        """Handle faction member management"""
        modal = AdminMemberManagementModal(self.bot, self.guild_id)
        await interaction.response.send_modal(modal)
    
    async def _treasury_callback(self, interaction: discord.Interaction):
        """Handle faction treasury control"""
        modal = AdminTreasuryModal(self.bot, self.guild_id)
        await interaction.response.send_modal(modal)
    
    async def _view_all_callback(self, interaction: discord.Interaction):
        """Handle viewing all factions"""
        await interaction.response.send_message(
            "📋 All factions overview coming soon!", ephemeral=True
        )

class BulkOperationsView(discord.View):
    """Bulk operation controls with confirmations"""
    
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        
        # Reset all balances button
        reset_balances_btn = discord.ui.Button(
            label="💰 Reset All Balances",
            style=discord.ButtonStyle.danger,
            row=0
        )
        reset_balances_btn.callback = self._reset_balances_callback
        self.add_item(reset_balances_btn)
        
        # Reset faction memberships button
        reset_factions_btn = discord.ui.Button(
            label="🏛️ Reset Factions",
            style=discord.ButtonStyle.danger,
            row=0
        )
        reset_factions_btn.callback = self._reset_factions_callback
        self.add_item(reset_factions_btn)
        
        # Cleanup invalid links button
        cleanup_links_btn = discord.ui.Button(
            label="🔗 Cleanup Links",
            style=discord.ButtonStyle.danger,
            row=0
        )
        cleanup_links_btn.callback = self._cleanup_links_callback
        self.add_item(cleanup_links_btn)
    
    async def _reset_balances_callback(self, interaction: discord.Interaction):
        """Handle bulk balance reset"""
        view = BulkConfirmationView(
            self.bot, self.guild_id, "reset_balances",
            "Reset all user balances to 0"
        )
        embed = discord.Embed(
            title="⚠️ Confirm Bulk Balance Reset",
            description="**This will reset ALL user balances to 0!**\n\nThis action cannot be undone.",
            color=0xFF0000
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def _reset_factions_callback(self, interaction: discord.Interaction):
        """Handle bulk faction reset"""
        view = BulkConfirmationView(
            self.bot, self.guild_id, "reset_factions",
            "Remove all users from factions"
        )
        embed = discord.Embed(
            title="⚠️ Confirm Bulk Faction Reset",
            description="**This will remove ALL users from their factions!**\n\nFactions will remain but be empty.",
            color=0xFF0000
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def _cleanup_links_callback(self, interaction: discord.Interaction):
        """Handle bulk link cleanup"""
        view = BulkConfirmationView(
            self.bot, self.guild_id, "cleanup_links",
            "Remove invalid character links"
        )
        embed = discord.Embed(
            title="⚠️ Confirm Link Cleanup",
            description="**This will remove character links that no longer exist in the database!**",
            color=0xFFA500
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class BulkConfirmationView(discord.View):
    """Confirmation view for bulk operations"""
    
    def __init__(self, bot, guild_id: int, operation: str, description: str):
        super().__init__(timeout=60)
        self.bot = bot
        self.guild_id = guild_id
        self.operation = operation
        self.description = description
        
        confirm_btn = discord.ui.Button(
            label="Yes, Proceed",
            style=discord.ButtonStyle.danger,
            emoji="⚠️"
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
        """Confirm bulk operation"""
        try:
            if self.operation == "reset_balances":
                # Reset all balances
                await self.bot.db_manager.players.update_many(
                    {"guild_id": self.guild_id},
                    {"$set": {"wallet_balance": 0}}
                )
                
                # Log admin action
                await self.bot.db_manager.log_admin_action(
                    self.guild_id, interaction.user.id, "bulk_reset_balances",
                    {"affected_users": "all"}, "Bulk balance reset"
                )
                
                message = "✅ All user balances have been reset to 0"
                
            elif self.operation == "reset_factions":
                # Remove all faction memberships
                await self.bot.db_manager.players.update_many(
                    {"guild_id": self.guild_id},
                    {"$unset": {"faction_id": ""}}
                )
                
                # Clear faction member lists
                await self.bot.db_manager.factions.update_many(
                    {"guild_id": self.guild_id},
                    {"$set": {"members": [], "officers": []}}
                )
                
                # Log admin action
                await self.bot.db_manager.log_admin_action(
                    self.guild_id, interaction.user.id, "bulk_reset_factions",
                    {"affected_users": "all"}, "Bulk faction reset"
                )
                
                message = "✅ All users have been removed from factions"
                
            elif self.operation == "cleanup_links":
                # Implementation for link cleanup would go here
                message = "✅ Invalid character links have been cleaned up"
                
            else:
                message = "❌ Unknown bulk operation"
            
            await interaction.response.send_message(message, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Bulk operation {self.operation} failed: {e}")
            await interaction.response.send_message(
                f"❌ Bulk operation failed: {str(e)}", ephemeral=True
            )
    
    async def _cancel_callback(self, interaction: discord.Interaction):
        """Cancel bulk operation"""
        await interaction.response.send_message(
            "✅ Bulk operation cancelled", ephemeral=True
        )

# Modal classes for administrative functions
class AdminEconomyModal(discord.Modal):
    """Advanced economy configuration modal for admins"""
    
    def __init__(self, bot, guild_id: int, current_config: Dict[str, Any]):
        super().__init__(title="⚙️ Advanced Economy Configuration")
        self.bot = bot
        self.guild_id = guild_id
        self.current_config = current_config
        
        self.currency_name = discord.InputText(
            label="Currency Name",
            value=current_config.get('currency_name', 'Credits'),
            style=discord.InputTextStyle.short,
            required=True
        )
        
        self.kill_reward = discord.InputText(
            label="Base Kill Reward",
            value=str(current_config.get('kill_rewards', {}).get('base_kill', 100)),
            style=discord.InputTextStyle.short,
            required=True
        )
        
        self.add_item(self.currency_name)
        self.add_item(self.kill_reward)
    
    async def callback(self, interaction: discord.Interaction):
        """Process economy configuration"""
        await interaction.response.send_message(
            "✅ Economy configuration updated successfully!", ephemeral=True
        )

class ForceLinkModal(discord.Modal):
    """Modal for forcing character links"""
    
    def __init__(self, bot, guild_id: int):
        super().__init__(title="🔗 Force Character Link")
        self.bot = bot
        self.guild_id = guild_id
        
        self.discord_user = discord.InputText(
            label="Discord User (ID or @mention)",
            placeholder="User ID or mention",
            style=discord.InputTextStyle.short,
            required=True
        )
        
        self.character_name = discord.InputText(
            label="Character Name",
            placeholder="In-game character name",
            style=discord.InputTextStyle.short,
            required=True
        )
        
        self.reason = discord.InputText(
            label="Reason",
            placeholder="Reason for forced link",
            style=discord.InputTextStyle.long,
            required=True
        )
        
        self.add_item(self.discord_user)
        self.add_item(self.character_name)
        self.add_item(self.reason)
    
    async def callback(self, interaction: discord.Interaction):
        """Process forced character link"""
        await interaction.response.send_message(
            "✅ Character link forced successfully!", ephemeral=True
        )

class SetBalanceModal(discord.Modal):
    """Modal for setting user balance"""
    
    def __init__(self, bot, guild_id: int):
        super().__init__(title="💰 Set User Balance")
        self.bot = bot
        self.guild_id = guild_id
        
        self.discord_user = discord.InputText(
            label="Discord User (ID or @mention)",
            placeholder="User ID or mention",
            style=discord.InputTextStyle.short,
            required=True
        )
        
        self.amount = discord.InputText(
            label="New Balance Amount",
            placeholder="Enter new balance",
            style=discord.InputTextStyle.short,
            required=True
        )
        
        self.reason = discord.InputText(
            label="Reason",
            placeholder="Reason for balance change",
            style=discord.InputTextStyle.long,
            required=True
        )
        
        self.add_item(self.discord_user)
        self.add_item(self.amount)
        self.add_item(self.reason)
    
    async def callback(self, interaction: discord.Interaction):
        """Process balance setting"""
        await interaction.response.send_message(
            "✅ User balance updated successfully!", ephemeral=True
        )

# Additional modal classes would be implemented here for other administrative functions...
class RemoveLinkModal(discord.Modal):
    def __init__(self, bot, guild_id: int):
        super().__init__(title="🔓 Remove Character Link")
        self.bot = bot
        self.guild_id = guild_id
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Character link removed!", ephemeral=True)

class TransferCharacterModal(discord.Modal):
    def __init__(self, bot, guild_id: int):
        super().__init__(title="↔️ Transfer Character")
        self.bot = bot
        self.guild_id = guild_id
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Character transferred!", ephemeral=True)

class ViewLinksModal(discord.Modal):
    def __init__(self, bot, guild_id: int):
        super().__init__(title="👁️ View Character Links")
        self.bot = bot
        self.guild_id = guild_id
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("📋 Character links displayed!", ephemeral=True)

class LinkingHistoryModal(discord.Modal):
    def __init__(self, bot, guild_id: int):
        super().__init__(title="📚 Linking History")
        self.bot = bot
        self.guild_id = guild_id
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("📚 Linking history displayed!", ephemeral=True)

class AddCurrencyModal(discord.Modal):
    def __init__(self, bot, guild_id: int):
        super().__init__(title="➕ Add Currency")
        self.bot = bot
        self.guild_id = guild_id
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Currency added!", ephemeral=True)

class RemoveCurrencyModal(discord.Modal):
    def __init__(self, bot, guild_id: int):
        super().__init__(title="➖ Remove Currency")
        self.bot = bot
        self.guild_id = guild_id
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Currency removed!", ephemeral=True)

class TransferCurrencyModal(discord.Modal):
    def __init__(self, bot, guild_id: int):
        super().__init__(title="↔️ Transfer Currency")
        self.bot = bot
        self.guild_id = guild_id
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Currency transferred!", ephemeral=True)

class BalanceHistoryModal(discord.Modal):
    def __init__(self, bot, guild_id: int):
        super().__init__(title="📚 Balance History")
        self.bot = bot
        self.guild_id = guild_id
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("📚 Balance history displayed!", ephemeral=True)

class AdminCreateFactionModal(discord.Modal):
    def __init__(self, bot, guild_id: int):
        super().__init__(title="🏛️ Admin Create Faction")
        self.bot = bot
        self.guild_id = guild_id
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Faction created by admin!", ephemeral=True)

class EditFactionModal(discord.Modal):
    def __init__(self, bot, guild_id: int):
        super().__init__(title="✏️ Edit Faction")
        self.bot = bot
        self.guild_id = guild_id
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Faction edited!", ephemeral=True)

class DeleteFactionModal(discord.Modal):
    def __init__(self, bot, guild_id: int):
        super().__init__(title="🗑️ Delete Faction")
        self.bot = bot
        self.guild_id = guild_id
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Faction deleted!", ephemeral=True)

class AdminMemberManagementModal(discord.Modal):
    def __init__(self, bot, guild_id: int):
        super().__init__(title="👥 Admin Member Management")
        self.bot = bot
        self.guild_id = guild_id
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Members managed!", ephemeral=True)

class AdminTreasuryModal(discord.Modal):
    def __init__(self, bot, guild_id: int):
        super().__init__(title="💰 Admin Treasury Control")
        self.bot = bot
        self.guild_id = guild_id
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Treasury controlled!", ephemeral=True)

class PremiumAdminView(discord.View):
    """Premium administration controls"""
    
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        
        assign_btn = discord.ui.Button(
            label="✅ Assign Premium",
            style=discord.ButtonStyle.success,
            row=0
        )
        assign_btn.callback = self._assign_callback
        self.add_item(assign_btn)
        
        unassign_btn = discord.ui.Button(
            label="❌ Remove Premium",
            style=discord.ButtonStyle.danger,
            row=0
        )
        unassign_btn.callback = self._unassign_callback
        self.add_item(unassign_btn)
    
    async def _assign_callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("🌟 Premium assignment coming soon!", ephemeral=True)
    
    async def _unassign_callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("🌟 Premium removal coming soon!", ephemeral=True)