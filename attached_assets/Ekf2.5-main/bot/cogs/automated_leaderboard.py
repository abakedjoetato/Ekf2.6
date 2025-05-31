"""
Emerald's Killfeed - Automated Consolidated Leaderboard
Posts and updates consolidated leaderboards every 30 minutes
"""

import discord
from discord.ext import commands, tasks
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from bot.utils.embed_factory import EmbedFactory

logger = logging.getLogger(__name__)

class AutomatedLeaderboard(commands.Cog):
    """Automated consolidated leaderboard system"""

    def __init__(self, bot):
        self.bot = bot
        self.message_cache = {}  # Store {guild_id: message_id}

    async def cog_load(self):
        """Start the automated leaderboard task when cog loads"""
        logger.info("Starting automated leaderboard task...")
        self.automated_leaderboard_task.start()

    def cog_unload(self):
        """Stop the task when cog unloads"""
        self.automated_leaderboard_task.cancel()

    @tasks.loop(minutes=30)
    async def automated_leaderboard_task(self):
        """Run automated leaderboard updates every 30 minutes"""
        try:
            logger.info("Running automated leaderboard update...")

            # Get all guilds with leaderboard channels configured
            guilds_cursor = self.bot.db_manager.guilds.find({
                "channels.leaderboard": {"$exists": True, "$ne": None},
                "leaderboard_enabled": True
            })

            guilds_with_leaderboard = await guilds_cursor.to_list(length=None)

            for guild_config in guilds_with_leaderboard:
                try:
                    await self.update_guild_leaderboard(guild_config)
                except Exception as e:
                    guild_id = guild_config.get('guild_id', 'Unknown')
                    logger.error(f"Failed to update leaderboard for guild {guild_id}: {e}")

            logger.info(f"Automated leaderboard update completed for {len(guilds_with_leaderboard)} guilds")

        except Exception as e:
            logger.error(f"Error in automated leaderboard task: {e}")

    @automated_leaderboard_task.before_loop
    async def before_automated_leaderboard(self):
        """Wait for bot to be ready before starting task"""
        await self.bot.wait_until_ready()

    async def get_top_kills(self, guild_id: int, limit: int = 10, server_id: str = None):
        """Get top killers for automated leaderboard"""
        try:
            query = {
                "guild_id": guild_id,
                "kills": {"$gt": 0}
            }

            # Add server filter if specified
            if server_id and server_id.strip():
                query["server_id"] = server_id

            cursor = self.bot.db_manager.pvp_data.find(query).sort("kills", -1).limit(limit)
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error getting top kills for automated leaderboard: {e}")
            return []

    async def update_guild_leaderboard(self, guild_config: Dict[str, Any]):
        """Update leaderboard for a specific guild"""
        try:
            guild_id = guild_config['guild_id']
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return

            # Get leaderboard channel
            channels = guild_config.get('channels', {})
            leaderboard_channel_id = channels.get('leaderboard')
            if not leaderboard_channel_id:
                return

            channel = guild.get_channel(leaderboard_channel_id)
            if not channel:
                return

            # Get servers for this guild
            servers = guild_config.get('servers', [])
            if not servers:
                return

            # Process each server
            for server_config in servers:
                server_id = str(server_config.get('_id', ''))
                server_name = server_config.get('name', 'Unknown Server')

                try:
                    # Create consolidated leaderboard
                    embed, file_attachment = await self.create_consolidated_leaderboard(
                        guild_id, server_id, server_name
                    )

                    if embed:
                        # Send via rate limiter if available
                        if hasattr(self.bot, 'advanced_rate_limiter') and self.bot.advanced_rate_limiter:
                            from bot.utils.advanced_rate_limiter import MessagePriority
                            await self.bot.advanced_rate_limiter.queue_message(
                                channel_id=channel.id,
                                embed=embed,
                                file=file_attachment,
                                priority=MessagePriority.LOW
                            )
                        else:
                            if file_attachment:
                                await channel.send(embed=embed, file=file_attachment)
                            else:
                                await channel.send(embed=embed)

                        logger.info(f"Posted automated leaderboard for {server_name}")

                except Exception as e:
                    logger.error(f"Failed to post leaderboard for {server_name}: {e}")

        except Exception as e:
            logger.error(f"Failed to update guild leaderboard: {e}")

    async def check_premium_access(self, guild_id: int) -> bool:
        """Check if guild has premium access"""
        try:
            guild_doc = await self.bot.db_manager.get_guild(guild_id)
            if not guild_doc:
                return False

            servers = guild_doc.get('servers', [])
            for server_config in servers:
                server_id = server_config.get('server_id', server_config.get('_id', 'default'))
                if await self.bot.db_manager.is_premium_server(guild_id, server_id):
                    return True

            return False

        except Exception as e:
            logger.error(f"Failed to check premium access: {e}")
            return False

    async def create_consolidated_leaderboard(self, guild_id: int, server_id: str, server_name: str):
        """Create consolidated leaderboard with top performers from each category"""
        try:
            # Get top players for each category using the same methods as leaderboards_fixed
            from bot.cogs.leaderboards_fixed import LeaderboardsFixed

            leaderboard_cog = LeaderboardsFixed(self.bot)

            # Create a consolidated leaderboard using EmbedFactory
            embed_data = {
                'title': f"Blood Money Rankings - {server_name}",
                'description': f"Most eliminations on {server_name}",
                'rankings': "Automated leaderboard data coming soon...",
                'total_kills': 0,
                'total_deaths': 0,
                'stat_type': 'consolidated',
                'style_variant': 'consolidated',
                'server_name': server_name,
                'thumbnail_url': 'attachment://Leaderboard.png'
            }

            # Get actual data for consolidated leaderboard
            top_killers = await self.get_top_kills(guild_id, 3, server_id)
            top_kdr = await self.get_top_kdr(guild_id, 3, server_id)
            top_distance = await self.get_top_distance(guild_id, 3, server_id)

            # Build sections with real data
            sections = []

            if top_killers:
                killer_lines = []
                for i, player in enumerate(top_killers, 1):
                    name = player.get('player_name', 'Unknown')
                    kills = player.get('kills', 0)
                    faction = await self.get_player_faction(guild_id, name)
                    faction_tag = f" [{faction}]" if faction else ""
                    killer_lines.append(f"**{i}.** {name}{faction_tag} — {kills:,} Kills")
                sections.append(f"**🔥 TOP KILLERS**\n" + "\n".join(killer_lines))

            if top_kdr:
                kdr_lines = []
                for i, player in enumerate(top_kdr, 1):
                    name = player.get('player_name', 'Unknown')
                    kdr = player.get('kdr', 0.0)
                    faction = await self.get_player_faction(guild_id, name)
                    faction_tag = f" [{faction}]" if faction else ""
                    kdr_lines.append(f"**{i}.** {name}{faction_tag} — {kdr:.2f} KDR")
                sections.append(f"**⚡ BEST KDR**\n" + "\n".join(kdr_lines))

            if top_distance:
                distance_lines = []
                for i, player in enumerate(top_distance, 1):
                    name = player.get('player_name', 'Unknown')
                    distance = player.get('personal_best_distance', 0.0)
                    faction = await self.get_player_faction(guild_id, name)
                    faction_tag = f" [{faction}]" if faction else ""
                    if distance >= 1000:
                        dist_str = f"{distance/1000:.1f}km"
                    else:
                        dist_str = f"{distance:.0f}m"
                    distance_lines.append(f"**{i}.** {name}{faction_tag} — {dist_str}")
                sections.append(f"**🎯 LONGEST SHOTS**\n" + "\n".join(distance_lines))

            if not sections:
                # No data available
                embed_data['rankings'] = "No statistical data available yet.\nPlay some matches to populate the leaderboards!"
            else:
                embed_data['rankings'] = "\n\n".join(sections)

            # Update totals with real data
            embed_data['total_kills'] = sum(p.get('kills', 0) for p in top_killers)
            embed_data['total_deaths'] = sum(p.get('deaths', 0) for p in top_killers)

            # Use EmbedFactory to create the embed
            embed, file = await EmbedFactory.build('leaderboard', embed_data)
            return embed, file



        except Exception as e:
            logger.error(f"Failed to create consolidated leaderboard: {e}")
            return None, None

    async def get_top_kdr(self, guild_id: int, limit: int, server_id: str = None) -> List[Dict[str, Any]]:
        """Get top KDR players"""
        try:
            query = {
                "guild_id": guild_id,
                "kills": {"$gte": 1}
            }

            # Add server filter if specified
            if server_id:
                query["server_id"] = server_id

            cursor = self.bot.db_manager.pvp_data.find(query).limit(50)
            all_players = await cursor.to_list(length=None)

            # Calculate KDR and sort in Python
            for player in all_players:
                kills = player.get('kills', 0)
                deaths = player.get('deaths', 0)
                player['kdr'] = kills / max(deaths, 1) if deaths > 0 else float(kills)

            players = sorted(all_players, key=lambda x: x['kdr'], reverse=True)[:limit]
            return players
        except Exception as e:
            logger.error(f"Failed to get top KDR: {e}")
            return []

    async def get_top_distance(self, guild_id: int, limit: int, server_id: str = None) -> List[Dict[str, Any]]:
        """Get top distance players"""
        try:
            query = {
                "guild_id": guild_id,
                "personal_best_distance": {"$gt": 0}
            }

            # Add server filter if specified
            if server_id:
                query["server_id"] = server_id

            cursor = self.bot.db_manager.pvp_data.find(query).sort("personal_best_distance", -1).limit(limit)
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Failed to get top distance: {e}")
            return []

    async def get_player_faction(self, guild_id: int, player_name: str) -> Optional[str]:
        """Get player's faction tag if they have one"""
        try:
            # First find the Discord ID for this player name
            player_link = await self.bot.db_manager.players.find_one({
                "guild_id": guild_id,
                "linked_characters": player_name
            })

            if not player_link:
                return None

            discord_id = player_link.get('discord_id')
            if not discord_id:
                return None

            # Now look up faction using Discord ID
            faction_doc = await self.bot.db_manager.factions.find_one({
                "guild_id": guild_id,
                "members": {"$in": [discord_id]}
            })

            if faction_doc:
                faction_tag = faction_doc.get('faction_tag')
                if faction_tag:
                    return faction_tag
                return faction_doc.get('faction_name')

            return None
        except Exception as e:
            logger.error(f"Error getting player faction for {player_name}: {e}")
            return None

    async def get_top_deaths(self, guild_id: int, limit: int) -> List[Dict[str, Any]]:
        """Get players with most deaths"""
        try:
            cursor = self.bot.db_manager.pvp_data.find({
                "guild_id": guild_id,
                "deaths": {"$gt": 0}
            }).sort("deaths", -1).limit(limit)
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Failed to get top deaths: {e}")
            return []

    async def get_top_weapons(self, guild_id: int, limit: int) -> List[Dict[str, Any]]:
        """Get top weapons"""
        try:
            cursor = self.bot.db_manager.kill_events.find({
                "guild_id": guild_id,
                "is_suicide": False,
                "weapon": {"$nin": ["Menu Suicide", "Suicide", "Falling", "suicide_by_relocation"]}
            })

            weapon_events = await cursor.to_list(length=None)

            # Group weapons
            weapon_stats = {}
            for event in weapon_events:
                weapon = event.get('weapon', 'Unknown')
                killer = event.get('killer', 'Unknown')

                if weapon not in weapon_stats:
                    weapon_stats[weapon] = {'kills': 0, 'top_killer': killer}
                weapon_stats[weapon]['kills'] += 1

            # Sort and limit
            weapons_data = []
            for weapon, stats in sorted(weapon_stats.items(), key=lambda x: x[1]['kills'], reverse=True)[:limit]:
                weapons_data.append({
                    '_id': weapon,
                    'kills': stats['kills'],
                    'top_killer': stats['top_killer']
                })

            return weapons_data
        except Exception as e:
            logger.error(f"Failed to get top weapons: {e}")
            return []

    async def get_top_faction(self, guild_id: int, limit: int) -> List[Dict[str, Any]]:
        """Get top faction"""
        try:
            factions_cursor = self.bot.db_manager.factions.find({"guild_id": guild_id})
            all_factions = await factions_cursor.to_list(length=None)

            faction_stats = {}

            for faction_doc in all_factions:
                faction_name = faction_doc.get('faction_name')
                faction_tag = faction_doc.get('faction_tag')
                faction_display = faction_tag if faction_tag else faction_name

                if not faction_display:
                    continue

                faction_stats[faction_display] = {
                    'kills': 0, 
                    'deaths': 0, 
                    'members': set(),
                    'faction_name': faction_name
                }

                # Get stats for each member
                for discord_id in faction_doc.get('members', []):
                    player_link = await self.bot.db_manager.players.find_one({
                        "guild_id": guild_id,
                        "discord_id": discord_id
                    })

                    if not player_link:
                        continue

                    for character in player_link.get('linked_characters', []):
                        player_stat = await self.bot.db_manager.pvp_data.find_one({
                            "guild_id": guild_id,
                            "player_name": character
                        })

                        if player_stat:
                            faction_stats[faction_display]['kills'] += player_stat.get('kills', 0)
                            faction_stats[faction_display]['deaths'] += player_stat.get('deaths', 0)
                            faction_stats[faction_display]['members'].add(character)

            # Convert member sets to counts and sort by kills
            for faction_name in faction_stats:
                faction_stats[faction_name]['member_count'] = len(faction_stats[faction_name]['members'])
                del faction_stats[faction_name]['members']

            sorted_factions = sorted(faction_stats.items(), key=lambda x: x[1]['kills'], reverse=True)[:limit]

            return [{'faction_name': name, **stats} for name, stats in sorted_factions]
        except Exception as e:
            logger.error(f"Failed to get top faction: {e}")
            return []

def setup(bot):
    bot.add_cog(AutomatedLeaderboard(bot))