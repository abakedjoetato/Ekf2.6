#!/usr/bin/env python3
"""
Advanced Unified Log Parser - 10/10 py-cord 2.6.1 Implementation
Cross-guild kill data with server-scoped premium analytics
"""

import asyncio
import asyncssh
import logging
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
import traceback

logger = logging.getLogger(__name__)

class AdvancedUnifiedParser:
    """
    Advanced Unified Log Parser for 10/10 Bot
    - Cross-guild kill data collection
    - Server-scoped premium analytics
    - Real-time player session tracking
    - Free server killfeed-only limitation
    """
    
    def __init__(self, db_manager, channel_router):
        self.db_manager = db_manager
        self.channel_router = channel_router
        self.logger = logging.getLogger(__name__)
        
        # Kill patterns for different game types
        self.kill_patterns = {
            'standard': re.compile(
                r'(\w+)\s+killed\s+(\w+)\s+with\s+(\w+)',
                re.IGNORECASE
            ),
            'detailed': re.compile(
                r'\[(\d{2}:\d{2}:\d{2})\]\s+(\w+)\s+\[.*?\]\s+killed\s+(\w+)\s+\[.*?\]\s+with\s+(\w+)',
                re.IGNORECASE
            ),
            'coordinates': re.compile(
                r'(\w+)\s+killed\s+(\w+)\s+with\s+(\w+)\s+at\s+\(([^)]+)\)',
                re.IGNORECASE
            )
        }
        
        # Connection patterns
        self.connection_patterns = {
            'join': re.compile(r'(\w+)\s+joined\s+the\s+game', re.IGNORECASE),
            'leave': re.compile(r'(\w+)\s+left\s+the\s+game', re.IGNORECASE),
            'disconnect': re.compile(r'(\w+)\s+disconnected', re.IGNORECASE)
        }
    
    async def run_log_parser(self):
        """Main parser execution for all registered servers"""
        try:
            self.logger.info("🔄 Starting advanced unified log parser")
            
            # Get all registered servers
            cursor = self.db_manager.db.servers.find({})
            servers = await cursor.to_list(length=None)
            
            if not servers:
                self.logger.info("📝 No servers registered for parsing")
                return
            
            # Process each server
            for server in servers:
                try:
                    await self._process_server(server)
                except Exception as e:
                    self.logger.error(f"❌ Failed to process server {server['server_id']}: {e}")
                    continue
            
            self.logger.info(f"✅ Advanced parser completed: {len(servers)} servers processed")
            
        except Exception as e:
            self.logger.error(f"❌ Advanced parser failed: {e}")
            self.logger.error(traceback.format_exc())
    
    async def _process_server(self, server: Dict[str, Any]):
        """Process individual server logs"""
        server_id = server['server_id']
        server_name = server['server_name']
        guild_id = server['guild_id']
        ssh_config = server['ssh_config']
        
        try:
            # Get parser state
            parser_state = await self.db_manager.db.parser_states.find_one(
                {"server_id": server_id}
            )
            
            last_position = parser_state['last_position'] if parser_state else 0
            
            # Read log file via SFTP
            log_content = await self._read_log_file(ssh_config)
            if not log_content:
                return
            
            # Determine processing mode
            if last_position == 0:
                # Cold start - rebuild current state
                await self._cold_start_processing(server_id, guild_id, log_content)
            else:
                # Hot start - process new content only
                new_content = log_content[last_position:]
                if new_content:
                    await self._hot_start_processing(server_id, guild_id, new_content)
            
            # Update parser state
            await self.db_manager.db.parser_states.update_one(
                {"server_id": server_id},
                {
                    "$set": {
                        "last_position": len(log_content),
                        "last_parsed": datetime.utcnow(),
                        "guild_id": guild_id
                    }
                },
                upsert=True
            )
            
        except Exception as e:
            self.logger.error(f"❌ Server {server_id} processing failed: {e}")
    
    async def _read_log_file(self, ssh_config: Dict[str, Any]) -> Optional[bytes]:
        """Read log file via SFTP with advanced error handling"""
        try:
            async with asyncssh.connect(
                host=ssh_config['host'],
                port=ssh_config['port'],
                username=ssh_config['username'],
                known_hosts=None
            ) as conn:
                async with conn.start_sftp_client() as sftp:
                    file_data = await sftp.get(ssh_config['log_path'])
                    self.logger.debug(f"✅ SFTP read {len(file_data)} bytes")
                    return file_data
                    
        except Exception as e:
            self.logger.error(f"❌ SFTP connection failed: {e}")
            return None
    
    async def _cold_start_processing(self, server_id: int, guild_id: int, log_content: bytes):
        """Cold start processing - rebuild current state from complete log"""
        self.logger.info(f"🧊 Cold start: rebuilding current state for server {server_id}")
        
        try:
            # Reset existing player sessions for this server
            await self.db_manager.db.player_sessions.update_many(
                {"server_id": server_id},
                {"$set": {"is_online": False}}
            )
            
            # Parse complete log
            log_lines = log_content.decode('utf-8', errors='ignore').splitlines()
            
            # Track current online players
            current_players = set()
            
            # Process connection events to rebuild state
            for line in log_lines:
                # Check for player connections
                for pattern_name, pattern in self.connection_patterns.items():
                    match = pattern.search(line)
                    if match:
                        player_name = match.group(1)
                        
                        if pattern_name == 'join':
                            current_players.add(player_name)
                        elif pattern_name in ['leave', 'disconnect']:
                            current_players.discard(player_name)
            
            # Update player sessions with current state
            for player_name in current_players:
                await self.db_manager.db.player_sessions.update_one(
                    {"server_id": server_id, "player_name": player_name},
                    {
                        "$set": {
                            "guild_id": guild_id,
                            "is_online": True,
                            "last_seen": datetime.utcnow(),
                            "server_name": await self._get_server_name(server_id)
                        }
                    },
                    upsert=True
                )
            
            # Process kill events for cross-guild data
            await self._process_kill_events(server_id, guild_id, log_lines)
            
            self.logger.info(f"🎮 Cold start complete: {len(current_players)} players online")
            
        except Exception as e:
            self.logger.error(f"❌ Cold start processing failed: {e}")
    
    async def _hot_start_processing(self, server_id: int, guild_id: int, new_content: bytes):
        """Hot start processing - process only new log content"""
        self.logger.info(f"🔥 Hot start: processing new content for server {server_id}")
        
        try:
            new_lines = new_content.decode('utf-8', errors='ignore').splitlines()
            
            # Process connection events
            for line in new_lines:
                await self._process_connection_event(server_id, guild_id, line)
            
            # Process kill events for cross-guild data
            await self._process_kill_events(server_id, guild_id, new_lines)
            
            # Send real-time updates (only for premium servers or basic killfeed)
            server_config = await self.db_manager.get_server_config(server_id)
            if server_config:
                await self._send_real_time_updates(server_config, new_lines)
            
        except Exception as e:
            self.logger.error(f"❌ Hot start processing failed: {e}")
    
    async def _process_connection_event(self, server_id: int, guild_id: int, line: str):
        """Process player connection events"""
        try:
            for pattern_name, pattern in self.connection_patterns.items():
                match = pattern.search(line)
                if match:
                    player_name = match.group(1)
                    
                    if pattern_name == 'join':
                        # Player joined
                        await self.db_manager.db.player_sessions.update_one(
                            {"server_id": server_id, "player_name": player_name},
                            {
                                "$set": {
                                    "guild_id": guild_id,
                                    "is_online": True,
                                    "last_seen": datetime.utcnow(),
                                    "server_name": await self._get_server_name(server_id)
                                }
                            },
                            upsert=True
                        )
                        
                    elif pattern_name in ['leave', 'disconnect']:
                        # Player left
                        await self.db_manager.db.player_sessions.update_one(
                            {"server_id": server_id, "player_name": player_name},
                            {
                                "$set": {
                                    "is_online": False,
                                    "last_seen": datetime.utcnow()
                                }
                            }
                        )
                    
                    break
                    
        except Exception as e:
            self.logger.error(f"❌ Connection event processing failed: {e}")
    
    async def _process_kill_events(self, server_id: int, guild_id: int, log_lines: List[str]):
        """Process kill events for cross-guild data collection"""
        try:
            for line in log_lines:
                # Try each kill pattern
                for pattern_name, pattern in self.kill_patterns.items():
                    match = pattern.search(line)
                    if match:
                        # Extract kill data based on pattern
                        if pattern_name == 'standard':
                            killer, victim, weapon = match.groups()
                            additional_data = {}
                        elif pattern_name == 'detailed':
                            timestamp, killer, victim, weapon = match.groups()
                            additional_data = {"timestamp": timestamp}
                        elif pattern_name == 'coordinates':
                            killer, victim, weapon, coordinates = match.groups()
                            additional_data = {"coordinates": coordinates}
                        
                        # Record kill event (cross-guild accessible)
                        await self.db_manager.record_kill(
                            server_id=server_id,
                            killer=killer,
                            victim=victim,
                            weapon=weapon,
                            additional_data=additional_data
                        )
                        
                        break
                        
        except Exception as e:
            self.logger.error(f"❌ Kill event processing failed: {e}")
    
    async def _send_real_time_updates(self, server_config, new_lines: List[str]):
        """Send real-time updates based on server premium status"""
        try:
            is_premium = server_config.premium_status
            guild_id = server_config.guild_id
            
            # Always send killfeed for all servers
            await self._send_killfeed_updates(guild_id, new_lines)
            
            # Premium servers get additional updates
            if is_premium:
                await self._send_premium_updates(guild_id, server_config.server_id, new_lines)
                
        except Exception as e:
            self.logger.error(f"❌ Real-time update sending failed: {e}")
    
    async def _send_killfeed_updates(self, guild_id: int, new_lines: List[str]):
        """Send basic killfeed updates (available for all servers)"""
        try:
            # Extract kill events for killfeed
            kill_events = []
            
            for line in new_lines:
                for pattern in self.kill_patterns.values():
                    match = pattern.search(line)
                    if match:
                        kill_events.append(line.strip())
                        break
            
            if kill_events and self.channel_router:
                await self.channel_router.send_killfeed(guild_id, kill_events)
                
        except Exception as e:
            self.logger.error(f"❌ Killfeed update failed: {e}")
    
    async def _send_premium_updates(self, guild_id: int, server_id: int, new_lines: List[str]):
        """Send premium updates (analytics, detailed stats)"""
        try:
            # Generate analytics update
            analytics = await self.db_manager.generate_guild_analytics(guild_id)
            
            if analytics and self.channel_router:
                await self.channel_router.send_analytics_update(guild_id, analytics)
                
        except Exception as e:
            self.logger.error(f"❌ Premium update failed: {e}")
    
    async def _get_server_name(self, server_id: int) -> str:
        """Get server name from database"""
        try:
            server = await self.db_manager.db.servers.find_one({"server_id": server_id})
            return server['server_name'] if server else f"Server {server_id}"
        except:
            return f"Server {server_id}"
    
    async def cleanup_stale_connections(self):
        """Clean up stale player connections"""
        try:
            # Mark players as offline if not seen for more than 1 hour
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            
            result = await self.db_manager.db.player_sessions.update_many(
                {
                    "last_seen": {"$lt": cutoff_time},
                    "is_online": True
                },
                {"$set": {"is_online": False}}
            )
            
            if result.modified_count > 0:
                self.logger.info(f"🧹 Cleaned up {result.modified_count} stale connections")
                
        except Exception as e:
            self.logger.error(f"❌ Stale connection cleanup failed: {e}")