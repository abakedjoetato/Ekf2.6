"""
Emerald's Killfeed - Unified Log Parser (Refactored)
Modular log parser using extracted components
"""

import asyncio
import asyncssh
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any

from bot.utils.embed_factory import EmbedFactory
from bot.parsers.components.player_lifecycle import PlayerLifecycleManager
from bot.parsers.components.log_event_processor import LogEventProcessor

logger = logging.getLogger(__name__)

class UnifiedLogParser:
    """Refactored unified log parser with modular architecture"""
    
    def __init__(self, bot):
        self.bot = bot
        self.lifecycle_manager = PlayerLifecycleManager()
        self.event_processor = LogEventProcessor()
        self.connections: Dict[str, Any] = {}
        self.parser_states: Dict[str, Dict] = {}
        
    async def run_log_parser(self):
        """Main parser execution method"""
        try:
            logger.info("🔄 Running unified log parser...")
            
            # Get guilds from bot's connected guilds
            guilds = []
            for guild in self.bot.guilds:
                guild_doc = await self.bot.db_manager.get_guild(guild.id)
                if guild_doc:
                    guilds.append(guild_doc)
            
            for guild in guilds:
                # Use the actual Discord guild ID, not the MongoDB document ID
                discord_guild_id = guild.get('guild_id', 0)
                servers = guild.get('servers', [])
                
                if not servers or not discord_guild_id:
                    continue
                    
                logger.info(f"📡 Processing {len(servers)} servers for Guild {discord_guild_id}")
                
                for server_config in servers:
                    await self.process_server(discord_guild_id, server_config)
                    
            logger.info("✅ Parser completed: {} servers processed".format(
                sum(len(g.get('servers', [])) for g in guilds)
            ))
            
        except Exception as e:
            logger.error(f"Parser execution failed: {e}")
            
    async def process_server(self, guild_id: int, server_config: Dict[str, Any]):
        """Process individual server logs"""
        try:
            server_name = server_config.get('name', 'Unknown Server')
            server_id = str(server_config.get('_id', server_config.get('server_id', 'unknown')))
            host = server_config.get('host')
            port = server_config.get('port', 8822)
            username = server_config.get('username', 'root')
            password = server_config.get('password')
            
            if not host:
                logger.warning(f"No host configured for server {server_name}")
                return
                
            logger.info(f"🔍 Processing {server_name} (ID: {server_id}, Host: {host})")
            
            # Get parser state
            parser_state = await self.get_parser_state(guild_id, server_id)
            
            # Connect and read logs
            log_content = await self.read_server_logs(host, port, username, server_id, password)
            if not log_content:
                return
                
            # Determine if cold start needed
            current_size = len(log_content)
            last_size = parser_state.get('last_log_size', 0)
            cold_start = current_size < last_size or last_size == 0
            
            if cold_start:
                logger.info(f"🧊 Cold start: processing {len(log_content.splitlines())} lines to rebuild player state")
                self.lifecycle_manager.clear_guild_sessions(guild_id)
                lines_to_process = log_content.splitlines()
                # Process all lines to rebuild current player state
                await self.rebuild_player_state(lines_to_process, guild_id, server_id)
            else:
                logger.info(f"🔥 Hot start: processing {current_size - last_size} new bytes")
                new_content = log_content[last_size:]
                lines_to_process = new_content.splitlines()
                
                # Check if we need to rebuild player state (no active players tracked)
                active_players = self.lifecycle_manager.get_active_players(guild_id)
                server_players = [p for p in active_players.values() if p.get('server_id') == server_id]
                
                if len(server_players) == 0:
                    logger.info(f"🔄 No active players tracked, rebuilding state from complete log")
                    all_lines = log_content.splitlines()
                    logger.info(f"🔍 Analyzing {len(all_lines)} total log lines for player history")
                    await self.rebuild_player_state(all_lines, guild_id, server_id)
                
            # Process log lines
            embeds = await self.process_log_lines(
                lines_to_process, guild_id, server_id, server_name, cold_start
            )
            
            # Send embeds
            if embeds and not cold_start:
                await self.send_embeds(guild_id, server_id, embeds)
                
            # Update parser state
            await self.update_parser_state(guild_id, server_id, {
                'last_log_size': current_size,
                'last_processed': datetime.now(timezone.utc).isoformat(),
                'server_name': server_name
            })
            
            # Update voice channel
            await self.update_voice_channel(guild_id, server_id, server_name)
            
            logger.info(f"✅ {server_name}: {'Cold start' if cold_start else f'{len(embeds)} total events sent'}")
            
        except Exception as e:
            logger.error(f"Error processing server {server_config.get('name', 'Unknown')}: {e}")
            
    async def rebuild_player_state(self, lines: List[str], guild_id: int, server_id: str):
        """Rebuild current player state from complete log history"""
        logger.info(f"🔄 Rebuilding player state from {len(lines)} log lines")
        
        # Track player state changes chronologically
        player_events = []
        
        # Extract all player events from log history
        for line in lines:
            events = self.event_processor.process_log_line(line)
            for event in events:
                if event['type'] in ['queue', 'join', 'disconnect']:
                    player_events.append(event)
        
        # Sort events chronologically
        player_events.sort(key=lambda x: x['timestamp'])
        logger.info(f"🔍 Found {len(player_events)} historical player events")
        
        # Replay events to determine current state
        active_players = set()
        
        for event in player_events:
            player_id = event['player_id']
            
            if event['type'] == 'queue':
                # Player queued - update lifecycle but don't count as online yet
                self.lifecycle_manager.update_player_queue(
                    guild_id, player_id, event.get('player_name', f"Player{player_id[:8].upper()}"), 
                    event.get('platform', 'Unknown'), event['timestamp']
                )
                
            elif event['type'] == 'join':
                # Player joined - mark as active
                session_data = self.lifecycle_manager.update_player_join(
                    guild_id, player_id, server_id, event['timestamp']
                )
                active_players.add(player_id)
                logger.info(f"🔍 State rebuild: {session_data.get('player_name')} joined (total: {len(active_players)})")
                
            elif event['type'] == 'disconnect':
                # Player left - remove from active
                disconnect_data = self.lifecycle_manager.update_player_disconnect(
                    guild_id, player_id, event['timestamp']
                )
                if player_id in active_players:
                    active_players.remove(player_id)
                    if disconnect_data:
                        logger.info(f"🔍 State rebuild: {disconnect_data.get('player_name')} left (total: {len(active_players)})")
        
        logger.info(f"✅ Player state rebuilt: {len(active_players)} players currently online")
            
    async def read_server_logs(self, host: str, port: int, username: str, server_id: str, password: Optional[str] = None) -> Optional[str]:
        """Read logs from server via SFTP"""
        try:
            logger.info(f"📡 Reading SFTP: ./{host}_{server_id}/Logs/Deadside.log")
            
            # P3R server connection with compatible SSH settings
            async with asyncssh.connect(
                host, port=port, username=username, password=password,
                known_hosts=None, 
                client_keys=[],
                server_host_key_algs=['ssh-rsa', 'ssh-dss'],
                kex_algs=['diffie-hellman-group1-sha1', 'diffie-hellman-group14-sha1'],
                encryption_algs=['aes128-cbc', 'aes192-cbc', 'aes256-cbc'],
                mac_algs=['hmac-sha1'],
                compression_algs=['none']
            ) as conn:
                logger.info(f"✅ SFTP connected to {host}:{port}")
                
                async with conn.start_sftp_client() as sftp:
                    log_path = f"./{host}_{server_id}/Logs/Deadside.log"
                    
                    try:
                        async with sftp.open(log_path, 'r') as f:
                            content = await f.read()
                            logger.info(f"✅ SFTP read {len(content)} bytes")
                            return content
                    except FileNotFoundError:
                        logger.warning(f"Log file not found: {log_path}")
                        return None
                        
        except Exception as e:
            logger.error(f"SFTP connection failed for {host}:{port} - {e}")
            return None
            
    async def process_log_lines(self, lines: List[str], guild_id: int, server_id: str, 
                               server_name: str, cold_start: bool) -> List[Any]:
        """Process log lines and generate embeds"""
        embeds = []
        player_events = []
        server_config = {}
        
        # Extract events from all lines
        for i, line in enumerate(lines):
            # Debug: Show sample log lines to understand format
            if i < 5:  # Show first 5 lines for debugging
                logger.info(f"🔍 Log line {i}: {line[:100]}...")
            
            events = self.event_processor.process_log_line(line)
            
            for event in events:
                if event['type'] in ['queue', 'join', 'disconnect']:
                    player_events.append(event)
                elif event['type'] == 'config':
                    server_config[event['key']] = event['value']
                elif event['type'] == 'mission':
                    if not cold_start:
                        embed_data = {
                            'mission_id': event['mission_id'],
                            'state': event['state'],
                            'server_name': server_name
                        }
                        final_embed, file_attachment = await EmbedFactory.build_mission_embed(embed_data)
                        embeds.append((final_embed, file_attachment, 'events'))
                        
        # Sort player events chronologically
        player_events.sort(key=lambda x: x['timestamp'])
        logger.info(f"🔄 Processing {len(player_events)} player events in chronological order")
        
        # Debug: Show all detected player events
        for event in player_events:
            logger.info(f"🔍 Player event: {event['type']} - Player {event['player_id'][:8]} at {event['timestamp']}")
        
        # Process player events
        for event in player_events:
            if event['type'] == 'queue':
                self.lifecycle_manager.update_player_queue(
                    guild_id, event['player_id'], event['player_name'], 
                    event['platform'], event['timestamp']
                )
                
            elif event['type'] == 'join':
                session_data = self.lifecycle_manager.update_player_join(
                    guild_id, event['player_id'], server_id, event['timestamp']
                )
                logger.info(f"🔍 Player joined: {session_data.get('player_name')} (ID: {event['player_id'][:8]}) on server {server_id}")
                
                # Save to database
                if hasattr(self.bot, 'db_manager'):
                    await self.bot.db_manager.save_player_session(
                        int(guild_id), server_id, event['player_id'], session_data
                    )
                    
                # Create connection embed (not during cold start)
                if not cold_start:
                    embed_data = {
                        'player_name': session_data['player_name'],
                        'platform': session_data['platform'],
                        'server_name': server_name
                    }
                    final_embed, file_attachment = await EmbedFactory.build_connection_embed(embed_data)
                    embeds.append((final_embed, file_attachment, 'connections'))
                    
            elif event['type'] == 'disconnect':
                disconnect_data = self.lifecycle_manager.update_player_disconnect(
                    guild_id, event['player_id'], event['timestamp']
                )
                if disconnect_data:
                    logger.info(f"🔍 Player disconnected: {disconnect_data.get('player_name')} (ID: {event['player_id'][:8]})")
                
                if disconnect_data:
                    # Remove from database
                    if hasattr(self.bot, 'db_manager'):
                        await self.bot.db_manager.remove_player_session(
                            int(guild_id), server_id, event['player_id']
                        )
                        
                    # Create disconnect embed (not during cold start)
                    if not cold_start:
                        embed_data = {
                            'player_name': disconnect_data['player_name'],
                            'platform': disconnect_data['platform'],
                            'server_name': server_name
                        }
                        final_embed, file_attachment = await EmbedFactory.build_disconnection_embed(embed_data)
                        embeds.append((final_embed, file_attachment, 'connections'))
                        
        return embeds
        
    async def send_embeds(self, guild_id: int, server_id: str, embeds: List[Any]):
        """Send embeds to appropriate channels with proper routing and theming"""
        try:
            if not embeds:
                return
                
            # Use channel router for proper routing
            if hasattr(self.bot, 'channel_router'):
                for embed_data in embeds[:10]:  # Limit to prevent spam
                    # Handle both old format (embed only) and new format (embed, file, channel_type)
                    if isinstance(embed_data, tuple) and len(embed_data) == 3:
                        embed, file_attachment, channel_type = embed_data
                    else:
                        # Fallback for old format
                        embed = embed_data
                        file_attachment = None
                        channel_type = self._determine_channel_type(embed)
                    
                    success = await self.bot.channel_router.send_embed_to_channel(
                        guild_id, server_id, channel_type, embed, file_attachment
                    )
                    
                    if not success:
                        logger.warning(f"Failed to send {channel_type} embed to appropriate channel")
            else:
                logger.error("Channel router not available")
                            
        except Exception as e:
            logger.error(f"Error sending embeds: {e}")
    
    def _determine_channel_type(self, embed) -> str:
        """Determine appropriate channel type based on embed content"""
        if not embed or not hasattr(embed, 'title'):
            return 'killfeed'
            
        title = embed.title.lower() if embed.title else ""
        
        # Check for connection/disconnection embeds
        if any(keyword in title for keyword in ['reinforcements', 'operative deployed', 'extraction', 'withdrawn']):
            return 'connections'
        
        # Check for mission embeds  
        if any(keyword in title for keyword in ['mission', 'operation', 'classified', 'objective']):
            return 'events'
            
        # Check for airdrop/helicrash embeds
        if any(keyword in title for keyword in ['airdrop', 'supply', 'helicrash', 'helicopter']):
            return 'events'
            
        # Default to killfeed for combat/kills
        return 'killfeed'
            
    async def update_voice_channel(self, guild_id: int, server_id: str, server_name: str):
        """Update voice channel with current player count"""
        try:
            # First try to get accurate count from lifecycle manager
            active_players = self.lifecycle_manager.get_active_players(guild_id)
            server_players = [p for p in active_players.values() if p.get('server_id') == server_id]
            tracked_player_count = len(server_players)
            
            # Try to get real player count via server query as fallback
            actual_player_count = tracked_player_count
            
            # Get server config to find host for querying
            guild_config = await self.bot.db_manager.get_guild(guild_id)
            if guild_config:
                servers = guild_config.get('servers', {})
                # Handle both dictionary and list formats for servers
                if isinstance(servers, dict):
                    server_config = servers.get(server_id, {})
                elif isinstance(servers, list):
                    server_config = next((s for s in servers if s.get('id') == server_id), {})
                else:
                    server_config = {}
                host = server_config.get('host')
                
                if host:
                    from bot.utils.server_query import ServerQuery
                    query_result = await ServerQuery.query_deadside_server(host)
                    if query_result and query_result.get('query_successful'):
                        actual_player_count = query_result.get('players', tracked_player_count)
                        logger.info(f"🔍 Server query successful: {actual_player_count} players online")
                    else:
                        logger.debug(f"🔍 Server query failed, using tracked count: {tracked_player_count}")
                        
            player_count = actual_player_count
            
            # Reduced logging for production
            if player_count != tracked_player_count:
                logger.info(f"Voice channel update: {server_name} has {player_count} players (tracked: {tracked_player_count})")
            else:
                logger.debug(f"Voice channel update: {server_name} has {player_count} players")
            
            # Get max players from config
            max_players = 50  # Default
            
            # Determine status
            if player_count == 0:
                status = "OFFLINE"
                color = "🔴"
            elif player_count < max_players * 0.3:
                status = "LOW"
                color = "🔵"
            elif player_count < max_players * 0.7:
                status = "MEDIUM"
                color = "🟡"
            else:
                status = "HIGH"
                color = "🟠"
                
            channel_name = f"{color} {server_name} [{status}] • {player_count}/{max_players}"
            
            # Update voice channel
            guild_config = await self.bot.db_manager.get_guild(int(guild_id))
            logger.info(f"🔍 Guild config found: {guild_config is not None}")
            
            if guild_config:
                # Check new server_channels structure first
                server_channels_config = guild_config.get('server_channels', {})
                server_specific = server_channels_config.get(server_id, {})
                default_server = server_channels_config.get('default', {})
                
                # Check legacy channels structure
                legacy_channels = guild_config.get('channels', {})
                
                # Priority: server-specific -> default server -> legacy channels
                vc_id = (server_specific.get('playercountvc') or 
                        default_server.get('playercountvc') or 
                        legacy_channels.get('playercountvc'))
                
                logger.info(f"🔍 Legacy channels: {legacy_channels}")
                logger.info(f"🔍 Server channels for {server_id}: {server_specific}")
                logger.info(f"🔍 Default server channels: {default_server}")
                logger.info(f"🔍 Legacy playercountvc: {legacy_channels.get('playercountvc')}")
                logger.info(f"🔍 Voice channel ID: {vc_id}")
                
                if vc_id:
                    voice_channel = self.bot.get_channel(int(vc_id))
                    logger.info(f"🔍 Voice channel found: {voice_channel is not None}")
                    
                    if voice_channel:
                        current_name = voice_channel.name
                        logger.info(f"🔍 Current name: '{current_name}' -> Target: '{channel_name}'")
                        
                        if current_name != channel_name:
                            await voice_channel.edit(name=channel_name)
                            logger.info(f"✅ Voice channel updated to: {channel_name}")
                        else:
                            logger.info(f"🔄 Voice channel already correct: {channel_name}")
                    else:
                        logger.warning(f"❌ Voice channel not found with ID: {vc_id}")
                else:
                    logger.info(f"🔍 No voice channel configured for server {server_id}")
            else:
                logger.warning(f"❌ No guild config found for guild {guild_id}")
                        
        except Exception as e:
            logger.error(f"Voice channel update failed: {e}")
            import traceback
            logger.error(f"Voice channel traceback: {traceback.format_exc()}")
            
    async def get_parser_state(self, guild_id: int, server_id: str) -> Dict[str, Any]:
        """Get parser state from database"""
        try:
            state = await self.bot.db_manager.get_parser_state(guild_id, server_id)
            return state or {}
        except Exception as e:
            logger.error(f"Failed to get parser state: {e}")
            return {}
            
    async def update_parser_state(self, guild_id: int, server_id: str, state_data: Dict[str, Any]):
        """Update parser state in database"""
        try:
            await self.bot.db_manager.save_parser_state(guild_id, server_id, "log_parser", state_data)
        except Exception as e:
            logger.error(f"Failed to save parser state: {e}")
            
    async def reset_parser_state(self, guild_id: int, server_id: str):
        """Reset parser state for a specific server"""
        try:
            await self.bot.db_manager.save_parser_state(guild_id, server_id, "log_parser", {
                'last_log_size': 0,
                'last_processed': datetime.now(timezone.utc).isoformat(),
                'reset_at': datetime.now(timezone.utc).isoformat()
            })
            logger.info(f"Parser state reset for {guild_id}_{server_id}")
        except Exception as e:
            logger.error(f"Failed to reset parser state: {e}")

def setup(bot):
    """Setup function for parser integration"""
    return UnifiedLogParser(bot)