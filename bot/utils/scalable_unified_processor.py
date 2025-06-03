"""
Scalable Unified Log Processor
Enterprise-grade unified log processing with connection pooling, file rotation detection, and chronological ordering
"""

import asyncio
import hashlib
import logging
import re
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
    
    def __init__(self, guild_id: int, bot=None):
        self.guild_id = guild_id
        self.bot = bot
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
                        logger.info(f"Processing {len(lines)} lines for {server_name} from position {start_position}")
                        
                        processed_entries = 0
                        entry_types_found = {}
                        for i, line in enumerate(lines):
                            if self.cancelled:
                                break
                            
                            entry = self._parse_log_line(line, server_name, start_line + i)
                            if entry:
                                entries.append(entry)
                                processed_entries += 1
                                # Track entry types
                                entry_type = entry.entry_type
                                entry_types_found[entry_type] = entry_types_found.get(entry_type, 0) + 1
                        
                        logger.info(f"Found {processed_entries} valid entries out of {len(lines)} lines for {server_name}")
                        logger.info(f"Entry types found: {entry_types_found}")
                        
                        # Update state
                        if self.state_manager:
                            new_position = start_position + len(content)
                            new_line = start_line + len(lines)
                            
                            logger.info(f"Updating parser state: position {start_position} -> {new_position}, line {start_line} -> {new_line}")
                            
                            await self.state_manager.update_parser_state(
                                self.guild_id, server_name,
                                'Deadside.log', new_line, new_position,
                                'unified', file_state.file_hash
                            )
                        else:
                            logger.warning(f"No state manager available to update parser state for {server_name}")
                    else:
                        logger.warning(f"No content read from log file for {server_name}")
                
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
        
        # Deadside player connection events
        if ('logsfpsnetworkmanager' in content_lower or 'logsfps' in content_lower):
            if 'player' in content_lower and ('connect' in content_lower or 'join' in content_lower or 'login' in content_lower):
                player_name = self._extract_deadside_player_name(content)
                return 'join', player_name, {
                    'action': 'connect',
                    'log_category': log_category,
                    'system': system_info,
                    'message': message
                }
            
            if 'player' in content_lower and ('disconnect' in content_lower or 'leave' in content_lower or 'logout' in content_lower):
                player_name = self._extract_deadside_player_name(content)
                return 'leave', player_name, {
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
        
        # Vehicle and gameplay events
        if 'logsfps' in content_lower:
            if 'vehicle' in content_lower:
                return 'vehicle', None, {
                    'log_category': log_category,
                    'system': system_info,
                    'message': message,
                    'event_type': 'vehicle'
                }
            
            if 'spawn' in content_lower or 'respawn' in content_lower:
                return 'spawn', None, {
                    'log_category': log_category,
                    'system': system_info,
                    'message': message,
                    'event_type': 'spawn'
                }
        
        # Server status events
        if 'logcore' in content_lower or 'logengine' in content_lower:
            if 'init' in content_lower or 'start' in content_lower:
                return 'server_start', None, {
                    'log_category': log_category,
                    'system': system_info,
                    'message': message
                }
            
            if 'shutdown' in content_lower or 'exit' in content_lower:
                return 'server_stop', None, {
                    'log_category': log_category,
                    'system': system_info,
                    'message': message
                }
        
        # General Deadside events
        return 'general', None, {
            'log_category': log_category,
            'system': system_info,
            'message': message
        }
    
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
            # This would integrate with existing player session management
            # Reset all players for this server to offline state
            logger.info(f"Handling server restart for {server_name} - resetting player states")
            
            if self.bot and hasattr(self.bot, 'db_manager') and self.bot.db_manager:
                # End all active sessions for this server
                await self.bot.db_manager.end_all_sessions_for_server(
                    self.guild_id, 
                    server_name
                )
                logger.info(f"Reset all player sessions for {server_name}")
            else:
                logger.warning(f"No database manager available to reset player states for {server_name}")
            
        except Exception as e:
            logger.error(f"Failed to handle server restart for {server_name}: {e}")
    
    async def _process_entries_chronologically(self, entries: List[LogEntry]):
        """Process log entries in chronological order"""
        try:
            logger.info(f"Processing {len(entries)} entries chronologically")
            
            entry_types = {}
            for entry in entries:
                if self.cancelled:
                    break
                
                # Track entry types for debugging
                entry_type = entry.entry_type
                entry_types[entry_type] = entry_types.get(entry_type, 0) + 1
                
                await self._process_single_entry(entry)
            
            logger.info(f"Chronological processing complete. Entry types: {entry_types}")
                
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
        """Handle player join event with proper session tracking"""
        try:
            if not entry.player_name:
                return
            
            logger.info(f"Player {entry.player_name} joined {entry.server_name}")
            
            # Get bot's database manager
            if self.bot and hasattr(self.bot, 'db_manager') and self.bot.db_manager:
                # Update player session to online
                await self.bot.db_manager.start_player_session(
                    self.guild_id,
                    entry.player_name,
                    entry.server_name,
                    entry.timestamp
                )
                logger.debug(f"Started session for {entry.player_name}")
            else:
                logger.warning(f"No database manager available to start session for {entry.player_name}")
            
        except Exception as e:
            logger.error(f"Failed to handle player join for {entry.player_name}: {e}")
    
    async def _handle_player_leave(self, entry: LogEntry):
        """Handle player leave event with proper session tracking"""
        try:
            if not entry.player_name:
                return
            
            logger.info(f"Player {entry.player_name} left {entry.server_name}")
            
            # Get bot's database manager
            if self.bot and hasattr(self.bot, 'db_manager') and self.bot.db_manager:
                # End player session
                await self.bot.db_manager.end_player_session(
                    self.guild_id,
                    entry.player_name,
                    entry.timestamp
                )
                logger.debug(f"Ended session for {entry.player_name}")
            else:
                logger.warning(f"No database manager available to end session for {entry.player_name}")
            
        except Exception as e:
            logger.error(f"Failed to handle player leave for {entry.player_name}: {e}")
    
    async def _handle_kill_event(self, entry: LogEntry):
        """Handle kill event with proper kill tracking"""
        try:
            kill_data = entry.additional_data
            if not kill_data or 'killer' not in kill_data or 'victim' not in kill_data:
                return
            
            killer = kill_data['killer']
            victim = kill_data['victim']
            weapon = kill_data.get('weapon', 'Unknown')
            
            logger.info(f"Kill event: {killer} killed {victim} with {weapon} on {entry.server_name}")
            
            # Get bot's database manager
            if self.bot and hasattr(self.bot, 'db_manager') and self.bot.db_manager:
                # Record the kill
                await self.bot.db_manager.record_kill(
                    guild_id=self.guild_id,
                    killer_name=killer,
                    victim_name=victim,
                    weapon=weapon,
                    server_name=entry.server_name,
                    timestamp=entry.timestamp,
                    distance=kill_data.get('distance', 0)
                )
                logger.debug(f"Recorded kill: {killer} -> {victim}")
            else:
                logger.warning(f"No database manager available to record kill: {killer} -> {victim}")
            
        except Exception as e:
            logger.error(f"Failed to handle kill event: {e}")
    
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
                await asyncio.sleep(30)
            
            logger.info(f"Processing server group {group_index + 1}/{len(server_groups)} with {len(server_group)} servers")
            
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
            batch_results = await asyncio.gather(
                *[task for _, task in batch_tasks], 
                return_exceptions=True
            )
            
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