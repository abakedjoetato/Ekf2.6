#!/usr/bin/env python3
"""
Systematic Discord.py to py-cord 2.6.1 Conversion
Fixes all syntax issues across the codebase
"""

import os
import re

def fix_cog_classes():
    """Fix all Cog class declarations to use discord.Cog"""
    files_to_fix = [
        'bot/cogs/core.py',
        'bot/cogs/admin_channels.py', 
        'bot/cogs/admin_batch.py',
        'bot/cogs/linking.py',
        'bot/cogs/stats.py',
        'bot/cogs/automated_leaderboard.py',
        'bot/cogs/economy.py',
        'bot/cogs/gambling_ultra_v2.py',
        'bot/cogs/bounties.py',
        'bot/cogs/factions.py',
        'bot/cogs/subscription_management.py',
        'bot/cogs/parsers.py',
        'bot/cogs/cache_management.py'
    ]
    
    for filepath in files_to_fix:
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                
                # Fix class declarations
                content = re.sub(r'class (\w+)\(commands\.Cog\)', r'class \1(discord.Cog)', content)
                
                # Fix slash command decorators
                content = re.sub(r'@commands\.slash_command', '@discord.slash_command', content)
                
                # Ensure discord import
                if 'import discord' not in content and 'from discord' in content:
                    content = 'import discord\n' + content
                
                with open(filepath, 'w') as f:
                    f.write(content)
                    
                print(f"Fixed {filepath}")
                    
            except Exception as e:
                print(f"Error fixing {filepath}: {e}")

def update_main_py():
    """Fix main.py Bot initialization"""
    try:
        with open('main.py', 'r') as f:
            content = f.read()
        
        # Fix Bot class usage
        content = re.sub(r'commands\.Bot\(', 'discord.Bot(', content)
        content = re.sub(r'from discord\.ext import commands', 'import discord\nimport discord
from discord.ext import commands', content)
        
        with open('main.py', 'w') as f:
            f.write(content)
            
        print("Fixed main.py")
        
    except Exception as e:
        print(f"Error fixing main.py: {e}")

def replace_gambling_system():
    """Replace old gambling system with new ultra-advanced casino"""
    try:
        # Update main.py to load the new casino instead
        with open('main.py', 'r') as f:
            content = f.read()
        
        # Replace gambling_ultra_v2 with ultra_casino_v3
        content = content.replace('bot.cogs.gambling_ultra_v2', 'bot.cogs.ultra_casino_v3')
        
        with open('main.py', 'w') as f:
            f.write(content)
            
        print("Updated main.py to use ultra_casino_v3")
        
    except Exception as e:
        print(f"Error updating gambling system: {e}")

if __name__ == "__main__":
    print("Starting systematic Discord.py syntax fixes...")
    fix_cog_classes()
    update_main_py()
    replace_gambling_system()
    print("Fixes complete!")