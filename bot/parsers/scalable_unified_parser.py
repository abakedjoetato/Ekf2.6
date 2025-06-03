"""
Scalable Unified Log Parser
Enterprise-grade unified log processing with Deadside.log focus, file rotation detection, and proper channel delivery
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from bot.utils.scalable_unified_processor import MultiGuildUnifiedProcessor, ScalableUnifiedProcessor
from bot.utils.shared_parser_state import get_shared_state_manager

logger = logging.getLogger(__name__)

class ScalableUnifiedParser:
    """Scalable unified parser with connection pooling and channel delivery integration"""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_sessions: Dict[int, ScalableUnifiedProcessor] = {}
        self.state_manager = get_shared_state_manager()
        self.activity_tracker = {}  # Track server activity levels
        self.last_activity_check = None
        
    async def run_log_parser(self):
        """Main scheduled unified log parser execution with adaptive scheduling"""
        try:
            logger.info("🔍 Starting scalable unified log parser run...")
            
            # Get all guilds with servers configured
            guild_configs = await self._get_all_guild_configs()
            
            if not guild_configs:
                logger.info("🔍 Scalable unified parser: Found 0 guilds with servers configured")
                return
            
            total_servers = sum(len(servers) for servers in guild_configs.values())
            logger.info(f"🔍 Scalable unified parser: Processing {len(guild_configs)} guilds with {total_servers} total servers")
            
            # Process all guilds using the multi-guild processor with activity tracking
            processor = MultiGuildUnifiedProcessor(self.bot)
            results = await processor.process_all_guilds(guild_configs)
            
            # Track activity levels for smart scheduling
            await self._update_activity_tracking(results)
            
            # Log summary with activity info
            activity_info = await self._get_activity_summary()
            logger.info(f"📊 Scalable unified parser completed: {results.get('successful_guilds', 0)}/{results.get('total_guilds', 0)} guilds, {results.get('processed_servers', 0)} servers processed, {results.get('rotated_servers', 0)} servers rotated{activity_info}")
            
            # Cleanup stale sessions periodically
            if self.state_manager:
                await self.state_manager.cleanup_stale_sessions()
            
        except Exception as e:
            logger.error(f"Scalable unified parser execution failed: {e}")
    
    async def _update_activity_tracking(self, results: Dict[str, Any]):
        """Update server activity tracking for smart scheduling"""
        try:
            current_time = datetime.now(timezone.utc)
            
            # Process guild results to track activity
            for guild_id, guild_result in results.get('guild_results', {}).items():
                for server_result in guild_result.get('server_results', {}).values():
                    server_id = server_result.get('server_id', 'unknown')
                    processed_kills = server_result.get('processed_kills', 0)
                    
                    # Initialize tracking for new servers
                    if server_id not in self.activity_tracker:
                        self.activity_tracker[server_id] = {
                            'recent_activity': [],
                            'avg_kills_per_hour': 0,
                            'last_active': None,
                            'activity_level': 'idle'  # idle, moderate, active, high
                        }
                    
                    # Record this parsing session
                    self.activity_tracker[server_id]['recent_activity'].append({
                        'timestamp': current_time,
                        'kills_processed': processed_kills
                    })
                    
                    # Keep only last 20 sessions for analysis (last hour of data)
                    self.activity_tracker[server_id]['recent_activity'] = \
                        self.activity_tracker[server_id]['recent_activity'][-20:]
                    
                    # Update activity metrics
                    if processed_kills > 0:
                        self.activity_tracker[server_id]['last_active'] = current_time
                    
                    # Calculate activity level
                    await self._calculate_activity_level(server_id)
            
            self.last_activity_check = current_time
            
        except Exception as e:
            logger.error(f"Failed to update activity tracking: {e}")
    
    async def _calculate_activity_level(self, server_id: str):
        """Calculate activity level for a server based on recent data"""
        try:
            tracker = self.activity_tracker[server_id]
            recent_sessions = tracker['recent_activity']
            
            if not recent_sessions:
                tracker['activity_level'] = 'idle'
                tracker['avg_kills_per_hour'] = 0
                return
            
            # Calculate kills per hour over recent sessions
            current_time = datetime.now(timezone.utc)
            one_hour_ago = current_time.replace(hour=current_time.hour-1) if current_time.hour > 0 else current_time.replace(day=current_time.day-1, hour=23)
            
            recent_kills = sum(
                session['kills_processed'] 
                for session in recent_sessions 
                if session['timestamp'] >= one_hour_ago
            )
            
            # Estimate kills per hour (3-minute intervals = 20 sessions per hour)
            sessions_in_hour = len([s for s in recent_sessions if s['timestamp'] >= one_hour_ago])
            if sessions_in_hour > 0:
                estimated_kills_per_hour = (recent_kills / sessions_in_hour) * 20
            else:
                estimated_kills_per_hour = 0
            
            tracker['avg_kills_per_hour'] = estimated_kills_per_hour
            
            # Classify activity level
            if estimated_kills_per_hour >= 60:  # 1+ kills per minute
                tracker['activity_level'] = 'high'
            elif estimated_kills_per_hour >= 20:  # 1 kill per 3 minutes
                tracker['activity_level'] = 'active'
            elif estimated_kills_per_hour >= 5:   # 1 kill per 12 minutes
                tracker['activity_level'] = 'moderate'
            else:
                tracker['activity_level'] = 'idle'
                
        except Exception as e:
            logger.error(f"Failed to calculate activity level for server {server_id}: {e}")
    
    async def _get_activity_summary(self) -> str:
        """Get a summary of current server activity levels"""
        try:
            if not self.activity_tracker:
                return ""
            
            activity_counts = {'high': 0, 'active': 0, 'moderate': 0, 'idle': 0}
            
            for tracker in self.activity_tracker.values():
                level = tracker.get('activity_level', 'idle')
                activity_counts[level] += 1
            
            if activity_counts['high'] > 0 or activity_counts['active'] > 0:
                return f" | Activity: {activity_counts['high']} high, {activity_counts['active']} active, {activity_counts['moderate']} moderate, {activity_counts['idle']} idle"
            else:
                return f" | Activity: {activity_counts['moderate']} moderate, {activity_counts['idle']} idle servers"
                
        except Exception:
            return ""
    
    def get_recommended_interval(self) -> int:
        """Get recommended parsing interval based on current activity levels"""
        try:
            if not self.activity_tracker:
                return 180  # Default 3 minutes
            
            activity_counts = {'high': 0, 'active': 0, 'moderate': 0, 'idle': 0}
            
            for tracker in self.activity_tracker.values():
                level = tracker.get('activity_level', 'idle')
                activity_counts[level] += 1
            
            # Smart interval selection
            if activity_counts['high'] > 0:
                return 60   # 1 minute for high activity servers
            elif activity_counts['active'] > 0:
                return 120  # 2 minutes for active servers
            elif activity_counts['moderate'] > 0:
                return 180  # 3 minutes for moderate activity
            else:
                return 300  # 5 minutes for idle servers only
                
        except Exception:
            return 180  # Safe default
    
    async def _get_all_guild_configs(self) -> Dict[int, List[Dict[str, Any]]]:
        """Get all guild configurations with servers"""
        guild_configs = {}
        
        try:
            # Access database through bot's db_manager
            if not hasattr(self.bot, 'db_manager') or not self.bot.db_manager:
                logger.error("Database manager not available")
                return guild_configs
            
            # Get the database connection
            if hasattr(self.bot.db_manager, 'get_database'):
                database = self.bot.db_manager.get_database()
            elif hasattr(self.bot.db_manager, 'database'):
                database = self.bot.db_manager.database
            elif hasattr(self.bot, 'database'):
                database = self.bot.database
            else:
                logger.error("Cannot access database")
                return guild_configs
            
            collection = database.guild_configs
            
            # Find all guilds with servers configured
            cursor = collection.find({
                'servers': {'$exists': True, '$not': {'$size': 0}}
            })
            
            async for guild_doc in cursor:
                guild_id = guild_doc.get('guild_id')
                servers = guild_doc.get('servers', [])
                
                if guild_id and servers:
                    # Add guild_id to each server config for processing
                    for server in servers:
                        server['guild_id'] = guild_id
                    
                    guild_configs[guild_id] = servers
            
        except Exception as e:
            logger.error(f"Failed to get guild configurations: {e}")
        
        return guild_configs
    
    async def process_guild_manual(self, guild_id: int) -> Dict[str, Any]:
        """Manually trigger unified processing for a specific guild"""
        try:
            # Get guild configuration
            guild_config = await self.bot.db_manager.get_guild(guild_id)
            if not guild_config or not guild_config.get('servers'):
                return {
                    'success': False,
                    'error': 'No servers configured for this guild'
                }
            
            servers = guild_config.get('servers', [])
            # Add guild_id to server configs
            for server in servers:
                server['guild_id'] = guild_id
            
            # Process guild
            processor = ScalableUnifiedProcessor(guild_id, self.bot)
            self.active_sessions[guild_id] = processor
            
            try:
                results = await processor.process_guild_servers(servers)
                return {
                    'success': True,
                    'guild_id': guild_id,
                    'results': results
                }
            finally:
                if guild_id in self.active_sessions:
                    del self.active_sessions[guild_id]
            
        except Exception as e:
            logger.error(f"Manual unified processing failed for guild {guild_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def process_server_manual(self, guild_id: int, server_name: str) -> Dict[str, Any]:
        """Manually trigger unified processing for a specific server"""
        try:
            # Get guild configuration
            guild_config = await self.bot.db_manager.get_guild(guild_id)
            if not guild_config or not guild_config.get('servers'):
                return {
                    'success': False,
                    'error': 'No servers configured for this guild'
                }
            
            # Find the specific server
            target_server = None
            for server in guild_config.get('servers', []):
                if server.get('name') == server_name or server.get('server_name') == server_name:
                    server['guild_id'] = guild_id
                    target_server = server
                    break
            
            if not target_server:
                return {
                    'success': False,
                    'error': f'Server {server_name} not found'
                }
            
            # Process single server
            processor = ScalableUnifiedProcessor(guild_id)
            results = await processor.process_guild_servers([target_server])
            
            return {
                'success': True,
                'server_name': server_name,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Manual server processing failed for {guild_id}/{server_name}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_processing_status(self, guild_id: int) -> Dict[str, Any]:
        """Get current processing status for a guild"""
        try:
            status = {
                'guild_id': guild_id,
                'active_session': guild_id in self.active_sessions,
                'servers_configured': 0,
                'historical_conflicts': 0
            }
            
            # Get guild configuration
            guild_config = await self.bot.db_manager.get_guild(guild_id)
            if guild_config and guild_config.get('servers'):
                status['servers_configured'] = len(guild_config['servers'])
                
                servers = []
                for server in guild_config['servers']:
                    server['guild_id'] = guild_id
                    servers.append(server)
                
                # Check for historical processing conflicts
                if self.state_manager and servers:
                    available_servers = await self.state_manager.get_available_servers_for_killfeed(servers)
                    status['historical_conflicts'] = len(servers) - len(available_servers)
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get processing status for guild {guild_id}: {e}")
            return {
                'guild_id': guild_id,
                'error': str(e)
            }
    
    async def cleanup_unified_connections(self):
        """Cleanup unified parser connections"""
        try:
            # Cancel any active sessions
            for guild_id, processor in list(self.active_sessions.items()):
                processor.cancel()
                del self.active_sessions[guild_id]
            
            logger.info("Cleaned up scalable unified parser connections")
            
        except Exception as e:
            logger.error(f"Failed to cleanup unified connections: {e}")
    
    def get_active_sessions(self) -> Dict[int, Any]:
        """Get currently active processing sessions"""
        return {
            guild_id: {
                'guild_id': guild_id,
                'active': True
            }
            for guild_id in self.active_sessions.keys()
        }