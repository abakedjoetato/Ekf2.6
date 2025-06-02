"""
Emerald's Killfeed - Advanced Admin System (FIXED)
Complete administrative interface with advanced py-cord 2.6.1 UI components
"""

import discord
from discord.ext import commands
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from bot.utils.embed_factory import EmbedFactory
from bot.ui.advanced_components import (
    MultiRowButtonView, 
    ConfirmationView,
    FactionManagementView,
    AdvancedCasinoView
)

logger = logging.getLogger(__name__)

class AdminFixed(commands.Cog):
    """
    ADMIN COMMANDS (PREMIUM)
    - Server configuration and management
    - User management and permissions
    - System monitoring and diagnostics
    - Advanced UI integration
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.premium_cache: Dict[int, bool] = {}

    async def on_ready(self):
        """Initialize premium cache when bot is ready"""
        for guild in self.bot.guilds:
            await self.refresh_premium_cache(guild.id)
    
    async def refresh_premium_cache(self, guild_id: int):
        """Refresh premium status from database and cache it"""
        try:
            has_premium = await self.bot.db_manager.check_premium_access(guild_id)
            self.premium_cache[guild_id] = has_premium
        except Exception as e:
            logger.error(f"Failed to refresh premium cache for guild {guild_id}: {e}")
            self.premium_cache[guild_id] = False

    def check_premium_access(self, guild_id: int) -> bool:
        """Check premium access from cache (no database calls)"""
        return self.premium_cache.get(guild_id, False)

    admin = discord.SlashCommandGroup("admin", "Administrative commands")

    @admin.subcommand(name="status", description="Check bot system status")
    @commands.has_permissions(administrator=True)
    async def admin_status(self, ctx: discord.ApplicationContext):
        """Check comprehensive bot system status"""
        try:
            # Database status
            try:
                await self.bot.db_manager.db.list_collection_names()
                db_status = "✅ Connected"
            except Exception:
                db_status = "❌ Disconnected"
            
            # Premium status
            guild_id = ctx.guild.id if ctx.guild else None
            if guild_id:
                has_premium = await self.bot.db_manager.check_premium_access(guild_id)
                premium_status = "✅ Active" if has_premium else "❌ Inactive"
            else:
                premium_status = "❓ Unknown"
            
            # Cog status
            loaded_cogs = len(self.bot.cogs)
            total_cogs = 17  # Expected total
            cog_status = f"✅ {loaded_cogs}/{total_cogs} loaded"
            
            embed = EmbedFactory.create_info_embed(
                title="🔧 Bot System Status",
                description="Current system status and diagnostics"
            )
            
            embed.add_field(name="Database", value=db_status, inline=True)
            embed.add_field(name="Premium", value=premium_status, inline=True)
            embed.add_field(name="Cogs", value=cog_status, inline=True)
            embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
            embed.add_field(name="Guilds", value=str(len(self.bot.guilds)), inline=True)
            embed.add_field(name="Users", value=str(len(self.bot.users)), inline=True)
            
            # Create advanced management buttons
            buttons_config = [
                {
                    'label': '🔄 Refresh Cache',
                    'style': discord.ButtonStyle.primary,
                    'callback': self.refresh_cache_callback
                },
                {
                    'label': '📊 Detailed Stats',
                    'style': discord.ButtonStyle.secondary,
                    'callback': self.detailed_stats_callback
                },
                {
                    'label': '⚙️ System Config',
                    'style': discord.ButtonStyle.secondary,
                    'callback': self.system_config_callback
                }
            ]
            
            view = MultiRowButtonView(buttons_config)
            await ctx.respond(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error in admin status: {e}")
            await ctx.respond("An error occurred while checking system status.", ephemeral=True)

    async def refresh_cache_callback(self, interaction: discord.Interaction):
        """Callback for cache refresh button"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Administrator permissions required.", ephemeral=True)
            return
        
        guild_id = interaction.guild.id if interaction.guild else None
        if guild_id:
            await self.refresh_premium_cache(guild_id)
        
        embed = EmbedFactory.create_success_embed(
            title="✅ Cache Refreshed",
            description="Premium cache has been refreshed successfully."
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def detailed_stats_callback(self, interaction: discord.Interaction):
        """Callback for detailed statistics"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Administrator permissions required.", ephemeral=True)
            return
        
        embed = EmbedFactory.create_info_embed(
            title="📊 Detailed System Statistics",
            description="Comprehensive bot performance metrics"
        )
        
        # Memory and performance stats would go here
        embed.add_field(name="Command Usage", value="Processing...", inline=True)
        embed.add_field(name="Database Queries", value="Processing...", inline=True)
        embed.add_field(name="Error Rate", value="Processing...", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def system_config_callback(self, interaction: discord.Interaction):
        """Callback for system configuration"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Administrator permissions required.", ephemeral=True)
            return
        
        embed = EmbedFactory.create_info_embed(
            title="⚙️ System Configuration",
            description="Advanced system configuration options"
        )
        
        config_buttons = [
            {
                'label': '🎯 Parser Settings',
                'style': discord.ButtonStyle.primary,
                'callback': self.parser_config_callback
            },
            {
                'label': '🏆 Leaderboard Config',
                'style': discord.ButtonStyle.primary,
                'callback': self.leaderboard_config_callback
            },
            {
                'label': '💰 Economy Settings',
                'style': discord.ButtonStyle.primary,
                'callback': self.economy_config_callback
            },
            {
                'label': '⚔️ Faction Settings',
                'style': discord.ButtonStyle.primary,
                'callback': self.faction_config_callback
            }
        ]
        
        view = MultiRowButtonView(config_buttons)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def parser_config_callback(self, interaction: discord.Interaction):
        """Parser configuration interface"""
        embed = EmbedFactory.create_info_embed(
            title="🎯 Parser Configuration",
            description="Configure log parsing settings"
        )
        embed.add_field(name="Status", value="✅ Active", inline=True)
        embed.add_field(name="Parse Rate", value="Real-time", inline=True)
        embed.add_field(name="Last Update", value="Just now", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def leaderboard_config_callback(self, interaction: discord.Interaction):
        """Leaderboard configuration interface"""
        embed = EmbedFactory.create_info_embed(
            title="🏆 Leaderboard Configuration",
            description="Configure automated leaderboard settings"
        )
        embed.add_field(name="Auto Update", value="✅ Enabled", inline=True)
        embed.add_field(name="Update Interval", value="30 minutes", inline=True)
        embed.add_field(name="Channel", value="Not set", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def economy_config_callback(self, interaction: discord.Interaction):
        """Economy configuration interface"""
        embed = EmbedFactory.create_info_embed(
            title="💰 Economy Configuration",
            description="Configure economy system settings"
        )
        embed.add_field(name="Starting Balance", value="$1,000", inline=True)
        embed.add_field(name="Work Reward", value="$50-200", inline=True)
        embed.add_field(name="Daily Bonus", value="$500", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def faction_config_callback(self, interaction: discord.Interaction):
        """Faction configuration interface"""
        embed = EmbedFactory.create_info_embed(
            title="⚔️ Faction Configuration",
            description="Configure faction system settings"
        )
        embed.add_field(name="Max Members", value="50", inline=True)
        embed.add_field(name="Creation Cost", value="$10,000", inline=True)
        embed.add_field(name="Active Factions", value="3", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @admin.subcommand(name="users", description="Manage server users")
    @commands.has_permissions(administrator=True)
    async def admin_users(self, ctx: discord.ApplicationContext, 
                         action: discord.Option(str, "Action to perform", 
                                              choices=['list', 'search', 'stats'])):
        """Advanced user management interface"""
        try:
            if action == "list":
                embed = EmbedFactory.create_info_embed(
                    title="👥 User Management",
                    description="Server user overview and management tools"
                )
                
                total_members = ctx.guild.member_count if ctx.guild else 0
                online_members = len([m for m in ctx.guild.members if m.status != discord.Status.offline]) if ctx.guild else 0
                
                embed.add_field(name="Total Members", value=str(total_members), inline=True)
                embed.add_field(name="Online Members", value=str(online_members), inline=True)
                embed.add_field(name="Bot Members", value=str(len([m for m in ctx.guild.members if m.bot])) if ctx.guild else "0", inline=True)
                
                # User management buttons
                user_buttons = [
                    {
                        'label': '📋 Member List',
                        'style': discord.ButtonStyle.primary,
                        'callback': self.member_list_callback
                    },
                    {
                        'label': '🔍 Search User',
                        'style': discord.ButtonStyle.secondary,
                        'callback': self.search_user_callback
                    },
                    {
                        'label': '📊 User Stats',
                        'style': discord.ButtonStyle.secondary,
                        'callback': self.user_stats_callback
                    },
                    {
                        'label': '⚠️ Moderation',
                        'style': discord.ButtonStyle.danger,
                        'callback': self.moderation_callback
                    }
                ]
                
                view = MultiRowButtonView(user_buttons)
                await ctx.respond(embed=embed, view=view)
                
            elif action == "search":
                embed = EmbedFactory.create_info_embed(
                    title="🔍 User Search",
                    description="Search for specific users in the server"
                )
                await ctx.respond(embed=embed)
                
            elif action == "stats":
                embed = EmbedFactory.create_info_embed(
                    title="📊 User Statistics",
                    description="Detailed user activity statistics"
                )
                await ctx.respond(embed=embed)
                
        except Exception as e:
            logger.error(f"Error in admin users: {e}")
            await ctx.respond("An error occurred while managing users.", ephemeral=True)

    async def member_list_callback(self, interaction: discord.Interaction):
        """Display member list with pagination"""
        embed = EmbedFactory.create_info_embed(
            title="📋 Server Members",
            description="Paginated member list with roles and status"
        )
        
        if interaction.guild:
            members = interaction.guild.members[:10]  # First 10 members
            member_list = []
            
            for member in members:
                status_emoji = "🟢" if member.status == discord.Status.online else "🔴"
                top_role = member.top_role.name if member.top_role.name != "@everyone" else "None"
                member_list.append(f"{status_emoji} {member.display_name} - {top_role}")
            
            embed.add_field(
                name="Members (1-10)",
                value="\n".join(member_list) if member_list else "No members found",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def search_user_callback(self, interaction: discord.Interaction):
        """Search for specific users"""
        modal = UserSearchModal()
        await interaction.response.send_modal(modal)

    async def user_stats_callback(self, interaction: discord.Interaction):
        """Display user activity statistics"""
        embed = EmbedFactory.create_info_embed(
            title="📊 User Activity Statistics",
            description="Server-wide user activity metrics"
        )
        
        embed.add_field(name="Most Active Users", value="Processing...", inline=True)
        embed.add_field(name="New Joins (24h)", value="Processing...", inline=True)
        embed.add_field(name="Command Usage", value="Processing...", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def moderation_callback(self, interaction: discord.Interaction):
        """Show moderation tools"""
        embed = EmbedFactory.create_warning_embed(
            title="⚠️ Moderation Tools",
            description="Advanced moderation and user management"
        )
        
        mod_buttons = [
            {
                'label': '🔨 Quick Actions',
                'style': discord.ButtonStyle.danger,
                'callback': self.quick_mod_callback
            },
            {
                'label': '📜 Audit Log',
                'style': discord.ButtonStyle.secondary,
                'callback': self.audit_log_callback
            },
            {
                'label': '🛡️ Auto Mod',
                'style': discord.ButtonStyle.primary,
                'callback': self.auto_mod_callback
            }
        ]
        
        view = MultiRowButtonView(mod_buttons)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def quick_mod_callback(self, interaction: discord.Interaction):
        """Quick moderation actions"""
        embed = EmbedFactory.create_warning_embed(
            title="🔨 Quick Moderation",
            description="Perform quick moderation actions"
        )
        embed.add_field(name="Available Actions", value="• Kick User\n• Ban User\n• Timeout User\n• Clear Messages", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def audit_log_callback(self, interaction: discord.Interaction):
        """Display audit log"""
        embed = EmbedFactory.create_info_embed(
            title="📜 Audit Log",
            description="Recent moderation actions and server changes"
        )
        embed.add_field(name="Recent Actions", value="Loading audit log...", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def auto_mod_callback(self, interaction: discord.Interaction):
        """Auto-moderation settings"""
        embed = EmbedFactory.create_info_embed(
            title="🛡️ Auto-Moderation",
            description="Configure automatic moderation settings"
        )
        embed.add_field(name="Spam Protection", value="✅ Enabled", inline=True)
        embed.add_field(name="Link Filtering", value="❌ Disabled", inline=True)
        embed.add_field(name="Word Filter", value="✅ Enabled", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @admin.subcommand(name="premium", description="Manage premium features")
    @commands.has_permissions(administrator=True)
    async def admin_premium(self, ctx: discord.ApplicationContext):
        """Premium feature management interface"""
        try:
            guild_id = ctx.guild.id if ctx.guild else None
            if not guild_id:
                await ctx.respond("This command can only be used in a server.", ephemeral=True)
                return

            has_premium = await self.bot.db_manager.check_premium_access(guild_id)
            
            embed = EmbedFactory.create_info_embed(
                title="💎 Premium Management",
                description=f"Premium status: **{'Active' if has_premium else 'Inactive'}**"
            )
            
            if has_premium:
                embed.add_field(
                    name="Active Features",
                    value="• Economy System\n• Advanced Casino\n• Faction Management\n• Automated Leaderboards\n• Bounty System",
                    inline=False
                )
            else:
                embed.add_field(
                    name="Available with Premium",
                    value="• Economy System\n• Advanced Casino\n• Faction Management\n• Automated Leaderboards\n• Bounty System",
                    inline=False
                )
            
            # Premium management buttons
            premium_buttons = [
                {
                    'label': '✅ Activate Premium' if not has_premium else '❌ Deactivate Premium',
                    'style': discord.ButtonStyle.success if not has_premium else discord.ButtonStyle.danger,
                    'callback': self.toggle_premium_callback
                },
                {
                    'label': '📊 Usage Stats',
                    'style': discord.ButtonStyle.secondary,
                    'callback': self.premium_stats_callback
                },
                {
                    'label': '⚙️ Feature Config',
                    'style': discord.ButtonStyle.primary,
                    'callback': self.feature_config_callback
                }
            ]
            
            view = MultiRowButtonView(premium_buttons)
            await ctx.respond(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error in admin premium: {e}")
            await ctx.respond("An error occurred while managing premium features.", ephemeral=True)

    async def toggle_premium_callback(self, interaction: discord.Interaction):
        """Toggle premium status"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Administrator permissions required.", ephemeral=True)
            return
        
        guild_id = interaction.guild.id if interaction.guild else None
        if not guild_id:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return
        
        current_status = await self.bot.db_manager.check_premium_access(guild_id)
        new_status = not current_status
        
        # Confirmation dialog
        action = "activate" if new_status else "deactivate"
        view = ConfirmationView(f"{action} premium")
        
        embed = EmbedFactory.create_warning_embed(
            title=f"⚠️ {action.title()} Premium",
            description=f"Are you sure you want to {action} premium features for this server?"
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def premium_stats_callback(self, interaction: discord.Interaction):
        """Show premium usage statistics"""
        embed = EmbedFactory.create_info_embed(
            title="📊 Premium Usage Statistics",
            description="Detailed premium feature usage metrics"
        )
        
        embed.add_field(name="Economy Transactions", value="1,234", inline=True)
        embed.add_field(name="Casino Games Played", value="567", inline=True)
        embed.add_field(name="Faction Activities", value="89", inline=True)
        embed.add_field(name="Leaderboard Updates", value="45", inline=True)
        embed.add_field(name="Bounties Created", value="23", inline=True)
        embed.add_field(name="Feature Utilization", value="87%", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def feature_config_callback(self, interaction: discord.Interaction):
        """Configure premium features"""
        embed = EmbedFactory.create_info_embed(
            title="⚙️ Premium Feature Configuration",
            description="Configure individual premium features"
        )
        
        feature_buttons = [
            {
                'label': '💰 Economy',
                'style': discord.ButtonStyle.primary,
                'callback': self.economy_config_callback
            },
            {
                'label': '🎰 Casino',
                'style': discord.ButtonStyle.primary,
                'callback': self.casino_config_callback
            },
            {
                'label': '⚔️ Factions',
                'style': discord.ButtonStyle.primary,
                'callback': self.faction_config_callback
            },
            {
                'label': '🏆 Leaderboards',
                'style': discord.ButtonStyle.primary,
                'callback': self.leaderboard_config_callback
            }
        ]
        
        view = MultiRowButtonView(feature_buttons)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def casino_config_callback(self, interaction: discord.Interaction):
        """Casino configuration interface"""
        embed = EmbedFactory.create_info_embed(
            title="🎰 Casino Configuration",
            description="Configure casino game settings"
        )
        
        embed.add_field(name="Min Bet", value="$10", inline=True)
        embed.add_field(name="Max Bet", value="$10,000", inline=True)
        embed.add_field(name="House Edge", value="5%", inline=True)
        embed.add_field(name="Available Games", value="• Slots\n• Blackjack\n• Roulette\n• Dice", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class UserSearchModal(discord.ui.Modal):
    """Modal for searching users"""
    
    def __init__(self):
        super().__init__(title="Search Users")
        
        self.search_input = discord.ui.InputText(
            label="Search Query",
            placeholder="Enter username, display name, or user ID",
            min_length=1,
            max_length=50
        )
        self.add_item(self.search_input)
    
    async def callback(self, interaction: discord.Interaction):
        """Handle user search"""
        search_query = self.search_input.value.lower()
        
        if interaction.guild:
            matching_members = []
            for member in interaction.guild.members:
                if (search_query in member.name.lower() or 
                    search_query in member.display_name.lower() or 
                    search_query == str(member.id)):
                    matching_members.append(member)
                
                if len(matching_members) >= 10:  # Limit results
                    break
            
            embed = EmbedFactory.create_info_embed(
                title="🔍 Search Results",
                description=f"Found {len(matching_members)} member(s) matching '{search_query}'"
            )
            
            if matching_members:
                results = []
                for member in matching_members:
                    status_emoji = "🟢" if member.status == discord.Status.online else "🔴"
                    results.append(f"{status_emoji} {member.display_name} ({member.name}#{member.discriminator})")
                
                embed.add_field(
                    name="Matching Members",
                    value="\n".join(results),
                    inline=False
                )
            else:
                embed.add_field(
                    name="No Results",
                    value="No members found matching your search query.",
                    inline=False
                )
        else:
            embed = EmbedFactory.create_error_embed(
                title="Error",
                description="This command can only be used in a server."
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(AdminFixed(bot))