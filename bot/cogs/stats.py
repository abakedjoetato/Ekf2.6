"""
Emerald's Killfeed - PvP Stats System (REFACTORED - PHASE 4)
/stats shows: Kills, deaths, KDR, Suicides, Longest streak, Most used weapon, Rival/Nemesis
/compare <user> compares two profiles
Uses py-cord 2.6.1 syntax and EmbedFactory
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

import discord
from discord.ext import commands
from bot.utils.embed_factory import EmbedFactory
from bot.cogs.autocomplete import ServerAutocomplete

logger = logging.getLogger(__name__)

class Stats(commands.Cog):
    """
    PVP STATS (FREE)
    - /stats shows: Kills, deaths, KDR, Suicides, Longest streak, Most used weapon, Rival/Nemesis
    - /compare <user> compares two profiles
    """

    def __init__(self, bot):
        self.bot = bot

    async def resolve_player(self, ctx: discord.ApplicationContext, target) -> Optional[Tuple[List[str], str]]:
        """
        Resolve a target (discord.Member or str) to player characters and display name.
        Returns (character_list, display_name) or None if not found.
        """
        guild_id = ctx.guild.id
        
        if isinstance(target, discord.Member):
            # Discord user - must be linked
            player_data = await self.bot.db_manager.get_linked_player(guild_id, target.id)
            if not player_data or not player_data.get('linked_characters'):
                return None
            return player_data['linked_characters'], target.display_name
        
        elif isinstance(target, str):
            # Raw player name - search database directly (case-insensitive)
            target_name = target.strip()
            if not target_name:
                return None
            
            # Find player in PvP data (case-insensitive match)
            cursor = self.bot.db_manager.pvp_data.find({
                'guild_id': guild_id,
                'player_name': {'$regex': f'^{target_name}$', '$options': 'i'}
            })
            
            async for player_doc in cursor:
                actual_player_name = player_doc.get('player_name')
                if actual_player_name:
                    return [actual_player_name], actual_player_name
            
            return None
        
        return None

    async def get_player_combined_stats(self, guild_id: int, player_characters: List[str], server_id: str = None) -> Dict[str, Any]:
        """Get combined stats across all servers for a player's characters"""
        # Initialize with safe defaults - ensure these are real values from database
        combined_stats = {
            'kills': 0,
            'deaths': 0,
            'suicides': 0,
            'kdr': 0.0,
            'best_streak': 0,
            'current_streak': 0,
            'personal_best_distance': 0.0,
            'total_distance': 0.0,
            'servers_played': 0,
            'favorite_weapon': None,
            'weapon_stats': {},
            'most_eliminated_player': None,
            'most_eliminated_count': 0,
            'eliminated_by_most_player': None,
            'eliminated_by_most_count': 0,
            'rivalry_score': 0,
            'active_days': 42  # Default for display
        }

        logger.debug(f"Getting combined stats for characters: {player_characters} in guild {guild_id}")

        try:
            if not player_characters:
                logger.warning("No player characters provided for stats calculation")
                return combined_stats

            # Get stats from all servers or specific server
            for character in player_characters:
                try:
                    query = {
                        'guild_id': guild_id,
                        'player_name': character
                    }
                    
                    # Add server filter if specified
                    if server_id:
                        query['server_id'] = server_id
                    
                    cursor = self.bot.db_manager.pvp_data.find(query)

                    async for server_stats in cursor:
                        if not isinstance(server_stats, dict):
                            logger.warning(f"Invalid server_stats type: {type(server_stats)}")
                            continue

                        # Enhanced logging to track actual data retrieval
                        logger.debug(f"Processing server stats for {character}: kills={server_stats.get('kills', 0)}, deaths={server_stats.get('deaths', 0)}")

                        kills = max(0, server_stats.get('kills', 0))
                        deaths = max(0, server_stats.get('deaths', 0))
                        suicides = max(0, server_stats.get('suicides', 0))
                        
                        combined_stats['kills'] += kills
                        combined_stats['deaths'] += deaths
                        combined_stats['suicides'] += suicides
                        
                        # Track personal best distance (take the maximum across all servers)
                        pb_distance = float(server_stats.get('personal_best_distance', 0.0))
                        if pb_distance > combined_stats['personal_best_distance']:
                            combined_stats['personal_best_distance'] = pb_distance
                        
                        # Add to total distance traveled
                        total_distance = float(server_stats.get('total_distance', 0.0))
                        combined_stats['total_distance'] += total_distance
                        
                        combined_stats['servers_played'] += 1

                        # Track best streak
                        best_streak = max(0, server_stats.get('best_streak', 0))
                        if best_streak > combined_stats['best_streak']:
                            combined_stats['best_streak'] = best_streak

                        logger.info(f"Character {character}: +{kills} kills, +{deaths} deaths. Total: {combined_stats['kills']} kills, {combined_stats['deaths']} deaths")

                except Exception as char_error:
                    logger.error(f"Error processing character {character}: {char_error}")
                    continue

            # Calculate KDR safely
            if combined_stats['deaths'] > 0:
                combined_stats['kdr'] = combined_stats['kills'] / combined_stats['deaths']
            else:
                combined_stats['kdr'] = float(combined_stats['kills'])

            # Get weapon statistics and rivals/nemesis
            try:
                await self._calculate_weapon_stats(guild_id, player_characters, combined_stats, server_id)
            except Exception as weapon_error:
                logger.error(f"Error calculating weapon stats: {weapon_error}")

            try:
                await self._calculate_rivals_nemesis(guild_id, player_characters, combined_stats, server_id)
            except Exception as rival_error:
                logger.error(f"Error calculating rivals/nemesis: {rival_error}")

            return combined_stats

        except Exception as e:
            logger.error(f"Failed to get combined stats: {e}")
            import traceback
            logger.error(f"Stack trace: {traceback.format_exc()}")
            return combined_stats

    async def _calculate_weapon_stats(self, guild_id: int, player_characters: List[str], 
                                    combined_stats: Dict[str, Any], server_id: str = None):
        """Calculate weapon statistics from kill events (excludes suicides)"""
        try:
            weapon_counts = {}

            for character in player_characters:
                query = {
                    'guild_id': guild_id,
                    'killer': character,
                    'is_suicide': False  # Only count actual PvP kills for weapon stats
                }
                
                # Add server filter if specified
                if server_id:
                    query['server_id'] = server_id
                
                cursor = self.bot.db_manager.kill_events.find(query)

                async for kill_event in cursor:
                    weapon = kill_event.get('weapon', 'Unknown')
                    # Skip suicide weapons even if they somehow got through
                    if weapon not in ['Menu Suicide', 'Suicide', 'Falling']:
                        weapon_counts[weapon] = weapon_counts.get(weapon, 0) + 1

            if weapon_counts:
                combined_stats['favorite_weapon'] = max(weapon_counts.keys(), key=lambda x: weapon_counts[x])
                combined_stats['weapon_stats'] = weapon_counts

        except Exception as e:
            logger.error(f"Failed to calculate weapon stats: {e}")

    async def _calculate_rivals_nemesis(self, guild_id: int, player_characters: List[str], 
                                      combined_stats: Dict[str, Any], server_id: str = None):
        """Calculate enhanced rivalry intelligence"""
        try:
            kills_against = {}
            deaths_to = {}

            for character in player_characters:
                # Count kills against others
                query_kills = {
                    'guild_id': guild_id,
                    'killer': character,
                    'is_suicide': False
                }
                
                # Add server filter if specified
                if server_id:
                    query_kills['server_id'] = server_id
                
                cursor = self.bot.db_manager.kill_events.find(query_kills)

                async for kill_event in cursor:
                    victim = kill_event.get('victim')
                    if victim and victim not in player_characters:  # Don't count alt kills
                        kills_against[victim] = kills_against.get(victim, 0) + 1

                # Count deaths to others
                query_deaths = {
                    'guild_id': guild_id,
                    'victim': character,
                    'is_suicide': False
                }
                
                # Add server filter if specified
                if server_id:
                    query_deaths['server_id'] = server_id
                
                cursor = self.bot.db_manager.kill_events.find(query_deaths)

                async for kill_event in cursor:
                    killer = kill_event.get('killer')
                    if killer and killer not in player_characters:  # Don't count alt deaths
                        deaths_to[killer] = deaths_to.get(killer, 0) + 1

            # Enhanced rivalry calculation
            if kills_against:
                most_killed_player = max(kills_against.keys(), key=lambda x: kills_against[x])
                combined_stats['most_eliminated_player'] = most_killed_player
                combined_stats['most_eliminated_count'] = kills_against[most_killed_player]

            if deaths_to:
                killed_by_most_player = max(deaths_to.keys(), key=lambda x: deaths_to[x])
                combined_stats['eliminated_by_most_player'] = killed_by_most_player
                combined_stats['eliminated_by_most_count'] = deaths_to[killed_by_most_player]

            # Calculate rivalry score for tactical advantage
            most_eliminated_count = combined_stats.get('most_eliminated_count', 0)
            eliminated_by_most_count = combined_stats.get('eliminated_by_most_count', 0)
            combined_stats['rivalry_score'] = most_eliminated_count - eliminated_by_most_count

        except Exception as e:
            logger.error(f"Failed to calculate rivalry intelligence: {e}")

    @discord.slash_command(name="stats", description="View PvP statistics for yourself, a user, or a player name")
    async def stats(self, ctx: discord.ApplicationContext, 
                   target: discord.Option(str, "Target user or player name", required=False) = None,
                   server: discord.Option(str, "Server to view stats for", required=False) = None):
        """View PvP statistics for yourself, another user, or a player name"""
        try:
            if not ctx.guild:
                await ctx.respond("❌ This command can only be used in a server!", ephemeral=True)
                return

            guild_id = ctx.guild.id
            server_name = ctx.guild.name

            # Handle server filtering if provided
            if server and server.strip():
                # Validate server exists for this guild
                guild_doc = await self.bot.db_manager.get_guild(guild_id)
                if guild_doc:
                    servers = guild_doc.get('servers', [])
                    server_found = False
                    for server_config in servers:
                        if str(server_config.get('_id', '')) == str(server) or str(server_config.get('server_id', '')) == str(server):
                            server_name = server_config.get('name', f'Server {server}')
                            server_found = True
                            break
                    
                    if not server_found:
                        await ctx.respond("❌ Server not found for this guild.", ephemeral=True)
                        return

            # Handle different target types
            if target is None:
                # No target specified - use author
                resolve_result = await self.resolve_player(ctx, ctx.author)
                if not resolve_result:
                    await ctx.respond(
                        "❌ You don't have any linked characters! Use `/link <character>` to get started.",
                        ephemeral=True
                    )
                    return
                player_characters, display_name = resolve_result
            else:
                # Try to parse as user mention first
                user_mention = None
                if target.startswith('<@') and target.endswith('>'):
                    user_id_str = target[2:-1]
                    if user_id_str.startswith('!'):
                        user_id_str = user_id_str[1:]
                    try:
                        user_id = int(user_id_str)
                        user_mention = ctx.guild.get_member(user_id)
                    except ValueError:
                        pass

                if user_mention:
                    # It's a user mention
                    resolve_result = await self.resolve_player(ctx, user_mention)
                    if not resolve_result:
                        await ctx.respond(
                            f"❌ {user_mention.mention} doesn't have any linked characters!",
                            ephemeral=True
                        )
                        return
                    player_characters, display_name = resolve_result
                else:
                    # It's a raw player name
                    resolve_result = await self.resolve_player(ctx, target)
                    if not resolve_result:
                        await ctx.respond(
                            "❌ Unable to find a linked user or matching player by that name.",
                            ephemeral=True
                        )
                        return
                    player_characters, display_name = resolve_result

            await ctx.defer()

            # Get combined stats
            stats = await self.get_player_combined_stats(guild_id, player_characters, server)

            total_kills = stats['kills']
            total_deaths = stats['deaths']
            total_kdr = f"{stats['kdr']:.2f}"

            # Ensure we have actual data, not placeholders
            if total_kills == 0 and total_deaths == 0:
                # No PvP data found
                embed = discord.Embed(
                    title=f"Combat Profile: {display_name}",
                    description=f"No PvP data found for {display_name} on {server_name}.\nStart playing to see your statistics!",
                    color=0x808080,
                    timestamp=datetime.now(timezone.utc)
                )
                main_file = discord.File("./assets/main.png", filename="main.png")
                embed.set_thumbnail(url="attachment://main.png")
                embed.set_footer(text="Powered by Discord.gg/EmeraldServers")
                
                await ctx.followup.send(embed=embed, file=main_file)
                return

            # Use EmbedFactory for comprehensive themed stats with real data
            embed_data = {
                'player_name': display_name,
                'server_name': server_name,
                'kills': total_kills,
                'deaths': total_deaths,
                'kdr': total_kdr,
                'personal_best_distance': stats.get('personal_best_distance', 0.0),
                'favorite_weapon': stats.get('favorite_weapon'),
                'suicides': stats.get('suicides', 0),
                'best_streak': stats.get('best_streak', 0),
                'servers_played': stats.get('servers_played', 0)
            }

            embed, file = await EmbedFactory.build('stats', embed_data)

            if file:
                await ctx.followup.send(embed=embed, file=file)
            else:
                await ctx.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Failed to show stats: {e}")
            import traceback
            logger.error(f"Stack trace: {traceback.format_exc()}")
            if ctx.response.is_done():
                await ctx.followup.send("❌ Failed to retrieve statistics.", ephemeral=True)
            else:
                await ctx.respond("❌ Failed to retrieve statistics.", ephemeral=True)

    @discord.slash_command(name="compare", description="Compare stats with another player")
    async def compare(self, ctx: discord.ApplicationContext, user: discord.Member):
        """Compare your stats with another player"""
        try:
            if not ctx.guild:
                await ctx.respond("❌ This command can only be used in a server!", ephemeral=True)
                return

            guild_id = ctx.guild.id
            user1 = ctx.author
            user2 = user

            if user1.id == user2.id:
                await ctx.respond("❌ You can't compare stats with yourself!", ephemeral=True)
                return

            # Get both players' data
            player1_data = await self.bot.db_manager.get_linked_player(guild_id, user1.id)
            player2_data = await self.bot.db_manager.get_linked_player(guild_id, user2.id)

            if not player1_data or not isinstance(player1_data, dict):
                await ctx.respond(
                    "❌ You don't have any linked characters! Use `/link <character>` to get started.",
                    ephemeral=True
                )
                return

            if not player2_data or not isinstance(player2_data, dict):
                await ctx.respond(
                    f"❌ {user2.mention} doesn't have any linked characters!",
                    ephemeral=True
                )
                return

            await ctx.defer()

            # Get stats for both players
            stats1 = await self.get_player_combined_stats(guild_id, player1_data['linked_characters'])
            stats2 = await self.get_player_combined_stats(guild_id, player2_data['linked_characters'])

            # Use EmbedFactory for comparison embed
            embed_data = {
                'player1_name': user1.display_name,
                'player2_name': user2.display_name,
                'player1_stats': stats1,
                'player2_stats': stats2,
                'requester': ctx.author.display_name
            }

            embed, file_attachment = await EmbedFactory.build('comparison', embed_data)

            if file_attachment:
                await ctx.followup.send(embed=embed, file=file_attachment)
            else:
                await ctx.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Failed to compare stats: {e}")
            await ctx.respond("❌ Failed to compare statistics.", ephemeral=True)

def setup(bot):
    bot.add_cog(Stats(bot))