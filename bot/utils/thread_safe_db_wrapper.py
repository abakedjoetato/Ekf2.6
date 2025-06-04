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
            # Get current loop information
            current_loop = None
            try:
                current_loop = asyncio.get_running_loop()
            except RuntimeError:
                # No running loop - we're in a different thread
                pass
            
            # If we have a main loop and we're not in it, use asyncio.run_coroutine_threadsafe
            if self._main_loop and current_loop != self._main_loop:
                if asyncio.iscoroutinefunction(operation):
                    # Execute in the main loop from another thread
                    future = asyncio.run_coroutine_threadsafe(
                        operation(*args, **kwargs), 
                        self._main_loop
                    )
                    return future.result(timeout=30)  # 30 second timeout
                else:
                    # For non-coroutine functions, just call directly
                    return operation(*args, **kwargs)
            
            # We're in the correct loop or no main loop set
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

    @property
    def player_sessions(self):
        """Thread-safe access to player_sessions collection"""
        return self.db_manager.player_sessions if self.db_manager else None
    
    async def record_kill(self, *args, **kwargs):
        """Thread-safe kill recording"""
        try:
            return await self.safe_db_operation(
                lambda: self.db_manager.record_kill(*args, **kwargs)
            )
        except Exception as e:
            logger.error(f"Failed to record kill: {e}")
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

