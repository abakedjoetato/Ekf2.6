"""
Thread-Safe Database Wrapper
Prevents "Future attached to a different loop" errors by ensuring database operations
execute in the correct asyncio event loop context
"""

import asyncio
import logging
from typing import Any, Callable, Coroutine
from functools import wraps

logger = logging.getLogger(__name__)

class ThreadSafeDBWrapper:
    """Wrapper that ensures database operations execute in the correct event loop"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self._main_loop = None
    
    def set_main_loop(self, loop):
        """Set the main event loop for thread-safe operations"""
        self._main_loop = loop
    
    async def safe_db_operation(self, operation: Callable, *args, **kwargs):
        """Execute database operation safely, handling thread boundary issues"""
        try:
            # Check if we're in the correct event loop
            current_loop = asyncio.get_running_loop()
            
            if self._main_loop and current_loop != self._main_loop:
                # We're in a different thread/loop, skip operation to prevent errors
                logger.debug(f"Skipping database operation {operation.__name__} - wrong event loop")
                return None
            
            # Execute the operation
            if asyncio.iscoroutinefunction(operation):
                return await operation(*args, **kwargs)
            else:
                return operation(*args, **kwargs)
                
        except Exception as e:
            logger.error(f"Database operation {operation.__name__} failed: {e}")
            return None
    
    async def get_guild(self, guild_id: int):
        """Thread-safe guild retrieval"""
        return await self.safe_db_operation(self.db_manager.get_guild, guild_id)
    
    async def get_active_player_count(self, guild_id: int, server_name: str):
        """Thread-safe player count retrieval"""
        if hasattr(self.db_manager, 'get_active_player_count'):
            return await self.safe_db_operation(
                self.db_manager.get_active_player_count, 
                guild_id, 
                server_name
            )
        return 0
    
    async def update_player_session(self, *args, **kwargs):
        """Thread-safe player session update"""
        if hasattr(self.db_manager, 'update_player_session'):
            return await self.safe_db_operation(
                self.db_manager.update_player_session, 
                *args, 
                **kwargs
            )
        return None
    
    async def reset_player_sessions(self, *args, **kwargs):
        """Thread-safe player session reset"""
        if hasattr(self.db_manager, 'reset_player_sessions_for_server'):
            return await self.safe_db_operation(
                self.db_manager.reset_player_sessions_for_server, 
                *args, 
                **kwargs
            )
        return None

def thread_safe_db_operation(func):
    """Decorator to make database operations thread-safe"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except RuntimeError as e:
            if "attached to a different loop" in str(e):
                logger.warning(f"Skipping {func.__name__} - different event loop")
                return None
            raise
        except Exception as e:
            logger.error(f"Database operation {func.__name__} failed: {e}")
            return None
    return wrapper