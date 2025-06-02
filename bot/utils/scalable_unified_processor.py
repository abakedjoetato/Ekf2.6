"""
Scalable Unified Log Processor
Enterprise-grade unified log processing with connection pooling, file rotation detection, and chronological ordering
"""

import asyncio
import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from bot.utils.connection_pool import connection_manager
from bot.utils.shared_parser_state import get_shared_state_manager, ParserState

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
    
    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        self.server_states: Dict[str, ServerFileState] = {}
        self.cancelled = False
        self.state_manager = get_shared_state_manager()
        
    async def process_guild_servers(self, server_configs: List[Dict[str, Any]], 
                                  progress_callback=None) -> Dict[str, Any]:
        """Process all servers for unified logging with file rotation detection"""
        results = {
            'success': False,
            'total_servers': len(server_configs),
            'processed_servers': 0,
            'rotated_servers': 0,
            'entries_processed': 0,
            'error': None
        }
        
        try:
            # Filter available servers (not under historical processing)
            if self.state_manager:
                available_servers = await self.state_manager.get_available_servers_for_killfeed(server_configs)
            else:
                available_servers = server_configs
            
            if not available_servers:
                results['error'] = 'No available servers for processing'
                return results
            
            # Phase 1: File discovery and rotation detection
            file_states = await self._discover_and_check_rotation(available_servers)
            
            # Phase 2: Process servers with file changes
            all_entries = []
            for server_config in available_servers:
                server_name = server_config.get('name', server_config.get('server_name', 'default'))
                
                if server_name in file_states:
                    file_state = file_states[server_name]
                    entries = await self._process_server_deadside_log(server_config, file_state)
                    all_entries.extend(entries)
                    
                    if file_state.rotation_detected:
                        results['rotated_servers'] += 1
                    
                    results['processed_servers'] += 1
            
            # Phase 3: Chronological processing of all entries
            if all_entries:
                # Sort by timestamp for chronological processing
                all_entries.sort(key=lambda x: x.timestamp)
                
                # Process entries in chronological order
                await self._process_entries_chronologically(all_entries)
                results['entries_processed'] = len(all_entries)
            
            results['success'] = True
            
        except Exception as e:
            logger.error(f"Unified processing failed for guild {self.guild_id}: {e}")
            results['error'] = str(e)
        
        return results
    
    async def _discover_and_check_rotation(self, server_configs: List[Dict[str, Any]]) -> Dict[str, ServerFileState]:
        """Discover Deadside.log files and check for rotation"""
        file_states = {}
        
        # Process servers concurrently for efficiency
        tasks = []
        for server_config in server_configs:
            task = self._check_server_file_rotation(server_config)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, ServerFileState):
                file_states[result.server_name] = result
            elif isinstance(result, Exception):
                server_name = server_configs[i].get('name', 'unknown')
                logger.error(f"Failed to check rotation for {server_name}: {result}")
        
        return file_states
    
    async def _check_server_file_rotation(self, server_config: Dict[str, Any]) -> Optional[ServerFileState]:
        """Check if Deadside.log has rotated by examining first line hash"""
        server_name = server_config.get('name', server_config.get('server_name', 'default'))
        
        try:
            # Use direct SFTP connection instead of connection pool to avoid SSH attribute issues
            import asyncssh
            
            conn = await asyncssh.connect(
                server_config.get('host', 'localhost'),
                port=server_config.get('port', 22),
                username=server_config.get('username', 'root'),
                password=server_config.get('password'),
                known_hosts=None,
                kex_algs=['diffie-hellman-group1-sha1', 'diffie-hellman-group14-sha1', 'diffie-hellman-group14-sha256', 'diffie-hellman-group16-sha512', 'ecdh-sha2-nistp256', 'ecdh-sha2-nistp384', 'ecdh-sha2-nistp521'],
                encryption_algs=['aes128-ctr', 'aes192-ctr', 'aes256-ctr', 'aes128-cbc', 'aes192-cbc', 'aes256-cbc'],
                mac_algs=['hmac-sha1', 'hmac-sha2-256', 'hmac-sha2-512'],
                compression_algs=['none'],
                server_host_key_algs=['ssh-rsa', 'rsa-sha2-256', 'rsa-sha2-512', 'ssh-dss']
            )
            
            try:
                sftp = await conn.start_sftp_client()
                host = server_config.get('host', 'unknown')
                server_id = server_config.get('server_id', 'unknown')
                deadside_log_path = f"./{host}_{server_id}/Logs/Deadside.log"
                
                # Read first line for hash calculation
                async with sftp.open(deadside_log_path, 'rb') as file:
                    first_line_bytes = await file.read(1024)  # Read first 1024 bytes
                    first_line = first_line_bytes.decode('utf-8', errors='ignore').split('\n')[0].strip()
                    
                    # Calculate hash of first line
                    current_hash = hashlib.md5(first_line.encode()).hexdigest()
                    
                    # Get stored state
                    stored_state = await self.state_manager.get_parser_state(self.guild_id, server_name) if self.state_manager else None
                    
                    rotation_detected = False
                    last_position = 0
                    last_line = 0
                    
                    if stored_state and stored_state.file_timestamp:  # Using file_timestamp to store hash
                        if stored_state.file_timestamp != current_hash:
                            rotation_detected = True
                            logger.info(f"File rotation detected for {server_name} - resetting state")
                        else:
                            last_position = stored_state.last_byte_position
                            last_line = stored_state.last_line
                    else:
                        # First time processing or no stored state
                        rotation_detected = True
                    
                    return ServerFileState(
                        server_name=server_name,
                        guild_id=self.guild_id,
                        file_hash=current_hash,
                        last_position=last_position,
                        last_line=last_line,
                        last_processed=datetime.now(timezone.utc),
                        rotation_detected=rotation_detected
                    )
            finally:
                conn.close()
                
        except FileNotFoundError:
            logger.warning(f"Deadside.log not found for {server_name}")
            return None
                
        except Exception as e:
            logger.error(f"Failed to check rotation for {server_name}: {e}")
            return None
    
    async def _process_server_deadside_log(self, server_config: Dict[str, Any], 
                                         file_state: ServerFileState) -> List[LogEntry]:
        """Process Deadside.log for a specific server"""
        entries = []
        server_name = file_state.server_name
        
        try:
            async with connection_manager.get_connection(self.guild_id, server_config) as conn:
                if not conn:
                    return entries
                
                sftp = await conn.start_sftp_client()
                host = server_config.get('host', 'unknown')
                server_id = server_config.get('server_id', 'unknown')
                deadside_log_path = f"./{host}_{server_id}/Logs/Deadside.log"
                
                async with sftp.open(deadside_log_path, 'rb') as file:
                    if file_state.rotation_detected:
                        # File rotated - process entire file and reset player states
                        content = await file.read()
                        await self._handle_server_restart(server_name)
                        start_position = 0
                        start_line = 0
                    else:
                        # Continue from last position
                        await file.seek(file_state.last_position)
                        content = await file.read()
                        start_position = file_state.last_position
                        start_line = file_state.last_line
                    
                    if content:
                        lines = content.decode('utf-8', errors='ignore').splitlines()
                        
                        for i, line in enumerate(lines):
                            if self.cancelled:
                                break
                            
                            entry = self._parse_log_line(line, server_name, start_line + i)
                            if entry:
                                entries.append(entry)
                        
                        # Update state
                        if self.state_manager:
                            new_position = start_position + len(content)
                            new_line = start_line + len(lines)
                            
                            await self.state_manager.update_parser_state(
                                self.guild_id, server_name,
                                'Deadside.log', new_line, new_position,
                                'unified', file_state.file_hash
                            )
                
        except Exception as e:
            logger.error(f"Failed to process Deadside.log for {server_name}: {e}")
        
        return entries
    
    def _parse_log_line(self, line: str, server_name: str, line_number: int) -> Optional[LogEntry]:
        """Parse a single log line into a LogEntry"""
        line = line.strip()
        if not line:
            return None
        
        try:
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
        """Classify log entry type and extract relevant data"""
        content_lower = content.lower()
        
        # Player connection events
        if 'joined the game' in content_lower or 'connected' in content_lower:
            player_name = self._extract_player_name(content)
            return 'join', player_name, {'action': 'connect'}
        
        if 'left the game' in content_lower or 'disconnected' in content_lower:
            player_name = self._extract_player_name(content)
            return 'leave', player_name, {'action': 'disconnect'}
        
        # Kill/death events
        if 'killed' in content_lower and 'with' in content_lower:
            return 'kill', None, self._parse_kill_event(content)
        
        # Server events
        if 'server' in content_lower and ('start' in content_lower or 'init' in content_lower):
            return 'server_start', None, {'message': content}
        
        if 'server' in content_lower and ('stop' in content_lower or 'shutdown' in content_lower):
            return 'server_stop', None, {'message': content}
        
        # General events
        return 'general', None, {'message': content}
    
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
            # This would integrate with existing player session management
            # Reset all players for this server to offline state
            logger.info(f"Handling server restart for {server_name} - resetting player states")
            
            # TODO: Integrate with existing player session reset logic
            
        except Exception as e:
            logger.error(f"Failed to handle server restart for {server_name}: {e}")
    
    async def _process_entries_chronologically(self, entries: List[LogEntry]):
        """Process log entries in chronological order"""
        try:
            for entry in entries:
                if self.cancelled:
                    break
                
                await self._process_single_entry(entry)
                
        except Exception as e:
            logger.error(f"Failed to process entries chronologically: {e}")
    
    async def _process_single_entry(self, entry: LogEntry):
        """Process a single log entry"""
        try:
            # This would integrate with existing unified log parser logic
            # Handle player connections, kills, etc.
            
            if entry.entry_type == 'join' and entry.player_name:
                await self._handle_player_join(entry)
            elif entry.entry_type == 'leave' and entry.player_name:
                await self._handle_player_leave(entry)
            elif entry.entry_type == 'kill':
                await self._handle_kill_event(entry)
            
        except Exception as e:
            logger.error(f"Failed to process log entry: {e}")
    
    async def _handle_player_join(self, entry: LogEntry):
        """Handle player join event"""
        # TODO: Integrate with existing player session tracking
        logger.debug(f"Player {entry.player_name} joined {entry.server_name}")
    
    async def _handle_player_leave(self, entry: LogEntry):
        """Handle player leave event"""
        # TODO: Integrate with existing player session tracking
        logger.debug(f"Player {entry.player_name} left {entry.server_name}")
    
    async def _handle_kill_event(self, entry: LogEntry):
        """Handle kill event"""
        # TODO: Integrate with existing kill tracking
        logger.debug(f"Kill event on {entry.server_name}")
    
    def cancel(self):
        """Cancel the processing"""
        self.cancelled = True

class MultiGuildUnifiedProcessor:
    """Manages unified processing across multiple guilds"""
    
    def __init__(self):
        self.processors: Dict[int, ScalableUnifiedProcessor] = {}
    
    async def process_all_guilds(self, guild_configs: Dict[int, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Process unified logs for all guilds"""
        tasks = []
        
        for guild_id, server_configs in guild_configs.items():
            processor = ScalableUnifiedProcessor(guild_id)
            self.processors[guild_id] = processor
            
            task = processor.process_guild_servers(server_configs)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Compile summary
        total_servers = sum(len(configs) for configs in guild_configs.values())
        successful_guilds = sum(1 for result in results if isinstance(result, dict) and result.get('success'))
        total_processed = sum(result.get('processed_servers', 0) for result in results if isinstance(result, dict))
        total_rotations = sum(result.get('rotated_servers', 0) for result in results if isinstance(result, dict))
        
        return {
            'success': True,
            'total_guilds': len(guild_configs),
            'successful_guilds': successful_guilds,
            'total_servers': total_servers,
            'processed_servers': total_processed,
            'rotated_servers': total_rotations,
            'results': results
        }