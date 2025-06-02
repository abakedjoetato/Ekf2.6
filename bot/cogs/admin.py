#!/usr/bin/env python3
"""
Admin System Cog - Server management and system controls
"""

import discord
from discord.ext import commands
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Admin(commands.Cog):
    """Admin commands for server management"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @discord.slash_command(name="admin", description="Admin commands")
    @commands.has_permissions(administrator=True)
    async def admin_group(self, ctx: discord.ApplicationContext):
        """Admin command group"""
        pass
    
    @admin_group.subcommand(name="status", description="Check bot system status")
    async def admin_status(self, ctx: discord.ApplicationContext):
        """Check bot system status"""
        try:
            # Check database connection
            db_status = "✅ Connected"
            try:
                await self.bot.db.admin.command('ping')
            except:
                db_status = "❌ Disconnected"
            
            # Check guild registration
            guild_id = ctx.guild.id if ctx.guild else None
            guild_doc = None
            if guild_id:
                guild_doc = await self.bot.db.guild_features.find_one({"guild_id": guild_id})
            
            embed = discord.Embed(
                title="🔧 Bot System Status",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="Database", value=db_status, inline=True)
            embed.add_field(name="Guilds", value=f"{len(self.bot.guilds)}", inline=True)
            embed.add_field(name="Latency", value=f"{self.bot.latency*1000:.1f}ms", inline=True)
            
            if guild_doc:
                premium_count = len(guild_doc.get('premium_servers', []))
                embed.add_field(name="Premium Servers", value=str(premium_count), inline=True)
            
            await ctx.respond(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in admin status: {e}")
            await ctx.respond("❌ An error occurred while checking status.", ephemeral=True)
    
    @admin_group.command(name="sync", description="Sync slash commands")
    async def admin_sync(self, ctx: discord.ApplicationContext):
        """Sync slash commands"""
        try:
            await ctx.defer(ephemeral=True)
            
            synced = await self.bot.sync_commands()
            
            embed = discord.Embed(
                title="🔄 Commands Synced",
                description=f"Successfully synced {len(synced)} commands",
                color=discord.Color.green()
            )
            
            await ctx.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error syncing commands: {e}")
            await ctx.respond("❌ An error occurred while syncing commands.", ephemeral=True)
    
    @admin_group.command(name="register_server", description="Register a server with this guild")
    async def admin_register_server(
        self,
        ctx: discord.ApplicationContext,
        server_id: discord.Option(int, description="Server ID to register"),
        server_name: discord.Option(str, description="Server name")
    ):
        """Register a server with this guild"""
        try:
            guild_id = ctx.guild.id if ctx.guild else None
            if not guild_id:
                await ctx.respond("❌ This command can only be used in a server.", ephemeral=True)
                return
            
            # Check if server already exists
            existing_server = await self.bot.db.servers.find_one({"server_id": server_id})
            if existing_server:
                await ctx.respond(f"❌ Server {server_id} is already registered.", ephemeral=True)
                return
            
            # Register server
            server_doc = {
                "server_id": server_id,
                "server_name": server_name,
                "guild_id": guild_id,
                "created_at": datetime.now(),
                "is_active": True
            }
            
            await self.bot.db.servers.insert_one(server_doc)
            
            embed = discord.Embed(
                title="🎮 Server Registered",
                description=f"✅ Server **{server_name}** (ID: {server_id}) has been registered with this guild.",
                color=discord.Color.green()
            )
            
            await ctx.respond(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error registering server: {e}")
            await ctx.respond("❌ An error occurred while registering the server.", ephemeral=True)

def setup(bot):
    bot.add_cog(Admin(bot))