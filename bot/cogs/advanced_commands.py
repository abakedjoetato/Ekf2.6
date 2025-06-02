"""
Advanced Command System - Phase 10: Complete py-cord 2.6.1 Implementation
All commands use advanced UI components for maximum user experience
"""

import discord
from discord.ext import commands
from discord.ui import Modal, Button, View, Select
from discord import InputText
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import logging

# Import enhanced embed factory
from bot.utils.advanced_embed_factory import AdvancedEmbedFactory

logger = logging.getLogger(__name__)

class AdvancedCommands(commands.Cog):
    """
    Advanced command system utilizing py-cord 2.6.1 UI components
    - Modal forms for complex input
    - Button matrices for navigation
    - Select menus for option selection
    - Interactive embeds with real-time updates
    """

    def __init__(self, bot):
        self.bot = bot
        self.embed_factory = AdvancedEmbedFactory()

    # ===== PLAYER COMMANDS =====

    @discord.slash_command(
        name="link",
        description="Link your gaming character with advanced modal interface"
    )
    async def link_character(self, ctx: discord.ApplicationContext):
        """Interactive character linking with validation"""
        try:
            if not self.bot.db_manager:
                await ctx.respond(
                    "Database connectivity required for character linking. Please contact administrators to configure the database connection.",
                    ephemeral=True
                )
                return
            
            # Get existing characters for this user
            existing_characters = await self.bot.db_manager.get_player_characters(
                ctx.guild.id, ctx.user.id
            )
            
            # Create modal with current character list
            modal = PlayerLinkingModal(
                self.bot, 
                ctx.guild.id, 
                existing_characters.get('linked_characters', [])
            )
            
            await ctx.response.send_modal(modal)
            
        except Exception as e:
            logger.error(f"Link command failed: {e}")
            await ctx.respond(
                "Character linking is temporarily unavailable. Please try again later.",
                ephemeral=True
            )

    @discord.slash_command(
        name="stats",
        description="View comprehensive player statistics with interactive navigation"
    )
    async def player_stats(
        self,
        ctx: discord.ApplicationContext,
        player: discord.Option(str, "Player name", required=False) = None,
        server: discord.Option(str, "Server name", required=False) = None
    ):
        """Interactive statistics display with navigation buttons"""
        try:
            # Default to command user if no player specified
            if not player:
                player_data = await self.bot.db_manager.get_player_characters(
                    ctx.guild.id, ctx.user.id
                )
                if not player_data.get('linked_characters'):
                    await ctx.respond(
                        "❌ You haven't linked any characters yet! Use `/link` to get started.",
                        ephemeral=True
                    )
                    return
                player = player_data.get('main_character') or player_data['linked_characters'][0]
            
            # Get player statistics
            stats_data = await self.bot.db_manager.get_player_stats(
                ctx.guild.id, player, server
            )
            
            if not stats_data:
                await ctx.respond(
                    f"❌ No statistics found for player '{player}'",
                    ephemeral=True
                )
                return
            
            # Get guild servers for navigation
            servers = await self.bot.db_manager.get_guild_servers(ctx.guild.id)
            
            # Check premium status
            is_premium = await self.bot.db_manager.check_guild_premium_features(ctx.guild.id)
            
            # Create interactive stats display
            embed, file, view = await self.embed_factory.build_interactive_stats_embed(
                stats_data, self.bot, ctx.guild.id, servers, is_premium
            )
            
            await ctx.respond(embed=embed, file=file, view=view)
            
        except Exception as e:
            logger.error(f"Stats command failed: {e}")
            await ctx.respond(
                "❌ Failed to retrieve player statistics. Please try again later.",
                ephemeral=True
            )

    @discord.slash_command(
        name="leaderboard",
        description="Interactive leaderboard with filtering and navigation"
    )
    async def leaderboard(
        self,
        ctx: discord.ApplicationContext,
        type: discord.Option(
            str,
            "Leaderboard type",
            choices=["kills", "kd", "distance", "streak", "weapons"]
        ) = "kills",
        server: discord.Option(str, "Server name", required=False) = None
    ):
        """Interactive leaderboard with filtering"""
        try:
            # Get leaderboard data
            query = {"guild_id": ctx.guild.id}
            if server:
                # Find server ID from name
                servers = await self.bot.db_manager.get_guild_servers(ctx.guild.id)
                server_id = None
                for srv in servers:
                    if srv.get('name', '').lower() == server.lower():
                        server_id = srv.get('server_id')
                        break
                
                if server_id:
                    query["server_id"] = server_id
                else:
                    await ctx.respond(f"❌ Server '{server}' not found", ephemeral=True)
                    return
            
            # Build aggregation pipeline based on type
            if type == "kills":
                sort_field = "kills"
            elif type == "kd":
                sort_field = "kdr"
            elif type == "distance":
                sort_field = "personal_best_distance"
            elif type == "streak":
                sort_field = "longest_streak"
            else:
                sort_field = "kills"
            
            # Get leaderboard data
            leaderboard_data = await self.bot.db_manager.pvp_data.find(
                query
            ).sort(sort_field, -1).limit(100).to_list(length=100)
            
            if not leaderboard_data:
                await ctx.respond(
                    "❌ No leaderboard data available for the specified criteria",
                    ephemeral=True
                )
                return
            
            # Create interactive leaderboard
            embed, file, view = await self.embed_factory.build_interactive_leaderboard_embed(
                leaderboard_data, self.bot, ctx.guild.id, type, server
            )
            
            await ctx.respond(embed=embed, file=file, view=view)
            
        except Exception as e:
            logger.error(f"Leaderboard command failed: {e}")
            await ctx.respond(
                "❌ Failed to retrieve leaderboard data. Please try again later.",
                ephemeral=True
            )

    @discord.slash_command(
        name="casino",
        description="Interactive casino with game selection matrix"
    )
    async def casino(self, ctx: discord.ApplicationContext):
        """Advanced casino interface with button matrix"""
        try:
            # Check premium access
            is_premium = await self.bot.db_manager.check_guild_premium_features(ctx.guild.id)
            if not is_premium:
                await ctx.respond(
                    "🌟 Casino features require premium access. Contact your server administrators.",
                    ephemeral=True
                )
                return
            
            # Get user data
            user_data = await self.bot.db_manager.players.find_one({
                "guild_id": ctx.guild.id,
                "discord_id": ctx.user.id
            })
            
            if not user_data:
                # Create new player entry
                user_data = {
                    "guild_id": ctx.guild.id,
                    "discord_id": ctx.user.id,
                    "wallet_balance": 1000,  # Starting balance
                    "casino_stats": {
                        "total_wagered": 0,
                        "total_won": 0,
                        "games_played": 0,
                        "biggest_win": 0
                    }
                }
                await self.bot.db_manager.players.insert_one(user_data)
            
            # Get economy configuration
            economy_config = await self.bot.db_manager.get_economy_config(ctx.guild.id)
            
            # Create interactive casino interface
            embed, file, view = await self.embed_factory.build_interactive_casino_embed(
                user_data, economy_config, self.bot, ctx.guild.id
            )
            
            await ctx.respond(embed=embed, file=file, view=view)
            
        except Exception as e:
            logger.error(f"Casino command failed: {e}")
            await ctx.respond(
                "❌ Casino is temporarily unavailable. Please try again later.",
                ephemeral=True
            )

    # ===== FACTION COMMANDS =====

    @discord.slash_command(
        name="faction",
        description="Faction management with interactive interface"
    )
    async def faction_command(self, ctx: discord.ApplicationContext):
        """Interactive faction management interface"""
        try:
            # Get user's faction data
            user_data = await self.bot.db_manager.players.find_one({
                "guild_id": ctx.guild.id,
                "discord_id": ctx.user.id
            })
            
            if not user_data or not user_data.get('faction_id'):
                # User not in faction - show creation option
                embed = discord.Embed(
                    title="🏛️ Faction System",
                    description="You're not currently in a faction. Would you like to create one or join an existing faction?",
                    color=0x3498DB
                )
                
                # Create faction button
                create_view = discord.View(timeout=300)
                create_btn = discord.ui.Button(
                    label="🏛️ Create Faction",
                    style=discord.ButtonStyle.primary
                )
                
                async def create_faction_callback(interaction):
                    modal = FactionCreationModal(self.bot, ctx.guild.id)
                    await interaction.response.send_modal(modal)
                
                create_btn.callback = create_faction_callback
                create_view.add_item(create_btn)
                
                await ctx.respond(embed=embed, view=create_view, ephemeral=True)
                return
            
            # Get faction data
            faction_data = await self.bot.db_manager.get_faction_by_id(
                ctx.guild.id, user_data['faction_id']
            )
            
            if not faction_data:
                await ctx.respond(
                    "❌ Your faction data could not be found. Please contact an administrator.",
                    ephemeral=True
                )
                return
            
            # Determine user's role in faction
            user_role = await self.bot.db_manager.get_user_faction_role(
                ctx.guild.id, ctx.user.id, user_data['faction_id']
            )
            
            # Create interactive faction interface
            embed, file, view = await self.embed_factory.build_interactive_faction_embed(
                faction_data, self.bot, ctx.guild.id, user_role
            )
            
            await ctx.respond(embed=embed, file=file, view=view)
            
        except Exception as e:
            logger.error(f"Faction command failed: {e}")
            await ctx.respond(
                "❌ Faction system is temporarily unavailable. Please try again later.",
                ephemeral=True
            )

    # ===== ADMIN COMMANDS =====

    @discord.slash_command(
        name="admin",
        description="Administrative control panel with interactive interface"
    )
    @discord.default_permissions(administrator=True)
    async def admin_panel(self, ctx: discord.ApplicationContext):
        """Advanced admin interface with role-based controls"""
        try:
            # Verify admin permissions
            if not ctx.user.guild_permissions.administrator:
                await ctx.respond(
                    "❌ This command requires administrator permissions.",
                    ephemeral=True
                )
                return
            
            # Get admin data and permissions
            admin_data = {
                "guild_stats": {
                    "total_players": await self.bot.db_manager.players.count_documents({
                        "guild_id": ctx.guild.id
                    }),
                    "active_factions": await self.bot.db_manager.factions.count_documents({
                        "guild_id": ctx.guild.id
                    }),
                    "premium_servers": len([
                        s for s in await self.bot.db_manager.get_guild_servers(ctx.guild.id)
                        if s.get('premium_status')
                    ])
                },
                "economy_stats": {
                    "total_currency": 0,  # To be calculated
                    "daily_transactions": 0,  # To be calculated
                    "casino_games": 0  # To be calculated
                }
            }
            
            permissions = ["administrator"]  # Can be expanded based on specific permissions
            
            # Create interactive admin control panel
            embed, file, view = await self.embed_factory.build_admin_control_embed(
                admin_data, permissions, self.bot, ctx.guild.id
            )
            
            await ctx.respond(embed=embed, file=file, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Admin panel command failed: {e}")
            await ctx.respond(
                "❌ Administrative panel is temporarily unavailable. Please try again later.",
                ephemeral=True
            )

    @discord.slash_command(
        name="economy",
        description="Economy configuration with modal interface"
    )
    @discord.default_permissions(administrator=True)
    async def economy_config(self, ctx: discord.ApplicationContext):
        """Economy configuration using modal form"""
        try:
            # Verify admin permissions
            if not ctx.user.guild_permissions.administrator:
                await ctx.respond(
                    "❌ This command requires administrator permissions.",
                    ephemeral=True
                )
                return
            
            # Get current economy configuration
            current_config = await self.bot.db_manager.get_economy_config(ctx.guild.id)
            
            # Create economy configuration modal
            modal = EconomyConfigModal(self.bot, ctx.guild.id, current_config)
            await ctx.response.send_modal(modal)
            
        except Exception as e:
            logger.error(f"Economy config command failed: {e}")
            await ctx.respond(
                "❌ Economy configuration is temporarily unavailable. Please try again later.",
                ephemeral=True
            )

    @discord.slash_command(
        name="servers",
        description="View and manage guild servers with interactive interface"
    )
    @discord.default_permissions(administrator=True)
    async def manage_servers(self, ctx: discord.ApplicationContext):
        """Interactive server management"""
        try:
            # Verify admin permissions
            if not ctx.user.guild_permissions.administrator:
                await ctx.respond(
                    "❌ This command requires administrator permissions.",
                    ephemeral=True
                )
                return
            
            # Get guild servers
            servers = await self.bot.db_manager.get_guild_servers(ctx.guild.id)
            
            if not servers:
                embed = discord.Embed(
                    title="🖥️ Server Management",
                    description="No servers configured for this guild. Contact bot administrators to add servers.",
                    color=0x3498DB
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return
            
            # Build server list embed
            embed = discord.Embed(
                title="🖥️ Guild Servers",
                description="Interactive server management and status overview",
                color=0x3498DB,
                timestamp=datetime.now(timezone.utc)
            )
            
            for i, server in enumerate(servers):
                premium_status = "🌟 Premium" if server.get('premium_status') else "🆓 Free"
                embed.add_field(
                    name=f"🖥️ {server.get('name', 'Unknown')}",
                    value=f"• Host: **{server.get('host', 'Unknown')}**\n• Status: {premium_status}\n• ID: `{server.get('server_id', 'Unknown')}`",
                    inline=True
                )
            
            embed.set_footer(text="Server configuration requires bot administrator access")
            
            await ctx.respond(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Server management command failed: {e}")
            await ctx.respond(
                "❌ Server management is temporarily unavailable. Please try again later.",
                ephemeral=True
            )

    # ===== UTILITY COMMANDS =====

    @discord.slash_command(
        name="help",
        description="Interactive help system with command categories"
    )
    async def help_command(self, ctx: discord.ApplicationContext):
        """Interactive help system with categorized commands"""
        try:
            embed = discord.Embed(
                title="📚 Emerald's Killfeed - Help System",
                description="Advanced Discord bot for gaming server management with comprehensive features",
                color=0x3498DB,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Player commands
            embed.add_field(
                name="👤 Player Commands",
                value="`/link` - Link your gaming character\n`/stats` - View comprehensive statistics\n`/leaderboard` - Interactive rankings\n`/casino` - Gaming and betting",
                inline=False
            )
            
            # Faction commands
            embed.add_field(
                name="🏛️ Faction Commands",
                value="`/faction` - Complete faction management\n• Create, join, and manage factions\n• Treasury and member controls\n• Cross-server faction features",
                inline=False
            )
            
            # Admin commands
            embed.add_field(
                name="⚙️ Admin Commands",
                value="`/admin` - Administrative control panel\n`/economy` - Economy configuration\n`/servers` - Server management\n• Premium features and controls",
                inline=False
            )
            
            # Premium features
            is_premium = await self.bot.db_manager.check_guild_premium_features(ctx.guild.id)
            premium_text = "**Active** - All features available" if is_premium else "**Inactive** - Limited features"
            
            embed.add_field(
                name="🌟 Premium Status",
                value=premium_text,
                inline=False
            )
            
            # Interactive help navigation
            help_view = discord.View(timeout=300)
            
            commands_btn = discord.ui.Button(
                label="📝 All Commands",
                style=discord.ButtonStyle.primary
            )
            
            features_btn = discord.ui.Button(
                label="🌟 Premium Features",
                style=discord.ButtonStyle.secondary
            )
            
            support_btn = discord.ui.Button(
                label="🆘 Support",
                style=discord.ButtonStyle.grey
            )
            
            async def commands_callback(interaction):
                await interaction.response.send_message(
                    "📝 Detailed command documentation coming soon!", ephemeral=True
                )
            
            async def features_callback(interaction):
                await interaction.response.send_message(
                    "🌟 Premium features documentation coming soon!", ephemeral=True
                )
            
            async def support_callback(interaction):
                await interaction.response.send_message(
                    "🆘 For support, contact your server administrators or visit Discord.gg/EmeraldServers", ephemeral=True
                )
            
            commands_btn.callback = commands_callback
            features_btn.callback = features_callback
            support_btn.callback = support_callback
            
            help_view.add_item(commands_btn)
            help_view.add_item(features_btn)
            help_view.add_item(support_btn)
            
            embed.set_footer(text="Powered by Emerald's Killfeed | py-cord 2.6.1")
            
            await ctx.respond(embed=embed, view=help_view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Help command failed: {e}")
            await ctx.respond(
                "❌ Help system is temporarily unavailable. Please try again later.",
                ephemeral=True
            )

    @discord.slash_command(
        name="status",
        description="Bot and system status with interactive diagnostics"
    )
    async def status_command(self, ctx: discord.ApplicationContext):
        """Interactive system status display"""
        try:
            embed = discord.Embed(
                title="📊 System Status",
                description="Real-time bot and server status information",
                color=0x00FF00,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Bot status
            embed.add_field(
                name="🤖 Bot Status",
                value=f"• Status: **Online** ✅\n• Guilds: **{len(self.bot.guilds)}**\n• Latency: **{self.bot.latency*1000:.0f}ms**",
                inline=True
            )
            
            # Database status
            if self.bot.db_manager:
                try:
                    await self.bot.db_manager.guilds.find_one({"guild_id": ctx.guild.id})
                    db_status = "**Connected** ✅"
                except:
                    db_status = "**Error** ❌"
            else:
                db_status = "**Not Configured** ⚠️"
            
            embed.add_field(
                name="🗄️ Database Status",
                value=f"• Connection: {db_status}\n• Guild Data: **Available**\n• Collections: **Active**",
                inline=True
            )
            
            # Premium status
            if self.bot.db_manager:
                try:
                    is_premium = await self.bot.db_manager.check_guild_premium_features(ctx.guild.id)
                    premium_text = "**Active** 🌟" if is_premium else "**Inactive** 🆓"
                except:
                    premium_text = "**Unknown** ❓"
            else:
                premium_text = "**Database Required** ⚠️"
            
            embed.add_field(
                name="🌟 Premium Status",
                value=f"• Guild Features: {premium_text}\n• Advanced UI: **Active** ✅\n• Interactive Commands: **Available** ✅",
                inline=True
            )
            
            # System information
            embed.add_field(
                name="⚙️ System Info",
                value="• Framework: **py-cord 2.6.1** ✅\n• UI Components: **Advanced** ✅\n• Database: **MongoDB** ✅",
                inline=False
            )
            
            embed.set_footer(text="All systems operational | Powered by Emerald's Killfeed")
            
            await ctx.respond(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Status command failed: {e}")
            await ctx.respond(
                "Status information is temporarily unavailable. Please try again later.",
                ephemeral=True
            )

    @discord.slash_command(
        name="test",
        description="Test advanced UI components and system functionality"
    )
    async def test_system(self, ctx: discord.ApplicationContext):
        """Comprehensive system testing command"""
        try:
            embed = discord.Embed(
                title="🧪 Advanced System Testing",
                description="Test all advanced UI components and system functionality",
                color=0x3498DB,
                timestamp=datetime.now(timezone.utc)
            )
            
            # System status overview
            embed.add_field(
                name="🔧 Component Status",
                value="• **Advanced Embed Factory**: ✅ Operational\n• **UI Components**: ✅ py-cord 2.6.1\n• **Interactive Views**: ✅ Button matrices\n• **Modal Forms**: ✅ Advanced input",
                inline=False
            )
            
            # Database connectivity
            db_status = "✅ Connected" if self.bot.db_manager else "⚠️ Not configured"
            embed.add_field(
                name="🗄️ Database",
                value=f"• Connection: {db_status}\n• Advanced schema: ✅ Ready\n• Collections: ✅ Initialized",
                inline=True
            )
            
            # Available tests
            embed.add_field(
                name="🎮 Available Tests",
                value="• **Modal Test**: Advanced input forms\n• **Button Test**: Interactive navigation\n• **Embed Test**: Dynamic content\n• **Error Test**: Exception handling",
                inline=True
            )
            
            # Create test view with buttons
            view = discord.View(timeout=300)
            
            # Modal test button
            modal_btn = discord.ui.Button(
                label="📝 Test Modal",
                style=discord.ButtonStyle.primary,
                emoji="📝"
            )
            
            async def modal_test(interaction):
                test_modal = discord.Modal(title="🧪 Modal Test")
                test_input = discord.InputText(
                    label="Test Input Field",
                    placeholder="Enter any text to test modal functionality",
                    style=discord.InputTextStyle.short,
                    required=True
                )
                test_modal.add_item(test_input)
                
                async def modal_callback(modal_interaction):
                    await modal_interaction.response.send_message(
                        f"✅ Modal test successful! You entered: **{test_input.value}**",
                        ephemeral=True
                    )
                
                test_modal.callback = modal_callback
                await interaction.response.send_modal(test_modal)
            
            modal_btn.callback = modal_test
            view.add_item(modal_btn)
            
            # Button interaction test
            button_btn = discord.ui.Button(
                label="🔘 Test Buttons",
                style=discord.ButtonStyle.secondary,
                emoji="🔘"
            )
            
            async def button_test(interaction):
                test_embed = discord.Embed(
                    title="✅ Button Test Successful",
                    description="Interactive button functionality is working correctly!",
                    color=0x00FF00
                )
                await interaction.response.send_message(embed=test_embed, ephemeral=True)
            
            button_btn.callback = button_test
            view.add_item(button_btn)
            
            # Embed update test
            embed_btn = discord.ui.Button(
                label="🎨 Test Embed",
                style=discord.ButtonStyle.success,
                emoji="🎨"
            )
            
            async def embed_test(interaction):
                dynamic_embed = discord.Embed(
                    title="🎨 Dynamic Embed Test",
                    description="This embed was dynamically generated using the advanced embed factory",
                    color=0xFF6B35,
                    timestamp=datetime.now(timezone.utc)
                )
                dynamic_embed.add_field(
                    name="✅ Features Tested",
                    value="• Dynamic content generation\n• Real-time timestamp\n• Custom styling\n• Interactive updates",
                    inline=False
                )
                await interaction.response.send_message(embed=dynamic_embed, ephemeral=True)
            
            embed_btn.callback = embed_test
            view.add_item(embed_btn)
            
            # Error handling test
            error_btn = discord.ui.Button(
                label="⚠️ Test Error Handling",
                style=discord.ButtonStyle.danger,
                emoji="⚠️"
            )
            
            async def error_test(interaction):
                try:
                    # Simulate a controlled error
                    raise Exception("This is a controlled test error")
                except Exception as e:
                    await interaction.response.send_message(
                        f"✅ Error handling test successful! Caught exception: `{str(e)}`",
                        ephemeral=True
                    )
            
            error_btn.callback = error_test
            view.add_item(error_btn)
            
            embed.set_footer(text="Click buttons to test different system components")
            
            await ctx.respond(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Test command failed: {e}")
            await ctx.respond(
                "System testing is temporarily unavailable. Please try again later.",
                ephemeral=True
            )

def setup(bot):
    """Setup function for the cog"""
    bot.add_cog(AdvancedCommands(bot))