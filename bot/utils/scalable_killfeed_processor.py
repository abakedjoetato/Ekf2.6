"""
Scalable Killfeed Processor
Real-time incremental processing with state coordination and connection pooling
"""

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from bot.utils.connection_pool import connection_manager
from bot.utils.shared_parser_state import get_shared_state_manager, ParserState
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class KillfeedEvent:
    """Represents a single killfeed event"""
    timestamp: datetime
    killer: str
    victim: str
    weapon: str
    distance: int
    killer_platform: str
    victim_platform: str
    raw_line: str
    line_number: int

class ScalableKillfeedProcessor:
    """Manages incremental killfeed processing for a single server with state coordination"""
    
    def __init__(self, guild_id: int, server_config: Dict[str, Any]):
        self.guild_id = guild_id
        self.server_config = server_config
        self.server_name = server_config.get('name', server_config.get('server_name', 'default'))
        self.cancelled = False
        self.state_manager = get_shared_state_manager()
        
    async def process_server_killfeed(self, progress_callback=None) -> Dict[str, Any]:
        """Main entry point for incremental killfeed processing"""
        results = {
            'success': False,
            'server_name': self.server_name,
            'events_processed': 0,
            'new_file_detected': False,
            'state_updated': False,
            'error': None
        }
        
        try:
            # Register session to prevent conflicts
            if self.state_manager and not await self.state_manager.register_session(self.guild_id, self.server_name, 'killfeed'):
                results['error'] = 'Server currently under historical processing'
                return results
            
            # Get current parser state
            current_state = None
            if self.state_manager:
                current_state = await self.state_manager.get_parser_state(self.guild_id, self.server_name)
            
            # Discover current newest file
            newest_file = await self._discover_newest_file()
            if not newest_file:
                results['error'] = 'No killfeed files found'
                return results
            
            file_timestamp = self._extract_timestamp_from_filename(newest_file)
            
            # Determine processing strategy
            if current_state and current_state.last_file:
                if newest_file != current_state.last_file:
                    # New file detected - process gap then switch
                    results['new_file_detected'] = True
                    await self._process_file_transition(current_state, newest_file, progress_callback)
                else:
                    # Continue with same file
                    await self._process_incremental_update(current_state, newest_file, progress_callback)
            else:
                # Fresh start - process from beginning
                await self._process_fresh_start(newest_file, file_timestamp or "", progress_callback)
            
            results['success'] = True
            results['state_updated'] = True
            
        except Exception as e:
            logger.error(f"Killfeed processing failed for {self.server_name}: {e}")
            results['error'] = str(e)
        
        finally:
            # Unregister session
            if self.state_manager:
                await self.state_manager.unregister_session(self.guild_id, self.server_name, 'killfeed')
        
        return results
    
    async def _discover_newest_file(self) -> Optional[str]:
        """Find the newest timestamped killfeed file"""
        try:
            async with connection_manager.get_connection(self.guild_id, self.server_config) as conn:
                if not conn:
                    return None
                
                sftp = await conn.start_sftp_client()
                killfeed_path = self.server_config.get('killfeed_path', '/path/to/killfeed/')
                
                # List files and find newest timestamp
                file_attrs = await sftp.listdir_attr(killfeed_path)
                csv_files = []
                
                for attr in file_attrs:
                    if attr.filename.endswith('.csv'):
                        # Extract timestamp from filename
                        timestamp = self._extract_timestamp_from_filename(attr.filename)
                        if timestamp:
                            csv_files.append((attr.filename, timestamp))
                
                if csv_files:
                    # Sort by timestamp and return newest
                    csv_files.sort(key=lambda x: x[1], reverse=True)
                    return csv_files[0][0]
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to discover newest file for {self.server_name}: {e}")
            return None
    
    def _extract_timestamp_from_filename(self, filename: str) -> Optional[str]:
        """Extract timestamp from killfeed filename"""
        # Match patterns like: killfeed_2024-06-02_21-45-30.csv
        timestamp_pattern = r'(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})'
        match = re.search(timestamp_pattern, filename)
        return match.group(1) if match else None
    
    async def _process_file_transition(self, current_state: ParserState, newest_file: str, progress_callback=None):
        """Process transition from old file to new file"""
        # First, check previous file for any missed lines
        if current_state.last_file and current_state.last_file != newest_file:
            await self._process_gap_from_previous_file(current_state, progress_callback)
        
        # Then start processing new file from beginning
        file_timestamp = self._extract_timestamp_from_filename(newest_file)
        await self._process_fresh_start(newest_file, file_timestamp, progress_callback)
    
    async def _process_gap_from_previous_file(self, current_state: ParserState, progress_callback=None):
        """Check previous file for any lines missed since last processing"""
        try:
            async with connection_manager.get_connection(self.guild_id, self.server_config) as conn:
                if not conn:
                    return
                
                sftp = await conn.start_sftp_client()
                killfeed_path = self.server_config.get('killfeed_path', '/path/to/killfeed/')
                file_path = f"{killfeed_path.rstrip('/')}/{current_state.last_file}"
                
                # Read from last known position to end of file
                async with sftp.open(file_path, 'rb') as file:
                    await file.seek(current_state.last_byte_position)
                    remaining_content = await file.read()
                    
                    if remaining_content:
                        lines = remaining_content.decode('utf-8', errors='ignore').splitlines()
                        await self._process_killfeed_lines(lines, current_state.last_line, current_state.last_file)
                        
                        # Update state with final position of previous file
                        final_position = current_state.last_byte_position + len(remaining_content)
                        final_line = current_state.last_line + len(lines)
                        
                        if self.state_manager:
                            await self.state_manager.update_parser_state(
                                self.guild_id, self.server_name,
                                current_state.last_file, final_line, final_position,
                                'killfeed', current_state.file_timestamp
                            )
                
        except Exception as e:
            logger.error(f"Failed to process gap from previous file: {e}")
    
    async def _process_incremental_update(self, current_state: ParserState, current_file: str, progress_callback=None):
        """Process incremental updates from current file"""
        try:
            async with connection_manager.get_connection(self.guild_id, self.server_config) as conn:
                if not conn:
                    return
                
                sftp = await conn.start_sftp_client()
                killfeed_path = self.server_config.get('killfeed_path', '/path/to/killfeed/')
                file_path = f"{killfeed_path.rstrip('/')}/{current_file}"
                
                # Get current file size
                file_attrs = await sftp.stat(file_path)
                current_size = file_attrs.st_size
                
                if current_size > current_state.last_byte_position:
                    # File has grown - read new content
                    async with sftp.open(file_path, 'rb') as file:
                        await file.seek(current_state.last_byte_position)
                        new_content = await file.read()
                        
                        if new_content:
                            lines = new_content.decode('utf-8', errors='ignore').splitlines()
                            await self._process_killfeed_lines(lines, current_state.last_line, current_file)
                            
                            # Update state
                            new_position = current_state.last_byte_position + len(new_content)
                            new_line = current_state.last_line + len(lines)
                            
                            if self.state_manager:
                                await self.state_manager.update_parser_state(
                                    self.guild_id, self.server_name,
                                    current_file, new_line, new_position,
                                    'killfeed', current_state.file_timestamp
                                )
                
        except Exception as e:
            logger.error(f"Failed to process incremental update: {e}")
    
    async def _process_fresh_start(self, newest_file: str, file_timestamp: str, progress_callback=None):
        """Process new file from the beginning"""
        try:
            async with connection_manager.get_connection(self.guild_id, self.server_config) as conn:
                if not conn:
                    return
                
                sftp = await conn.start_sftp_client()
                killfeed_path = self.server_config.get('killfeed_path', '/path/to/killfeed/')
                file_path = f"{killfeed_path.rstrip('/')}/{newest_file}"
                
                # Read entire file content
                async with sftp.open(file_path, 'rb') as file:
                    content = await file.read()
                    
                    if content:
                        lines = content.decode('utf-8', errors='ignore').splitlines()
                        await self._process_killfeed_lines(lines, 0, newest_file)
                        
                        # Update state
                        if self.state_manager:
                            await self.state_manager.update_parser_state(
                                self.guild_id, self.server_name,
                                newest_file, len(lines), len(content),
                                'killfeed', file_timestamp
                            )
                
        except Exception as e:
            logger.error(f"Failed to process fresh start: {e}")
    
    async def _process_killfeed_lines(self, lines: List[str], start_line_number: int, filename: str):
        """Process killfeed lines and extract events"""
        events = []
        
        for i, line in enumerate(lines):
            if self.cancelled:
                break
                
            line = line.strip()
            if not line:
                continue
                
            # Parse killfeed line (no header - starts with kill data immediately)
            event = self._parse_killfeed_line(line, start_line_number + i, filename)
            if event:
                events.append(event)
        
        # Process events if any found
        if events:
            await self._deliver_killfeed_events(events)
    
    def _parse_killfeed_line(self, line: str, line_number: int, filename: str) -> Optional[KillfeedEvent]:
        """Parse a single killfeed CSV line"""
        try:
            # CSV format: timestamp,killer,victim,weapon,distance,killer_platform,victim_platform
            parts = [part.strip().strip('"') for part in line.split(',')]
            
            if len(parts) >= 7:
                timestamp_str = parts[0]
                timestamp = self._parse_timestamp(timestamp_str)
                
                if timestamp:
                    return KillfeedEvent(
                        timestamp=timestamp,
                        killer=parts[1],
                        victim=parts[2],
                        weapon=parts[3],
                        distance=int(parts[4]) if parts[4].isdigit() else 0,
                        killer_platform=parts[5],
                        victim_platform=parts[6],
                        raw_line=line,
                        line_number=line_number
                    )
            
        except Exception as e:
            logger.debug(f"Failed to parse killfeed line {line_number}: {e}")
        
        return None
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp from killfeed data"""
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d_%H-%M-%S',
            '%m/%d/%Y %H:%M:%S',
            '%d/%m/%Y %H:%M:%S'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        
        return None
    
    async def _deliver_killfeed_events(self, events: List[KillfeedEvent]):
        """Deliver killfeed events to Discord channels"""
        try:
            # This would integrate with the existing killfeed delivery system
            # For now, just log the events processed
            logger.info(f"Processed {len(events)} killfeed events for {self.server_name}")
            
            # TODO: Integrate with Discord channel delivery system
            # This should call the existing killfeed formatting and delivery logic
            
        except Exception as e:
            logger.error(f"Failed to deliver killfeed events: {e}")
    
    def cancel(self):
        """Cancel the processing"""
        self.cancelled = True

class MultiServerKillfeedProcessor:
    """Manages parallel killfeed processing across multiple servers with conflict avoidance"""
    
    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        self.processors: Dict[str, ScalableKillfeedProcessor] = {}
        self.state_manager = get_shared_state_manager()
    
    async def process_available_servers(self, server_configs: List[Dict[str, Any]], 
                                      progress_callback=None) -> Dict[str, Any]:
        """Process all available servers for killfeed updates"""
        # Filter out servers under historical processing
        available_servers = await self.state_manager.get_available_servers_for_killfeed(server_configs)
        
        if not available_servers:
            return {
                'success': True,
                'total_servers': len(server_configs),
                'available_servers': 0,
                'processed_servers': 0,
                'skipped_servers': len(server_configs)
            }
        
        # Process available servers in parallel
        tasks = []
        for server_config in available_servers:
            processor = ScalableKillfeedProcessor(self.guild_id, server_config)
            self.processors[server_config.get('name', 'default')] = processor
            tasks.append(processor.process_server_killfeed(progress_callback))
        
        # Execute all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Compile summary
        successful = sum(1 for result in results if isinstance(result, dict) and result.get('success'))
        
        return {
            'success': True,
            'total_servers': len(server_configs),
            'available_servers': len(available_servers),
            'processed_servers': successful,
            'skipped_servers': len(server_configs) - len(available_servers),
            'results': results
        }