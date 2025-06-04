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
        """Compile regex patterns for connection events"""
        return {
            'player_connect': re.compile(r'Player "([^"]+)" \(id=(\d+)\) has been connected'),
            'player_disconnect': re.compile(r'Player "([^"]+)" \(id=(\d+)\) has been disconnected'),
            'player_login': re.compile(r'Player "([^"]+)" is connected'),
            'player_logout': re.compile(r'Player "([^"]+)" has been disconnected')
        }
    
    def _compile_event_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for game events"""
        return {
            'mission_start': re.compile(r'Mission ([^:]+): (\w+) Event'),
            'helicopter_crash': re.compile(r'Helicopter crash site spawned'),
            'airdrop': re.compile(r'Airdrop.*spawned'),
            'trader': re.compile(r'Trader.*event')
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
                    return {
                        'timestamp': timestamp,
                        'type': 'connection',
                        'event': event_type,
                        'player_name': match.group(1),
                        'player_id': match.group(2) if len(match.groups()) > 1 else None,
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
        
        for line in lines:
            parsed = self.parse_log_line(line)
            if parsed:
                parsed['server_name'] = server_config.get('name', 'Unknown')
                parsed['guild_id'] = server_config.get('guild_id')
                events.append(parsed)
        
        return events
    
    async def update_player_sessions(self, events: List[Dict[str, Any]]) -> bool:
        """Update player session states based on connection events"""
        if not self.bot.db_manager:
            return False
        
        try:
            for event in events:
                if event['type'] != 'connection':
                    continue
                
                player_name = event['player_name']
                guild_id = event['guild_id']
                server_name = event['server_name']
                timestamp = event['timestamp']
                
                if event['event'] in ['player_connect', 'player_login']:
                    # Player connected
                    await self.bot.db_manager.player_sessions.update_one(
                        {
                            'character_name': player_name,
                            'guild_id': guild_id,
                            'server_name': server_name
                        },
                        {
                            '$set': {
                                'state': 'online',
                                'joined_at': timestamp,
                                'last_seen': timestamp
                            }
                        },
                        upsert=True
                    )
                    
                elif event['event'] in ['player_disconnect', 'player_logout']:
                    # Player disconnected
                    await self.bot.db_manager.player_sessions.update_one(
                        {
                            'character_name': player_name,
                            'guild_id': guild_id,
                            'server_name': server_name
                        },
                        {
                            '$set': {
                                'state': 'offline',
                                'last_seen': timestamp
                            }
                        }
                    )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update player sessions: {e}")
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
                        await channel_router.route_embed(
                            embed_type=embed_type,
                            guild_id=event['guild_id'],
                            embed_data=event
                        )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send event embeds: {e}")
            return False
    
    def _map_event_to_embed_type(self, event_type: str) -> Optional[str]:
        """Map event types to embed types"""
        mapping = {
            'mission_start': 'mission',
            'helicopter_crash': 'helicrash',
            'airdrop': 'airdrop',
            'trader': 'trader'
        }
        return mapping.get(event_type)