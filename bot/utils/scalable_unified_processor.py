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
                    embed_data = {
                        'type': 'connection',
                        'event': 'player_connected',
                        'player_name': change['player_name'],
                        'eos_id': change['eos_id'],
                        'timestamp': change['timestamp'],
                        'guild_id': change['guild_id'],
                        'server_id': change['server_id']
                    }
                    await channel_router.send_embed_to_channel(
                        guild_id=change['guild_id'],
                        server_id=change['server_id'],
                        channel_type='killfeed',
                        embed=embed_data
                    )
                
                elif change['old_state'] == 'online' and change['new_state'] == 'offline':
                    # Player disconnected (online -> offline)
                    embed_data = {
                        'type': 'connection',
                        'event': 'player_disconnected',
                        'player_name': change['player_name'],
                        'eos_id': change['eos_id'],
                        'timestamp': change['timestamp'],
                        'guild_id': change['guild_id'],
                        'server_id': change['server_id']
                    }
                    await channel_router.send_embed_to_channel(
                        guild_id=change['guild_id'],
                        server_id=change['server_id'],
                        channel_type='killfeed',
                        embed=embed_data
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