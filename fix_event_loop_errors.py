"""
Fix Event Loop Errors - Comprehensive solution for asyncio threading issues
Addresses "Future attached to a different loop" errors in the unified parser
"""

import os
import re

def fix_event_loop_errors():
    """Fix all event loop and threading issues in the unified parser"""
    
    # Fix 1: Update scalable_unified_processor to use proper thread-safe database access
    processor_file = "bot/utils/scalable_unified_processor.py"
    
    if os.path.exists(processor_file):
        with open(processor_file, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Replace direct database manager calls with thread-safe wrapper calls
        replacements = [
            # Fix guild database calls
            (
                r"await self\.bot\.db_manager\.get_guild\(",
                "await self._safe_db_call(self.bot.db_manager.get_guild, "
            ),
            # Fix player session database calls
            (
                r"await self\.bot\.db_manager\.player_sessions\.",
                "await self._safe_db_call(lambda: self.bot.db_manager.player_sessions."
            ),
            # Fix guild config database calls
            (
                r"await self\.bot\.db_manager\.guild_configs\.",
                "await self._safe_db_call(lambda: self.bot.db_manager.guild_configs."
            )
        ]
        
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)
        
        # Add thread-safe database call method
        if "_safe_db_call" not in content:
            safe_method = '''
    async def _safe_db_call(self, operation, *args, **kwargs):
        """Execute database operation safely across thread boundaries"""
        try:
            import asyncio
            
            # Get current loop
            try:
                current_loop = asyncio.get_running_loop()
            except RuntimeError:
                current_loop = None
            
            # If we have a bot with main loop and we're not in it
            if hasattr(self.bot, '_main_loop') and current_loop != self.bot._main_loop:
                if asyncio.iscoroutinefunction(operation):
                    future = asyncio.run_coroutine_threadsafe(
                        operation(*args, **kwargs),
                        self.bot._main_loop
                    )
                    return future.result(timeout=30)
                else:
                    return operation(*args, **kwargs)
            
            # We're in the correct loop
            if asyncio.iscoroutinefunction(operation):
                return await operation(*args, **kwargs)
            else:
                return operation(*args, **kwargs)
                
        except Exception as e:
            logger.error(f"Thread-safe database call failed: {e}")
            return None
'''
            
            # Insert the method before the first async method
            insert_pos = content.find("async def ")
            if insert_pos > 0:
                content = content[:insert_pos] + safe_method + "\n    " + content[insert_pos:]
        
        if content != original_content:
            with open(processor_file, 'w') as f:
                f.write(content)
            print(f"✅ Fixed event loop errors in {processor_file}")
    
    # Fix 2: Update main.py to store the main event loop reference
    main_file = "main.py"
    
    if os.path.exists(main_file):
        with open(main_file, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Add main loop storage in the on_ready method
        if "self._main_loop" not in content:
            # Find the on_ready method and add main loop storage
            on_ready_pattern = r"(async def on_ready\(self\):.*?\n)(.*?)(\n        # Initialize)"
            
            def add_main_loop(match):
                method_start = match.group(1)
                method_body = match.group(2)
                next_section = match.group(3)
                
                main_loop_code = """
        # Store main event loop for thread-safe operations
        import asyncio
        self._main_loop = asyncio.get_running_loop()
        logger.info("Main event loop stored for thread-safe operations")
"""
                
                return method_start + method_body + main_loop_code + next_section
            
            content = re.sub(on_ready_pattern, add_main_loop, content, flags=re.DOTALL)
        
        if content != original_content:
            with open(main_file, 'w') as f:
                f.write(content)
            print(f"✅ Added main loop storage to {main_file}")
    
    # Fix 3: Update threaded parser wrapper to handle loop boundaries properly
    wrapper_file = "bot/utils/threaded_parser_wrapper.py"
    
    if os.path.exists(wrapper_file):
        with open(wrapper_file, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Add loop isolation for threaded operations
        if "loop_isolation" not in content:
            isolation_code = """
    def _isolate_loop_operations(self, parser_method):
        \"\"\"Isolate parser operations to prevent loop conflicts\"\"\"
        import asyncio
        
        async def isolated_method():
            try:
                # Create new event loop for this thread if needed
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                return await parser_method()
                
            except Exception as e:
                logger.error(f"Isolated operation failed: {e}")
                raise
        
        return isolated_method
"""
            
            # Insert before the first method
            insert_pos = content.find("def ")
            if insert_pos > 0:
                content = content[:insert_pos] + isolation_code + "\n    " + content[insert_pos:]
        
        if content != original_content:
            with open(wrapper_file, 'w') as f:
                f.write(content)
            print(f"✅ Added loop isolation to {wrapper_file}")
    
    print("🔧 Event loop error fixes completed")

if __name__ == "__main__":
    fix_event_loop_errors()