"""
Emerald's Killfeed - Automated Consolidated Leaderboard
Posts and updates consolidated leaderboards every 30 minutes
"""

import discord
import discord
import discord
from discord.ext import commands, tasks
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from bot.utils.embed_factory import EmbedFactory

logger = logging.getLogger(__name__)

class AutomatedLeaderboard(discord.Cog):
    """Automated consolidated leaderboard system"""

    def __init__(self, bot):
        self.bot = bot
        self.message_cache = {}  # Store {guild_id: message_id}
        logger.info("🤖 Automated leaderboard cog initialized")
        
        # Start tasks after bot is ready
        self.bot.loop.create_task(self.start_after_ready())

    async def start_after_ready(self):
        """Start automated leaderboard after bot is ready"""
        await self.bot.wait_until_ready()
        logger.info("🔄 Starting automated leaderboard task...")
        self.automated_leaderboard_task.start()
        
        # Don't run initial check to prevent duplicates - regular task will handle it
        logger.info("🚀 Automated leaderboard will run on schedule to prevent duplicates")

    def cog_unload(self):
        """Stop the task when cog unloads"""
        self.automated_leaderboard_task.cancel()

    @tasks.loop(minutes=60)
    async def automated_leaderboard_task(self):
        """Run automated leaderboard updates every 60 minutes"""
        try:

            pass
            logger.info("Running automated leaderboard update...")

            # Get all guilds with leaderboard channels configured
            guilds_cursor = self.bot.db_manager.guilds.find({
                "leaderboard_enabled": True,
                "leaderboard_channel": {"$exists": True, "$ne": None}
            })

            guilds_with_leaderboard = await guilds_cursor.to_list(length=None)

            for guild_config in guilds_with_leaderboard:
                try:

                    pass
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

    async def initial_leaderboard_check(self):
        """Check if leaderboards are missing and create only if needed"""
        try:

            pass
            # Get all guilds with leaderboard channels configured
            guilds_cursor = self.bot.db_manager.guilds.find({
                "$or": [
                    {"channels.leaderboard": {"$exists": True, "$ne": None}},
                    {"server_channels.default.leaderboard": {"$exists": True, "$ne": None}}
                ],
                "leaderboard_enabled": True
            })

            guilds_with_leaderboard = await guilds_cursor.to_list(length=None)

            for guild_config in guilds_with_leaderboard:
                try:

                    pass
                    # Only create if missing
                    missing = await self.check_missing_leaderboards(guild_config)
                    if missing:
                        await self.update_guild_leaderboard(guild_config, force_create=True)
                        logger.info(f"Created missing leaderboard for guild {guild_config.get('guild_id')}")
                    else:
                        logger.info(f"Leaderboard already exists for guild {guild_config.get('guild_id')}")
                except Exception as e:
                    guild_id = guild_config.get('guild_id', 'Unknown')
                    logger.error(f"Failed to check/create leaderboard for guild {guild_id}: {e}")

        except Exception as e:
            logger.error(f"Error in initial leaderboard check: {e}")

    async def check_missing_leaderboards(self, guild_config: Dict[str, Any]) -> bool:
        """Check if leaderboard messages are missing in the channel"""
        try:

            pass
            guild_id = guild_config['guild_id']
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return False

            # Get leaderboard channel
            channel = await self.get_leaderboard_channel(guild_config)
            if not channel:
                return False

            # Check last 50 messages for bot's leaderboard embeds
            async for message in channel.history(limit=50):
                if (message.author == self.bot.user and 
                    message.embeds and 
                    any("Leaderboard" in embed.title for embed in message.embeds)):
                    return False  # Found existing leaderboard
            
            return True  # No leaderboard found, needs creation
            
        except Exception as e:
            logger.error(f"Error checking missing leaderboards: {e}")
            return True  # Assume missing on error

    async def get_leaderboard_channel(self, guild_config: Dict[str, Any]):
        """Get the configured leaderboard channel"""
        try:

            pass
            guild_id = guild_config['guild_id']
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return None

            # Check new server_channels structure first
            server_channels_config = guild_config.get('server_channels', {})
            default_server = server_channels_config.get('default', {})
            
            # Check legacy channels structure
            legacy_channels = guild_config.get('channels', {})
            
            # Priority: default server -> legacy channels
            leaderboard_channel_id = (default_server.get('leaderboard') or 
                                    legacy_channels.get('leaderboard'))
            
            if not leaderboard_channel_id:
                return None

            return guild.get_channel(leaderboard_channel_id)
            
        except Exception as e:
            logger.error(f"Error getting leaderboard channel: {e}")
            return None

    async def get_top_kills(self, guild_id: int, limit: int = 10, server_id: str = None):
        """Get top killers for automated leaderboard"""
        try:

            pass
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

    
    async def _collect_leaderboard_data(self, guild_id: int, server_id: str = None) -> Dict[str, Any]:
        """Collect all leaderboard data from correct database collections"""
        try:

            pass
            data = {}
            
            # Base query for filtering
            base_query = {"guild_id": guild_id}
            if server_id and server_id != "all":
                base_query["server_id"] = server_id
            
            # Top killers from pvp_data
            kills_cursor = self.bot.db_manager.pvp_data.find(base_query).sort("kills", -1).limit(10)
            data["top_killers"] = await kills_cursor.to_list(length=None)
            
            # Top KDR (only players with deaths > 0)
            kdr_query = {**base_query, "deaths": {"$gt": 0}}
            kdr_pipeline = [
                {"$match": kdr_query},
                {"$addFields": {"kdr": {"$divide": ["$kills", "$deaths"]}}},
                {"$sort": {"kdr": -1}},
                {"$limit": 10}
            ]
            kdr_cursor = self.bot.db_manager.pvp_data.aggregate(kdr_pipeline)
            data["top_kdr"] = await kdr_cursor.to_list(length=None)
            
            # Longest distances from pvp_data
            distance_cursor = self.bot.db_manager.pvp_data.find(base_query).sort("personal_best_distance", -1).limit(10)
            data["top_distances"] = await distance_cursor.to_list(length=None)
            
            # Best streaks from pvp_data
            streak_cursor = self.bot.db_manager.pvp_data.find(base_query).sort("longest_streak", -1).limit(10)
            data["top_streaks"] = await streak_cursor.to_list(length=None)
            
            # Top weapons from kill_events
            weapon_pipeline = [
                {"$match": {**base_query, "is_suicide": False}},
                {"$group": {"_id": "$weapon", "kills": {"$sum": 1}, "top_user": {"$first": "$killer"}}},
                {"$sort": {"kills": -1}},
                {"$limit": 10}
            ]
            weapon_cursor = self.bot.db_manager.kill_events.aggregate(weapon_pipeline)
            data["top_weapons"] = await weapon_cursor.to_list(length=None)
            
            # Top factions from factions collection
            faction_cursor = self.bot.db_manager.factions.find(base_query).sort("kills", -1).limit(5)
            data["top_factions"] = await faction_cursor.to_list(length=None)
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to collect leaderboard data: {e}")
            return {}


    async def update_guild_leaderboard(self, guild_config: Dict[str, Any], force_create: bool = False):
        """Update leaderboard for a specific guild"""
        try:

            pass
            guild_id = guild_config['guild_id']
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return

            # Get leaderboard channel using the helper function
            channel = await self.get_leaderboard_channel(guild_config)
            if not channel:
                logger.warning(f"No leaderboard channel found for guild {guild_id}")
                return

            # Get servers for this guild
            servers = guild_config.get('servers', [])
            if not servers:
                logger.warning(f"No servers configured for guild {guild_id}")
                return

            # Create one consolidated leaderboard for all servers in the guild
            try:

                pass
                # Create consolidated leaderboard for the entire guild (all servers combined)
                embed, file_attachment = await self.create_consolidated_leaderboard(
                    guild_id, None, "All Servers"
                )

                if embed:
                    # Try to find and update existing leaderboard message
                    existing_message = None
                    if not force_create:
                        existing_message = await self.find_existing_leaderboard_message(channel, "Consolidated Leaderboard")
                    
                    if existing_message:
                        # Edit existing message (without file attachments to avoid errors)
                        try:

                            pass
                            await existing_message.edit(embed=embed)
                            logger.info(f"Updated existing consolidated leaderboard")
                        except Exception as edit_error:
                            logger.warning(f"Failed to edit existing message, posting new one: {edit_error}")
                            # Fall back to posting new message
                            await self.post_new_leaderboard_message(channel, embed, file_attachment)
                            logger.info(f"Posted new consolidated leaderboard")
                    else:
                        # Post new message
                        await self.post_new_leaderboard_message(channel, embed, file_attachment)
                        logger.info(f"Posted new consolidated leaderboard")

            except Exception as e:
                logger.error(f"Failed to post consolidated leaderboard: {e}")

        except Exception as e:
            logger.error(f"Failed to update guild leaderboard: {e}")

    async def get_stored_leaderboard_message_id(self, guild_id: int, channel_id: int) -> Optional[int]:
        """Get stored leaderboard message ID from database for persistence across restarts"""
        try:

            pass
            stored_data = await self.bot.db_manager.leaderboard_messages.find_one({
                "guild_id": guild_id,
                "channel_id": channel_id,
                "message_type": "consolidated_leaderboard"
            })
            return stored_data.get('message_id') if stored_data else None
        except Exception as e:
            logger.error(f"Error getting stored leaderboard message ID: {e}")
            return None

    async def store_leaderboard_message_id(self, guild_id: int, channel_id: int, message_id: int):
        """Store leaderboard message ID in database for persistence across restarts"""
        try:

            pass
            await self.bot.db_manager.leaderboard_messages.update_one(
                {
                    "guild_id": guild_id,
                    "channel_id": channel_id,
                    "message_type": "consolidated_leaderboard"
                },
                {
                    "$set": {
                        "guild_id": guild_id,
                        "channel_id": channel_id,
                        "message_id": message_id,
                        "message_type": "consolidated_leaderboard",
                        "last_updated": datetime.now(timezone.utc)
                    }
                },
                upsert=True
            )
            logger.info(f"Stored leaderboard message ID {message_id} for persistence")
        except Exception as e:
            logger.error(f"Error storing leaderboard message ID: {e}")

    async def find_existing_leaderboard_message(self, channel, server_name: str):
        """Find existing leaderboard message using stored ID for persistence across restarts"""
        try:

            pass
            # First try to get stored message ID from database
            stored_message_id = await self.get_stored_leaderboard_message_id(channel.guild.id, channel.id)
            
            if stored_message_id:
                try:

                    pass
                    # Try to fetch the stored message
                    stored_message = await channel.fetch_message(stored_message_id)
                    # Verify it's still a valid leaderboard message
                    if stored_message.author == self.bot.user and stored_message.embeds:
                        embed = stored_message.embeds[0]
                        if embed.title and any(keyword in embed.title.upper() for keyword in ['RANKING', 'LEADERBOARD', 'COMBAT', 'ELITE']):
                            return stored_message
                except discord.NotFound:
                    # Message was deleted, remove from database
                    await self.bot.db_manager.leaderboard_messages.delete_one({
                        "guild_id": channel.guild.id,
                        "channel_id": channel.id,
                        "message_type": "consolidated_leaderboard"
                    })
                    logger.info("Stored message was deleted, removed from database")
            
            # Fallback: search recent messages
            async for message in channel.history(limit=50):
                if (message.author == self.bot.user and 
                    message.embeds and 
                    any(server_name in embed.title for embed in message.embeds if embed.title)):
                    # Store this message ID for future use
                    await self.store_leaderboard_message_id(channel.guild.id, channel.id, message.id)
                    return message
            return None
        except Exception as e:
            logger.error(f"Error finding existing leaderboard message: {e}")
            return None

    async def post_new_leaderboard_message(self, channel, embed, file_attachment):
        """Post a new leaderboard message and store ID for persistence across restarts"""
        try:

            pass
            message = None
            if hasattr(self.bot, 'advanced_rate_limiter') and self.bot.advanced_rate_limiter:
                from bot.utils.advanced_rate_limiter import MessagePriority
                message = await self.bot.advanced_rate_limiter.queue_message(
                    channel_id=channel.id,
                    embed=embed,
                    file=file_attachment,
                    priority=MessagePriority.LOW
                )
            else:
                if file_attachment:
                    message = await channel.send(embed=embed, file=file_attachment)
                else:
                    message = await channel.send(embed=embed)
            
            # Store message ID for persistence across bot restarts
            if message:
                await self.store_leaderboard_message_id(channel.guild.id, channel.id, message.id)
                
        except Exception as e:
            logger.error(f"Error posting new leaderboard message: {e}")

    async def check_premium_access(self, guild_id: int) -> bool:
        """Check if guild has premium access"""
        # Automated leaderboards is guild-wide premium feature - requires at least 1 premium server
        try:

            pass
            if hasattr(self.bot, 'premium_manager_v2'):
                return await self.bot.premium_manager_v2.has_premium_access(guild_id)
            else:
                # Fallback to old method
                guild_doc = await self.bot.db_manager.get_guild(guild_id)
                if not guild_doc:
                    return False

                servers = guild_doc.get('servers', [])
                for server_config in servers:
                    server_id = server_config.get('server_id', server_config.get('_id', 'default'))
                    if await self.check_premium_access(guild_id):
                        return True
                return False
        except Exception as e:
            logger.error(f"Failed to check premium access for leaderboards: {e}")
            return False

    async def create_consolidated_leaderboard(self, guild_id: int, server_id: str, server_name: str):
        """Create consolidated leaderboard with top performers from each category"""
        try:

            pass
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

            # Get actual data for consolidated leaderboard with specific counts
            top_killers = await self.get_top_kills(guild_id or 0, 5, server_id)
            top_kdr = await self.get_top_kdr(guild_id or 0, 3, server_id)
            top_distance = await self.get_top_distance(guild_id or 0, 3, server_id)
            top_streaks = await self.get_top_streaks(guild_id or 0, 3, server_id)
            top_weapons = await self.get_top_weapons(guild_id or 0, 3, server_id)
            top_faction = await self.get_top_factions(guild_id or 0, 1, server_id)

            # Build sections with real data
            sections = []

            if top_killers:
                killer_lines = []
                for i, player in enumerate(top_killers, 1):
                    name = player.get('player_name', 'Unknown')
                    kills = player.get('kills', 0)
                    faction = await self.get_player_faction(guild_id or 0, name)
                    faction_tag = f" [{faction}]" if faction else ""
                    # Use shorter format to prevent wrapping
                    killer_lines.append(f"**{i}.** {name}{faction_tag}\n{kills:,} Kills")
                sections.append(f"**TOP KILLERS**\n" + "\n".join(killer_lines))

            if top_kdr:
                kdr_lines = []
                for i, player in enumerate(top_kdr, 1):
                    name = player.get('player_name', 'Unknown')
                    kdr = player.get('kdr', 0.0)
                    faction = await self.get_player_faction(guild_id or 0, name)
                    faction_tag = f" [{faction}]" if faction else ""
                    # Use shorter format to prevent wrapping
                    kdr_lines.append(f"**{i}.** {name}{faction_tag}\n{kdr:.2f} KDR")
                sections.append(f"**BEST KDR**\n" + "\n".join(kdr_lines))

            if top_distance:
                distance_lines = []
                for i, player in enumerate(top_distance, 1):
                    name = player.get('player_name', 'Unknown')
                    distance = player.get('personal_best_distance', 0.0)
                    faction = await self.get_player_faction(guild_id or 0, name)
                    faction_tag = f" [{faction}]" if faction else ""
                    if distance >= 1000:
                        dist_str = f"{distance/1000:.1f}km"
                    else:
                        dist_str = f"{distance:.0f}m"
                    # Use shorter format to prevent wrapping
                    distance_lines.append(f"**{i}.** {name}{faction_tag}\n{dist_str}")
                sections.append(f"**LONGEST SHOTS**\n" + "\n".join(distance_lines))

            if top_streaks:
                streak_lines = []
                for i, player in enumerate(top_streaks, 1):
                    name = player.get('player_name', 'Unknown')
                    streak = player.get('longest_streak', 0)
                    faction = await self.get_player_faction(guild_id or 0, name)
                    faction_tag = f" [{faction}]" if faction else ""
                    # Use shorter format to prevent wrapping
                    streak_lines.append(f"**{i}.** {name}{faction_tag}\n{streak} Kill Streak")
                sections.append(f"**BEST STREAKS**\n" + "\n".join(streak_lines))

            if top_weapons:
                weapon_lines = []
                for i, weapon in enumerate(top_weapons, 1):
                    weapon_name = weapon.get('weapon_name', 'Unknown Weapon')
                    kills = weapon.get('kills', 0)
                    top_user = weapon.get('top_user', 'Unknown')
                    # Shorten the format to prevent text wrapping
                    weapon_lines.append(f"**{i}.** {weapon_name} — {kills:,} Kills\nTop: {top_user}")
                sections.append(f"**TOP WEAPONS**\n" + "\n".join(weapon_lines))

            if top_faction:
                faction = top_faction[0] if top_faction else None
                if faction:
                    faction_name = faction.get('faction_name', 'Unknown Faction')
                    kills = faction.get('kills', 0)
                    members = faction.get('members', 0)
                    # Use shorter format to prevent wrapping
                    sections.append(f"**TOP FACTION**\n**1.** [{faction_name}]\n{kills:,} Kills | {members} Members")

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

            pass
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

            pass
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

    async def get_top_streaks(self, guild_id: int, limit: int, server_id: str = None) -> List[Dict[str, Any]]:
        """Get top streak players"""
        try:

            pass
            query = {
                "guild_id": guild_id,
                "longest_streak": {"$gt": 0}
            }

            # Add server filter if specified
            if server_id:
                query["server_id"] = server_id

            cursor = self.bot.db_manager.pvp_data.find(query).sort("longest_streak", -1).limit(limit)
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Failed to get top streaks: {e}")
            return []

    async def get_top_weapons(self, guild_id: int, limit: int, server_id: str = None) -> List[Dict[str, Any]]:
        """Get top weapons by kill count - using same method as working /leaderboard weapons"""
        try:

            pass
            # Use exact same query as working leaderboard command
            cursor = self.bot.db_manager.kill_events.find({
                "guild_id": guild_id,
                "is_suicide": False,
                "weapon": {"$nin": ["Menu Suicide", "Suicide", "Falling", "suicide_by_relocation"]}
            })

            weapon_events = await cursor.to_list(length=None)

            # Group weapons in Python (same as working command)
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
                    'weapon_name': weapon,
                    'kills': stats['kills'],
                    'top_user': stats['top_killer']
                })

            return weapons_data
        except Exception as e:
            logger.error(f"Failed to get top weapons: {e}")
            return []

    async def get_top_factions(self, guild_id: int, limit: int = 1, server_id: str = None) -> List[Dict[str, Any]]:
        """Get top factions by total kills - aggregate stats from all members including alts"""
        try:

            pass
            # Get all factions for this guild first
            factions_cursor = self.bot.db_manager.factions.find({"guild_id": guild_id})
            all_factions = await factions_cursor.to_list(length=None)

            faction_stats = {}

            # Process each faction (same logic as working leaderboard command)
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

                # Get stats for each member and their alts
                for discord_id in faction_doc.get('members', []):
                    # Get player's linked characters
                    player_link = await self.bot.db_manager.players.find_one({
                        "guild_id": guild_id,
                        "discord_id": discord_id
                    })

                    if not player_link:
                        continue

                    # Get stats for each character (main and alts)
                    for character in player_link.get('linked_characters', []):
                        player_stat = await self.bot.db_manager.pvp_data.find_one({
                            "guild_id": guild_id,
                            "player_name": character
                        })

                        if player_stat:
                            faction_stats[faction_display]['kills'] += player_stat.get('kills', 0)
                            faction_stats[faction_display]['deaths'] += player_stat.get('deaths', 0)
                            faction_stats[faction_display]['members'].add(character)

            # Convert to list format and sort by kills
            factions_list = []
            for faction_display, stats in faction_stats.items():
                factions_list.append({
                    'faction_name': faction_display,
                    'kills': stats['kills'],
                    'deaths': stats['deaths'],
                    'members': len(stats['members'])
                })

            # Sort by kills and limit
            factions_list.sort(key=lambda x: x['kills'], reverse=True)
            return factions_list[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get top factions: {e}")
            return []

    async def get_player_faction(self, guild_id: int, player_name: str) -> Optional[str]:
        """Get player's faction tag if they have one"""
        try:

            pass
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

            pass
            cursor = self.bot.db_manager.pvp_data.find({
                "guild_id": guild_id,
                "deaths": {"$gt": 0}
            }).sort("deaths", -1).limit(limit)
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Failed to get top deaths: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to get top weapons: {e}")
            return []

    async def get_top_faction(self, guild_id: int, limit: int) -> List[Dict[str, Any]]:
        """Get top faction"""
        try:

            pass
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