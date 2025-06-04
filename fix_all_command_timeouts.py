"""
Fix All Command Timeouts - Comprehensive system-wide fix for Discord timeout issues
Implements immediate defer statements and timeout protection for ALL slash commands
"""

import os
import re
import asyncio

def fix_all_command_timeouts():
    """Fix timeout issues across all command files"""
    print("🔧 Implementing comprehensive command timeout fixes...")
    
    # Files containing slash commands
    command_files = [
        'bot/cogs/stats.py',
        'bot/cogs/linking.py', 
        'bot/cogs/admin_channels.py'
    ]
    
    fixes_applied = 0
    
    for file_path in command_files:
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            continue
            
        print(f"🔧 Processing {file_path}...")
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern to find slash command functions that need defer fixes
        pattern = r'(@discord\.slash_command[^)]*\)\s*(?:@[^\n]*\n)*\s*async def [^(]+\([^)]*\):[^{]*?\n\s*"""[^"]*"""\s*\n\s*)(try:\s*\n)'
        
        def add_defer_fix(match):
            """Add immediate defer statement after try block"""
            prefix = match.group(1)
            try_statement = match.group(2)
            
            # Check if defer is already present
            if 'await ctx.defer()' in prefix or 'await asyncio.wait_for(ctx.defer()' in prefix:
                return match.group(0)  # No change needed
            
            # Add import and immediate defer
            defer_fix = """import asyncio
        
        try:
            # Immediate defer to prevent Discord timeout
            await asyncio.wait_for(ctx.defer(), timeout=2.0)
            
"""
            return prefix + defer_fix
        
        # Apply the fix
        content = re.sub(pattern, add_defer_fix, content, flags=re.MULTILINE | re.DOTALL)
        
        # Also fix any ctx.respond calls to ctx.followup.send after defer
        content = re.sub(r'await ctx\.respond\(', 'await ctx.followup.send(', content)
        
        # Save if changes were made
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            fixes_applied += 1
            print(f"✅ Applied timeout fixes to {file_path}")
        else:
            print(f"ℹ️ No fixes needed for {file_path}")
    
    print(f"🎯 Timeout fixes applied to {fixes_applied} files")
    return fixes_applied

if __name__ == "__main__":
    fix_all_command_timeouts()