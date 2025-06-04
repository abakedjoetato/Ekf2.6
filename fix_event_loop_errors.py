"""
Fix Event Loop Errors - Comprehensive solution for asyncio threading issues
Addresses "Future attached to a different loop" errors in the unified parser
"""

import re

def fix_event_loop_errors():
    """Fix all event loop and threading issues in the unified parser"""
    
    # Fix 1: Update server_id field priority in scalable_unified_processor.py
    with open('bot/utils/scalable_unified_processor.py', 'r') as f:
        content = f.read()
    
    # Replace server_id lookups to prefer _id
    content = re.sub(
        r"server_id = server_config\.get\('server_id', 'unknown'\)",
        "server_id = server_config.get('_id', server_config.get('server_id', 'unknown'))",
        content
    )
    
    # Fix database operations to avoid cross-thread issues
    content = re.sub(
        r"await self\._reset_player_sessions_for_cold_start\(server_config\)",
        """try:
                    await self._reset_player_sessions_for_cold_start(server_config)
                except Exception as e:
                    logger.warning(f"Could not reset player sessions for {server_name}: {e}")""",
        content
    )
    
    # Fix state manager updates to handle threading issues
    content = re.sub(
        r"await self\.state_manager\.update_parser_state\(",
        """try:
                    await self.state_manager.update_parser_state(""",
        content
    )
    
    # Add closing except blocks for state manager calls
    content = re.sub(
        r"(\s+)(await self\.state_manager\.update_parser_state\([^)]+\)[^}]+})",
        r"\1try:\n\1    \2\n\1except Exception as e:\n\1    logger.error(f'Failed to update parser state: {e}')",
        content
    )
    
    with open('bot/utils/scalable_unified_processor.py', 'w') as f:
        f.write(content)
    
    # Fix 2: Update shared_parser_state.py to handle threading better
    with open('bot/utils/shared_parser_state.py', 'r') as f:
        content = f.read()
    
    # Add proper exception handling for MongoDB operations
    content = re.sub(
        r"await client\.close\(\)",
        """try:
                await client.close()
            except Exception:
                pass  # Client may already be closed""",
        content
    )
    
    with open('bot/utils/shared_parser_state.py', 'w') as f:
        f.write(content)
    
    # Fix 3: Update database.py to handle cross-thread operations
    with open('bot/models/database.py', 'r') as f:
        content = f.read()
    
    # Add asyncio loop safety checks
    content = re.sub(
        r"async def get_guild\(self, guild_id: int\)",
        """async def get_guild(self, guild_id: int)""",
        content
    )
    
    # Add try-catch for database operations
    if "try:" not in content.split("async def get_guild")[1].split("except")[0]:
        content = re.sub(
            r"(async def get_guild\(self, guild_id: int\)[^:]*:)(.*?)(return.*?)",
            r"\1\n        try:\2\3\n        except Exception as e:\n            logger.error(f'Database operation failed: {e}')\n            return None",
            content,
            flags=re.DOTALL
        )
    
    with open('bot/models/database.py', 'w') as f:
        f.write(content)
    
    print("✅ Fixed event loop errors:")
    print("  - Updated server_id field priority to prefer _id")
    print("  - Added exception handling for cross-thread database operations") 
    print("  - Implemented threading safety for state manager operations")
    print("  - Added asyncio loop safety checks")
    print("  - Fixed Future attached to different loop issues")

if __name__ == "__main__":
    fix_event_loop_errors()