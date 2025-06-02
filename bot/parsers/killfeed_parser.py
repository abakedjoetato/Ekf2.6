"""
Emerald's Killfeed - Killfeed Parser (PHASE 2)
Parses CSV files for kill events and generates embeds
"""

import asyncio
import asyncssh
import csv
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from bot.utils.embed_factory import EmbedFactory

logger = logging.getLogger(__name__)

class KillfeedParser:
    """
    KILLFEED PARSER (FREE)
    - Runs every 300 seconds
    - SFTP path: ./{host}_{serverID}/actual1/deathlogs/*/*.csv
    - Loads most recent file only
    - Tracks and skips previously parsed lines
    - Suicides normalized (killer == victim, Suicide_by_relocation → Menu Suicide)
    - Emits killfeed embeds with distance, weapon, styled headers
    """

    def __init__(self, bot):
        self.bot = bot
        self.sftp_connections = {}
        self.connection_locks = {}
        self.last_processed_lines = {}
        self.last_csv_files = {}

    def parse_csv_line(self, line: str) -> Dict[str, Any]:
        """Parse a single CSV line into kill event data"""
        try:
            parts = line.strip().split(',')
            if len(parts) < 6:
                return {}
            timestamp_str = parts[0].strip()
            killer = parts[1].strip()
            victim = parts[2].strip()
            weapon = parts[3].strip()
            distance = parts[4].strip()

            killer = killer.strip()
            victim = victim.strip()

            # Parse timestamp - handle multiple formats
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y.%m.%d-%H.%M.%S')
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            except ValueError:
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
                except ValueError:
                    timestamp = datetime.utcnow().replace(tzinfo=timezone.utc)

            # Normalize suicide events
            is_suicide = killer == victim or weapon.lower() == 'suicide_by_relocation'
            if is_suicide:
                if weapon.lower() == 'suicide_by_relocation':
                    weapon = 'Menu Suicide'
                elif weapon.lower() == 'falling':
                    weapon = 'Falling'
                    is_suicide = True
                else:
                    weapon = 'Suicide'

            # Parse distance
            try:
                if distance and distance != '':
                    distance_float = float(distance)
                else:
                    distance_float = 0.0
            except ValueError:
                distance_float = 0.0

            return {
                'timestamp': timestamp,
                'killer': killer,
                'victim': victim,
                'weapon': weapon,
                'distance': distance_float,
                'is_suicide': is_suicide
            }

        except Exception as e:
            logger.error(f"Error parsing CSV line: {e}")
            return {}
    def normalize_suicide_event(self, killer, victim, weapon):
        """Normalize suicide events"""
        is_suicide = killer == victim or weapon.lower() == 'suicide_by_relocation'
        if is_suicide:
            if weapon.lower() == 'suicide_by_relocation':
                weapon = 'Menu Suicide'
            elif weapon.lower() == 'falling':
                weapon = 'Falling'
            else:
                weapon = 'Suicide'
        return weapon, is_suicide

    async def get_sftp_connection(self, server_config: Dict[str, Any]) -> Optional[asyncssh.SSHClientConnection]:
        """Get or create SFTP connection with health checks and pooling"""
        try:
            server_key = f"{server_config['host']}:{server_config['port']}"
            
            if server_key in self.sftp_connections:
                conn = self.sftp_connections[server_key]
                if conn and not conn.is_closed():
                    return conn
                else:
                    # Remove dead connection
                    del self.sftp_connections[server_key]

            # Enhanced connection with multiple retry attempts
            max_retries = 3
            for attempt in range(1, max_retries + 1):
                try:
                    # Configure connection options with legacy support
                    options = {
                        'username': server_config['username'],
                        'password': server_config['password'],
                        'known_hosts': None,
                        'client_keys': None,
                        'preferred_auth': 'password,keyboard-interactive',
                        'kex_algs': [
                            'diffie-hellman-group14-sha256',
                            'diffie-hellman-group16-sha512',
                            'diffie-hellman-group18-sha512',
                            'diffie-hellman-group14-sha1',
                            'diffie-hellman-group1-sha1',
                            'diffie-hellman-group-exchange-sha256',
                            'diffie-hellman-group-exchange-sha1'
                        ],
                        'encryption_algs': [
                            'aes256-ctr', 'aes192-ctr', 'aes128-ctr',
                            'aes256-cbc', 'aes192-cbc', 'aes128-cbc',
                            '3des-cbc', 'blowfish-cbc'
                        ],
                        'mac_algs': [
                            'hmac-sha2-256', 'hmac-sha2-512',
                            'hmac-sha1', 'hmac-md5'
                        ]
                    }
                    
                    # Establish connection with timeout
                    logger.debug(f"SFTP connection attempt {attempt}/{max_retries} to {server_config['host']}:{server_config['port']}")
                    conn = await asyncio.wait_for(
                        asyncssh.connect(server_config['host'], port=server_config['port'], **options),
                        timeout=30
                    )

                    logger.info(f"Successfully connected to SFTP server {server_config['host']}")
                    self.sftp_connections[server_key] = conn
                    return conn

                except asyncio.TimeoutError:
                    logger.warning(f"SFTP connection timed out (attempt {attempt}/{max_retries})")
                except asyncssh.DisconnectError as e:
                    logger.warning(f"SFTP server disconnected: {e} (attempt {attempt}/{max_retries})")
                except Exception as e:
                    if 'Invalid DH parameters' in str(e):
                        logger.warning(f"DH parameters rejected, trying fallback options (attempt {attempt}/{max_retries})")
                    elif 'auth' in str(e).lower():
                        logger.error(f"SFTP authentication failed with provided credentials")
                        return None
                    else:
                        logger.warning(f"SFTP connection error: {e} (attempt {attempt}/{max_retries})")

                # Apply exponential backoff between retries
                if attempt < max_retries:
                    delay = 2 ** attempt
                    logger.debug(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)

            logger.error(f"Failed to connect to SFTP server after {max_retries} attempts")
            return None

        except Exception as e:
            logger.error(f"SFTP connection failed: {e}")
            return None
    async def get_sftp_csv_files(self, server_config: Dict[str, Any]) -> List[str]:
        """Get CSV files from SFTP server"""
        try:
            conn = await self.get_sftp_connection(server_config)
            if not conn:
                return []

            async with conn.start_sftp_client() as sftp:
                base_path = f"./{server_config['host']}_{server_config['server_id']}/actual1/deathlogs"
                
                try:
                    dirs = await sftp.listdir(base_path)
                    csv_files = []
                    
                    for dir_name in dirs:
                        dir_path = f"{base_path}/{dir_name}"
                        try:
                            files = await sftp.listdir(dir_path)
                            for file_name in files:
                                if file_name.endswith('.csv'):
                                    csv_files.append(f"{dir_path}/{file_name}")
                        except Exception:
                            continue
                    
                    return sorted(csv_files)
                    
                except Exception:
                    return []

        except Exception as e:
            logger.error(f"Error getting SFTP CSV files: {e}")
            return []

    async def process_kill_event(self, guild_id: int, server_id: str, kill_data: Dict[str, Any]):
        """Process a kill event and update database"""
        try:
            # Update database with kill event
            await self.bot.db_manager.record_kill_event(
                guild_id=guild_id,
                server_id=server_id,
                timestamp=kill_data['timestamp'],
                killer=kill_data['killer'],
                victim=kill_data['victim'],
                weapon=kill_data['weapon'],
                distance=kill_data['distance'],
                is_suicide=kill_data['is_suicide']
            )

        except Exception as e:
            logger.error(f"Error processing kill event: {e}")

    async def send_killfeed_embed(self, guild_id: int, server_id: str, kill_data: Dict[str, Any]):
        """Send killfeed embed to designated channel"""
        try:
            channel_data = await self.bot.db_manager.get_channel(guild_id, server_id, 'killfeed')
            if not channel_data:
                return

            channel = self.bot.get_channel(channel_data['channel_id'])
            if not channel:
                return

            # Create killfeed embed
            embed_factory = EmbedFactory(self.bot)
            embed = await EmbedFactory.create_killfeed_embed(kill_data, server_id)
            
            await channel.send(embed=embed)

        except Exception as e:
            logger.error(f"Error sending killfeed embed: {e}")

    async def parse_server_killfeed(self, guild_id: int, server_config: Dict[str, Any]):
        """Parse killfeed for a single server"""
        try:
            server_id = server_config['server_id']
            csv_files = await self.get_sftp_csv_files(server_config)
            
            if not csv_files:
                logger.info(f"⚠️ No CSV files found for server {server_id}")
                return
            
            logger.info(f"📁 Found {len(csv_files)} CSV files for server {server_id}")

            # Get most recent CSV file
            latest_file = csv_files[-1]
            server_key = f"{guild_id}:{server_id}"
            
            # Get last processed line count
            last_line_count = self.last_processed_lines.get(server_key, 0)
            
            # Read and parse CSV file
            conn = await self.get_sftp_connection(server_config)
            if not conn:
                return

            async with conn.start_sftp_client() as sftp:
                try:
                    async with sftp.open(latest_file, 'r') as f:
                        content = await f.read()
                        lines = content.strip().split('\n')
                        
                        # Skip header and previously processed lines
                        new_lines = lines[max(1, last_line_count):]
                        logger.info(f"📊 Processing {len(new_lines)} new lines (total: {len(lines)}, last processed: {last_line_count})")
                        
                        kill_count = 0
                        for line in new_lines:
                            if line.strip():
                                kill_data = self.parse_csv_line(line)
                                if kill_data:
                                    kill_count += 1
                                    await self.process_kill_event(guild_id, server_id, kill_data)
                                    await self.send_killfeed_embed(guild_id, server_id, kill_data)
                        
                        logger.info(f"🎯 Processed {kill_count} kill events from {latest_file}")
                        
                        # Update last processed line count
                        self.last_processed_lines[server_key] = len(lines)
                        
                except Exception as e:
                    logger.error(f"Error reading CSV file {latest_file}: {e}")

        except Exception as e:
            logger.error(f"Error parsing server killfeed: {e}")

    async def run_killfeed_parser(self):
        """Run killfeed parser for all configured servers"""
        try:
            # Get all servers with killfeed enabled
            servers = await self.bot.db_manager.get_all_servers_with_killfeed()
            logger.info(f"🔍 Killfeed parser: Found {len(servers)} servers with killfeed enabled")
            
            for server in servers:
                try:
                    server_name = server.get('name', 'Unknown')
                    logger.info(f"🔍 Processing killfeed for {server_name}")
                    await self.parse_server_killfeed(server['guild_id'], server)
                except Exception as e:
                    logger.error(f"Error parsing killfeed for server {server.get('server_id')}: {e}")

        except Exception as e:
            logger.error(f"Error in killfeed parser: {e}")

    def schedule_killfeed_parser(self):
        """Schedule killfeed parser to run every 300 seconds"""
        try:
            if hasattr(self.bot, 'scheduler'):
                self.bot.scheduler.add_job(
                    self.run_killfeed_parser,
                    'interval',
                    seconds=300,
                    id='killfeed_parser',
                    replace_existing=True
                )
                logger.info("Killfeed parser scheduled")
        except Exception as e:
            logger.error(f"Error scheduling killfeed parser: {e}")

    async def cleanup_sftp_connections(self):
        """Clean up idle SFTP connections"""
        try:
            for server_key, conn in list(self.sftp_connections.items()):
                try:
                    if conn and hasattr(conn, 'is_closed') and conn.is_closed():
                        del self.sftp_connections[server_key]
                    elif conn and hasattr(conn, '_transport') and conn._transport:
                        if hasattr(conn._transport, '_transport') and not conn._transport._transport:
                            del self.sftp_connections[server_key]
                except Exception:
                    del self.sftp_connections[server_key]
        except Exception as e:
            logger.error(f"Error cleaning up SFTP connections: {e}")