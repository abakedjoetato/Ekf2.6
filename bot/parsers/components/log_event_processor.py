"""
Log Event Processor
Handles log line parsing and event extraction
"""

import re
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import urllib.parse

logger = logging.getLogger(__name__)

class LogEventProcessor:
    """Processes log lines and extracts structured events"""
    
    def __init__(self):
        self.patterns = self._compile_patterns()
        
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile all regex patterns for log parsing"""
        return {
            # Player patterns with improved name handling
            'player_queue_join': re.compile(
                r'LogNet: Join request: /Game/Maps/world_\d+/World_\d+\?.*?eosid=\|([a-f0-9]+).*?Name=([^&\?]+?)(?:&|\?|$).*?(?:platformid=([^&\?\s]+))?',
                re.IGNORECASE
            ),
            'player_registered': re.compile(
                r'LogOnline: Warning: Player \|([a-f0-9]+) successfully registered!',
                re.IGNORECASE
            ),
            'player_disconnect': re.compile(
                r'LogNet: UChannel::Close: Sending CloseBunch.*?UniqueId: EOS:\|([a-f0-9]+)',
                re.IGNORECASE
            ),
            
            # Server configuration patterns
            'max_player_count': re.compile(r'playersmaxcount\s*=\s*(\d+)', re.IGNORECASE),
            'server_name_pattern': re.compile(r'ServerName\s*=\s*([^,\s]+)', re.IGNORECASE),
            
            # Mission patterns
            'mission_respawn': re.compile(r'LogSFPS: Mission (GA_[A-Za-z0-9_]+) will respawn in (\d+)', re.IGNORECASE),
            'mission_state_change': re.compile(r'LogSFPS: Mission (GA_[A-Za-z0-9_]+) switched to ([A-Z_]+)', re.IGNORECASE),
            'mission_ready': re.compile(r'LogSFPS: Mission (GA_[A-Za-z0-9_]+) switched to READY', re.IGNORECASE),
            'mission_initial': re.compile(r'LogSFPS: Mission (GA_[A-Za-z0-9_]+) switched to INITIAL', re.IGNORECASE),
            'mission_in_progress': re.compile(r'LogSFPS: Mission (GA_[A-Za-z0-9_]+) switched to IN_PROGRESS', re.IGNORECASE),
            'mission_completed': re.compile(r'LogSFPS: Mission (GA_[A-Za-z0-9_]+) switched to COMPLETED', re.IGNORECASE),
            
            # Event patterns
            'airdrop_event': re.compile(r'Event_AirDrop.*spawned.*location.*X=([\d\.-]+).*Y=([\d\.-]+)', re.IGNORECASE),
            'helicrash_event': re.compile(r'LogSFPS:.*(?:helicrash|helicopter.*crash)', re.IGNORECASE),
            'trader_spawn': re.compile(r'LogSFPS:.*trader.*(?:spawn|ready|arrived)', re.IGNORECASE),
            
            # Player activity patterns (for detecting active players)
            'player_activity': re.compile(r'LogNet:.*UChannel.*ActorChannel.*\|([a-f0-9]+)', re.IGNORECASE),
            'player_network_activity': re.compile(r'LogNet:.*Player.*\|([a-f0-9]+)', re.IGNORECASE),
            
            # Timestamp pattern
            'timestamp': re.compile(r'\[(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3})\]')
        }
        
    def parse_timestamp(self, line: str) -> Optional[datetime]:
        """Extract and parse timestamp from log line"""
        try:
            timestamp_match = self.patterns['timestamp'].search(line)
            if timestamp_match:
                timestamp_str = timestamp_match.group(1)
                return datetime.strptime(timestamp_str, '%Y.%m.%d-%H.%M.%S:%f').replace(tzinfo=timezone.utc)
        except (ValueError, AttributeError) as e:
            logger.debug(f"Timestamp parsing failed: {e}")
        return None
        
    def extract_player_name(self, raw_name: str) -> str:
        """Extract and clean player name from URL encoding"""
        try:
            # URL decode the name
            decoded_name = urllib.parse.unquote(raw_name)
            # Replace + with spaces and clean
            clean_name = decoded_name.replace('+', ' ').strip()
            
            # Validate name length
            if len(clean_name) < 1:
                return "Unknown Player"
            if len(clean_name) > 32:
                clean_name = clean_name[:32]
                
            return clean_name
        except Exception as e:
            logger.warning(f"Name extraction failed for '{raw_name}': {e}")
            return "Unknown Player"
            
    def process_queue_event(self, line: str, timestamp: datetime) -> Optional[Dict]:
        """Process player queue join event"""
        queue_match = self.patterns['player_queue_join'].search(line)
        if queue_match:
            groups = queue_match.groups()
            player_id = groups[0]
            raw_name = groups[1] if len(groups) > 1 else "Unknown"
            platform = groups[2] if len(groups) > 2 and groups[2] else "Unknown"
            
            # Extract platform from platformid format
            if platform and ":" in platform:
                platform = platform.split(":")[0]
                
            player_name = self.extract_player_name(raw_name)
            
            return {
                'type': 'queue',
                'player_id': player_id,
                'player_name': player_name,
                'platform': platform,
                'timestamp': timestamp,
                'line': line
            }
        return None
        
    def process_join_event(self, line: str, timestamp: datetime) -> Optional[Dict]:
        """Process player registration (join) event"""
        register_match = self.patterns['player_registered'].search(line)
        if register_match:
            player_id = register_match.group(1)
            return {
                'type': 'join',
                'player_id': player_id,
                'timestamp': timestamp,
                'line': line
            }
        return None
        
    def process_disconnect_event(self, line: str, timestamp: datetime) -> Optional[Dict]:
        """Process player disconnect event"""
        disconnect_match = self.patterns['player_disconnect'].search(line)
        if disconnect_match:
            player_id = disconnect_match.group(1)
            return {
                'type': 'disconnect',
                'player_id': player_id,
                'timestamp': timestamp,
                'line': line
            }
        return None
        
    def process_mission_event(self, line: str, timestamp: datetime) -> Optional[Dict]:
        """Process mission state change events"""
        mission_match = self.patterns['mission_state_change'].search(line)
        if mission_match:
            mission_id = mission_match.group(1)
            state = mission_match.group(2)
            
            return {
                'type': 'mission',
                'mission_id': mission_id,
                'state': state,
                'timestamp': timestamp,
                'line': line
            }
        return None
        
    def process_server_config(self, line: str) -> Optional[Dict]:
        """Process server configuration lines"""
        max_player_match = self.patterns['max_player_count'].search(line)
        if max_player_match:
            return {
                'type': 'config',
                'key': 'max_players',
                'value': int(max_player_match.group(1))
            }
        return None
        
    def process_log_line(self, line: str) -> List[Dict]:
        """Process a single log line and extract all events"""
        events = []
        
        # Parse timestamp
        timestamp = self.parse_timestamp(line)
        if not timestamp:
            timestamp = datetime.now(timezone.utc)
            
        # Try each event type
        event = self.process_queue_event(line, timestamp)
        if event:
            events.append(event)
            
        event = self.process_join_event(line, timestamp)
        if event:
            events.append(event)
            
        event = self.process_disconnect_event(line, timestamp)
        if event:
            events.append(event)
            
        event = self.process_mission_event(line, timestamp)
        if event:
            events.append(event)
            
        event = self.process_server_config(line)
        if event:
            events.append(event)
            
        return events