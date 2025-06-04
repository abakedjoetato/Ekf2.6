"""
Threaded Parser Wrapper - Moves heavy parser operations to background threads
Eliminates command timeouts by keeping the main event loop responsive
"""

import asyncio
import logging
from typing import Any, Callable, Dict, Optional
from bot.utils.task_pool import dispatch_background, dispatch_background_with_lock

logger = logging.getLogger(__name__)

class ThreadedParserWrapper:
    """Wrapper that moves parser operations to background threads"""
    
    def __init__(self, parser_instance):
        self.parser = parser_instance
        self.parser_name = parser_instance.__class__.__name__
        
    async def run_parser_threaded(self, guild_id: int = None) -> bool:
        """Run parser in background thread with proper error handling"""
        
        # Create unique lock key for this parser and guild
        lock_key = f"{self.parser_name}_{guild_id or 'global'}"
        task_id = f"{self.parser_name}_run_{guild_id or 'global'}"
        
        try:
            logger.info(f"🔄 Starting {self.parser_name} in background thread...")
            
            # Run parser in background thread with deduplication
            result = await dispatch_background_with_lock(
                self._sync_parser_run,
                lock_key=lock_key,
                task_id=task_id,
                timeout=300  # 5 minute timeout for parser operations
            )
            
            logger.info(f"✅ {self.parser_name} completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"❌ {self.parser_name} failed: {e}")
            return False
    
    def _sync_parser_run(self) -> bool:
        """Synchronous parser execution for thread pool with proper event loop handling"""
        
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Handle different parser types
                if hasattr(self.parser, 'run_log_parser'):
                    # For ScalableUnifiedParser
                    loop.run_until_complete(self.parser.run_log_parser())
                elif hasattr(self.parser, 'run_killfeed_parser'):
                    # For ScalableKillfeedParser
                    loop.run_until_complete(self.parser.run_killfeed_parser())
                elif hasattr(self.parser, 'process_historical_data'):
                    # For HistoricalParser
                    loop.run_until_complete(self.parser.process_historical_data())
                else:
                    logger.warning(f"Unknown parser type: {self.parser_name}")
                    return False
                    
                return True
                
            finally:
                loop.close()
            
        except Exception as e:
            logger.error(f"Sync parser execution failed: {e}")
            return False

class ThreadedSFTPOperations:
    """Thread-safe SFTP operations wrapper"""
    
    @staticmethod
    async def connect_sftp_threaded(connection_config: Dict[str, Any]) -> Any:
        """Establish SFTP connection in background thread"""
        
        return await dispatch_background(
            ThreadedSFTPOperations._sync_sftp_connect,
            connection_config,
            task_id=f"sftp_connect_{connection_config.get('host', 'unknown')}",
            timeout=30
        )
    
    @staticmethod
    def _sync_sftp_connect(connection_config: Dict[str, Any]) -> Any:
        """Synchronous SFTP connection for thread pool"""
        
        import asyncssh
        
        async def _async_connect():
            try:
                connection = await asyncssh.connect(
                    host=connection_config['host'],
                    port=connection_config.get('port', 22),
                    username=connection_config['username'],
                    password=connection_config.get('password'),
                    known_hosts=None
                )
                return connection
            except Exception as e:
                logger.error(f"SFTP connection failed: {e}")
                raise
        
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(_async_connect())
        finally:
            loop.close()
    
    @staticmethod
    async def read_file_threaded(sftp_client, file_path: str) -> str:
        """Read file content in background thread"""
        
        return await dispatch_background(
            ThreadedSFTPOperations._sync_file_read,
            sftp_client,
            file_path,
            task_id=f"file_read_{file_path.split('/')[-1]}",
            timeout=60
        )
    
    @staticmethod
    def _sync_file_read(sftp_client, file_path: str) -> str:
        """Synchronous file reading for thread pool"""
        
        async def _async_read():
            try:
                async with sftp_client.open(file_path, 'r') as f:
                    return await f.read()
            except Exception as e:
                logger.error(f"File read failed for {file_path}: {e}")
                raise
        
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(_async_read())
        finally:
            loop.close()

class ThreadedDatabaseOperations:
    """Thread-safe database operations wrapper"""
    
    @staticmethod
    async def bulk_write_threaded(collection, operations: list) -> bool:
        """Perform bulk database writes in background thread"""
        
        return await dispatch_background(
            ThreadedDatabaseOperations._sync_bulk_write,
            collection,
            operations,
            task_id=f"bulk_write_{len(operations)}_ops",
            timeout=120
        )
    
    @staticmethod
    def _sync_bulk_write(collection, operations: list) -> bool:
        """Synchronous bulk write for thread pool"""
        
        async def _async_write():
            try:
                if operations:
                    result = await collection.bulk_write(operations)
                    return result.acknowledged
                return True
            except Exception as e:
                logger.error(f"Bulk write failed: {e}")
                raise
        
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(_async_write())
        finally:
            loop.close()
    
    @staticmethod
    async def aggregate_threaded(collection, pipeline: list) -> list:
        """Perform database aggregation in background thread"""
        
        return await dispatch_background(
            ThreadedDatabaseOperations._sync_aggregate,
            collection,
            pipeline,
            task_id=f"aggregate_{len(pipeline)}_stages",
            timeout=180
        )
    
    @staticmethod
    def _sync_aggregate(collection, pipeline: list) -> list:
        """Synchronous aggregation for thread pool using sync MongoDB operations"""
        
        try:
            # Use synchronous PyMongo operations instead of motor async operations
            # Convert motor collection to pymongo collection for sync operations
            sync_collection = collection.with_options(codec_options=collection.codec_options)
            
            # Perform synchronous aggregation
            cursor = sync_collection.aggregate(pipeline)
            return list(cursor)
            
        except Exception as e:
            logger.error(f"Sync aggregation failed: {e}")
            # Fallback: return empty list to prevent blocking
            return []

# Factory function for creating threaded parser wrappers
def create_threaded_parser(parser_instance) -> ThreadedParserWrapper:
    """Create a threaded wrapper for any parser instance"""
    return ThreadedParserWrapper(parser_instance)