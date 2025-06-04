"""
Scalable Unified Processor - Fixed Version
Handles log parsing and event detection with proper syntax
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class ScalableUnifiedProcessor:
    """Unified processor for parsing game server logs"""
    
    def __init__(self, bot):
        self.bot = bot
        self.connection_patterns = self._compile_connection_patterns()
        self.event_patterns = self._compile_event_patterns()
    
    def _compile_connection_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for connection events - Real Deadside server format"""
        return {
            # Queue state - player joining
            'player_queue': re.compile(r'LogNet: Join request: /Game/Maps/world_[^?]*\?.*?login=([^?]+).*?eosid=\|([a-f0-9]+).*?Name=([^?]+)', re.IGNORECASE),
            # Connected state - player registered 
            'player_connect': re.compile(r'LogOnline: Warning: Player \|([a-f0-9]+) successfully registered!', re.IGNORECASE),
            # Disconnected state - player left
            'player_disconnect': re.compile(r'LogNet: UChannel::Close:.*UniqueId: EOS:\|([a-f0-9]+)', re.IGNORECASE)
        }
    
    def _compile_event_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for game events - Updated for real Deadside server format"""
        return {
            'mission_start': re.compile(r'LogSFPS: Mission (\w+) switched to READY', re.IGNORECASE),
            'mission_end': re.compile(r'LogSFPS: Mission (\w+) switched to WAITING', re.IGNORECASE),
            'airdrop': re.compile(r'LogSFPS: AirDrop switched to Dropping', re.IGNORECASE),
            'patrol_active': re.compile(r'LogSFPS: PatrolPoint (\w+) switched to ACTIVE', re.IGNORECASE),
            'patrol_initial': re.compile(r'LogSFPS: PatrolPoint (\w+) switched to INITIAL', re.IGNORECASE),
            'vehicle_deleted': re.compile(r'LogSFPS: .*Del vehicle.*Total (\d+)', re.IGNORECASE)
        }
    
    def parse_log_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single log line and extract relevant information"""
        line = line.strip()
        if not line:
            return None
        
        try:
            # Extract timestamp
            if not line.startswith('['):
                return None
            
            timestamp_end = line.find(']')
            if timestamp_end == -1:
                return None
            
            timestamp_str = line[1:timestamp_end]
            message = line[timestamp_end + 1:].strip()
            
            # Parse timestamp
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y.%m.%d-%H.%M.%S:%f')
            except ValueError:
                return None
            
            # Check connection patterns
            for event_type, pattern in self.connection_patterns.items():
                match = pattern.search(message)
                if match:
                    if event_type == 'player_queue':
                        # Queue: login=PlayerName, eosid=PlayerID, Name=PlayerName
                        return {
                            'timestamp': timestamp,
                            'type': 'connection',
                            'event': event_type,
                            'player_name': match.group(3),  # Name field
                            'login_name': match.group(1),   # Login field
                            'eos_id': match.group(2),       # EOS ID
                            'raw_message': message
                        }
                    elif event_type == 'player_connect':
                        # Connect: Player |EOS_ID successfully registered
                        return {
                            'timestamp': timestamp,
                            'type': 'connection',
                            'event': event_type,
                            'eos_id': match.group(1),
                            'raw_message': message
                        }
                    elif event_type == 'player_disconnect':
                        # Disconnect: UniqueId: EOS:|EOS_ID
                        return {
                            'timestamp': timestamp,
                            'type': 'connection',
                            'event': event_type,
                            'eos_id': match.group(1),
                            'raw_message': message
                        }
            
            # Check event patterns
            for event_type, pattern in self.event_patterns.items():
                match = pattern.search(message)
                if match:
                    return {
                        'timestamp': timestamp,
                        'type': 'event',
                        'event': event_type,
                        'details': match.groups(),
                        'raw_message': message
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing log line: {e}")
            return None
    
    async def process_log_data(self, log_data: str, server_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process multiple log lines and return parsed events"""
        events = []
        lines = log_data.split('\n')
        
        logger.info(f"Processing {len(lines)} log lines from {server_config.get('name', 'Unknown')}")
        
        connection_count = 0
        event_count = 0
        
        for line in lines:
            parsed = self.parse_log_line(line)
            if parsed:
                parsed['server_name'] = server_config.get('name', 'Unknown')
                parsed['guild_id'] = server_config.get('guild_id')
                parsed['server_id'] = server_config.get('server_id', 'Unknown')
                events.append(parsed)
                
                if parsed['type'] == 'connection':
                    connection_count += 1
                elif parsed['type'] == 'event':
                    event_count += 1
        
        logger.info(f"Parsed {len(events)} total events: {connection_count} connections, {event_count} game events")
        
        # Log sample of first few lines for debugging
        if not events and len(lines) > 10:
            logger.info("Sample log lines for debugging:")
            for i, line in enumerate(lines[:5]):
                if line.strip():
                    logger.info(f"  Line {i}: {line[:100]}...")
        
        return events
    
    async def update_player_sessions(self, events: List[Dict[str, Any]]) -> bool:
        """Update player session states based on connection events using EOS ID tracking"""
        if not self.bot.db_manager:
            return False
        
        try:
            state_changes = []  # Track actual state changes for embed sending
            
            for event in events:
                if event['type'] != 'connection':
                    continue
                
                eos_id = event.get('eos_id')
                guild_id = event['guild_id']
                server_id = event['server_id']
                timestamp = event['timestamp']
                event_type = event['event']
                
                if not eos_id:
                    continue
                
                # Get current player state
                current_session = await self.bot.db_manager.player_sessions.find_one({
                    'eos_id': eos_id,
                    'guild_id': guild_id,
                    'server_id': server_id
                })
                
                current_state = current_session.get('state', 'offline') if current_session else 'offline'
                new_state = current_state
                player_data = {}
                
                if event_type == 'player_queue':
                    # Player is queuing to join
                    new_state = 'queued'
                    player_data = {
                        'eos_id': eos_id,
                        'player_name': event.get('player_name', 'Unknown'),
                        'login_name': event.get('login_name', 'Unknown'),
                        'guild_id': guild_id,
                        'server_id': server_id,
                        'state': 'queued',
                        'queued_at': timestamp,
                        'last_seen': timestamp
                    }
                    
                elif event_type == 'player_connect':
                    # Player successfully registered (queued -> online)
                    new_state = 'online'
                    player_data = {
                        'state': 'online',
                        'joined_at': timestamp,
                        'last_seen': timestamp
                    }
                    
                elif event_type == 'player_disconnect':
                    # Player disconnected (online -> offline)
                    new_state = 'offline'
                    player_data = {
                        'state': 'offline',
                        'left_at': timestamp,
                        'last_seen': timestamp
                    }
                
                # Only update if state actually changed
                if new_state != current_state:
                    await self.bot.db_manager.player_sessions.update_one(
                        {
                            'eos_id': eos_id,
                            'guild_id': guild_id,
                            'server_id': server_id
                        },
                        {'$set': player_data},
                        upsert=True
                    )
                    
                    # Track state change for embed sending
                    state_changes.append({
                        'eos_id': eos_id,
                        'player_name': event.get('player_name') or (current_session.get('player_name', 'Unknown') if current_session else 'Unknown'),
                        'old_state': current_state,
                        'new_state': new_state,
                        'timestamp': timestamp,
                        'guild_id': guild_id,
                        'server_id': server_id
                    })
                    
                    logger.info(f"Player state change: {eos_id[:8]}... {current_state} -> {new_state}")
            
            # Send embeds for actual state changes
            if state_changes:
                await self._send_connection_embeds(state_changes)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update player sessions: {e}")
            return False
    
    async def _send_connection_embeds(self, state_changes: List[Dict[str, Any]]) -> bool:
        """Send connection embeds only for actual state changes"""
        try:
            from bot.utils.channel_router import ChannelRouter
            
            channel_router = ChannelRouter(self.bot)
            
            for change in state_changes:
                # Only send embeds for specific state transitions
                if change['old_state'] == 'queued' and change['new_state'] == 'online':
                    # Player connected (queued -> online)
                    import discord
                    from datetime import datetime, timezone
                    
                    embed = discord.Embed(
                        title="🟢 Player Connected",
                        description=f"**{change['player_name']}** joined the server",
                        color=0x00FF00,
                        timestamp=datetime.now(timezone.utc)
                    )
                    embed.add_field(name="EOS ID", value=f"`{change['eos_id'][:16]}...`", inline=True)
                    embed.add_field(name="Server", value=change.get('server_name', 'Unknown'), inline=True)
                    
                    await channel_router.send_embed_to_channel(
                        guild_id=change['guild_id'],
                        server_id=change['server_id'],
                        channel_type='killfeed',
                        embed=embed
                    )
                
                elif change['old_state'] == 'online' and change['new_state'] == 'offline':
                    # Player disconnected (online -> offline)
                    import discord
                    from datetime import datetime, timezone
                    
                    embed = discord.Embed(
                        title="🔴 Player Disconnected",
                        description=f"**{change['player_name']}** left the server",
                        color=0xFF0000,
                        timestamp=datetime.now(timezone.utc)
                    )
                    embed.add_field(name="EOS ID", value=f"`{change['eos_id'][:16]}...`", inline=True)
                    embed.add_field(name="Server", value=change.get('server_name', 'Unknown'), inline=True)
                    
                    await channel_router.send_embed_to_channel(
                        guild_id=change['guild_id'],
                        server_id=change['server_id'],
                        channel_type='killfeed',
                        embed=embed
                    )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send connection embeds: {e}")
            return False
    
    async def send_event_embeds(self, events: List[Dict[str, Any]]) -> bool:
        """Send Discord embeds for game events"""
        if not events:
            return True
        
        try:
            from bot.utils.channel_router import ChannelRouter
            
            channel_router = ChannelRouter(self.bot)
            
            for event in events:
                if event['type'] == 'event':
                    embed_type = self._map_event_to_embed_type(event['event'])
                    if embed_type:
                        await channel_router.send_embed_to_channel(
                            guild_id=event['guild_id'],
                            server_id=event['server_id'],
                            channel_type=embed_type,
                            embed=event
                        )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send event embeds: {e}")
            return False
    
    def _map_event_to_embed_type(self, event_type: str) -> Optional[str]:
        """Map event types to embed types"""
        mapping = {
            'mission_start': 'missions',
            'mission_end': 'missions',
            'airdrop': 'events',
            'patrol_active': 'events',
            'patrol_initial': 'events',
            'vehicle_deleted': 'events'
        }
        return mapping.get(event_type)

    async def process_log_data_cold_start(self, server_config: Dict[str, Any], guild_id: int) -> List[Dict[str, Any]]:
        """Process all log data chronologically from beginning for cold start"""
        try:
            # Fetch all log data from server
            log_data = await self._fetch_server_logs(server_config)
            if not log_data:
                return []
            
            events = []
            for line in log_data.split('\n'):
                parsed = self.parse_log_line(line)
                if parsed:
                    parsed['guild_id'] = guild_id
                    parsed['server_id'] = server_config.get('server_id', 'default')
                    parsed['server_name'] = server_config.get('server_name', 'Unknown')
                    events.append(parsed)
            
            # Sort chronologically
            events.sort(key=lambda x: x.get('timestamp', ''))
            return events
            
        except Exception as e:
            logger.error(f"Error in cold start processing: {e}")
            return []
    
    async def process_log_data_hot_start(self, server_config: Dict[str, Any], guild_id: int, last_timestamp: Optional[str]) -> List[Dict[str, Any]]:
        """Process only new log data since last timestamp for hot start"""
        try:
            # Fetch all log data from server
            log_data = await self._fetch_server_logs(server_config)
            if not log_data:
                return []
            
            events = []
            for line in log_data.split('\n'):
                parsed = self.parse_log_line(line)
                if parsed:
                    # Only include events newer than last timestamp
                    if last_timestamp and parsed.get('timestamp', '') <= last_timestamp:
                        continue
                        
                    parsed['guild_id'] = guild_id
                    parsed['server_id'] = server_config.get('server_id', 'default')
                    parsed['server_name'] = server_config.get('server_name', 'Unknown')
                    events.append(parsed)
            
            # Sort chronologically
            events.sort(key=lambda x: x.get('timestamp', ''))
            return events
            
        except Exception as e:
            logger.error(f"Error in hot start processing: {e}")
            return []
    
    async def update_player_sessions_cold(self, events: List[Dict[str, Any]], guild_id: int, server_id: str):
        """Update player sessions for cold start - no embeds sent"""
        try:
            for event in events:
                if event.get('type') == 'connection':
                    await self._update_single_player_session(event, send_embeds=False)
            
            logger.info(f"Cold start: Updated player sessions for {len(events)} events")
            
        except Exception as e:
            logger.error(f"Error updating player sessions in cold start: {e}")
    
    async def send_connection_embeds_batch(self, state_changes: List[Dict[str, Any]]):
        """Send connection embeds using batch sending"""
        try:
            from bot.utils.channel_router import ChannelRouter
            import discord
            from datetime import datetime, timezone
            
            channel_router = ChannelRouter(self.bot)
            
            for change in state_changes:
                if change['old_state'] == 'queued' and change['new_state'] == 'online':
                    # Player connected
                    embed = discord.Embed(
                        title="🟢 Player Connected",
                        description=f"**{change['player_name']}** joined the server",
                        color=0x00FF00,
                        timestamp=datetime.now(timezone.utc)
                    )
                    embed.add_field(name="EOS ID", value=f"`{change['eos_id'][:16]}...`", inline=True)
                    embed.add_field(name="Server", value=change.get('server_name', 'Unknown'), inline=True)
                    
                    await channel_router.send_embed_to_channel(
                        guild_id=change['guild_id'],
                        server_id=change['server_id'],
                        channel_type='killfeed',
                        embed=embed
                    )
                
                elif change['old_state'] == 'online' and change['new_state'] == 'offline':
                    # Player disconnected
                    embed = discord.Embed(
                        title="🔴 Player Disconnected",
                        description=f"**{change['player_name']}** left the server",
                        color=0xFF0000,
                        timestamp=datetime.now(timezone.utc)
                    )
                    embed.add_field(name="EOS ID", value=f"`{change['eos_id'][:16]}...`", inline=True)
                    embed.add_field(name="Server", value=change.get('server_name', 'Unknown'), inline=True)
                    
                    await channel_router.send_embed_to_channel(
                        guild_id=change['guild_id'],
                        server_id=change['server_id'],
                        channel_type='killfeed',
                        embed=embed
                    )
                    
        except Exception as e:
            logger.error(f"Error sending connection embeds batch: {e}")
    
    async def send_event_embeds_batch(self, game_events: List[Dict[str, Any]]):
        """Send game event embeds using batch sending"""
        try:
            from bot.utils.channel_router import ChannelRouter
            import discord
            from datetime import datetime, timezone
            
            channel_router = ChannelRouter(self.bot)
            
            for event in game_events:
                embed = self._create_event_embed(event)
                if embed:
                    channel_type = self._get_channel_type_for_event(event.get('event'))
                    
                    await channel_router.send_embed_to_channel(
                        guild_id=event['guild_id'],
                        server_id=event['server_id'],
                        channel_type=channel_type,
                        embed=embed
                    )
                    
        except Exception as e:
            logger.error(f"Error sending event embeds batch: {e}")
    
    def _create_event_embed(self, event: Dict[str, Any]) -> Optional[Any]:
        """Create Discord embed for game event"""
        try:
            import discord
            from datetime import datetime, timezone
            
            event_type = event.get('event')
            
            if event_type == 'mission_start':
                embed = discord.Embed(
                    title="🎯 Mission Started",
                    description=f"Mission **{event.get('mission_name', 'Unknown')}** is now active",
                    color=0x00FF00,
                    timestamp=datetime.now(timezone.utc)
                )
            elif event_type == 'mission_end':
                embed = discord.Embed(
                    title="🎯 Mission Ended",
                    description=f"Mission **{event.get('mission_name', 'Unknown')}** has ended",
                    color=0xFF0000,
                    timestamp=datetime.now(timezone.utc)
                )
            elif event_type == 'airdrop':
                embed = discord.Embed(
                    title="📦 Airdrop Incoming",
                    description="An airdrop is being deployed",
                    color=0x0099FF,
                    timestamp=datetime.now(timezone.utc)
                )
            else:
                return None
                
            embed.add_field(name="Server", value=event.get('server_name', 'Unknown'), inline=True)
            return embed
            
        except Exception as e:
            logger.error(f"Error creating event embed: {e}")
            return None
    
    def _get_channel_type_for_event(self, event_type: str) -> str:
        """Get appropriate channel type for event"""
        if event_type in ['mission_start', 'mission_end']:
            return 'missions'
        elif event_type == 'airdrop':
            return 'events'
        else:
            return 'events'
    
    async def _update_single_player_session(self, event: Dict[str, Any], send_embeds: bool = True):
        """Update a single player session based on connection event"""
        try:
            from datetime import timezone
            
            eos_id = event.get('eos_id')
            if not eos_id:
                return
                
            event_type = event.get('event')
            
            if event_type == 'player_queue':
                # Player joined queue
                await self.bot.db_manager.player_sessions.update_one(
                    {'eos_id': eos_id, 'guild_id': event['guild_id'], 'server_id': event['server_id']},
                    {
                        '$set': {
                            'state': 'queued',
                            'player_name': event.get('player_name', 'Unknown'),
                            'last_updated': datetime.now(timezone.utc)
                        }
                    },
                    upsert=True
                )
                
            elif event_type == 'player_connect':
                # Player connected
                await self.bot.db_manager.player_sessions.update_one(
                    {'eos_id': eos_id, 'guild_id': event['guild_id'], 'server_id': event['server_id']},
                    {
                        '$set': {
                            'state': 'online',
                            'last_updated': datetime.now(timezone.utc)
                        }
                    }
                )
                
            elif event_type == 'player_disconnect':
                # Player disconnected
                await self.bot.db_manager.player_sessions.update_one(
                    {'eos_id': eos_id, 'guild_id': event['guild_id'], 'server_id': event['server_id']},
                    {
                        '$set': {
                            'state': 'offline',
                            'last_updated': datetime.now(timezone.utc)
                        }
                    }
                )
                
        except Exception as e:
            logger.error(f"Error updating player session: {e}")

    async def _fetch_server_logs(self, server_config: Dict[str, Any]) -> str:
        """Fetch log data from server via SFTP using robust connection strategies"""
        try:
            import asyncssh
            from bot.utils.connection_pool import connection_manager
            
            # Priority order for SSH credentials:
            # 1. sftp_credentials (preferred)
            # 2. individual ssh_* fields
            # 3. legacy host/username/password fields
            
            sftp_creds = server_config.get('sftp_credentials', {})
            if sftp_creds:
                ssh_host = sftp_creds.get('host', '').strip()
                ssh_username = sftp_creds.get('username')
                ssh_password = sftp_creds.get('password')
                ssh_port = sftp_creds.get('port', 22)
            else:
                # Fallback to individual fields
                ssh_host = server_config.get('ssh_host') or server_config.get('host')
                ssh_username = server_config.get('ssh_username') or server_config.get('username')
                ssh_password = server_config.get('ssh_password') or server_config.get('password')
                ssh_port = server_config.get('ssh_port') or server_config.get('port', 22)
            
            if not all([ssh_host, ssh_username, ssh_password]):
                logger.error(f"Server {server_config.get('server_name', 'Unknown')} missing SSH credentials in database")
                return ""
            
            # Get log path from server config
            log_path = server_config.get('log_path', '/home/deadside/79.127.236.1_7020/actual1/Deadside/Saved/Logs/Deadside.log')
            
            logger.info(f"Connecting to {ssh_host}:{ssh_port} as {ssh_username} for {server_config.get('server_name', 'Unknown')}")
            
            # Create connection config for the robust connection manager
            connection_config = {
                'host': ssh_host,
                'port': ssh_port,
                'username': ssh_username,
                'password': ssh_password
            }
            
            # Use the same robust connection manager as killfeed parser
            guild_id = server_config.get('guild_id', 1219706687980568769)
            async with connection_manager.get_connection(guild_id, connection_config) as conn:
                async with conn.start_sftp_client() as sftp:
                    # Read the log file
                    try:
                        async with sftp.open(log_path, 'r') as f:
                            log_data = await f.read()
                            return log_data
                    except Exception as e:
                        logger.error(f"Failed to read log file {log_path}: {e}")
                        return ""
                        
        except Exception as e:
            logger.error(f"Error fetching server logs: {e}")
            return ""