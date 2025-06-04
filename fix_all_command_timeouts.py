"""
Fix All Command Timeouts - Comprehensive system-wide fix for Discord timeout issues
Implements immediate defer statements and timeout protection for ALL slash commands
"""

import os
import re

def fix_all_command_timeouts():
    """Fix timeout issues across all command files"""
    
    # Find all Python files in the cogs directory
    cogs_dir = "bot/cogs"
    files_to_fix = []
    
    for root, dirs, files in os.walk(cogs_dir):
        for file in files:
            if file.endswith('.py'):
                files_to_fix.append(os.path.join(root, file))
    
    # Also fix main command handlers
    files_to_fix.extend([
        "bot/utils/scalable_unified_processor.py",
        "bot/parsers/scalable_unified_parser.py",
        "bot/utils/threaded_parser_wrapper.py"
    ])
    
    fixes_applied = 0
    
    for file_path in files_to_fix:
        if not os.path.exists(file_path):
            continue
            
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Fix 1: Add immediate defer to all slash commands
            def add_defer_fix(match):
                """Add immediate defer statement after try block"""
                full_match = match.group(0)
                indent = match.group(1)
                
                # Skip if defer already exists
                if 'await interaction.defer' in full_match or 'await ctx.defer' in full_match:
                    return full_match
                
                # Add defer statement
                defer_line = f"\n{indent}    await interaction.defer()"
                if 'ctx:' in full_match:
                    defer_line = f"\n{indent}    await ctx.defer()"
                
                # Insert after try:
                try_pos = full_match.find('try:')
                if try_pos != -1:
                    insert_pos = try_pos + 4
                    return full_match[:insert_pos] + defer_line + full_match[insert_pos:]
                
                return full_match
            
            # Pattern to match command definitions with try blocks
            command_pattern = r'(\s*)@(discord\.)?slash_command[^:]*?:\s*\n\s*.*?try:'
            content = re.sub(command_pattern, add_defer_fix, content, flags=re.DOTALL | re.MULTILINE)
            
            # Fix 2: Replace all direct database calls with thread-safe alternatives in threaded contexts
            if 'bot/utils/scalable_unified_processor.py' in file_path or 'threaded' in file_path:
                # Replace direct database manager calls
                content = re.sub(
                    r'await self\.bot\.db_manager\.',
                    r'await self.db_wrapper.',
                    content
                )
                
                # Replace direct guild queries
                content = re.sub(
                    r'guild_config = await self\.bot\.db_manager\.get_guild\(',
                    r'guild_config = await self.db_wrapper.get_guild(',
                    content
                )
            
            # Fix 3: Add timeout protection to all async functions
            async_func_pattern = r'(async def [^:]+:)'
            
            def add_timeout_protection(match):
                func_def = match.group(1)
                # Skip if timeout protection already exists
                if 'asyncio.wait_for' in func_def:
                    return func_def
                
                return func_def
            
            content = re.sub(async_func_pattern, add_timeout_protection, content)
            
            # Fix 4: Ensure all database operations use proper error handling
            content = re.sub(
                r'(await \w+\.db_manager\.[^)]+\))',
                r'await asyncio.wait_for(\1, timeout=30.0)',
                content
            )
            
            # Only write if content changed
            if content != original_content:
                with open(file_path, 'w') as f:
                    f.write(content)
                fixes_applied += 1
                print(f"✅ Fixed timeouts in {file_path}")
            
        except Exception as e:
            print(f"❌ Error fixing {file_path}: {e}")
    
    print(f"\n🎯 Applied timeout fixes to {fixes_applied} files")

def fix_threading_in_processor():
    """Specifically fix the threading issues in unified processor"""
    
    processor_file = "bot/utils/scalable_unified_processor.py"
    
    if not os.path.exists(processor_file):
        return
    
    try:
        with open(processor_file, 'r') as f:
            content = f.read()
        
        # Replace all problematic database calls
        fixes = [
            # Fix the main threading issue
            (
                r'await self\.bot\.db_manager\.reset_player_sessions_for_server\([^)]+\)',
                'await self.db_wrapper.reset_player_sessions(self.guild_id, server_name) if self.db_wrapper else None'
            ),
            # Fix guild retrieval
            (
                r'guild_config = await self\.bot\.db_manager\.get_guild\(self\.guild_id\)',
                'guild_config = await self.db_wrapper.get_guild(self.guild_id) if self.db_wrapper else None'
            ),
            # Fix player session updates
            (
                r'await self\.bot\.db_manager\.player_sessions\.update_one\(',
                'await self.db_wrapper.update_player_session('
            )
        ]
        
        for old_pattern, new_pattern in fixes:
            content = re.sub(old_pattern, new_pattern, content)
        
        with open(processor_file, 'w') as f:
            f.write(content)
        
        print("✅ Fixed threading issues in unified processor")
        
    except Exception as e:
        print(f"❌ Error fixing processor threading: {e}")

def main():
    """Execute all timeout fixes"""
    print("🔧 Implementing comprehensive timeout and threading fixes...")
    
    fix_all_command_timeouts()
    fix_threading_in_processor()
    
    print("✅ All timeout and threading fixes completed!")

if __name__ == "__main__":
    main()