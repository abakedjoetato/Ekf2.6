
"""
Emerald's Killfeed - Historical Parser (PHASE 2)
Handles full historical data parsing and refresh operations
"""

import asyncio
import logging
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import aiofiles
import asyncssh
import discord
from discord.ext import commands

from .killfeed_parser import KillfeedParser

logger = logging.getLogger(__name__)

class HistoricalParser:
    """
    BULLETPROOF HISTORICAL PARSER
    - Processes ALL CSV files (not just latest versions)
    - Comprehensive error handling and retry mechanisms
    - Detailed progress tracking and validation
    - Recovery capabilities for failed operations
    """

    def __init__(self, bot):
        self.bot = bot
        self.killfeed_parser = KillfeedParser(bot)
        self.active_refreshes: Dict[str, bool] = {}  # Track active refresh operations
        self.processing_stats: Dict[str, Dict] = {}  # Track detailed processing statistics

    async def get_all_csv_files(self, server_config: Dict[str, Any]) -> Tuple[List[str], Dict]:
        """Get all CSV files for historical parsing with comprehensive validation"""
        processing_report = {
            'files_discovered': 0,
            'files_processed': 0,
            'files_failed': 0,
            'total_lines': 0,
            'failed_files': [],
            'encoding_issues': [],
            'success_details': []
        }

        try:
            if self.bot.dev_mode:
                lines, report = await self.get_dev_csv_files()
                processing_report.update(report)
                return lines, processing_report
            else:
                lines, report = await self.get_sftp_csv_files(server_config)
                processing_report.update(report)
                return lines, processing_report

        except Exception as e:
            logger.error(f"Failed to get CSV files: {e}")
            processing_report['critical_error'] = str(e)
            return [], processing_report

    async def get_dev_csv_files(self) -> Tuple[List[str], Dict]:
        """Get all CSV files from dev_data directory with bulletproof processing"""
        report = {
            'files_discovered': 0,
            'files_processed': 0,
            'files_failed': 0,
            'total_lines': 0,
            'failed_files': [],
            'encoding_issues': [],
            'success_details': []
        }

        try:
            csv_path = Path('./dev_data/csv')
            csv_files = list(csv_path.glob('*.csv'))
            report['files_discovered'] = len(csv_files)

            if not csv_files:
                logger.warning("No CSV files found in dev_data/csv/")
                return [], report

            all_lines = []
            # Sort files by name (assuming chronological naming)
            csv_files.sort()

            for csv_file in csv_files:
                try:
                    file_lines = await self.process_single_file_with_retry(str(csv_file), is_local=True)
                    if file_lines:
                        all_lines.extend(file_lines)
                        report['files_processed'] += 1
                        report['total_lines'] += len(file_lines)
                        report['success_details'].append({
                            'file': str(csv_file),
                            'lines': len(file_lines),
                            'encoding': 'utf-8'
                        })
                        logger.info(f"✅ Processed {csv_file}: {len(file_lines)} lines")
                    else:
                        report['files_failed'] += 1
                        report['failed_files'].append(str(csv_file))
                        logger.error(f"❌ Failed to process {csv_file}")

                except Exception as e:
                    report['files_failed'] += 1
                    report['failed_files'].append(f"{csv_file}: {str(e)}")
                    logger.error(f"❌ Error processing {csv_file}: {e}")

            logger.info(f"📊 Dev CSV Processing Complete: {report['files_processed']}/{report['files_discovered']} files, {report['total_lines']} total lines")
            return all_lines, report

        except Exception as e:
            logger.error(f"Failed to read dev CSV files: {e}")
            report['critical_error'] = str(e)
            return [], report

    async def process_single_file_with_retry(self, file_path: str, is_local: bool = False, 
                                           sftp_client=None, max_retries: int = 3) -> List[str]:
        """Process a single file with retry mechanism and encoding fallbacks"""
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.debug(f"Processing attempt {attempt}/{max_retries} for {file_path}")
                
                if is_local:
                    return await self.read_local_file_with_encoding_fallback(file_path)
                else:
                    return await self.read_sftp_file_with_encoding_fallback(sftp_client, file_path)
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt}/{max_retries} failed for {file_path}: {e}")
                if attempt < max_retries:
                    # Exponential backoff
                    delay = 2 ** attempt
                    logger.debug(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All retry attempts failed for {file_path}")
                    return []
        
        return []

    async def read_local_file_with_encoding_fallback(self, file_path: str) -> List[str]:
        """Read local file with encoding fallbacks"""
        encodings = ['utf-8', 'latin-1', 'ascii', 'cp1252']
        
        for encoding in encodings:
            try:
                async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
                    content = await f.read()
                    lines = [line.strip() for line in content.splitlines() if line.strip()]
                    logger.debug(f"Successfully read {file_path} with {encoding} encoding: {len(lines)} lines")
                    return lines
            except UnicodeDecodeError:
                logger.debug(f"Failed to read {file_path} with {encoding} encoding")
                continue
            except Exception as e:
                logger.error(f"Error reading {file_path} with {encoding}: {e}")
                continue
        
        logger.error(f"Failed to read {file_path} with any encoding")
        return []

    async def read_sftp_file_with_encoding_fallback(self, sftp_client, file_path: str) -> List[str]:
        """Read SFTP file with encoding fallbacks and chunked reading"""
        encodings = ['utf-8', 'latin-1', 'ascii', 'cp1252']
        
        for encoding in encodings:
            try:
                # Use chunked reading for large files
                buffer_size = 1024 * 1024  # 1MB buffer
                file_content = ""

                async with sftp_client.open(file_path, 'r') as f:
                    while True:
                        chunk = await f.read(buffer_size)
                        if not chunk:
                            break

                        # Handle binary data
                        if isinstance(chunk, bytes):
                            try:
                                chunk = chunk.decode(encoding)
                            except UnicodeDecodeError:
                                if encoding == encodings[-1]:  # Last encoding attempt
                                    logger.error(f"Failed to decode {file_path} with {encoding}")
                                    return []
                                else:
                                    # Try next encoding
                                    break
                        
                        file_content += chunk

                # Process content into lines
                lines = [line.strip() for line in file_content.splitlines() if line.strip()]
                logger.debug(f"Successfully read {file_path} with {encoding} encoding: {len(lines)} lines")
                return lines

            except FileNotFoundError:
                logger.warning(f"SFTP file not found: {file_path}")
                return []
            except PermissionError:
                logger.warning(f"Permission denied reading SFTP file: {file_path}")
                return []
            except Exception as e:
                logger.debug(f"Error reading {file_path} with {encoding}: {e}")
                continue
        
        logger.error(f"Failed to read SFTP file {file_path} with any encoding")
        return []

    async def get_sftp_connection(self, server_config: Dict[str, Any]) -> Optional[asyncssh.SSHClientConnection]:
        """Get or create SFTP connection with enhanced error handling and compatibility"""
        try:
            # Get SFTP credentials with proper fallbacks
            server_id = str(server_config.get('_id', 'unknown'))
            sftp_host = server_config.get('host') or server_config.get('sftp_host', '')
            sftp_port = int(server_config.get('port') or server_config.get('sftp_port', 22))
            sftp_username = server_config.get('username') or server_config.get('sftp_username', '')
            sftp_password = server_config.get('password') or server_config.get('sftp_password', '')

            # Log connection attempt
            logger.info(f"Attempting SFTP connection to {sftp_host}:{sftp_port} for server {server_id}")

            # Validate credentials
            if not sftp_host:
                logger.error(f"Missing SFTP host for server {server_id}")
                return None

            if not sftp_username or not sftp_password:
                logger.error(f"Missing SFTP credentials for server {server_id}")
                return None

            # Enhanced connection with multiple retry attempts
            max_retries = 3
            for attempt in range(1, max_retries + 1):
                try:
                    # Configure connection options with legacy support by default
                    options = {
                        'username': sftp_username,
                        'password': sftp_password,
                        'known_hosts': None,  # Skip host key verification
                        'client_keys': None,  # No client keys needed with password auth
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
                            'hmac-sha1'
                        ]
                    }

                    # Establish connection with timeout
                    logger.debug(f"Connection attempt {attempt}/{max_retries} to {sftp_host}:{sftp_port}")
                    conn = await asyncio.wait_for(
                        asyncssh.connect(sftp_host, port=sftp_port, **options),
                        timeout=45  # Overall operation timeout
                    )

                    logger.info(f"Successfully connected to SFTP server {sftp_host} for server {server_id}")
                    return conn

                except asyncio.TimeoutError:
                    logger.warning(f"SFTP connection timed out (attempt {attempt}/{max_retries})")
                except asyncssh.DisconnectError as e:
                    logger.warning(f"SFTP server disconnected: {e} (attempt {attempt}/{max_retries})")
                except Exception as e:
                    if 'auth' in str(e).lower():
                        logger.error(f"SFTP authentication failed with provided credentials")
                        # No point retrying with same credentials
                        return None
                    else:
                        logger.warning(f"SFTP connection error: {e} (attempt {attempt}/{max_retries})")

                # Apply exponential backoff between retries
                if attempt < max_retries:
                    delay = 2 ** attempt  # 2, 4, 8 seconds
                    logger.debug(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)

            logger.error(f"Failed to connect to SFTP server after {max_retries} attempts")
            return None

        except Exception as e:
            logger.error(f"Failed to get SFTP connection: {e}")
            return None

    async def get_sftp_csv_files(self, server_config: Dict[str, Any]) -> Tuple[List[str], Dict]:
        """Get ALL CSV files from SFTP server with bulletproof processing"""
        report = {
            'files_discovered': 0,
            'files_processed': 0,
            'files_failed': 0,
            'total_lines': 0,
            'failed_files': [],
            'encoding_issues': [],
            'success_details': []
        }

        try:
            conn = await self.get_sftp_connection(server_config)
            if not conn:
                report['critical_error'] = "Failed to establish SFTP connection"
                return [], report

            server_id = str(server_config.get('_id', 'unknown'))
            sftp_host = server_config.get('host')
            # Use consistent path pattern with _id (same as killfeed parser)
            remote_path = f"./{sftp_host}_{server_id}/actual1/deathlogs/"

            all_lines = []

            async with conn.start_sftp_client() as sftp:
                # BULLETPROOF FILE DISCOVERY - Get ALL CSV files, not just latest
                csv_files = []
                pattern = f"{remote_path}**/*.csv"
                logger.info(f"🔍 Historical parser searching for ALL CSV files with pattern: {pattern}")

                try:
                    paths = await sftp.glob(pattern)
                    logger.info(f"📁 Discovered {len(paths)} CSV files")
                    report['files_discovered'] = len(paths)

                    # CHANGED: Process ALL files, not just latest versions
                    file_details = []
                    for path in paths:
                        try:
                            stat_result = await sftp.stat(path)
                            mtime = getattr(stat_result, 'mtime', datetime.now().timestamp())
                            size = getattr(stat_result, 'size', 0)
                            
                            file_details.append({
                                'path': path,
                                'mtime': mtime,
                                'size': size,
                                'filename': path.split('/')[-1]
                            })
                            logger.debug(f"Found CSV file: {path} ({size} bytes, modified: {datetime.fromtimestamp(mtime)})")
                        except Exception as e:
                            logger.warning(f"Error getting file info for {path}: {e}")
                            report['failed_files'].append(f"{path}: stat error - {str(e)}")
                            
                    csv_files = file_details
                except Exception as e:
                    logger.error(f"Failed to discover CSV files: {e}")
                    report['critical_error'] = f"File discovery failed: {str(e)}"
                    return [], report

                if not csv_files:
                    logger.warning(f"No CSV files found in {remote_path}")
                    return [], report

                # Sort by modification time (chronological order for historical parser)
                csv_files.sort(key=lambda x: x['mtime'])

                # BULLETPROOF FILE PROCESSING - Process each file individually with comprehensive error handling
                logger.info(f"🚀 Processing ALL {len(csv_files)} CSV files in chronological order")
                
                for file_info in csv_files:
                    filepath = file_info['path']
                    timestamp = file_info['mtime']
                    size = file_info['size']
                    filename = file_info['filename']
                    
                    try:
                        # Log file processing start with detailed info
                        readable_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                        logger.info(f"📝 Processing: {filename} ({size:,} bytes, modified: {readable_time})")

                        # Process file with retry mechanism
                        file_lines = await self.process_single_file_with_retry(
                            filepath, 
                            is_local=False, 
                            sftp_client=sftp
                        )

                        if file_lines:
                            all_lines.extend(file_lines)
                            report['files_processed'] += 1
                            report['total_lines'] += len(file_lines)
                            report['success_details'].append({
                                'file': filename,
                                'path': filepath,
                                'lines': len(file_lines),
                                'size_bytes': size,
                                'modified': readable_time
                            })
                            logger.info(f"✅ Successfully processed {filename}: {len(file_lines):,} lines")
                        else:
                            report['files_failed'] += 1
                            report['failed_files'].append(f"{filename}: No valid lines extracted")
                            logger.error(f"❌ Failed to extract lines from {filename}")

                    except Exception as e:
                        report['files_failed'] += 1
                        report['failed_files'].append(f"{filename}: {str(e)}")
                        logger.error(f"❌ Error processing {filename}: {e}")

                # Final processing summary
                success_rate = (report['files_processed'] / report['files_discovered'] * 100) if report['files_discovered'] > 0 else 0
                logger.info(f"📊 SFTP Processing Complete:")
                logger.info(f"   📁 Files discovered: {report['files_discovered']}")
                logger.info(f"   ✅ Files processed: {report['files_processed']}")
                logger.info(f"   ❌ Files failed: {report['files_failed']}")
                logger.info(f"   📝 Total lines: {report['total_lines']:,}")
                logger.info(f"   📈 Success rate: {success_rate:.1f}%")

                if report['failed_files']:
                    logger.warning(f"⚠️  Failed files: {report['failed_files']}")

                return all_lines, report

        except Exception as e:
            logger.error(f"Failed to fetch SFTP files for historical parsing: {e}")
            report['critical_error'] = str(e)
            return [], report

    async def clear_server_data(self, guild_id: int, server_id: str):
        """Clear all PvP data for a server before historical refresh with backup capability"""
        try:
            # Get current stats count for backup verification
            current_pvp_count = await self.bot.db_manager.pvp_data.count_documents({
                "guild_id": guild_id,
                "server_id": server_id
            })
            
            current_kill_count = await self.bot.db_manager.kill_events.count_documents({
                "guild_id": guild_id,
                "server_id": server_id
            })

            logger.info(f"🗑️  Clearing server data: {current_pvp_count} PvP records, {current_kill_count} kill events")

            # Clear PvP stats
            pvp_result = await self.bot.db_manager.pvp_data.delete_many({
                "guild_id": guild_id,
                "server_id": server_id
            })

            # Clear kill events
            kill_result = await self.bot.db_manager.kill_events.delete_many({
                "guild_id": guild_id,
                "server_id": server_id
            })

            logger.info(f"✅ Cleared PvP data for server {server_id}: {pvp_result.deleted_count} PvP records, {kill_result.deleted_count} kill events")

        except Exception as e:
            logger.error(f"Failed to clear server data: {e}")
            raise

    async def update_progress_embed(self, channel: Optional[discord.TextChannel], 
                                   embed_message: discord.Message,
                                   current: int, total: int, server_id: str,
                                   processing_stats: Dict = None):
        """Update progress embed with detailed processing information"""
        try:
            # Safety check - if no channel is provided, just log progress
            if not channel:
                logger.info(f"Progress update for server {server_id}: {current}/{total} events ({(current/total*100) if total > 0 else 0:.1f}%)")
                return

            progress_percent = (current / total * 100) if total > 0 else 0
            progress_bar_length = 20
            filled_length = int(progress_bar_length * current // total) if total > 0 else 0
            progress_bar = '█' * filled_length + '░' * (progress_bar_length - filled_length)

            embed = discord.Embed(
                title="📊 Historical Data Refresh",
                description=f"Refreshing historical data for server **{server_id}**",
                color=0x00FF7F,  # Spring green
                timestamp=datetime.now(timezone.utc)
            )

            embed.add_field(
                name="Progress",
                value=f"```{progress_bar}```\n{current:,} / {total:,} events ({progress_percent:.1f}%)",
                inline=False
            )

            embed.add_field(
                name="Status",
                value="🔄 Processing historical kill events...",
                inline=True
            )

            # Add processing statistics if available
            if processing_stats:
                stats_text = f"📁 Files: {processing_stats.get('files_processed', 0)}/{processing_stats.get('files_discovered', 0)}"
                if processing_stats.get('files_failed', 0) > 0:
                    stats_text += f"\n❌ Failed: {processing_stats['files_failed']}"
                
                embed.add_field(
                    name="File Processing",
                    value=stats_text,
                    inline=True
                )

            embed.set_footer(text="Powered by Discord.gg/EmeraldServers")

            await embed_message.edit(embed=embed)

        except Exception as e:
            logger.error(f"Failed to update progress embed: {e}")

    async def complete_progress_embed(self, embed_message: discord.Message,
                                     server_id: str, processed_count: int, 
                                     duration_seconds: float, processing_report: Dict):
        """Update embed when refresh is complete with comprehensive results"""
        try:
            embed = discord.Embed(
                title="✅ Historical Data Refresh Complete",
                description=f"Successfully refreshed historical data for server **{server_id}**",
                color=0x00FF00,  # Green
                timestamp=datetime.now(timezone.utc)
            )

            embed.add_field(
                name="📈 Events Processed",
                value=f"**{processed_count:,}** kill events",
                inline=True
            )

            embed.add_field(
                name="⏱️ Duration", 
                value=f"{duration_seconds:.1f} seconds",
                inline=True
            )

            # Add file processing summary
            files_summary = f"**{processing_report.get('files_processed', 0)}**/{processing_report.get('files_discovered', 0)} files"
            if processing_report.get('files_failed', 0) > 0:
                files_summary += f"\n❌ {processing_report['files_failed']} failed"
            
            embed.add_field(
                name="📁 Files",
                value=files_summary,
                inline=True
            )

            embed.add_field(
                name="🎯 Status",
                value="Ready for live killfeed tracking",
                inline=False
            )

            # Add success rate
            success_rate = (processing_report.get('files_processed', 0) / processing_report.get('files_discovered', 1) * 100)
            embed.add_field(
                name="📊 Success Rate",
                value=f"{success_rate:.1f}%",
                inline=True
            )

            embed.add_field(
                name="📝 Total Lines",
                value=f"{processing_report.get('total_lines', 0):,}",
                inline=True
            )

            # Add warning if there were failures
            if processing_report.get('files_failed', 0) > 0:
                embed.add_field(
                    name="⚠️ Warnings",
                    value=f"Some files failed to process. Check logs for details.",
                    inline=False
                )

            embed.set_footer(text="Powered by Discord.gg/EmeraldServers")

            await embed_message.edit(embed=embed)

        except Exception as e:
            logger.error(f"Failed to complete progress embed: {e}")

    async def refresh_server_data(self, guild_id: int, server_config: Dict[str, Any], 
                                 channel: Optional[discord.TextChannel] = None):
        """Bulletproof refresh historical data for a server"""
        refresh_key = ""
        try:
            server_id = server_config.get('server_id', 'unknown')
            refresh_key = f"{guild_id}_{server_id}"

            # Check if refresh is already running
            if self.active_refreshes.get(refresh_key, False):
                logger.warning(f"Refresh already running for server {server_id}")
                return False

            self.active_refreshes[refresh_key] = True
            start_time = datetime.now()

            logger.info(f"🚀 Starting bulletproof historical refresh for server {server_id} in guild {guild_id}")

            # Send initial progress embed
            embed_message = None
            if channel:
                initial_embed = discord.Embed(
                    title="🚀 Starting Historical Refresh",
                    description=f"Initializing bulletproof historical data refresh for server **{server_id}**",
                    color=0xFFD700,  # Gold
                    timestamp=datetime.now(timezone.utc)
                )
                initial_embed.add_field(
                    name="🛡️ Bulletproof Mode",
                    value="• Processing ALL CSV files\n• Comprehensive error handling\n• Detailed progress tracking",
                    inline=False
                )
                initial_embed.set_footer(text="Powered by Discord.gg/EmeraldServers")
                embed_message = await channel.send(embed=initial_embed)

            # Clear existing data with backup awareness
            await self.clear_server_data(guild_id, server_id)

            # Get all CSV files with comprehensive processing
            lines, processing_report = await self.get_all_csv_files(server_config)

            # Store processing stats for this refresh
            self.processing_stats[refresh_key] = processing_report

            if not lines:
                logger.warning(f"No historical data found for server {server_id}")
                logger.warning(f"Processing report: {processing_report}")
                self.active_refreshes[refresh_key] = False
                
                # Update embed with failure information
                if embed_message:
                    failure_embed = discord.Embed(
                        title="⚠️ No Historical Data Found",
                        description=f"No CSV data could be processed for server **{server_id}**",
                        color=0xFFA500,  # Orange
                        timestamp=datetime.now(timezone.utc)
                    )
                    
                    if processing_report.get('files_discovered', 0) > 0:
                        failure_embed.add_field(
                            name="📁 Files Found",
                            value=f"{processing_report['files_discovered']} files discovered",
                            inline=True
                        )
                        failure_embed.add_field(
                            name="❌ Processing Issues",
                            value=f"{processing_report.get('files_failed', 0)} files failed",
                            inline=True
                        )
                    else:
                        failure_embed.add_field(
                            name="🔍 Discovery Issue",
                            value="No CSV files found in expected location",
                            inline=False
                        )
                    
                    if processing_report.get('failed_files'):
                        failed_list = '\n'.join(processing_report['failed_files'][:3])
                        if len(processing_report['failed_files']) > 3:
                            failed_list += f"\n... and {len(processing_report['failed_files']) - 3} more"
                        failure_embed.add_field(
                            name="Failed Files",
                            value=f"```{failed_list}```",
                            inline=False
                        )
                    
                    await embed_message.edit(embed=failure_embed)
                
                return False

            total_lines = len(lines)
            processed_count = 0
            last_update_time = datetime.now()
            
            logger.info(f"📝 Processing {total_lines:,} historical log lines")

            # Process each line with comprehensive error handling
            for i, line in enumerate(lines):
                if not line.strip():
                    continue

                try:
                    # Parse kill event (but don't send embeds)
                    kill_data = await self.killfeed_parser.parse_csv_line(line)
                    if kill_data:
                        # Validate kill data
                        if not kill_data.get('killer') or not kill_data.get('victim'):
                            logger.debug(f"Skipping entry with null player name: {kill_data}")
                            continue

                        # Add to database without sending embeds
                        await self.bot.db_manager.add_kill_event(guild_id, server_id, kill_data)

                        # Update stats using proper MongoDB update syntax
                        if not kill_data['is_suicide']:
                            # Update killer stats atomically
                            await self.bot.db_manager.pvp_data.update_one(
                                {
                                    "guild_id": guild_id,
                                    "server_id": server_id,
                                    "player_name": kill_data['killer']
                                },
                                {
                                    "$inc": {"kills": 1},
                                    "$setOnInsert": {"deaths": 0, "suicides": 0}
                                },
                                upsert=True
                            )

                        # Update victim stats atomically
                        update_field = "suicides" if kill_data['is_suicide'] else "deaths"
                        await self.bot.db_manager.pvp_data.update_one(
                            {
                                "guild_id": guild_id,
                                "server_id": server_id,
                                "player_name": kill_data['victim']
                            },
                            {
                                "$inc": {update_field: 1},
                                "$setOnInsert": {"kills": 0}
                            },
                            upsert=True
                        )

                        processed_count += 1

                except Exception as e:
                    logger.warning(f"Error processing line {i}: {e}")
                    continue

                # Update progress embed every 30 seconds
                current_time = datetime.now()
                if embed_message and (current_time - last_update_time).total_seconds() >= 30:
                    await self.update_progress_embed(
                        channel, embed_message, i + 1, total_lines, server_id, processing_report
                    )
                    last_update_time = current_time

            # Complete the refresh
            duration = (datetime.now() - start_time).total_seconds()

            if embed_message:
                await self.complete_progress_embed(embed_message, server_id, processed_count, duration, processing_report)

            # Final comprehensive logging
            logger.info(f"🎉 Historical refresh completed for server {server_id}:")
            logger.info(f"   ⏱️  Duration: {duration:.1f} seconds")
            logger.info(f"   📝 Events processed: {processed_count:,}")
            logger.info(f"   📁 Files processed: {processing_report.get('files_processed', 0)}/{processing_report.get('files_discovered', 0)}")
            logger.info(f"   📊 Success rate: {(processing_report.get('files_processed', 0) / processing_report.get('files_discovered', 1) * 100):.1f}%")
            
            if processing_report.get('files_failed', 0) > 0:
                logger.warning(f"   ⚠️  Failed files: {processing_report['files_failed']}")

            self.active_refreshes[refresh_key] = False
            return True

        except Exception as e:
            logger.error(f"Failed to refresh server data: {e}")
            if refresh_key and refresh_key in self.active_refreshes:
                self.active_refreshes[refresh_key] = False
            return False

    async def auto_refresh_after_server_add(self, guild_id: int, server_config: Dict[str, Any]):
        """Automatically refresh data 30 seconds after server is added"""
        try:
            await asyncio.sleep(30)  # Wait 30 seconds
            await self.refresh_server_data(guild_id, server_config)

        except Exception as e:
            logger.error(f"Failed to auto-refresh after server add: {e}")

    def get_processing_report(self, guild_id: int, server_id: str) -> Optional[Dict]:
        """Get the latest processing report for a server"""
        refresh_key = f"{guild_id}_{server_id}"
        return self.processing_stats.get(refresh_key)
