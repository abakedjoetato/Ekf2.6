#!/usr/bin/env python3
"""
Advanced Premium System - 10/10 py-cord 2.6.1 Implementation
Server-scoped premium subscriptions with guild feature unlocking
"""

import discord
from discord.ext import commands
from discord import SlashCommandGroup, Option, default_permissions
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import asyncio

logger = logging.getLogger(__name__)

class AdvancedPremium(discord.Cog):
    """
    Advanced Premium Management System
    - Server-scoped premium subscriptions
    - Guild feature unlocking (1+ premium server enables guild features) 
    - Premium validation with advanced caching
    - Administrative controls with proper permissions
    """
    
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.db_manager = bot.db_manager
        self.logger = logging.getLogger(__name__)
        
        # Premium tier configurations
        self.premium_tiers = {
            "basic": {
                "name": "Basic Premium",
                "features": ["analytics", "leaderboards", "killfeed_customization"],
                "price": 5.00,
                "description": "Essential analytics and leaderboard features"
            },
            "premium": {
                "name": "Premium Plus", 
                "features": ["analytics", "leaderboards", "killfeed_customization", "advanced_stats", "export"],
                "price": 10.00,
                "description": "Advanced statistics and data export capabilities"
            },
            "enterprise": {
                "name": "Enterprise",
                "features": ["analytics", "leaderboards", "killfeed_customization", "advanced_stats", "export", "api_access", "priority_support"],
                "price": 25.00,
                "description": "Complete feature set with API access and priority support"
            }
        }
    
    # Advanced premium command group
    premium = SlashCommandGroup(
        name="premium",
        description="Premium subscription management",
        default_member_permissions=discord.Permissions(administrator=True)
    )
    
    @premium.command(
        name="status",
        description="Check premium status for servers in this guild"
    )
    async def premium_status(
        self,
        ctx: discord.ApplicationContext,
        server_id: Option(int, "Server ID to check (optional)", required=False) = None
    ):
        """Check premium status with detailed information"""
        await ctx.defer()
        
        try:
            if not ctx.guild:
                await ctx.respond("❌ This command can only be used in a server.", ephemeral=True)
                return
            
            embed = discord.Embed(
                title="🌟 Premium Status",
                color=discord.Color.gold(),
                timestamp=datetime.utcnow()
            )
            
            if server_id:
                # Check specific server
                server_config = await self.db_manager.get_server_config(server_id)
                if not server_config:
                    await ctx.respond("❌ Server not found in database.", ephemeral=True)
                    return
                
                if server_config.guild_id != ctx.guild.id:
                    await ctx.respond("❌ Server does not belong to this guild.", ephemeral=True)
                    return
                
                is_premium = await self.db_manager.check_server_premium(server_id)
                
                embed.add_field(
                    name=f"Server {server_id} ({server_config.server_name})",
                    value=f"**Status:** {'🟢 Premium' if is_premium else '🔴 Free'}\n"
                          f"**Tier:** {server_config.premium_tier or 'None'}\n"
                          f"**Features:** {', '.join(server_config.features.keys()) if server_config.features else 'Basic killfeed only'}",
                    inline=False
                )
            else:
                # Check all servers in guild
                guild_features_enabled = await self.db_manager.check_guild_features_enabled(ctx.guild.id)
                premium_servers = await self.db_manager.get_guild_premium_servers(ctx.guild.id)
                
                embed.add_field(
                    name="Guild Premium Status",
                    value=f"**Features Enabled:** {'🟢 Yes' if guild_features_enabled else '🔴 No'}\n"
                          f"**Premium Servers:** {len(premium_servers)}\n"
                          f"**Server IDs:** {', '.join(map(str, premium_servers)) if premium_servers else 'None'}",
                    inline=False
                )
                
                # List all servers in guild
                cursor = self.db_manager.db.servers.find({"guild_id": ctx.guild.id})
                servers = await cursor.to_list(length=None)
                
                if servers:
                    server_list = []
                    for server in servers:
                        status = "🟢 Premium" if server['premium_status'] else "🔴 Free"
                        server_list.append(f"**{server['server_id']}** ({server['server_name']}): {status}")
                    
                    embed.add_field(
                        name="All Servers",
                        value="\n".join(server_list) if server_list else "No servers registered",
                        inline=False
                    )
            
            embed.set_footer(text=f"Requested by {ctx.author.display_name}")
            await ctx.respond(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Error in premium_status: {e}")
            await ctx.respond("❌ An error occurred while checking premium status.", ephemeral=True)
    
    @premium.command(
        name="add",
        description="Add premium subscription to a server"
    )
    @default_permissions(administrator=True)
    async def add_premium(
        self,
        ctx: discord.ApplicationContext,
        server_id: Option(int, "Server ID to upgrade"),
        tier: Option(str, "Premium tier", choices=["basic", "premium", "enterprise"]),
        duration: Option(int, "Duration in days", min_value=1, max_value=365) = 30
    ):
        """Add premium subscription to server"""
        await ctx.defer()
        
        try:
            if not ctx.guild:
                await ctx.respond("❌ This command can only be used in a server.", ephemeral=True)
                return
            
            # Verify server exists and belongs to guild
            server_config = await self.db_manager.get_server_config(server_id)
            if not server_config:
                await ctx.respond("❌ Server not found. Please register the server first.", ephemeral=True)
                return
            
            if server_config.guild_id != ctx.guild.id:
                await ctx.respond("❌ Server does not belong to this guild.", ephemeral=True)
                return
            
            # Add premium subscription
            success = await self.db_manager.add_premium_subscription(
                server_id=server_id,
                guild_id=ctx.guild.id,
                tier=tier,
                duration_days=duration
            )
            
            if success:
                tier_info = self.premium_tiers[tier]
                expires_at = datetime.utcnow() + timedelta(days=duration)
                
                embed = discord.Embed(
                    title="✅ Premium Subscription Added",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(
                    name="Server Details",
                    value=f"**Server ID:** {server_id}\n"
                          f"**Server Name:** {server_config.server_name}\n"
                          f"**Tier:** {tier_info['name']}\n"
                          f"**Duration:** {duration} days\n"
                          f"**Expires:** {expires_at.strftime('%Y-%m-%d %H:%M:%S')} UTC",
                    inline=False
                )
                
                embed.add_field(
                    name="Features Enabled",
                    value=", ".join(tier_info['features']),
                    inline=False
                )
                
                # Check if this enables guild features
                guild_features_enabled = await self.db_manager.check_guild_features_enabled(ctx.guild.id)
                if guild_features_enabled:
                    embed.add_field(
                        name="🎉 Guild Features Unlocked",
                        value="This guild now has access to cross-server analytics, guild leaderboards, and advanced admin tools!",
                        inline=False
                    )
                
                embed.set_footer(text=f"Added by {ctx.author.display_name}")
                await ctx.respond(embed=embed)
                
            else:
                await ctx.respond("❌ Failed to add premium subscription. Please try again.", ephemeral=True)
                
        except Exception as e:
            self.logger.error(f"Error in add_premium: {e}")
            await ctx.respond("❌ An error occurred while adding premium subscription.", ephemeral=True)
    
    @premium.command(
        name="remove",
        description="Remove premium subscription from a server"
    )
    @default_permissions(administrator=True)
    async def remove_premium(
        self,
        ctx: discord.ApplicationContext,
        server_id: Option(int, "Server ID to downgrade")
    ):
        """Remove premium subscription from server"""
        await ctx.defer()
        
        try:
            if not ctx.guild:
                await ctx.respond("❌ This command can only be used in a server.", ephemeral=True)
                return
            
            # Verify server exists and belongs to guild
            server_config = await self.db_manager.get_server_config(server_id)
            if not server_config:
                await ctx.respond("❌ Server not found.", ephemeral=True)
                return
            
            if server_config.guild_id != ctx.guild.id:
                await ctx.respond("❌ Server does not belong to this guild.", ephemeral=True)
                return
            
            # Remove premium subscription
            success = await self.db_manager.update_server_premium_status(server_id, False, None)
            
            if success:
                # Deactivate subscription
                await self.db_manager.db.premium_subscriptions.update_one(
                    {"server_id": server_id},
                    {"$set": {"is_active": False, "deactivated_at": datetime.utcnow()}}
                )
                
                embed = discord.Embed(
                    title="✅ Premium Subscription Removed",
                    color=discord.Color.orange(),
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(
                    name="Server Details",
                    value=f"**Server ID:** {server_id}\n"
                          f"**Server Name:** {server_config.server_name}\n"
                          f"**Status:** Now Free (killfeed only)",
                    inline=False
                )
                
                # Check if guild still has premium features
                guild_features_enabled = await self.db_manager.check_guild_features_enabled(ctx.guild.id)
                if not guild_features_enabled:
                    embed.add_field(
                        name="⚠️ Guild Features Disabled",
                        value="This guild no longer has any premium servers. Guild-wide features have been disabled.",
                        inline=False
                    )
                
                embed.set_footer(text=f"Removed by {ctx.author.display_name}")
                await ctx.respond(embed=embed)
                
            else:
                await ctx.respond("❌ Failed to remove premium subscription. Please try again.", ephemeral=True)
                
        except Exception as e:
            self.logger.error(f"Error in remove_premium: {e}")
            await ctx.respond("❌ An error occurred while removing premium subscription.", ephemeral=True)
    
    @premium.command(
        name="tiers",
        description="View available premium tiers and features"
    )
    async def premium_tiers_command(self, ctx: discord.ApplicationContext):
        """Display premium tiers and features"""
        embed = discord.Embed(
            title="🌟 Premium Tiers",
            description="Choose the perfect plan for your server",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        
        for tier_id, tier_info in self.premium_tiers.items():
            features_text = "\n".join([f"• {feature.replace('_', ' ').title()}" for feature in tier_info['features']])
            
            embed.add_field(
                name=f"{tier_info['name']} - ${tier_info['price']}/month",
                value=f"{tier_info['description']}\n\n**Features:**\n{features_text}",
                inline=True
            )
        
        embed.add_field(
            name="💡 How It Works",
            value="• Premium is purchased per server\n"
                  "• Having 1+ premium servers unlocks guild-wide features\n"
                  "• Free servers only provide killfeed output\n"
                  "• Premium servers contribute to guild analytics",
            inline=False
        )
        
        embed.set_footer(text="Use /premium add to upgrade a server")
        await ctx.respond(embed=embed)
    
    @premium.command(
        name="features",
        description="Check what features are available for this guild"
    )
    async def premium_features(self, ctx: discord.ApplicationContext):
        """Display available features based on premium status"""
        await ctx.defer()
        
        try:
            if not ctx.guild:
                await ctx.respond("❌ This command can only be used in a server.", ephemeral=True)
                return
            
            guild_features_enabled = await self.db_manager.check_guild_features_enabled(ctx.guild.id)
            premium_servers = await self.db_manager.get_guild_premium_servers(ctx.guild.id)
            
            embed = discord.Embed(
                title="🎯 Available Features",
                color=discord.Color.green() if guild_features_enabled else discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            
            if guild_features_enabled:
                embed.add_field(
                    name="✅ Guild Features (Enabled)",
                    value="• Cross-server analytics\n"
                          "• Guild-wide leaderboards\n"
                          "• Advanced admin tools\n"
                          "• Custom configurations\n"
                          "• Data export capabilities",
                    inline=True
                )
                
                embed.add_field(
                    name="🟢 Premium Servers",
                    value=f"**Count:** {len(premium_servers)}\n"
                          f"**IDs:** {', '.join(map(str, premium_servers)) if premium_servers else 'None'}",
                    inline=True
                )
            else:
                embed.add_field(
                    name="❌ Guild Features (Disabled)",
                    value="No premium servers in this guild.\n"
                          "Upgrade at least one server to unlock guild-wide features.",
                    inline=False
                )
            
            embed.add_field(
                name="📊 Available for All Servers",
                value="• Basic killfeed output\n"
                      "• Player session tracking\n"
                      "• Server registration",
                inline=False
            )
            
            embed.set_footer(text=f"Guild ID: {ctx.guild.id}")
            await ctx.respond(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Error in premium_features: {e}")
            await ctx.respond("❌ An error occurred while checking features.", ephemeral=True)
    
    # Utility methods for other cogs
    async def check_server_premium_access(self, server_id: int) -> bool:
        """Check if server has premium access - for use by other cogs"""
        return await self.db_manager.check_server_premium(server_id)
    
    async def check_guild_premium_access(self, guild_id: int) -> bool:
        """Check if guild has premium features enabled - for use by other cogs"""
        return await self.db_manager.check_guild_features_enabled(guild_id)
    
    async def require_server_premium(self, ctx: discord.ApplicationContext, server_id: int) -> bool:
        """Require server premium for command execution"""
        has_premium = await self.check_server_premium_access(server_id)
        if not has_premium:
            embed = discord.Embed(
                title="🌟 Premium Required",
                description="This feature requires a premium subscription for the specified server.",
                color=discord.Color.gold()
            )
            embed.add_field(
                name="Upgrade Now",
                value="Use `/premium add` to upgrade this server and unlock advanced features.",
                inline=False
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return False
        return True
    
    async def require_guild_premium(self, ctx: discord.ApplicationContext) -> bool:
        """Require guild premium features for command execution"""
        if not ctx.guild:
            return False
            
        has_premium = await self.check_guild_premium_access(ctx.guild.id)
        if not has_premium:
            embed = discord.Embed(
                title="🌟 Premium Required",
                description="This feature requires at least one premium server in your guild.",
                color=discord.Color.gold()
            )
            embed.add_field(
                name="Upgrade Now",
                value="Use `/premium add` to upgrade a server and unlock guild-wide features.",
                inline=False
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return False
        return True
    
    @discord.Cog.listener()
    async def on_ready(self):
        """Initialize premium system on bot ready"""
        self.logger.info("✅ Advanced Premium System loaded")

def setup(bot):
    bot.add_cog(AdvancedPremium(bot))