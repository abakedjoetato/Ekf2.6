"""
Enhanced Statistics System - Player Stats with Integrated Rivalries
Comprehensive player statistics with autocomplete and comparison features
"""

import discord
from discord.ext import commands
from discord import SlashCommandGroup, Option
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class StatisticsEnhanced(discord.Cog):
    """
    ENHANCED STATISTICS SYSTEM
    - Player statistics with integrated rivalry information
    - Server-scoped data with intelligent autocomplete
    - Player comparison functionality
    - Weapon and combat statistics
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.stats_cache = {}
        
    async def get_configured_servers(self, guild_id: int) -> List[Dict[str, Any]]:
        """Get all configured servers for a guild"""
        try:
            guild_config = await self.bot.db_manager.guilds.find_one({"guild_id": guild_id})
            if guild_config and 'servers' in guild_config:
                return guild_config['servers']
            return []
        except Exception as e:
            logger.error(f"Failed to get configured servers: {e}")
            return []
    
    async def get_players_for_guild(self, guild_id: int, server_id: str = None) -> List[str]:
        """Get all players with statistics for a guild/server"""
        try:
            query = {"guild_id": guild_id}
            if server_id:
                query["server_id"] = server_id
            
            players = await self.bot.db_manager.player_stats.distinct("player_name", query)
            return sorted(players)
        except Exception as e:
            logger.error(f"Failed to get players: {e}")
            return []
    
    async def get_player_statistics(self, guild_id: int, player_name: str, server_id: str = None) -> Dict[str, Any]:
        """Get comprehensive player statistics including rivalries"""
        try:
            query = {"guild_id": guild_id, "player_name": player_name}
            if server_id:
                query["server_id"] = server_id
            
            # Get basic stats
            stats = await self.bot.db_manager.player_stats.find_one(query)
            if not stats:
                return None
            
            # Get rivalry information
            rivalries = await self.get_player_rivalries(guild_id, player_name, server_id)
            stats['rivalries'] = rivalries
            
            # Get recent activity
            recent_kills = await self.bot.db_manager.kill_events.find(
                {**query, "killer": player_name},
                sort=[("timestamp", -1)],
                limit=5
            ).to_list(5)
            
            recent_deaths = await self.bot.db_manager.kill_events.find(
                {**query, "victim": player_name},
                sort=[("timestamp", -1)],
                limit=5
            ).to_list(5)
            
            stats['recent_kills'] = recent_kills
            stats['recent_deaths'] = recent_deaths
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get player statistics: {e}")
            return None
    
    async def get_player_rivalries(self, guild_id: int, player_name: str, server_id: str = None) -> Dict[str, Any]:
        """Get player rivalry information"""
        try:
            query = {
                "guild_id": guild_id,
                "$or": [
                    {"player_a": player_name},
                    {"player_b": player_name}
                ]
            }
            if server_id:
                query["server_id"] = server_id
            
            rivalries = await self.bot.db_manager.player_encounters.find(query).to_list(None)
            
            nemesis = None
            prey = None
            nemesis_deficit = 0
            prey_advantage = 0
            
            for rivalry in rivalries:
                if rivalry["player_a"] == player_name:
                    # Player A is our target player
                    kills_for = rivalry["encounters"]["a_killed_b"]
                    kills_against = rivalry["encounters"]["b_killed_a"]
                    opponent = rivalry["player_b"]
                else:
                    # Player B is our target player
                    kills_for = rivalry["encounters"]["b_killed_a"]
                    kills_against = rivalry["encounters"]["a_killed_b"]
                    opponent = rivalry["player_a"]
                
                # Check for nemesis (someone who kills us more)
                if kills_against > kills_for:
                    deficit = kills_against - kills_for
                    if deficit > nemesis_deficit:
                        nemesis_deficit = deficit
                        nemesis = {
                            "player": opponent,
                            "their_kills": kills_against,
                            "our_kills": kills_for,
                            "deficit": deficit
                        }
                
                # Check for prey (someone we kill more)
                if kills_for > kills_against:
                    advantage = kills_for - kills_against
                    if advantage > prey_advantage:
                        prey_advantage = advantage
                        prey = {
                            "player": opponent,
                            "our_kills": kills_for,
                            "their_kills": kills_against,
                            "advantage": advantage
                        }
            
            return {
                "nemesis": nemesis,
                "prey": prey,
                "total_rivalries": len(rivalries)
            }
            
        except Exception as e:
            logger.error(f"Failed to get player rivalries: {e}")
            return {"nemesis": None, "prey": None, "total_rivalries": 0}
    
    # Autocomplete functions
    async def server_autocomplete(self, ctx: discord.AutocompleteContext):
        """Autocomplete for configured servers"""
        try:
            servers = await self.get_configured_servers(ctx.interaction.guild_id)
            choices = []
            
            for server in servers:
                server_name = server.get('name', 'Unknown Server')
                server_id = server.get('_id', 'unknown')
                
                # Add status indicator
                status = "🟢" if server.get('connection_status') == 'connected' else "🔴"
                display_name = f"{status} {server_name}"
                
                choices.append(discord.OptionChoice(name=display_name, value=server_id))
            
            # Add "All Servers" option
            choices.insert(0, discord.OptionChoice(name="🌐 All Servers", value="all"))
            
            return choices[:25]
            
        except Exception as e:
            logger.error(f"Server autocomplete error: {e}")
            return []
    
    async def player_autocomplete(self, ctx: discord.AutocompleteContext):
        """Autocomplete for players with recent activity priority"""
        try:
            guild_id = ctx.interaction.guild_id
            current_input = ctx.value.lower() if ctx.value else ""
            
            # Get players from all servers
            players = await self.get_players_for_guild(guild_id)
            
            # Filter and sort players
            if current_input:
                filtered_players = [p for p in players if current_input in p.lower()]
            else:
                filtered_players = players
            
            choices = []
            for player in filtered_players[:25]:
                # Get last activity for display
                try:
                    last_activity = await self.bot.db_manager.kill_events.find_one(
                        {
                            "guild_id": guild_id,
                            "$or": [{"killer": player}, {"victim": player}]
                        },
                        sort=[("timestamp", -1)]
                    )
                    
                    if last_activity and last_activity.get('timestamp'):
                        timestamp = last_activity['timestamp']
                        display_name = f"{player} (Last seen: <t:{int(timestamp.timestamp())}:R>)"
                    else:
                        display_name = f"{player} (No recent activity)"
                        
                except:
                    display_name = player
                
                choices.append(discord.OptionChoice(name=display_name, value=player))
            
            return choices
            
        except Exception as e:
            logger.error(f"Player autocomplete error: {e}")
            return []
    
    # Command group
    stats = SlashCommandGroup("stats", "Enhanced statistics and player information")
    
    @stats.command(name="player", description="View comprehensive player statistics")
    async def player_stats(self,
                          ctx: discord.ApplicationContext,
                          player: Option(str, "Player name", autocomplete=player_autocomplete),
                          server: Option(str, "Specific server (optional)", autocomplete=server_autocomplete, required=False)):
        """Display comprehensive player statistics with integrated rivalries"""
        await ctx.defer(ephemeral=True)
        
        try:
            guild_id = ctx.guild.id
            server_id = server if server and server != "all" else None
            
            # Get player statistics
            stats = await self.get_player_statistics(guild_id, player, server_id)
            if not stats:
                await ctx.followup.send(f"❌ No statistics found for player **{player}**", ephemeral=True)
                return
            
            # Create comprehensive embed
            embed = discord.Embed(
                title=f"📊 Player Statistics - {player}",
                color=0x3498DB,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Server context
            if server_id:
                servers = await self.get_configured_servers(guild_id)
                server_info = next((s for s in servers if s.get('_id') == server_id), None)
                server_name = server_info.get('name', server_id) if server_info else server_id
                embed.add_field(name="Server", value=server_name, inline=True)
            else:
                embed.add_field(name="Data Scope", value="All Servers", inline=True)
            
            # Basic combat statistics
            kills = stats.get('kills', 0)
            deaths = stats.get('deaths', 0)
            kd_ratio = round(kills / deaths, 2) if deaths > 0 else kills
            
            embed.add_field(name="Kills", value=f"{kills:,}", inline=True)
            embed.add_field(name="Deaths", value=f"{deaths:,}", inline=True)
            embed.add_field(name="K/D Ratio", value=f"{kd_ratio}", inline=True)
            
            # Distance and accuracy stats
            if 'total_distance' in stats:
                avg_distance = round(stats.get('total_distance', 0) / kills, 1) if kills > 0 else 0
                embed.add_field(name="Avg Kill Distance", value=f"{avg_distance}m", inline=True)
            
            if 'headshots' in stats:
                headshot_rate = round((stats.get('headshots', 0) / kills) * 100, 1) if kills > 0 else 0
                embed.add_field(name="Headshot Rate", value=f"{headshot_rate}%", inline=True)
            
            # Rivalry information
            rivalries = stats.get('rivalries', {})
            nemesis = rivalries.get('nemesis')
            prey = rivalries.get('prey')
            
            rivalry_text = ""
            if nemesis:
                rivalry_text += f"**Nemesis:** {nemesis['player']}\n"
                rivalry_text += f"└ Record: {nemesis['our_kills']}-{nemesis['their_kills']} (deficit: {nemesis['deficit']})\n\n"
            
            if prey:
                rivalry_text += f"**Prey:** {prey['player']}\n"
                rivalry_text += f"└ Record: {prey['our_kills']}-{prey['their_kills']} (advantage: {prey['advantage']})\n\n"
            
            if not rivalry_text:
                rivalry_text = "No significant rivalries established"
            
            embed.add_field(
                name="⚔️ Rivalries",
                value=rivalry_text,
                inline=False
            )
            
            # Recent activity
            recent_kills = stats.get('recent_kills', [])
            recent_deaths = stats.get('recent_deaths', [])
            
            activity_text = ""
            if recent_kills:
                last_kill = recent_kills[0]
                weapon = last_kill.get('weapon', 'Unknown')
                victim = last_kill.get('victim', 'Unknown')
                distance = last_kill.get('distance', 0)
                activity_text += f"**Last Kill:** {victim} with {weapon} at {distance}m\n"
            
            if recent_deaths:
                last_death = recent_deaths[0]
                killer = last_death.get('killer', 'Unknown')
                weapon = last_death.get('weapon', 'Unknown')
                distance = last_death.get('distance', 0)
                activity_text += f"**Last Death:** {killer} with {weapon} at {distance}m"
            
            if activity_text:
                embed.add_field(
                    name="🎯 Recent Activity",
                    value=activity_text,
                    inline=False
                )
            
            # Performance indicators
            if kills > 50:  # Only show for active players
                performance_indicators = []
                
                if kd_ratio >= 2.0:
                    performance_indicators.append("🔥 Elite Fighter")
                elif kd_ratio >= 1.5:
                    performance_indicators.append("⚡ Skilled Player")
                
                if headshot_rate >= 50:
                    performance_indicators.append("🎯 Sharpshooter")
                
                if avg_distance >= 300:
                    performance_indicators.append("🔭 Long Range Specialist")
                
                if rivalries.get('total_rivalries', 0) >= 5:
                    performance_indicators.append("⚔️ Rivalry Master")
                
                if performance_indicators:
                    embed.add_field(
                        name="🏆 Performance Badges",
                        value=" • ".join(performance_indicators),
                        inline=False
                    )
            
            await ctx.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error displaying player stats: {e}")
            await ctx.followup.send("❌ An error occurred while retrieving player statistics.", ephemeral=True)
    
    @stats.command(name="compare", description="Compare two players' statistics")
    async def compare_players(self,
                             ctx: discord.ApplicationContext,
                             player1: Option(str, "First player", autocomplete=player_autocomplete),
                             player2: Option(str, "Second player", autocomplete=player_autocomplete),
                             server: Option(str, "Specific server (optional)", autocomplete=server_autocomplete, required=False)):
        """Compare statistics between two players"""
        await ctx.defer(ephemeral=True)
        
        try:
            guild_id = ctx.guild.id
            server_id = server if server and server != "all" else None
            
            # Get statistics for both players
            stats1 = await self.get_player_statistics(guild_id, player1, server_id)
            stats2 = await self.get_player_statistics(guild_id, player2, server_id)
            
            if not stats1:
                await ctx.followup.send(f"❌ No statistics found for player **{player1}**", ephemeral=True)
                return
            
            if not stats2:
                await ctx.followup.send(f"❌ No statistics found for player **{player2}**", ephemeral=True)
                return
            
            # Create comparison embed
            embed = discord.Embed(
                title=f"⚖️ Player Comparison",
                description=f"**{player1}** vs **{player2}**",
                color=0x9B59B6,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Server context
            if server_id:
                servers = await self.get_configured_servers(guild_id)
                server_info = next((s for s in servers if s.get('_id') == server_id), None)
                server_name = server_info.get('name', server_id) if server_info else server_id
                embed.add_field(name="Server", value=server_name, inline=False)
            
            # Combat statistics comparison
            kills1 = stats1.get('kills', 0)
            kills2 = stats2.get('kills', 0)
            deaths1 = stats1.get('deaths', 0)
            deaths2 = stats2.get('deaths', 0)
            kd1 = round(kills1 / deaths1, 2) if deaths1 > 0 else kills1
            kd2 = round(kills2 / deaths2, 2) if deaths2 > 0 else kills2
            
            # Determine winners for each category
            kills_winner = "🏆" if kills1 > kills2 else ("🏆" if kills2 > kills1 else "🤝")
            kd_winner = "🏆" if kd1 > kd2 else ("🏆" if kd2 > kd1 else "🤝")
            
            comparison_text = (
                f"**Kills**\n"
                f"{player1}: {kills1:,} {'🏆' if kills_winner == '🏆' and kills1 > kills2 else ''}\n"
                f"{player2}: {kills2:,} {'🏆' if kills_winner == '🏆' and kills2 > kills1 else ''}\n\n"
                f"**K/D Ratio**\n"
                f"{player1}: {kd1} {'🏆' if kd_winner == '🏆' and kd1 > kd2 else ''}\n"
                f"{player2}: {kd2} {'🏆' if kd_winner == '🏆' and kd2 > kd1 else ''}"
            )
            
            embed.add_field(
                name="📊 Combat Statistics",
                value=comparison_text,
                inline=False
            )
            
            # Head-to-head record if they have fought
            h2h_query = {
                "guild_id": guild_id,
                "$or": [
                    {"player_a": player1, "player_b": player2},
                    {"player_a": player2, "player_b": player1}
                ]
            }
            if server_id:
                h2h_query["server_id"] = server_id
            
            h2h_record = await self.bot.db_manager.player_encounters.find_one(h2h_query)
            
            if h2h_record:
                if h2h_record["player_a"] == player1:
                    p1_kills = h2h_record["encounters"]["a_killed_b"]
                    p2_kills = h2h_record["encounters"]["b_killed_a"]
                else:
                    p1_kills = h2h_record["encounters"]["b_killed_a"]
                    p2_kills = h2h_record["encounters"]["a_killed_b"]
                
                total_encounters = p1_kills + p2_kills
                h2h_winner = player1 if p1_kills > p2_kills else (player2 if p2_kills > p1_kills else "Tied")
                
                h2h_text = (
                    f"**Total Encounters:** {total_encounters}\n"
                    f"**{player1}:** {p1_kills} kills\n"
                    f"**{player2}:** {p2_kills} kills\n"
                    f"**Head-to-Head Winner:** {h2h_winner} {'🏆' if h2h_winner != 'Tied' else '🤝'}"
                )
                
                embed.add_field(
                    name="⚔️ Head-to-Head Record",
                    value=h2h_text,
                    inline=False
                )
            else:
                embed.add_field(
                    name="⚔️ Head-to-Head Record",
                    value="These players have not encountered each other in combat",
                    inline=False
                )
            
            # Performance comparison
            performance1 = []
            performance2 = []
            
            if kd1 >= 2.0:
                performance1.append("Elite K/D")
            if kd2 >= 2.0:
                performance2.append("Elite K/D")
            
            # Add rivalry information
            rivalries1 = stats1.get('rivalries', {})
            rivalries2 = stats2.get('rivalries', {})
            
            if rivalries1.get('nemesis'):
                performance1.append(f"Nemesis: {rivalries1['nemesis']['player']}")
            if rivalries2.get('nemesis'):
                performance2.append(f"Nemesis: {rivalries2['nemesis']['player']}")
            
            if rivalries1.get('prey'):
                performance1.append(f"Prey: {rivalries1['prey']['player']}")
            if rivalries2.get('prey'):
                performance2.append(f"Prey: {rivalries2['prey']['player']}")
            
            if performance1 or performance2:
                perf_text = ""
                if performance1:
                    perf_text += f"**{player1}:**\n• " + "\n• ".join(performance1) + "\n\n"
                if performance2:
                    perf_text += f"**{player2}:**\n• " + "\n• ".join(performance2)
                
                embed.add_field(
                    name="🎯 Notable Attributes",
                    value=perf_text,
                    inline=False
                )
            
            await ctx.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error comparing players: {e}")
            await ctx.followup.send("❌ An error occurred while comparing players.", ephemeral=True)
    
    @stats.command(name="server", description="View server statistics overview")
    async def server_stats(self,
                          ctx: discord.ApplicationContext,
                          server: Option(str, "Server to analyze", autocomplete=server_autocomplete)):
        """Display comprehensive server statistics"""
        await ctx.defer(ephemeral=True)
        
        try:
            guild_id = ctx.guild.id
            
            if server == "all":
                # All servers combined
                embed = discord.Embed(
                    title="📊 Combined Server Statistics",
                    description="Statistics across all configured servers",
                    color=0x3498DB,
                    timestamp=datetime.now(timezone.utc)
                )
                query = {"guild_id": guild_id}
            else:
                # Specific server
                servers = await self.get_configured_servers(guild_id)
                server_info = next((s for s in servers if s.get('_id') == server), None)
                
                if not server_info:
                    await ctx.followup.send("❌ Server not found!", ephemeral=True)
                    return
                
                embed = discord.Embed(
                    title=f"📊 Server Statistics - {server_info['name']}",
                    color=0x3498DB,
                    timestamp=datetime.now(timezone.utc)
                )
                query = {"guild_id": guild_id, "server_id": server}
            
            # Get basic statistics
            total_players = await self.bot.db_manager.player_stats.count_documents(query)
            total_kills = await self.bot.db_manager.kill_events.count_documents(query)
            
            # Get aggregated statistics
            pipeline = [
                {"$match": query},
                {"$group": {
                    "_id": None,
                    "total_kills": {"$sum": "$kills"},
                    "total_deaths": {"$sum": "$deaths"},
                    "total_headshots": {"$sum": "$headshots"},
                    "avg_distance": {"$avg": "$average_distance"}
                }}
            ]
            
            agg_result = await self.bot.db_manager.player_stats.aggregate(pipeline).to_list(1)
            
            if agg_result:
                stats = agg_result[0]
                total_agg_kills = stats.get('total_kills', 0)
                total_deaths = stats.get('total_deaths', 0)
                total_headshots = stats.get('total_headshots', 0)
                avg_distance = round(stats.get('avg_distance', 0), 1)
                
                overall_kd = round(total_agg_kills / total_deaths, 2) if total_deaths > 0 else 0
                headshot_rate = round((total_headshots / total_agg_kills) * 100, 1) if total_agg_kills > 0 else 0
            else:
                total_agg_kills = total_deaths = total_headshots = 0
                overall_kd = avg_distance = headshot_rate = 0
            
            # Add statistics to embed
            embed.add_field(name="Active Players", value=f"{total_players:,}", inline=True)
            embed.add_field(name="Total Kill Events", value=f"{total_kills:,}", inline=True)
            embed.add_field(name="Overall K/D", value=f"{overall_kd}", inline=True)
            
            embed.add_field(name="Total Headshots", value=f"{total_headshots:,}", inline=True)
            embed.add_field(name="Headshot Rate", value=f"{headshot_rate}%", inline=True)
            embed.add_field(name="Avg Kill Distance", value=f"{avg_distance}m", inline=True)
            
            # Get top performers
            top_killers = await self.bot.db_manager.player_stats.find(
                query,
                sort=[("kills", -1)],
                limit=3
            ).to_list(3)
            
            if top_killers:
                top_text = ""
                for i, player in enumerate(top_killers, 1):
                    medal = ["🥇", "🥈", "🥉"][i-1]
                    kills = player.get('kills', 0)
                    kd = round(player.get('kills', 0) / max(player.get('deaths', 1), 1), 2)
                    top_text += f"{medal} {player['player_name']} - {kills:,} kills (K/D: {kd})\n"
                
                embed.add_field(
                    name="🏆 Top Killers",
                    value=top_text,
                    inline=False
                )
            
            # Recent activity
            recent_events = await self.bot.db_manager.kill_events.find(
                query,
                sort=[("timestamp", -1)],
                limit=1
            ).to_list(1)
            
            if recent_events:
                last_event = recent_events[0]
                last_activity = f"<t:{int(last_event['timestamp'].timestamp())}:R>"
                embed.add_field(
                    name="📅 Last Activity",
                    value=last_activity,
                    inline=True
                )
            
            await ctx.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error displaying server stats: {e}")
            await ctx.followup.send("❌ An error occurred while retrieving server statistics.", ephemeral=True)

def setup(bot):
    bot.add_cog(StatisticsEnhanced(bot))