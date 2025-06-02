#!/usr/bin/env python3
"""
Emergency Casino Command Restoration
Fixes the professional_casino.py cog to restore /casino functionality
"""

import os
import re

def restore_casino_cog():
    """Restore professional_casino.py to working state"""
    file_path = 'bot/cogs/professional_casino.py'
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Find the class definition to add premium cache properly
        class_match = re.search(r'class\s+\w+\(discord\.Cog\):', content)
        if not class_match:
            print("Could not find class definition")
            return
        
        # Find the __init__ method and add premium cache
        init_pattern = r'(def __init__\(self, bot\):.*?self\.bot = bot)'
        init_match = re.search(init_pattern, content, re.DOTALL)
        
        if init_match:
            # Add premium cache initialization
            new_init = init_match.group(1) + '\n        self.premium_cache = {}'
            content = content.replace(init_match.group(1), new_init)
        
        # Remove any broken premium methods and add clean ones
        # Remove corrupted premium cache methods
        content = re.sub(r'async def refresh_premium_cache.*?return self\.premium_cache\.get\(guild_id, False\)', '', content, flags=re.DOTALL)
        
        # Add clean premium methods before the casino command
        premium_methods = '''
    async def refresh_premium_cache(self, guild_id: int):
        """Refresh premium status from database and cache it"""
        try:
            guild_config = await self.bot.db_manager.guilds.find_one({"guild_id": guild_id})
            if guild_config:
                has_premium_access = guild_config.get('premium_access', False)
                has_premium_servers = bool(guild_config.get('premium_servers', []))
                self.premium_cache[guild_id] = has_premium_access or has_premium_servers
            else:
                self.premium_cache[guild_id] = False
        except Exception as e:
            logger.error(f"Failed to refresh premium cache: {e}")
            self.premium_cache[guild_id] = False

    def check_premium_access(self, guild_id: int) -> bool:
        """Check premium access from cache (no database calls)"""
        return self.premium_cache.get(guild_id, False)
'''
        
        # Insert before casino command
        casino_pattern = r'(@discord\.slash_command\(name="casino")'
        content = re.sub(casino_pattern, premium_methods + r'\n    \1', content)
        
        # Fix any remaining syntax issues
        content = re.sub(r'guild_config = has_premium = self\.check_premium_access\(guild_id\)\}"?\)', 'guild_config = await self.bot.db_manager.guilds.find_one({"guild_id": guild_id})', content)
        
        # Ensure proper premium check in casino command
        casino_check_pattern = r'if not await self\.check_premium_access\(guild_id\):'
        if casino_check_pattern not in content:
            content = re.sub(
                r'(# Check premium access\s+)if not await.*?:',
                r'\1if not self.check_premium_access(guild_id):',
                content
            )
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Fixed professional_casino.py")
        
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")

if __name__ == "__main__":
    restore_casino_cog()
    print("🎉 Casino command restoration completed")