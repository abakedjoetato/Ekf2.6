"""
Emerald's Killfeed - Premium Management System (PHASE 9)
/sethome by BOT_OWNER_ID
Game server management via /gameserver commands
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any

import discord
from discord.ext import commands
from bot.cogs.autocomplete import ServerAutocomplete

logger = logging.getLogger(__name__)

class Premium(discord.Cog):
    """
    PREMIUM MGMT (PHASE 9)
    - /sethome by BOT_OWNER_ID
    - /gameserver add, /gameserver list, /gameserver remove, /gameserver refresh
    - Premium individual server management handled by subscription_management.py
    """

    def __init__(self, bot):
        self.bot = bot
        self.bot_owner_id = int(os.getenv('BOT_OWNER_ID', 0))

    def is_bot_owner(self, user_id: int) -> bool:
        """Check if user is the bot owner"""
        import os
        bot_owner_id = int(os.getenv('BOT_OWNER_ID', 0))
        return user_id == bot_owner_id

    @discord.slash_command(name="sethome", description="Set this server as the bot's home server")
    async def sethome(self, ctx: discord.ApplicationContext):
        """Set this server as the bot's home server (BOT_OWNER_ID only)"""
        try:
            # Check if user is bot owner
            if not self.is_bot_owner(ctx.user.id):
                await ctx.respond("Only the bot owner can use this command!", ephemeral=True)
                return

            guild_id = ctx.guild.id if ctx.guild else None
            if not guild_id:
                await ctx.respond("This command must be used in a server!", ephemeral=True)
                return

            # Update or create guild as home server
            await self.bot.db_manager.guilds.update_one(
                {"guild_id": guild_id},
                {
                    "$set": {
                        "guild_id": guild_id,
                        "name": ctx.guild.name,
                        "is_home_server": True,
                        "created_at": datetime.now(timezone.utc),
                        "servers": [],
                        "channels": {}
                    }
                },
                upsert=True
            )

            # Remove home server status from other guilds
            await self.bot.db_manager.guilds.update_many(
                {"guild_id": {"$ne": guild_id}},
                {"$unset": {"is_home_server": ""}}
            )

            guild_name = ctx.guild.name if ctx.guild else "Unknown Guild"
            embed = discord.Embed(
                title="🏠 Home Server Set",
                description=f"**{guild_name}** has been set as the bot's home server!",
                color=0x00FF00,
                timestamp=datetime.now(timezone.utc)
            )

            embed.add_field(
                name="Benefits",
                value="• Full access to all premium features\n• Administrative controls\n• Premium management commands",
                inline=False
            )

            main_file = discord.File("./assets/main.png", filename="main.png")
            embed.set_thumbnail(url="attachment://main.png")
            embed.set_footer(text="Powered by Discord.gg/EmeraldServers")

            await ctx.respond(embed=embed, file=main_file)

        except Exception as e:
            logger.error(f"Failed to set home server: {e}")
            await ctx.respond("Failed to set home server.", ephemeral=True)

    gameserver = discord.SlashCommandGroup("gameserver", "Game server management commands")

    @gameserver.command(name="add", description="Add a game server with SFTP credentials to this guild")
    @discord.default_permissions(administrator=True)
    async def server_add(self, ctx: discord.ApplicationContext):
        """Add a game server with full SFTP credentials to the guild"""
        
        class ServerAddModal(discord.ui.Modal):
            def __init__(self):
                super().__init__(title="Add Game Server")
                
                self.server_name = discord.ui.InputText(
                    label="Server Name",
                    placeholder="e.g., Main PvP Server",
                    max_length=50
                )
                self.server_id = discord.ui.InputText(
                    label="Server ID",
                    placeholder="e.g., server1 (unique identifier)",
                    max_length=20
                )
                self.host_port = discord.ui.InputText(
                    label="Host:Port",
                    placeholder="e.g., 192.168.1.100:22",
                    max_length=100
                )
                self.username = discord.ui.InputText(
                    label="SFTP Username",
                    placeholder="Username for SFTP access",
                    max_length=50
                )
                self.password = discord.ui.InputText(
                    label="SFTP Password",
                    placeholder="Password for SFTP access",
                    max_length=100,
                    style=discord.InputTextStyle.short
                )
                
                self.add_item(self.server_name)
                self.add_item(self.server_id)
                self.add_item(self.host_port)
                self.add_item(self.username)
                self.add_item(self.password)
            
            async def callback(self, interaction: discord.Interaction):
                await interaction.response.defer(ephemeral=True)
                
                # Extract values from modal inputs with null safety
                name = (self.server_name.value or "").strip()
                serverid = (self.server_id.value or "").strip()
                host_port = (self.host_port.value or "").strip()
                username = (self.username.value or "").strip()
                password = (self.password.value or "").strip()
                
                # Parse host:port
                if ':' in host_port:
                    host, port_str = host_port.rsplit(':', 1)
                    try:
                        port = int(port_str)
                    except ValueError:
                        await interaction.followup.send("Port must be a valid number!", ephemeral=True)
                        return
                else:
                    host = host_port
                    port = 22  # Default SFTP port
                
                # Process the server addition
                guild_id = interaction.guild.id if interaction.guild else None
                
                # Validate inputs
                if not all([serverid, name, host, username, password]):
                    await interaction.followup.send("All fields are required!", ephemeral=True)
                    return

                if not (1 <= port <= 65535):
                    await interaction.followup.send("Port must be between 1 and 65535", ephemeral=True)
                    return

                # Get bot instance from interaction
                bot = interaction.client
                
                # Get or create guild (access db_manager safely)
                if hasattr(bot, 'db_manager'):
                    guild_config = await bot.db_manager.get_guild(guild_id)
                    if not guild_config:
                        guild_name = interaction.guild.name if interaction.guild else "Unknown Guild"
                        guild_config = await bot.db_manager.create_guild(guild_id, guild_name)
                else:
                    await interaction.followup.send("Database system not available!", ephemeral=True)
                    return

                # Check if server already exists
                existing_servers = guild_config.get('servers', [])
                for server in existing_servers:
                    if server and server.get('_id') == serverid:
                        await interaction.followup.send(f"Server **{serverid}** is already added!", ephemeral=True)
                        return

                # Create server config with full SFTP credentials and enable by default
                # Dynamic log path based on host and server ID
                log_path = f"./{host}_{serverid}/Logs/Deadside.log"
                
                server_config = {
                    '_id': serverid,
                    'server_id': serverid,
                    'name': name,
                    'server_name': name,
                    'host': host,
                    'hostname': host,
                    'port': port,
                    'username': username,
                    'password': password,
                    'enabled': True,  # Enable server by default for immediate data collection
                    'log_path': log_path,  # Dynamic log path based on server specifics
                    'added_at': datetime.now(timezone.utc),
                    'updated_at': datetime.now(timezone.utc)
                }

                # Add server to guild config
                add_result = await bot.db_manager.add_server_to_guild(guild_id, server_config)
                
                if add_result:
                    logger.info(f"✅ Server {serverid} successfully added to guild {guild_id}")
                    
                    # Verify server was saved by checking database
                    guild_config = await bot.db_manager.get_guild(guild_id)
                    servers_count = len(guild_config.get('servers', [])) if guild_config else 0
                    logger.info(f"📊 Guild now has {servers_count} servers configured")
                    
                    logger.info(f"✅ Server {serverid} added successfully - ready for parsing")
                else:
                    logger.error(f"❌ Failed to add server {serverid} to database")

                # Respond with success
                embed = discord.Embed(
                    title="Server Added",
                    description=f"Server **{name}** has been added to this guild!",
                    color=0x00FF00,
                    timestamp=datetime.now(timezone.utc)
                )

                embed.add_field(
                    name="Server Details",
                    value=f"**ID:** {serverid}\n**Host:** {host}:{port}\n**Username:** {username}",
                    inline=False
                )

                embed.add_field(
                    name="Background Processing",
                    value="The system is now connecting to verify credentials and parse historical data.",
                    inline=False
                )

                main_file = discord.File("./assets/main.png", filename="main.png")
                embed.set_thumbnail(url="attachment://main.png")
                embed.set_footer(text="Powered by Discord.gg/EmeraldServers")

                await interaction.followup.send(embed=embed, file=main_file, ephemeral=False)
        
        modal = ServerAddModal()
        await ctx.send_modal(modal)

    @gameserver.command(name="list", description="List all configured servers in this guild")
    async def server_list(self, ctx: discord.ApplicationContext):
        """List all servers configured in this guild"""
        try:
            guild_id = (ctx.guild.id if ctx.guild else None)

            # Get guild configuration
            guild_config = await self.bot.db_manager.get_guild(guild_id)

            if not guild_config:
                await ctx.respond("This guild is not configured!", ephemeral=True)
                return

            servers = guild_config.get('servers', [])

            if not servers:
                embed = discord.Embed(
                    title="Server List",
                    description="No servers configured for this guild.",
                    color=0x808080,
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(
                    name="Next Steps",
                    value="Use `/gameserver add` to add a game server.",
                    inline=False
                )
                embed.set_footer(text="Powered by Discord.gg/EmeraldServers")
                await ctx.respond(embed=embed)
                return

            # Create server list embed
            embed = discord.Embed(
                title="Server List",
                description=f"Configured servers for **{ctx.guild.name}**",
                color=0x3498DB,
                timestamp=datetime.now(timezone.utc)
            )

            # Add server details
            for server in servers:
                server_id = str(server.get('server_id', server.get('_id', server.get('id', 'unknown'))))
                server_name = server.get('name', server.get('server_name', f'Server {server_id}'))
                sftp_host = server.get('host', server.get('hostname', 'Not configured'))
                sftp_port = server.get('port', 22)

                # Format server details
                server_details = f"**Host:** {sftp_host}:{sftp_port}\n**Status:** Available"

                embed.add_field(
                    name=f"{server_name} (ID: {server_id})",
                    value=server_details,
                    inline=False
                )

            main_file = discord.File("./assets/main.png", filename="main.png")
            embed.set_thumbnail(url="attachment://main.png")
            embed.set_footer(text="Powered by Discord.gg/EmeraldServers")

            await ctx.respond(embed=embed, file=main_file)

        except Exception as e:
            logger.error(f"Failed to list servers: {e}")
            await ctx.respond("Failed to list servers. Please try again.", ephemeral=True)

    @gameserver.command(name="remove", description="Remove a server from this guild")
    @discord.default_permissions(administrator=True)
    async def server_remove(self, ctx: discord.ApplicationContext, 
                           server: discord.Option(str, "Select a server to remove", autocomplete=ServerAutocomplete.autocomplete_server_name)):
        """Remove a server from the guild"""
        try:
            guild_id = (ctx.guild.id if ctx.guild else None)
            server_id = server

            # Get guild configuration
            guild_config = await self.bot.db_manager.get_guild(guild_id)

            if not guild_config:
                await ctx.respond("This guild is not configured!", ephemeral=True)
                return

            # Find server in the guild config
            servers = guild_config.get('servers', [])
            server_found = False
            server_name = "Unknown Server"

            for srv in servers:
                srv_id = str(srv.get('_id', srv.get('server_id', 'unknown')))
                if srv_id == server_id:
                    server_found = True
                    server_name = srv.get('name', srv.get('server_name', f'Server {server_id}'))
                    break

            if not server_found:
                await ctx.respond(f"Server **{server_id}** not found in this guild!", ephemeral=True)
                return

            # Remove server from guild config
            result = await self.bot.db_manager.remove_server_from_guild(guild_id, server_id)

            if result:
                embed = discord.Embed(
                    title="Server Removed",
                    description=f"The server **{server_name}** has been removed from this guild.",
                    color=0x00FF00,
                    timestamp=datetime.now(timezone.utc)
                )

                main_file = discord.File("./assets/main.png", filename="main.png")
                embed.set_thumbnail(url="attachment://main.png")
                embed.set_footer(text="Powered by Discord.gg/EmeraldServers")

                await ctx.respond(embed=embed, file=main_file)
            else:
                await ctx.respond("Failed to remove server. Please try again.", ephemeral=True)

        except Exception as e:
            logger.error(f"Failed to remove server: {e}")
            await ctx.respond("Failed to remove server. Please try again.", ephemeral=True)

    @gameserver.command(name="refresh", description="Refresh data for a server")
    @discord.default_permissions(administrator=True)
    async def server_refresh(self, ctx: discord.ApplicationContext, 
                            server: discord.Option(str, "Select a server to refresh", autocomplete=ServerAutocomplete.autocomplete_server_name)):
        """Refresh data for a server"""
        # Defer immediately to prevent timeout
        await ctx.response.defer(ephemeral=True)
        
        try:
            guild_id = (ctx.guild.id if ctx.guild else None)
            server_id = server

            # Get guild configuration
            guild_config = await self.bot.db_manager.get_guild(guild_id)

            if not guild_config:
                await ctx.followup.send("This guild is not configured!", ephemeral=True)
                return

            # Find server in the guild config
            servers = guild_config.get('servers', [])
            server_found = False
            server_config = None
            server_name = "Unknown Server"

            for srv in servers:
                srv_id = str(srv.get('_id', srv.get('server_id', 'unknown')))
                if srv_id == server_id:
                    server_found = True
                    server_config = srv
                    server_name = srv.get('name', srv.get('server_name', f'Server {server_id}'))
                    break

            if not server_found:
                await ctx.followup.send(f"Server **{server_id}** not found in this guild!", ephemeral=True)
                return

            # Trigger refresh with the bot's historical parser directly and pass target channel
            if hasattr(self.bot, 'historical_parser') and self.bot.historical_parser:
                try:
                    await self.bot.historical_parser.auto_refresh_after_server_add(guild_id, server_config, ctx.channel)
                    
                    embed = discord.Embed(
                        title="Server Refresh Started",
                        description=f"Data refresh has been triggered for server **{server_name}**.",
                        color=0x3498DB,
                        timestamp=datetime.now(timezone.utc)
                    )

                    embed.add_field(
                        name="Processing",
                        value="The system is now refreshing server data. This may take a few minutes.",
                        inline=False
                    )

                    main_file = discord.File("./assets/main.png", filename="main.png")
                    embed.set_thumbnail(url="attachment://main.png")
                    embed.set_footer(text="Powered by Discord.gg/EmeraldServers")

                    await ctx.followup.send(embed=embed, file=main_file, ephemeral=True)

                except Exception as e:
                    logger.error(f"Failed to trigger refresh: {e}")
                    await ctx.followup.send("Failed to trigger server refresh. Please try again.", ephemeral=True)
            else:
                await ctx.followup.send("Parser system not available for refresh.", ephemeral=True)

        except Exception as e:
            logger.error(f"Failed to refresh server: {e}")
            await ctx.followup.send("Failed to refresh server. Please try again.", ephemeral=True)

def setup(bot):
    bot.add_cog(Premium(bot))