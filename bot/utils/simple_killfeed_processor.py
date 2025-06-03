"""
Simple Killfeed Processor
Based on historical parser's proven CSV discovery and processing approach
Maintains state instead of clearing it like historical parser does
Shares state system with historical parser (separate from unified parser)
"""

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from bot.utils.connection_pool import GlobalConnectionManager, connection_manager
from bot.utils.shared_parser_state import get_shared_state_manager, ParserState

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
    filename: str

class SimpleKillfeedProcessor:
    """Simple killfeed processor without shared state dependencies"""
    
    def __init__(self, guild_id: int, server_config: Dict[str, Any], bot=None):
        self.guild_id = guild_id
        self.server_config = server_config
        self.server_name = server_config.get('name', 'Unknown')
        self.state_manager = get_shared_state_manager()
        self.bot = bot
        self.cancelled = False
        
    def _get_killfeed_path(self) -> str:
        """Get the killfeed path for this server"""
        server_id = self.server_config.get('server_id', self.server_config.get('_id', 'unknown'))
        return f"/home/ds{server_id}/killfeed/"
    
    async def process_server_killfeed(self, progress_callback=None) -> Dict[str, Any]:
        """Main entry point for killfeed processing"""
        results = {
            'success': False,
            'events_processed': 0,
            'errors': []
        }
        
        try:
            # Register session with shared state manager
            if self.state_manager:
                await self.state_manager.register_session(self.guild_id, self.server_name, 'killfeed')
            
            # Get current state from shared manager
            current_state = None
            if self.state_manager:
                current_state = await self.state_manager.get_parser_state(self.guild_id, self.server_name)
            
            events = []
            
            # Finish processing previous file if state exists
            if current_state and current_state.last_file:
                events.extend(await self._finish_previous_file(current_state))
            
            # Discover and process newest CSV file
            newest_file = await self._discover_newest_csv_file()
            if newest_file:
                # Check if we need to switch to a newer file
                if not current_state or current_state.last_file != newest_file:
                    new_events = await self._process_csv_file(newest_file, current_state)
                    events.extend(new_events)
            
            if events:
                # Deliver events to Discord
                await self._deliver_killfeed_events(events)
                results['events_processed'] = len(events)
                logger.info(f"✅ Processed {len(events)} killfeed events for {self.server_name}")
            
            results['success'] = True
            
        except Exception as e:
            logger.error(f"Killfeed processing failed for {self.server_name}: {e}")
            results['error'] = str(e)
        
        finally:
            # Unregister session
            if self.state_manager:
                await self.state_manager.unregister_session(self.guild_id, self.server_name, 'killfeed')
        
        return results
    
    async def _finish_previous_file(self, current_state: ParserState) -> List[KillfeedEvent]:
        """Finish processing the previous file from last known position"""
        events = []
        
        try:
            # Construct path to previous file
            killfeed_path = self._get_killfeed_path()
            previous_file_path = f"{killfeed_path}world_0/{current_state.last_file}"
            
            logger.info(f"Finishing previous file: {current_state.last_file} from line {current_state.last_line}")
            
            async with connection_manager.get_connection(self.guild_id, self.server_config) as conn:
                if not conn:
                    return events
                
                sftp = await conn.start_sftp_client()
                
                # Check if previous file still exists
                try:
                    await sftp.stat(previous_file_path)
                except:
                    logger.warning(f"Previous file {current_state.last_file} no longer exists")
                    return events
                
                # Read from last known position to end of file
                async with sftp.open(previous_file_path, 'rb') as file:
                    await file.seek(current_state.last_byte_position)
                    remaining_content = await file.read()
                    
                    if remaining_content:
                        lines = remaining_content.decode('utf-8', errors='ignore').splitlines()
                        
                        # Process remaining lines
                        for i, line in enumerate(lines):
                            if self.cancelled:
                                break
                            
                            line = line.strip()
                            if not line:
                                continue
                            
                            event = self._parse_killfeed_line(line, current_state.last_line + i, current_state.last_file)
                            if event:
                                events.append(event)
                        
                        # Update state to reflect completion of previous file
                        if self.state_manager and lines:
                            final_line = current_state.last_line + len(lines)
                            final_byte = current_state.last_byte_position + len(remaining_content)
                            
                            await self.state_manager.update_parser_state(
                                self.guild_id, self.server_name,
                                current_state.last_file, final_line, final_byte,
                                'killfeed', current_state.file_timestamp
                            )
                            
        except Exception as e:
            logger.error(f"Failed to finish previous file: {e}")
        
        return events

    async def _discover_newest_csv_file(self) -> Optional[str]:
        """Discover newest CSV file using historical parser's proven glob method"""
        try:
            async with connection_manager.get_connection(self.guild_id, self.server_config) as conn:
                if not conn:
                    return None
                
                sftp = await conn.start_sftp_client()
                killfeed_path = self._get_killfeed_path()
                world_path = f"{killfeed_path}world_0/"
                
                # List CSV files in world_0 directory
                try:
                    entries = await sftp.listdir(world_path)
                    csv_files = [f for f in entries if f.endswith('.csv')]
                    
                    if not csv_files:
                        return None
                    
                    # Get newest file (max by filename which includes timestamp)
                    newest_file = max(csv_files)
                    logger.info(f"Found newest killfeed file: {newest_file}")
                    return newest_file
                    
                except Exception as e:
                    logger.warning(f"Failed to list killfeed directory {world_path}: {e}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to discover killfeed files: {e}")
            return None
    
    async def _process_csv_file(self, filename: str, current_state: Optional[ParserState] = None) -> List[KillfeedEvent]:
        """Process CSV file from last known position"""
        events = []
        
        try:
            async with connection_manager.get_connection(self.guild_id, self.server_config) as conn:
                if not conn:
                    return events
                
                sftp = await conn.start_sftp_client()
                killfeed_path = self._get_killfeed_path()
                file_path = f"{killfeed_path}world_0/{filename}"
                
                # Determine starting position
                start_line = 0
                start_byte = 0
                
                if current_state and current_state.last_file == filename:
                    start_line = current_state.last_line
                    start_byte = current_state.last_byte_position
                
                # Read file content from starting position
                async with sftp.open(file_path, 'rb') as file:
                    await file.seek(start_byte)
                    content = await file.read()
                    
                if not content:
                    return events
                
                # Process lines
                lines = content.decode('utf-8', errors='ignore').splitlines()
                
                # Extract timestamp from filename for state management
                file_timestamp = self._extract_timestamp_from_filename(filename)
                
                for i, line in enumerate(lines):
                    if self.cancelled:
                        break
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    event = self._parse_killfeed_line(line, start_line + i + 1, filename)
                    if event:
                        events.append(event)
                
                # Update state after processing
                if self.state_manager and lines:
                    final_line = start_line + len(lines)
                    final_byte = start_byte + len(content.encode('utf-8'))
                    
                    await self.state_manager.update_parser_state(
                        self.guild_id, self.server_name,
                        filename, final_line, final_byte,
                        'killfeed', file_timestamp
                    )
                
        except Exception as e:
            logger.error(f"Failed to process CSV file {filename}: {e}")
        
        return events
    
    def _parse_killfeed_line(self, line: str, line_number: int, filename: str) -> Optional[KillfeedEvent]:
        """Parse a single killfeed CSV line using historical parser's exact logic"""
        try:
            # Historical parser uses semicolon delimiter with 9+ columns
            parts = line.split(';')
            
            if len(parts) < 9:
                return None
            
            # Extract fields (0-indexed)
            timestamp_str = parts[0].strip()
            killer = parts[1].strip()
            victim = parts[2].strip() 
            weapon = parts[3].strip()
            distance_str = parts[4].strip()
            killer_platform = parts[5].strip() if len(parts) > 5 else "Unknown"
            victim_platform = parts[6].strip() if len(parts) > 6 else "Unknown"
            
            # Parse timestamp
            event_timestamp = self._parse_timestamp(timestamp_str)
            if not event_timestamp:
                return None
                
            # Parse distance
            try:
                distance = int(float(distance_str))
            except (ValueError, TypeError):
                distance = 0
            
            # Create event
            return KillfeedEvent(
                timestamp=event_timestamp,
                killer=killer,
                victim=victim,
                weapon=weapon,
                distance=distance,
                killer_platform=killer_platform,
                victim_platform=victim_platform,
                raw_line=line,
                line_number=line_number,
                filename=filename
            )
            
        except Exception as e:
            logger.debug(f"Failed to parse killfeed line: {line} - {e}")
            return None
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp from killfeed data"""
        try:
            # Try multiple timestamp formats
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y/%m/%d %H:%M:%S',
                '%d/%m/%Y %H:%M:%S',
                '%Y-%m-%d_%H-%M-%S'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(timestamp_str, fmt).replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
            
            return None
            
        except Exception as e:
            logger.debug(f"Failed to parse timestamp {timestamp_str}: {e}")
            return None
    
    async def _deliver_killfeed_events(self, events: List[KillfeedEvent]):
        """Deliver killfeed events to Discord channels"""
        try:
            logger.info(f"Starting delivery of {len(events)} killfeed events")
            
            if not self.bot:
                logger.error("CRITICAL: No bot instance available for killfeed delivery")
                return
                
            # Get killfeed channel directly from database
            guild_config = await self.bot.db_manager.get_guild(self.guild_id)
            if not guild_config:
                logger.warning(f"No guild config found for guild {self.guild_id}")
                return

            server_channels = guild_config.get('server_channels', {})
            channel_id = None
            
            # Try server-specific channel first
            if self.server_name in server_channels:
                channel_id = server_channels[self.server_name].get('killfeed')
            
            # Fall back to default server channel
            if not channel_id and 'default' in server_channels:
                channel_id = server_channels['default'].get('killfeed')
            
            if not channel_id:
                logger.warning(f"No killfeed channel configured for {self.server_name}")
                return
            
            # Get Discord channel
            channel = self.bot.get_channel(channel_id)
            if not channel:
                logger.warning(f"Killfeed channel {channel_id} not found")
                return
            
            # Send events to channel
            for event in events:
                try:
                    # Create killfeed embed
                    embed = await self._create_killfeed_embed(event)
                    
                    # Send directly to channel
                    await channel.send(embed=embed)
                    logger.info(f"✅ Delivered killfeed event: {event.killer} killed {event.victim} with {event.weapon}")
                    
                except Exception as e:
                    logger.error(f"Failed to deliver killfeed event: {e}")
                    
        except Exception as e:
            logger.error(f"Killfeed delivery failed: {e}")
    
    async def _create_killfeed_embed(self, event: KillfeedEvent):
        """Create Discord embed for killfeed event"""
        import discord
        
        embed = discord.Embed(
            title="💀 Player Eliminated",
            color=0xFF0000,
            timestamp=event.timestamp
        )
        
        embed.add_field(
            name="Killer",
            value=f"**{event.killer}** ({event.killer_platform})",
            inline=True
        )
        
        embed.add_field(
            name="Victim", 
            value=f"**{event.victim}** ({event.victim_platform})",
            inline=True
        )
        
        embed.add_field(
            name="Weapon",
            value=f"**{event.weapon}**",
            inline=True
        )
        
        if event.distance > 0:
            embed.add_field(
                name="Distance",
                value=f"**{event.distance}m**",
                inline=True
            )
        
        embed.set_footer(text=f"Server: {self.server_name}")
        
        return embed
    
    def cancel(self):
        """Cancel the processing"""
        self.cancelled = True

class MultiServerSimpleKillfeedProcessor:
    """Process killfeed for multiple servers using simple approach"""
    
    def __init__(self, guild_id: int, bot=None):
        self.guild_id = guild_id
        self.bot = bot
        self.active_processors = {}
    
    async def process_available_servers(self, server_configs: List[Dict[str, Any]], 
                                      progress_callback=None) -> Dict[str, Any]:
        """Process all available servers for killfeed updates"""
        results = {
            'processed_servers': 0,
            'skipped_servers': 0,
            'total_events': 0
        }
        
        for server_config in server_configs:
            server_name = server_config.get('name', 'Unknown')
            
            try:
                # Create processor for this server
                processor = SimpleKillfeedProcessor(self.guild_id, server_config, self.bot)
                self.active_processors[server_name] = processor
                
                # Process killfeed
                server_results = await processor.process_server_killfeed(progress_callback)
                
                if server_results.get('success'):
                    results['processed_servers'] += 1
                    results['total_events'] += server_results.get('events_processed', 0)
                else:
                    results['skipped_servers'] += 1
                
            except Exception as e:
                logger.error(f"Failed to process killfeed for {server_name}: {e}")
                results['skipped_servers'] += 1
            finally:
                # Cleanup
                if server_name in self.active_processors:
                    del self.active_processors[server_name]
        
        return results