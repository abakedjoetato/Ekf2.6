"""
Scalable Unified Log Processor
Enterprise-grade unified log processing with connection pooling, file rotation detection, and chronological ordering
"""

import asyncio
import hashlib
import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from bot.utils.connection_pool import connection_manager
from bot.utils.shared_parser_state import get_shared_state_manager, ParserState
from bot.utils.message_rate_limiter import get_rate_limiter
from bot.utils.thread_safe_db_wrapper import ThreadSafeDBWrapper

logger = logging.getLogger(__name__)

@dataclass
class LogEntry:
    """Represents a single log entry with metadata"""
    timestamp: datetime
    server_name: str
    guild_id: int
    raw_line: str
    entry_type: str  # 'join', 'leave', 'kill', 'death', etc.
    player_name: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None
    line_number: int = 0

@dataclass
class ServerFileState:
    """Tracks file state for rotation detection"""
    server_name: str
    guild_id: int
    file_hash: str
    last_position: int
    last_line: int
    last_processed: datetime
    rotation_detected: bool = False

class ScalableUnifiedProcessor:
    """Manages scalable unified log processing for a single guild"""
    
    def __init__(self, guild_id: int, bot=None):
        """Initialize the processor with proper loop management"""
        self.guild_id = guild_id
        self.bot = bot
        self.db_wrapper = None
        self._main_loop = None
        self._cold_start_player_states = {}
        self._voice_channel_updates_deferred = False
        
        # Initialize missing attributes
        self._cold_start_mode = False
        self._hot_start_state_changes = []
        self._player_name_cache = {}
        
        # Set up loop management
        try:
                pass
            except Exception:
                pass
            self._main_loop = asyncio.get_running_loop()
            logger.debug(f"ScalableUnifiedProcessor: Main loop set to {id(self._main_loop)}")
        except RuntimeError:
            logger.warning("ScalableUnifiedProcessor: No running loop detected during init")
        
        # Initialize database wrapper if bot is available
        if bot and hasattr(bot, 'db_manager') and bot.db_manager:
            from bot.utils.thread_safe_db_wrapper import ThreadSafeDBWrapper
            self.db_wrapper = ThreadSafeDBWrapper(bot.db_manager)
            if self._main_loop:
                self.db_wrapper.set_main_loop(self._main_loop)
    def _parse_log_line(self, line: str, server_name: str, line_number: int) -> Optional[LogEntry]:
        """Parse a single log line into a LogEntry"""
        line = line.strip()
        if not line:
            return None
        
        try:
                pass
            except Exception:
                pass
            # Extract timestamp (assuming format: [YYYY.MM.DD-HH.MM.SS:mmm])
            if not line.startswith('['):
                return None
            
            timestamp_end = line.find(']')
            if timestamp_end == -1:
                return None
            
            timestamp_str = line[1:timestamp_end]
            timestamp = self._parse_timestamp(timestamp_str)
            
            if not timestamp:
                return None
            
            # Extract log content
            content = line[timestamp_end + 1:].strip()
            
            # Determine entry type and extract data
            entry_type, player_name, additional_data = self._classify_log_entry(content)
            
            return LogEntry(
                timestamp=timestamp,
                server_name=server_name,
                guild_id=self.guild_id,
                raw_line=line,
                entry_type=entry_type,
                player_name=player_name,
                additional_data=additional_data,
                line_number=line_number
            )
            
        except Exception as e:
            logger.debug(f"Failed to parse log line {line_number}: {e}")
            return None
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp from log entry"""
        formats = [
            '%Y.%m.%d-%H.%M.%S:%f',
            '%Y.%m.%d-%H.%M.%S',
            '%Y-%m-%d %H:%M:%S',
            '%m/%d/%Y %H:%M:%S'
        ]
        
        for fmt in formats:
            try:
                    pass
                except Exception:
                    pass
                # Handle microseconds if present
                if ':' in timestamp_str and '.' in timestamp_str.split(':')[-1]:
                    # Truncate microseconds to 6 digits
                    parts = timestamp_str.split(':')
                    if len(parts[-1]) > 6:
                        parts[-1] = parts[-1][:6]
                    timestamp_str = ':'.join(parts)
                
                return datetime.strptime(timestamp_str, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        
        return None
    
    def _classify_log_entry(self, content: str) -> Tuple[str, Optional[str], Optional[Dict[str, Any]]]:
        """Classify log entry type and extract relevant data for Deadside logs"""
        content_lower = content.lower()
        
        # Parse Deadside log format: [frame_id]LogCategory: [System] Message
        # Example: [977]LogSFPS: [ASFPSGameMode::CanSpawnVehicle] NewVehicles 11 Max 80
        
        # Extract log category and system info
        log_category = None
        system_info = None
        message = content
        
        # Parse frame and log category
        if ']log' in content_lower:
            try:
                    pass
                except Exception:
                    pass
                parts = content.split(']', 1)
                if len(parts) > 1:
                    frame_part = parts[0] + ']'
                    remaining = parts[1]
                    
                    if ':' in remaining:
                        log_parts = remaining.split(':', 1)
                        log_category = log_parts[0].strip()
                        message = log_parts[1].strip()
                        
                        # Extract system info if present
                        if message.startswith('[') and ']' in message:
                            system_end = message.find(']')
                            system_info = message[1:system_end]
                            message = message[system_end + 1:].strip()
            except:
                pass
        
        # Deadside player lifecycle events - using proven regex patterns
        import re
        
        # Player queue/join request
        queue_match = re.search(
            r'LogNet: Join request: /Game/Maps/world_\d+/World_\d+\?.*?eosid=\|([a-f0-9]+).*?Name=([^&\?\s]+).*?(?:platformid=([^&\?\s]+))?',
            content, re.IGNORECASE
        )
        if queue_match:
            eosid, name, platform_id = queue_match.groups()
            return 'queue', eosid, {
                'action': 'queue',
                'player_name': name,
                'platform_id': platform_id,
                'log_category': log_category,
                'system': system_info,
                'message': message
            }
        
        # Player successfully registered (online)
        registered_match = re.search(
            r'LogOnline: Warning: Player \|([a-f0-9]+) successfully registered!',
            content, re.IGNORECASE
        )
        if registered_match:
            eosid = registered_match.group(1)
            return 'join', eosid, {
                'action': 'registered',
                'log_category': log_category,
                'system': system_info,
                'message': message
            }
        
        # Player disconnect
        disconnect_match = re.search(
            r'LogNet: UChannel::Close: Sending CloseBunch.*?UniqueId: EOS:\|([a-f0-9]+)',
            content, re.IGNORECASE
        )
        if disconnect_match:
            eosid = disconnect_match.group(1)
            return 'leave', eosid, {
                'action': 'disconnect',
                'log_category': log_category,
                'system': system_info,
                'message': message
            }
        
        # Deadside kill/death events
        if ('logsfps' in content_lower and 'kill' in content_lower) or ('damage' in content_lower and 'death' in content_lower):
            kill_data = self._parse_deadside_kill_event(content)
            if kill_data:
                return 'kill', None, {
                    **kill_data,
                    'log_category': log_category,
                    'system': system_info
                }
        
        # Mission events - using proven patterns
        mission_respawn_match = re.search(r'LogSFPS: Mission (GA_[A-Za-z0-9_]+) will respawn in (\d+)', content, re.IGNORECASE)
        if mission_respawn_match:
            mission_id, respawn_time = mission_respawn_match.groups()
            return 'mission', None, {
                'mission_id': mission_id,
                'respawn_time': int(respawn_time),
                'state': 'respawn',
                'log_category': log_category,
                'system': system_info,
                'message': message
            }
        
        mission_state_match = re.search(r'LogSFPS: Mission (GA_[A-Za-z0-9_]+) switched to ([A-Z_]+)', content, re.IGNORECASE)
        if mission_state_match:
            mission_id, state = mission_state_match.groups()
            return 'mission', None, {
                'mission_id': mission_id,
                'state': state.lower(),
                'log_category': log_category,
                'system': system_info,
                'message': message
            }
        
        # Kill events - comprehensive PvP kill detection
        kill_patterns = [
            r'LogSFPS.*?Player.*?([a-f0-9]{32}).*?killed.*?Player.*?([a-f0-9]{32}).*?with.*?([A-Za-z0-9_]+)',
            r'LogSFPS.*?([a-f0-9]{32}).*?killed.*?([a-f0-9]{32}).*?using.*?([A-Za-z0-9_]+)',
            r'LogSFPS.*?Player.*?([a-f0-9]{32}).*?eliminated.*?Player.*?([a-f0-9]{32}).*?([A-Za-z0-9_]+)',
            r'LogSFPS.*?([a-f0-9]{32}).*?eliminated.*?([a-f0-9]{32}).*?([A-Za-z0-9_]+)',
            r'LogSFPS.*?Kill.*?([a-f0-9]{32}).*?([a-f0-9]{32}).*?([A-Za-z0-9_]+)',
            r'LogSFPS.*?PvP.*?([a-f0-9]{32}).*?([a-f0-9]{32}).*?([A-Za-z0-9_]+)',
            r'LogSFPS.*?Damage.*?killed.*?([a-f0-9]{32}).*?([a-f0-9]{32}).*?([A-Za-z0-9_]+)'
        ]
        
        for pattern in kill_patterns:
            kill_match = re.search(pattern, content, re.IGNORECASE)
            if kill_match and len(kill_match.groups()) >= 3:
                killer_id, victim_id, weapon = kill_match.groups()[:3]
                return 'kill', None, {
                    'killer_id': killer_id,
                    'victim_id': victim_id,
                    'weapon': weapon,
                    'kill_type': 'pvp',
                    'log_category': log_category,
                    'system': system_info,
                    'message': message
                }
        
        # Death events - player deaths without specific killer
        death_patterns = [
            r'LogSFPS.*?Player.*?([a-f0-9]{32}).*?died.*?([A-Za-z0-9_]+)',
            r'LogSFPS.*?([a-f0-9]{32}).*?death.*?([A-Za-z0-9_]+)',
            r'LogSFPS.*?Player.*?([a-f0-9]{32}).*?eliminated.*?([A-Za-z0-9_]+)',
            r'LogSFPS.*?([a-f0-9]{32}).*?eliminated.*?([A-Za-z0-9_]+)'
        ]
        
        for pattern in death_patterns:
            death_match = re.search(pattern, content, re.IGNORECASE)
            if death_match and len(death_match.groups()) >= 2:
                victim_id, cause = death_match.groups()[:2]
                return 'death', victim_id, {
                    'victim_id': victim_id,
                    'cause': cause,
                    'death_type': 'environmental',
                    'log_category': log_category,
                    'system': system_info,
                    'message': message
                }
        
        # Vehicle events - using proven patterns
        vehicle_spawn_match = re.search(r'LogSFPS: \[ASFPSGameMode::NewVehicle_Add\] Add vehicle (BP_SFPSVehicle_[A-Za-z0-9_]+)', content, re.IGNORECASE)
        if vehicle_spawn_match:
            vehicle_type = vehicle_spawn_match.group(1)
            return 'vehicle', None, {
                'vehicle_type': vehicle_type,
                'action': 'spawn',
                'log_category': log_category,
                'system': system_info,
                'message': message
            }
        
        vehicle_delete_match = re.search(r'LogSFPS: \[ASFPSGameMode::NewVehicle_Del\] Del vehicle (BP_SFPSVehicle_[A-Za-z0-9_]+)', content, re.IGNORECASE)
        if vehicle_delete_match:
            vehicle_type = vehicle_delete_match.group(1)
            return 'vehicle', None, {
                'vehicle_type': vehicle_type,
                'action': 'delete',
                'log_category': log_category,
                'system': system_info,
                'message': message
            }
        
        # Airdrop events - precise regex patterns for SFPS system
        airdrop_patterns = [
            r'LogSFPS.*?airdrop.*?X=([\d\.-]+).*?Y=([\d\.-]+)',
            r'LogSFPS.*?AirDrop.*?X=([\d\.-]+).*?Y=([\d\.-]+)',
            r'LogSFPS.*?air.*?drop.*?X=([\d\.-]+).*?Y=([\d\.-]+)',
            r'LogSFPS.*?Supply.*?Drop.*?X=([\d\.-]+).*?Y=([\d\.-]+)',
            r'LogSFPS.*?Cargo.*?Drop.*?X=([\d\.-]+).*?Y=([\d\.-]+)'
        ]
        
        for pattern in airdrop_patterns:
            airdrop_match = re.search(pattern, content, re.IGNORECASE)
            if airdrop_match:
                if len(airdrop_match.groups()) >= 2:
                    x_coord, y_coord = airdrop_match.groups()[:2]
                    return 'airdrop', None, {
                        'x_coordinate': float(x_coord),
                        'y_coordinate': float(y_coord),
                        'log_category': log_category,
                        'system': system_info,
                        'message': message
                    }
                else:
                    return 'airdrop', None, {
                        'location': 'Unknown',
                        'log_category': log_category,
                        'system': system_info,
                        'message': message
                    }
        
        # Helicrash events - precise SFPS system patterns
        helicrash_patterns = [
            r'LogSFPS.*?helicrash.*?X=([\d\.-]+).*?Y=([\d\.-]+)',
            r'LogSFPS.*?helicopter.*?crash.*?X=([\d\.-]+).*?Y=([\d\.-]+)',
            r'LogSFPS.*?heli.*?crash.*?X=([\d\.-]+).*?Y=([\d\.-]+)',
            r'LogSFPS.*?Helicopter.*?Crash.*?X=([\d\.-]+).*?Y=([\d\.-]+)',
            r'LogSFPS.*?HeliCrash.*?X=([\d\.-]+).*?Y=([\d\.-]+)'
        ]
        
        for pattern in helicrash_patterns:
            helicrash_match = re.search(pattern, content, re.IGNORECASE)
            if helicrash_match:
                if len(helicrash_match.groups()) >= 2:
                    x_coord, y_coord = helicrash_match.groups()[:2]
                    return 'helicrash', None, {
                        'x_coordinate': float(x_coord),
                        'y_coordinate': float(y_coord),
                        'log_category': log_category,
                        'system': system_info,
                        'message': message
                    }
                else:
                    return 'helicrash', None, {
                        'location': 'Unknown',
                        'log_category': log_category,
                        'system': system_info,
                        'message': message
                    }
        
        # Mission events - comprehensive SFPS system patterns for all mission states
        mission_patterns = [
            r'LogSFPS.*?mission.*?status.*?changed.*?to.*?READY.*?at.*?X=([\d\.-]+).*?Y=([\d\.-]+)',
            r'LogSFPS.*?Mission.*?event.*?Status=READY.*?Location=X=([\d\.-]+).*?Y=([\d\.-]+)',
            r'LogSFPS.*?Mission.*?objective.*?activated.*?X=([\d\.-]+).*?Y=([\d\.-]+)',
            r'LogSFPS.*?mission.*?status.*?ready.*?X=([\d\.-]+).*?Y=([\d\.-]+)',
            r'LogSFPS.*?Mission.*?Status.*?READY.*?X=([\d\.-]+).*?Y=([\d\.-]+)',
            r'LogSFPS.*?mission.*?ready.*?X=([\d\.-]+).*?Y=([\d\.-]+)',
            r'LogSFPS.*?Mission.*?READY.*?X=([\d\.-]+).*?Y=([\d\.-]+)',
            r'LogSFPS.*?mission.*?objective.*?X=([\d\.-]+).*?Y=([\d\.-]+)',
            r'LogSFPS.*?Mission.*?objective.*?X=([\d\.-]+).*?Y=([\d\.-]+)'
        ]
        
        for pattern in mission_patterns:
            mission_match = re.search(pattern, content, re.IGNORECASE)
            if mission_match:
                if len(mission_match.groups()) >= 2:
                    x_coord, y_coord = mission_match.groups()[:2]
                    return 'mission', None, {
                        'x_coordinate': float(x_coord),
                        'y_coordinate': float(y_coord),
                        'log_category': log_category,
                        'system': system_info,
                        'message': message
                    }
                else:
                    return 'mission', None, {
                        'location': 'Unknown',
                        'log_category': log_category,
                        'system': system_info,
                        'message': message
                    }
        
        # Trader events - comprehensive SFPS system patterns
        trader_patterns = [
            r'LogSFPS.*?trader.*?X=([\d\.-]+).*?Y=([\d\.-]+)',
            r'LogSFPS.*?Trader.*?X=([\d\.-]+).*?Y=([\d\.-]+)', 
            r'LogSFPS.*?trading.*?post.*?X=([\d\.-]+).*?Y=([\d\.-]+)',
            r'LogSFPS.*?Trade.*?Zone.*?X=([\d\.-]+).*?Y=([\d\.-]+)',
            r'LogSFPS.*?Trading.*?zone.*?active.*?X=([\d\.-]+).*?Y=([\d\.-]+)',
            r'LogSFPS.*?merchant.*?X=([\d\.-]+).*?Y=([\d\.-]+)',
            r'LogSFPS.*?shop.*?X=([\d\.-]+).*?Y=([\d\.-]+)',
            r'LogSFPS.*?trader',
            r'LogSFPS.*?merchant',
            r'LogSFPS.*?shop'
        ]
        
        for pattern in trader_patterns:
            trader_match = re.search(pattern, content, re.IGNORECASE)
            if trader_match:
                if len(trader_match.groups()) >= 2:
                    x_coord, y_coord = trader_match.groups()[:2]
                    return 'trader', None, {
                        'x_coordinate': float(x_coord),
                        'y_coordinate': float(y_coord),
                        'log_category': log_category,
                        'system': system_info,
                        'message': message
                    }
                else:
                    # Generic trader without coordinates
                    return 'trader', None, {
                        'location': 'Unknown',
                        'log_category': log_category,
                        'system': system_info,
                        'message': message
                    }
        
        # Zone events - precise SFPS system patterns
        zone_patterns = [
            r'LogSFPS.*?zone.*?enter.*?X=([\d\.-]+).*?Y=([\d\.-]+)',
            r'LogSFPS.*?zone.*?exit.*?X=([\d\.-]+).*?Y=([\d\.-]+)',
            r'LogSFPS.*?safezone.*?X=([\d\.-]+).*?Y=([\d\.-]+)',
            r'LogSFPS.*?pvp.*?zone.*?X=([\d\.-]+).*?Y=([\d\.-]+)'
        ]
        
        for pattern in zone_patterns:
            zone_match = re.search(pattern, content, re.IGNORECASE)
            if zone_match:
                if len(zone_match.groups()) >= 2:
                    x_coord, y_coord = zone_match.groups()[:2]
                    return 'zone', None, {
                        'x_coordinate': float(x_coord),
                        'y_coordinate': float(y_coord),
                        'log_category': log_category,
                        'system': system_info,
                        'message': message
                    }
        
        # Check for player connection events that might be classified as general
        # Pattern: Player |000240ecc1ba45d59962bc2d34e0177e successfully registered!
        registration_match = re.search(r'Player \|([a-f0-9]{32}) successfully registered', content, re.IGNORECASE)
        if registration_match:
            eosid = registration_match.group(1)
            return 'join', eosid, {
                'log_category': log_category,
                'system': system_info,
                'message': message,
                'eosid': eosid
            }
        
        # Pattern: UChannel::Close: ... UniqueId: EOS:|000240ecc1ba45d59962bc2d34e0177e
        disconnect_match = re.search(r'UniqueId: EOS:\|([a-f0-9]{32})', content, re.IGNORECASE)
        if disconnect_match:
            eosid = disconnect_match.group(1)
            return 'leave', eosid, {
                'log_category': log_category,
                'system': system_info,
                'message': message,
                'eosid': eosid
            }
        
        # Pattern: Join request: ... eosid=|000240ecc1ba45d59962bc2d34e0177e ... Name=PlayerName
        queue_match = re.search(r'Join request:.*?eosid=\|([a-f0-9]{32}).*?Name=([^?]+)', content, re.IGNORECASE)
        if queue_match:
            eosid = queue_match.group(1)
            player_name = queue_match.group(2).strip()
            return 'queue', eosid, {
                'log_category': log_category,
                'system': system_info,
                'message': message,
                'eosid': eosid,
                'player_name': player_name
            }
        
        # No specific patterns matched - return general event for unclassified entries
        return 'general', None, {
            'log_category': log_category,
            'system': system_info,
            'message': message
        }
    
    def _extract_deadside_queue_data(self, content: str) -> Optional[Dict[str, str]]:
        """Extract player data from join request queue log"""
        import re
        # Pattern: Join request: /Game/Maps/world_0/World_0?logintype=eos?login=ExHyper?password=*?eosid=|000240ecc1ba45d59962bc2d34e0177e?ver=1.3.2.24846c?nativeplatform=PS5?platformid=PS5:3566759921101398874?Name=ExHyper?SplitscreenCount=1
        
        patterns = {
            'eosid': r'eosid=\|([a-f0-9]{32})',
            'name': r'Name=([^?]+)',
            'platformid': r'platformid=([^?]+)',
            'nativeplatform': r'nativeplatform=([^?]+)',
            'login': r'login=([^?]+)'
        }
        
        data = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                data[key] = match.group(1).strip()
        
        return data if 'eosid' in data else None
    
    def _extract_eosid_from_registration(self, content: str) -> Optional[str]:
        """Extract EOSID from player registration log"""
        import re
        # Pattern: Player |000240ecc1ba45d59962bc2d34e0177e successfully registered!
        pattern = r'Player \|([a-f0-9]{32}) successfully registered'
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_eosid_from_disconnect(self, content: str) -> Optional[str]:
        """Extract EOSID from disconnect log"""
        import re
        # Pattern: UChannel::Close: ... UniqueId: EOS:|000240ecc1ba45d59962bc2d34e0177e
        pattern = r'UniqueId: EOS:\|([a-f0-9]{32})'
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def _extract_deadside_player_name(self, content: str) -> Optional[str]:
        """Extract player name from Deadside log content"""
        # Deadside specific patterns for player names
        # Look for patterns like: Player "PlayerName" connected
        
        patterns = [
            r'Player "([^"]+)"',
            r'player "([^"]+)"',
            r'User "([^"]+)"',
            r'user "([^"]+)"',
            r'Player ([^\s]+)',
            r'player ([^\s]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _parse_deadside_kill_event(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse Deadside kill event from log content"""
        
        # Deadside kill patterns
        # Look for patterns like: Player "Killer" killed Player "Victim" with WeaponName
        kill_patterns = [
            r'Player "([^"]+)" killed Player "([^"]+)" with (.+)',
            r'player "([^"]+)" killed player "([^"]+)" with (.+)',
            r'([^\s]+) killed ([^\s]+) with (.+)',
        ]
        
        for pattern in kill_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return {
                    'killer': match.group(1).strip(),
                    'victim': match.group(2).strip(),
                    'weapon': match.group(3).strip(),
                    'raw_message': content
                }
        
        return None
    
    def _extract_player_name(self, content: str) -> Optional[str]:
        """Extract player name from log content"""
        # Common patterns for player names in logs
        patterns = [
            r"Player '([^']+)'",
            r"Player \"([^\"]+)\"",
            r"Player ([^\s]+)",
            r"'([^']+)' joined",
            r"'([^']+)' left",
            r"([^\s]+) joined",
            r"([^\s]+) left"
        ]
        
        import re
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _parse_kill_event(self, content: str) -> Dict[str, Any]:
        """Parse kill event details"""
        # Extract killer, victim, weapon from kill log
        # This would need to be adapted based on actual Deadside log format
        return {
            'type': 'kill',
            'raw_content': content
        }
    
    async def _handle_server_restart(self, server_name: str):
        """Handle server restart by resetting all player states"""
        try:
                pass
            except Exception:
                pass
            # This would integrate with existing player session management
            # Reset all players for this server to offline state
            logger.info(f"Handling server restart for {server_name} - resetting player states")
            
            # Thread-safe database operations for cold start
            if self.db_wrapper:
                try:
                        pass
                    except Exception:
                        pass
                    # Use thread-safe wrapper for session reset
                    result = self.db_wrapper.reset_player_sessions(self.guild_id, server_name)
if asyncio.iscoroutine(result):
    await result
                    logger.info(f"Reset all player sessions for {server_name}")
                except Exception as e:
                    logger.warning(f"Could not reset player sessions for {server_name}: {e}")
            else:
                logger.warning(f"No database wrapper available to reset player states for {server_name}")
            
        except Exception as e:
            logger.error(f"Failed to handle server restart for {server_name}: {e}")
    
    async def _process_entries_chronologically(self, entries: List[LogEntry]):
        """Process log entries in chronological order"""
        try:
                pass
            except Exception:
                pass
            logger.debug(f"Processing {len(entries)} entries chronologically")
            
            entry_types = {}
            for entry in entries:
                if self.cancelled:
                    break
                
                # Track entry types for debugging
                entry_type = entry.entry_type
                entry_types[entry_type] = entry_types.get(entry_type, 0) + 1
                
                result = self._process_single_entry(entry)
if asyncio.iscoroutine(result):
    await result
            
            logger.debug(f"Chronological processing complete. Entry types: {entry_types}")
            
            # Commit cold start batch data if needed
            if self._cold_start_mode and self._cold_start_player_states:
                await self._commit_cold_start_player_states()
            
            # Update voice channel after processing all entries
            if self._cold_start_mode or self._hot_start_state_changes:
                await self._update_voice_channel_for_servers()
                
            # Clear hot start state changes after processing
            if not self._cold_start_mode:
                self._hot_start_state_changes.clear()
                
        except Exception as e:
            logger.error(f"Failed to process entries chronologically: {e}")
    
    async def _commit_cold_start_player_states(self):
        """Commit batched player states to database after cold start processing"""
        if not self._cold_start_player_states or not self.bot or not hasattr(self.bot, 'db_manager'):
            return
        
        try:
                pass
            except Exception:
                pass
            batch_count = len(self._cold_start_player_states)
            logger.info(f"🔄 Committing {batch_count} player states from cold start batch processing")
            
            # Use individual upserts with enhanced verification
            committed_count = 0
            failed_count = 0
            
            for player_id, session_data in self._cold_start_player_states.items():
                try:
                        pass
                    except Exception:
                        pass
                    if self.bot and hasattr(self.bot, 'db_manager') and self.bot.db_manager:
                        result = self.bot.db_manager.save_player_session(
                            guild_id=session_data['guild_id'],
                            server_id=session_data.get('server_name', 'default')
if asyncio.iscoroutine(result):
    await result,
                            player_id=player_id,
                            session_data=session_data
                        )
                        committed_count += 1
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Failed to commit player state {player_id[:8]}...: {e}")
            
            logger.info(f"✅ Cold start batch commit: {committed_count}/{batch_count} sessions committed, {failed_count} failed")
            
        except Exception as e:
            logger.error(f"Cold start commit failed: {e}")
            
        # Clear the batch after processing
        self._cold_start_player_states.clear()

    async def _update_voice_channel_for_servers(self):
        """Update voice channel after processing all entries"""
        try:
                pass
            except Exception:
                pass
            if not self.bot or not hasattr(self.bot, 'voice_channel_batcher'):
                return
            
            # Get guild config to find servers using thread-safe wrapper
            if not self.db_wrapper:
                return
                
            guild_config = result = self.db_wrapper.get_guild(self.guild_id)
if asyncio.iscoroutine(result):
    await result
            if not guild_config:
                return
            
            servers = guild_config.get('servers', [])
            for server in servers:
                server_name = server.get('name', 'Unknown Server')
                server_id = str(server.get('_id', ''))
                
                # Get current player count from database using thread-safe wrapper
                try:
                        pass
                    except Exception:
                        pass
                    if self.db_wrapper:
                        player_count = result = self.db_wrapper.get_active_player_count(
                            self.guild_id, server_name
                        )
if asyncio.iscoroutine(result):
    await result
                    else:
                        player_count = 0
                except Exception as e:
                    logger.error(f"Failed to get player count for {server_name}: {e}")
                    player_count = 0
                
                # Get max players from config
                max_players = server.get('max_players', 50)
                
                # Find voice channel ID
                server_channels_config = guild_config.get('server_channels', {})
                server_specific = server_channels_config.get(server_id, {})
                default_server = server_channels_config.get('default', {})
                legacy_channels = guild_config.get('channels', {})
                
                vc_id = (server_specific.get('playercountvc') or 
                        default_server.get('playercountvc') or 
                        legacy_channels.get('playercountvc'))
                
                if vc_id:
                    result = self.bot.voice_channel_batcher.queue_voice_channel_update(
                        int(vc_id)
if asyncio.iscoroutine(result):
    await result, server_name, player_count, max_players
                    )
                    logger.debug(f"Voice channel update queued for {server_name}: {player_count}/{max_players} players")
                else:
                    logger.warning(f"No voice channel configured for server {server_name} (ID: {server_id})")
        
        except Exception as e:
            logger.error(f"Failed to update voice channels: {e}")

    async def _process_single_entry(self, entry: LogEntry):
        """Process a single log entry"""
        try:
                pass
            except Exception:
                pass
            # Check if this is a cold start (rotation detected) to avoid sending embeds
            is_cold_start = getattr(self, '_cold_start_mode', False)
            
            # Handle player lifecycle events (always process for state tracking)
            if entry.entry_type == 'queue' and entry.player_name:
                result = self._handle_player_queue(entry)
if asyncio.iscoroutine(result):
    await result
            elif entry.entry_type == 'join' and entry.player_name:
                result = self._handle_player_join(entry)
if asyncio.iscoroutine(result):
    await result
            elif entry.entry_type == 'leave' and entry.player_name:
                result = self._handle_player_leave(entry)
if asyncio.iscoroutine(result):
    await result
            elif entry.entry_type == 'kill':
                result = self._handle_kill_event(entry)
if asyncio.iscoroutine(result):
    await result
            elif entry.entry_type == 'general':
                # Check general entries for missed player connections
                result = self._handle_general_entry(entry)
if asyncio.iscoroutine(result):
    await result
            
            # Handle embed-worthy events only if NOT in cold start mode
            if not is_cold_start:
                if entry.entry_type == 'mission':
                    result = self._handle_mission_event(entry)
if asyncio.iscoroutine(result):
    await result
                elif entry.entry_type == 'airdrop':
                    result = self._handle_airdrop_event(entry)
if asyncio.iscoroutine(result):
    await result
                elif entry.entry_type == 'helicrash':
                    result = self._handle_helicrash_event(entry)
if asyncio.iscoroutine(result):
    await result
                elif entry.entry_type == 'trader':
                    result = self._handle_trader_event(entry)
if asyncio.iscoroutine(result):
    await result
            
            # Note: vehicle and spawn events are classified but not processed for embeds
            
        except Exception as e:
            logger.error(f"Failed to process log entry: {e}")
    
    async def _handle_player_queue(self, entry: LogEntry):
        """Handle player queue event (join request)"""
        try:
                pass
            except Exception:
                pass
            if not entry.player_name:
                return
            
            eosid = entry.player_name  # EOSID is stored in player_name field
            additional_data = entry.additional_data or {}
            player_name = additional_data.get('player_name', f'Player{eosid[:8]}')
            
            # Store player name in cache for when they register
            self._player_name_cache[eosid] = player_name
            
            logger.debug(f"Player {player_name} ({eosid}) queued for {entry.server_name}")
            
        except Exception as e:
            logger.error(f"Failed to handle player queue: {e}")

    async def _handle_player_join(self, entry: LogEntry):
        """Handle player join event (successfully registered)"""
        try:
                pass
            except Exception:
                pass
            if not entry.player_name:
                return
            
            eosid = entry.player_name  # EOSID is stored in player_name field
            
            if self.bot and hasattr(self.bot, 'db_manager') and self.bot.db_manager:
                try:
                        pass
                    except Exception:
                        pass
                    # During cold start, store in memory for batch processing
                    if self._cold_start_mode:
                        # Get player name from cache if available
                        character_name = self._player_name_cache.get(eosid, f'Player{eosid[:8]}')
                        
                        # Store player state in memory for batch write later
                        self._cold_start_player_states[eosid] = {
                            'guild_id': self.guild_id,
                            'player_id': eosid,
                            'state': 'online',
                            'server_name': entry.server_name,
                            'last_updated': entry.timestamp,
                            'joined_at': entry.timestamp.isoformat(),
                            'platform': 'Unknown',
                            'character_name': character_name
                        }
                        logger.debug(f"Player {character_name} ({eosid[:8]}...) queued for batch update (online on {entry.server_name})")
                        state_changed = True
                    else:
                        # Hot start processing - update database immediately and track for voice updates
                        try:
                                pass
                            except Exception:
                                pass
                            # Get player name from cache if available
                            character_name = self._player_name_cache.get(eosid, f'Player{eosid[:8]}')
                            
                            # Update player session using thread-safe wrapper
                            result = None
                            if self.db_wrapper:
                                try:
                                        pass
                                    except Exception:
                                        pass
                                    result = result = self.db_wrapper.update_player_session(
                                    {"guild_id": self.guild_id, "player_id": eosid},
                                    {
                                        "$set": {
                                            "state": "online",
                                            "server_name": entry.server_name,
                                            "last_updated": entry.timestamp,
                                            "joined_at": entry.timestamp.isoformat()
if asyncio.iscoroutine(result):
    await result,
                                            "platform": "Unknown",
                                            "character_name": character_name
                                        }
                                    },
                                    upsert=True
                                    )
                                except Exception as db_error:
                                    logger.error(f"Thread-safe database operation failed: {db_error}")
                                    result = None
                            
                            state_changed = (hasattr(result, "upserted_id") and result.upserted_id is not None) or (hasattr(result, "modified_count") and result.modified_count > 0) if result else False
                            
                            # Track servers with state changes for voice channel updates
                            if locals().get("state_changed", False):
                                self._hot_start_state_changes.append(entry.server_name)
                                logger.debug(f"Hot start: Player {character_name} ({eosid[:8]}...) joined {entry.server_name}")
                            else:
                                logger.debug(f"No state change for {character_name} (already online)")
                        except Exception as db_error:
                            logger.error(f"Database update failed for {eosid[:8]}...: {db_error}")
                            import traceback
                            logger.error(f"Full traceback: {traceback.format_exc()}")
                            state_changed = False
                    
                    # Only send connection embed if state actually changed (offline -> online)
                    if locals().get("state_changed", False) and not self._cold_start_mode:
                        # Use character name from cache if available, fallback to database
                        character_name = self._player_name_cache.get(eosid, f'Player{eosid[:8]}')
                        display_name = character_name
                        
                        logger.debug(f"Player connection: {display_name} joined {entry.server_name}")
                        
                        # Create connection embed using proper EmbedFactory theming
                        if hasattr(self.bot, 'embed_factory'):
                            embed_data = {
                                'player_name': display_name,
                                'event_type': 'join',
                                'server_name': entry.server_name,
                                'timestamp': entry.timestamp,
                                'platform': 'Unknown'
                            }
                            
                            try:
                                    pass
                                except Exception:
                                    pass
                                embed, file_attachment = result = self.bot.embed_factory.build('connection', embed_data)
if asyncio.iscoroutine(result):
    await result
                                
                                if embed and hasattr(self.bot, 'channel_router'):
                                    result = self.bot.channel_router.send_embed_to_channel(
                                        guild_id=self.guild_id,
                                        server_id=entry.server_name,
                                        channel_type='connections',
                                        embed=embed,
                                        file=file_attachment
                                    )
if asyncio.iscoroutine(result):
    await result
                                    logger.info(f"Sent connection embed for {display_name} joining {entry.server_name}")
                            except Exception as embed_error:
                                logger.error(f"Failed to create connection embed: {embed_error}")
                    elif not locals().get("state_changed", False):
                        logger.debug(f"Player {eosid[:8]}... already online - no embed sent")
                
                except Exception as e:
                    logger.error(f"Database error for join event: {e}")
                    
            else:
                logger.warning(f"No database manager available for join event: {eosid}")
                
        except Exception as e:
            logger.error(f"Failed to handle player join for {entry.player_name}: {e}")
    
    async def _handle_player_leave(self, entry: LogEntry):
        """Handle player leave event (connection closed)"""
        try:
                pass
            except Exception:
                pass
            if not entry.player_name:
                return
            
            eosid = entry.player_name  # EOSID is stored in player_name field
            
            if self.bot and hasattr(self.bot, 'db_manager') and self.bot.db_manager:
                try:
                        pass
                    except Exception:
                        pass
                    # During cold start, remove from memory state
                    if self._cold_start_mode:
                        if eosid in self._cold_start_player_states:
                            del self._cold_start_player_states[eosid]
                            logger.debug(f"Player {eosid[:8]}... removed from batch update (disconnected from {entry.server_name})")
                        state_changed = True
                    else:
                        # Hot start processing - update database using thread-safe wrapper
                        if self.db_wrapper:
                            try:
                                    pass
                                except Exception:
                                    pass
                                result = result = self.db_wrapper.update_player_session(
                                    {"guild_id": self.guild_id, "player_id": eosid, "state": "online"},
                                    {
                                        "$set": {
                                            "state": "offline",
                                            "last_updated": entry.timestamp,
                                            "disconnected_at": entry.timestamp.isoformat()
if asyncio.iscoroutine(result):
    await result
                                        }
                                    }
                                )
                                state_changed = result.modified_count > 0 if result else False
                            except Exception as e:
                                logger.error(f"Failed to update player session for disconnect: {e}")
                                state_changed = False
                        
                        # Track servers with state changes for voice channel updates
                        if locals().get("state_changed", False):
                            self._hot_start_state_changes.append(entry.server_name)
                            logger.debug(f"Hot start: Player {eosid[:8]}... left {entry.server_name}")
                    
                    # Only send connection embed if state actually changed (online -> offline)
                    if locals().get("state_changed", False) and not self._cold_start_mode:
                        # Use character name from cache if available, fallback to database
                        character_name = self._player_name_cache.get(eosid, f'Player{eosid[:8]}')
                        display_name = character_name
                        
                        logger.debug(f"Player connection: {display_name} left {entry.server_name}")
                        
                        # Create connection embed using proper EmbedFactory theming
                        if hasattr(self.bot, 'embed_factory'):
                            embed_data = {
                                'player_name': display_name,
                                'event_type': 'leave',
                                'server_name': entry.server_name,
                                'timestamp': entry.timestamp,
                                'platform': 'Unknown'
                            }
                            
                            try:
                                    pass
                                except Exception:
                                    pass
                                embed, file_attachment = result = self.bot.embed_factory.build('connection', embed_data)
if asyncio.iscoroutine(result):
    await result
                                
                                if embed and hasattr(self.bot, 'channel_router'):
                                    result = self.bot.channel_router.send_embed_to_channel(
                                        guild_id=self.guild_id,
                                        server_id=entry.server_name,
                                        channel_type='connections',
                                        embed=embed,
                                        file=file_attachment
                                    )
if asyncio.iscoroutine(result):
    await result
                                    logger.info(f"Sent connection embed for {display_name} leaving {entry.server_name}")
                            except Exception as embed_error:
                                logger.error(f"Failed to create connection embed: {embed_error}")
                    elif not locals().get("state_changed", False):
                        logger.debug(f"Player {eosid[:8]}... already offline - no embed sent")
                
                except Exception as e:
                    logger.error(f"Database error for leave event: {e}")
                    
            else:
                logger.warning(f"No database manager available for leave event: {eosid}")
                
        except Exception as e:
            logger.error(f"Failed to handle player leave for {entry.player_name}: {e}")

    async def _handle_general_entry(self, entry: LogEntry):
        """Handle general entries that might contain player connection events"""
        try:
                pass
            except Exception:
                pass
            if not entry.additional_data:
                return
            
            message = entry.additional_data.get('message', '')
            
            # Check for player registration in general entries
            if 'successfully registered' in message.lower():
                # Extract EOSID from message
                import re
                registration_match = re.search(r'Player \|([a-f0-9]{32}) successfully registered', message, re.IGNORECASE)
                if registration_match:
                    eosid = registration_match.group(1)
                    
                    # Create synthetic join entry
                    join_entry = LogEntry(
                        timestamp=entry.timestamp,
                        server_name=entry.server_name,
                        entry_type='join',
                        player_name=eosid,
                        guild_id=entry.guild_id,
                        raw_line=entry.raw_line,
                        additional_data={'eosid': eosid, 'source': 'general_registration'}
                    )
                    
                    result = self._handle_player_join(join_entry)
if asyncio.iscoroutine(result):
    await result
                    logger.info(f"Extracted player join from general entry: {eosid[:8]}...")
            
            # Check for player disconnection in general entries
            elif 'uchannel::close' in message.lower() or 'uniqueid: eos:' in message.lower():
                import re
                disconnect_match = re.search(r'UniqueId: EOS:\|([a-f0-9]{32})', message, re.IGNORECASE)
                if disconnect_match:
                    eosid = disconnect_match.group(1)
                    
                    # Create synthetic leave entry
                    leave_entry = LogEntry(
                        timestamp=entry.timestamp,
                        server_name=entry.server_name,
                        entry_type='leave',
                        player_name=eosid,
                        guild_id=entry.guild_id,
                        raw_line=entry.raw_line,
                        additional_data={'eosid': eosid, 'source': 'general_disconnect'}
                    )
                    
                    result = self._handle_player_leave(leave_entry)
if asyncio.iscoroutine(result):
    await result
                    logger.info(f"Extracted player leave from general entry: {eosid[:8]}...")
            
            # Check for join requests in general entries
            elif 'join request:' in message.lower():
                import re
                queue_match = re.search(r'Join request:.*?eosid=\|([a-f0-9]{32}).*?Name=([^?]+)', message, re.IGNORECASE)
                if queue_match:
                    eosid = queue_match.group(1)
                    player_name = queue_match.group(2).strip()
                    
                    # Create synthetic queue entry
                    queue_entry = LogEntry(
                        timestamp=entry.timestamp,
                        server_name=entry.server_name,
                        entry_type='queue',
                        player_name=eosid,
                        guild_id=entry.guild_id,
                        raw_line=entry.raw_line,
                        additional_data={'eosid': eosid, 'player_name': player_name, 'source': 'general_queue'}
                    )
                    
                    result = self._handle_player_queue(queue_entry)
if asyncio.iscoroutine(result):
    await result
                    logger.info(f"Extracted player queue from general entry: {player_name} ({eosid[:8]}...)")
                    
        except Exception as e:
            logger.error(f"Failed to handle general entry: {e}")
    
    async def _handle_kill_event(self, entry: LogEntry):
        """Handle kill event with proper kill tracking"""
        try:
                pass
            except Exception:
                pass
            kill_data = entry.additional_data
            if not kill_data or 'killer' not in kill_data or 'victim' not in kill_data:
                return
            
            killer = kill_data['killer']
            victim = kill_data['victim']
            weapon = kill_data.get('weapon', 'Unknown')
            
            logger.info(f"Kill event: {killer} killed {victim} with {weapon} on {entry.server_name}")
            
            if self.bot and hasattr(self.bot, 'db_manager') and self.bot.db_manager:
                # Record the kill
                kill_event_data = {
                    "killer": killer,
                    "victim": victim,
                    "weapon": weapon,
                    "timestamp": entry.timestamp,
                    "distance": kill_data.get('distance', 0),
                    "raw_line": entry.raw_line
                }
                result = self.bot.db_manager.add_kill_event(
                    guild_id=self.guild_id,
                    server_id=entry.server_name,
                    kill_data=kill_event_data
                )
if asyncio.iscoroutine(result):
    await result
                logger.debug(f"Recorded kill: {killer} -> {victim}")
            else:
                logger.warning(f"No database manager available to record kill: {killer} -> {victim}")
            
        except Exception as e:
            logger.error(f"Failed to handle kill event: {e}")
    
    async def _handle_mission_event(self, entry: LogEntry):
        """Handle mission events - only send embeds for READY status"""
        try:
                pass
            except Exception:
                pass
            # Skip embed creation during cold start to prevent spam
            if self._cold_start_mode:
                logger.debug(f"Skipping mission embed during cold start for {entry.server_name}")
                return
            
            additional_data = entry.additional_data or {}
            mission_id = additional_data.get('mission_id')
            state = additional_data.get('state')
            
            if not mission_id or state != 'ready':
                return  # Only process READY missions for embeds
            
            logger.info(f"Mission {mission_id} is ready on {entry.server_name}")
            
            # Create mission embed using proper EmbedFactory with theming
            if self.bot and hasattr(self.bot, 'embed_factory'):
                embed_data = {
                    'mission_id': mission_id,
                    'state': 'READY',
                    'server_name': entry.server_name,
                    'timestamp': entry.timestamp
                }
                
                try:
                        pass
                    except Exception:
                        pass
                    embed, file_attachment = result = self.bot.embed_factory.build('mission', embed_data)
if asyncio.iscoroutine(result):
    await result
                    
                    if embed and hasattr(self.bot, 'channel_router'):
                        # Send to events channel with server-specific routing and proper theming
                        result = self.bot.channel_router.send_embed_to_channel(
                            guild_id=self.guild_id,
                            server_id=entry.server_name,
                            channel_type='events',
                            embed=embed,
                            file=file_attachment
                        )
if asyncio.iscoroutine(result):
    await result
                        logger.info(f"Sent mission ready embed for {mission_id} on {entry.server_name}")
                except Exception as embed_error:
                    logger.error(f"Failed to create mission embed: {embed_error}")
                    # Fallback to basic embed
                    mission_name = self.bot.embed_factory.normalize_mission_name(mission_id)
                    embed = self.bot.embed_factory.create_mission_embed(
                        title="🎯 Mission Ready",
                        description=f"**{mission_name}** is now available for deployment",
                        mission_id=mission_id,
                        level=self.bot.embed_factory.get_mission_level(mission_id),
                        state='READY',
                        respawn_time=None
                    )
                    
                    if embed and hasattr(self.bot, 'channel_router'):
                        result = self.bot.channel_router.send_embed_to_channel(
                            guild_id=self.guild_id,
                            server_id=entry.server_name,
                            channel_type='events',
                            embed=embed
                        )
if asyncio.iscoroutine(result):
    await result
                        logger.info(f"Sent fallback mission embed for {mission_id} on {entry.server_name}")
            
        except Exception as e:
            logger.error(f"Failed to handle mission event: {e}")
    
    async def _handle_airdrop_event(self, entry: LogEntry):
        """Handle airdrop events using proper EmbedFactory theming"""
        try:
                pass
            except Exception:
                pass
            # Skip embed creation during cold start to prevent spam
            if self._cold_start_mode:
                logger.debug(f"Skipping airdrop embed during cold start for {entry.server_name}")
                return
            
            additional_data = entry.additional_data or {}
            x_coord = additional_data.get('x_coordinate')
            y_coord = additional_data.get('y_coordinate')
            location = additional_data.get('location', 'Unknown')
            
            # Handle both coordinate and generic location data
            if x_coord is not None and y_coord is not None:
                location = f"({x_coord}, {y_coord})"
            
            logger.info(f"Airdrop event at {location} on {entry.server_name}")
            
            # Create airdrop embed using proper EmbedFactory theming
            if self.bot and hasattr(self.bot, 'embed_factory'):
                embed_data = {
                    'state': 'flying',
                    'location': location,
                    'server_name': entry.server_name,
                    'timestamp': entry.timestamp
                }
                
                try:
                        pass
                    except Exception:
                        pass
                    embed, file_attachment = result = self.bot.embed_factory.build('airdrop', embed_data)
if asyncio.iscoroutine(result):
    await result
                    
                    if embed and hasattr(self.bot, 'channel_router'):
                        result = self.bot.channel_router.send_embed_to_channel(
                            guild_id=self.guild_id,
                            server_id=entry.server_name,
                            channel_type='airdrops',
                            embed=embed,
                            file=file_attachment
                        )
if asyncio.iscoroutine(result):
    await result
                        logger.info(f"Sent airdrop embed for {entry.server_name} at {location}")
                except Exception as embed_error:
                    logger.error(f"Failed to create airdrop embed: {embed_error}")
            
        except Exception as e:
            logger.error(f"Failed to handle airdrop event: {e}")
    
    async def _handle_helicrash_event(self, entry: LogEntry):
        """Handle helicrash events using proper EmbedFactory theming"""
        try:
                pass
            except Exception:
                pass
            # Skip embed creation during cold start to prevent spam
            if self._cold_start_mode:
                logger.debug(f"Skipping helicrash embed during cold start for {entry.server_name}")
                return
            
            additional_data = entry.additional_data or {}
            x_coord = additional_data.get('x_coordinate')
            y_coord = additional_data.get('y_coordinate')
            location = additional_data.get('location', 'Unknown')
            
            # Handle both coordinate and generic location data
            if x_coord is not None and y_coord is not None:
                location = f"({x_coord}, {y_coord})"
            
            logger.info(f"Helicrash event at {location} on {entry.server_name}")
            
            # Create helicrash embed using proper EmbedFactory theming
            if self.bot and hasattr(self.bot, 'embed_factory'):
                embed_data = {
                    'location': location,
                    'server_name': entry.server_name,
                    'timestamp': entry.timestamp
                }
                
                try:
                        pass
                    except Exception:
                        pass
                    embed, file_attachment = result = self.bot.embed_factory.build('helicrash', embed_data)
if asyncio.iscoroutine(result):
    await result
                    
                    if embed and hasattr(self.bot, 'channel_router'):
                        result = self.bot.channel_router.send_embed_to_channel(
                            guild_id=self.guild_id,
                            server_id=entry.server_name,
                            channel_type='helicrashes',
                            embed=embed,
                            file=file_attachment
                        )
if asyncio.iscoroutine(result):
    await result
                        logger.info(f"Sent helicrash embed for {entry.server_name} at {location}")
                except Exception as embed_error:
                    logger.error(f"Failed to create helicrash embed: {embed_error}")
            
        except Exception as e:
            logger.error(f"Failed to handle helicrash event: {e}")
    
    async def _handle_trader_event(self, entry: LogEntry):
        """Handle trader events using proper EmbedFactory theming with deduplication"""
        try:
                pass
            except Exception:
                pass
            # Skip embed creation during cold start to prevent spam
            if self._cold_start_mode:
                logger.debug(f"Skipping trader embed during cold start for {entry.server_name}")
                return
            
            additional_data = entry.additional_data or {}
            x_coord = additional_data.get('x_coordinate')
            y_coord = additional_data.get('y_coordinate')
            location = additional_data.get('location', 'Unknown')
            
            # Handle both coordinate and generic location data
            if x_coord is not None and y_coord is not None:
                location = f"({x_coord}, {y_coord})"
            
            # Deduplication: Create unique key for this trader event
            trader_key = f"trader_{entry.server_name}_{location}_{entry.timestamp.hour}_{entry.timestamp.minute}"
            
            # Check if we've already processed this trader event recently (within same minute)
            if not hasattr(self, '_processed_trader_events'):
                self._processed_trader_events = set()
            
            if trader_key in self._processed_trader_events:
                logger.debug(f"Skipping duplicate trader event at {location} on {entry.server_name}")
                return
            
            # Add to processed events
            self._processed_trader_events.add(trader_key)
            
            # Clean up old events (keep only last 100)
            if len(self._processed_trader_events) > 100:
                old_events = list(self._processed_trader_events)[:50]
                for old_event in old_events:
                    self._processed_trader_events.discard(old_event)
            
            logger.info(f"Trader event at {location} on {entry.server_name}")
            
            # Create trader embed using proper EmbedFactory theming
            if self.bot and hasattr(self.bot, 'embed_factory'):
                embed_data = {
                    'location': location,
                    'server_name': entry.server_name,
                    'timestamp': entry.timestamp
                }
                
                try:
                        pass
                    except Exception:
                        pass
                    embed, file_attachment = result = self.bot.embed_factory.build('trader', embed_data)
if asyncio.iscoroutine(result):
    await result
                    
                    if embed and hasattr(self.bot, 'channel_router'):
                        result = self.bot.channel_router.send_embed_to_channel(
                            guild_id=self.guild_id,
                            server_id=entry.server_name,
                            channel_type='traders',
                            embed=embed,
                            file=file_attachment
                        )
if asyncio.iscoroutine(result):
    await result
                        logger.info(f"Sent trader embed for {entry.server_name} at {location}")
                except Exception as embed_error:
                    logger.error(f"Failed to create trader embed: {embed_error}")
            
        except Exception as e:
            logger.error(f"Failed to handle trader event: {e}")
    
    async def process_guild_servers(self, server_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process all servers for a specific guild"""
        processed_count = 0
        rotated_count = 0
        errors = []
        
        try:
                pass
            except Exception:
                pass
            for server_config in server_configs:
                try:
                        pass
                    except Exception:
                        pass
                    # Process individual server (simplified implementation)
                    server_name = server_config.get('server_name', 'Unknown')
                    processed_count += 1
                    
                    # Check for file rotation (simplified)
                    if server_config.get('rotation_detected', False):
                        rotated_count += 1
                        
                except Exception as server_error:
                    errors.append(f"Server {server_config.get('server_name', 'Unknown')}: {server_error}")
                    logger.error(f"Error processing server {server_config.get('server_name', 'Unknown')}: {server_error}")
            
            return {
                'success': True,
                'processed_servers': processed_count,
                'rotated_servers': rotated_count,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Failed to process guild {self.guild_id} servers: {e}")
            return {
                'success': False,
                'error': str(e),
                'processed_servers': processed_count,
                'rotated_servers': rotated_count
            }

    def cancel(self):
        """Cancel the processing"""
        self.cancelled = True

class MultiGuildUnifiedProcessor:
    """Manages unified processing across multiple guilds"""
    
    def __init__(self, bot=None):
        self.processors: Dict[int, ScalableUnifiedProcessor] = {}
        self.bot = bot
    
    async def process_all_guilds(self, guild_configs: Dict[int, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Process unified logs for all guilds with staggered processing for resource management"""
        # Group servers into staggered batches to reduce resource pressure
        server_groups = []
        current_group = []
        servers_per_group = 15  # Process up to 15 servers simultaneously
        
        for guild_id, server_configs in guild_configs.items():
            for server_config in server_configs:
                current_group.append((guild_id, server_config))
                if len(current_group) >= servers_per_group:
                    server_groups.append(current_group)
                    current_group = []
        
        if current_group:  # Add remaining servers
            server_groups.append(current_group)
        
        total_processed = 0
        total_rotations = 0
        successful_guilds = set()
        all_results = {}
        
        # Process server groups with 30-second stagger
        for group_index, server_group in enumerate(server_groups):
            if group_index > 0:
                logger.info(f"Staggering processing: waiting 30 seconds before processing group {group_index + 1}/{len(server_groups)}")
                result = asyncio.sleep(30)
if asyncio.iscoroutine(result):
    await result
            
            logger.debug(f"Processing server group {group_index + 1}/{len(server_groups)} with {len(server_group)} servers")
            
            # Group servers by guild for this batch
            guild_batch = {}
            for guild_id, server_config in server_group:
                if guild_id not in guild_batch:
                    guild_batch[guild_id] = []
                guild_batch[guild_id].append(server_config)
            
            # Process this batch of guilds
            batch_tasks = []
            batch_processors = {}
            
            for guild_id, batch_server_configs in guild_batch.items():
                processor = ScalableUnifiedProcessor(guild_id, self.bot)
                batch_processors[guild_id] = processor
                
                task = processor.process_guild_servers(batch_server_configs)
                batch_tasks.append((guild_id, task))
            
            # Execute batch
            batch_results = result = asyncio.gather(
                *[task for _, task in batch_tasks], 
                return_exceptions=True
            )
if asyncio.iscoroutine(result):
    await result
            
            # Collect batch results
            for (guild_id, _), result in zip(batch_tasks, batch_results):
                if isinstance(result, dict) and result.get('success'):
                    successful_guilds.add(guild_id)
                    total_processed += result.get('processed_servers', 0)
                    total_rotations += result.get('rotated_servers', 0)
                
                all_results[f"guild_{guild_id}_batch_{group_index}"] = result
        
        return {
            'success': True,
            'total_guilds': len(guild_configs),
            'successful_guilds': len(successful_guilds),
            'total_servers': sum(len(configs) for configs in guild_configs.values()),
            'processed_servers': total_processed,
            'rotated_servers': total_rotations,
            'guild_results': all_results,
            'processing_groups': len(server_groups)
        }