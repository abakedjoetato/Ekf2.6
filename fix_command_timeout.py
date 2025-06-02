#!/usr/bin/env python3
"""
Fix Command Timeout Issues
Fixes database access patterns and response handling in admin_channels.py
"""

import re

def fix_admin_channels():
    """Fix all issues in admin_channels.py"""
    
    with open("bot/cogs/admin_channels.py", "r") as f:
        content = f.read()
    
    original_content = content
    
    # Fix all remaining database access patterns
    content = re.sub(
        r'guild_config = await self\.bot\.db_manager\.get_guild\(guild_id\)',
        r'guild_config = await self.bot.db_manager.guilds.find_one({"guild_id": guild_id})',
        content
    )
    
    # Fix remaining .db.guilds patterns
    content = re.sub(
        r'self\.bot\.db_manager\.db\.guilds\.',
        r'self.bot.db_manager.guilds.',
        content
    )
    
    # Fix guild_id type issues
    content = re.sub(
        r'guild_id = \(ctx\.guild\.id if ctx\.guild else None\)',
        r'guild_id = ctx.guild.id if ctx.guild else 0',
        content
    )
    
    if content != original_content:
        with open("bot/cogs/admin_channels.py", "w") as f:
            f.write(content)
        print("✅ Fixed admin_channels.py database access patterns")
    else:
        print("ℹ️ No changes needed in admin_channels.py")

if __name__ == "__main__":
    fix_admin_channels()