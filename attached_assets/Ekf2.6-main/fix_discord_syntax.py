#!/usr/bin/env python3
"""
Mass Discord.py to py-cord 2.6.1 Syntax Converter
Fixes the 1000+ syntax issues found in the audit
"""

import os
import re

def fix_file_syntax(filepath):
    """Fix Discord.py syntax in a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False
    
    original_content = content
    
    # Primary fixes for py-cord 2.6.1
    conversions = [
        # Core command system
        (r'from discord\.ext import commands', 'import discord\nfrom discord.ext import commands'),
        (r'class (\w+)\(commands\.Cog\)', r'class \1(discord.Cog)'),
        (r'commands\.slash_command', 'discord.slash_command'),
        (r'@commands\.slash_command', '@discord.slash_command'),
        (r'@bot\.slash_command', '@discord.slash_command'),
        (r'commands\.ApplicationContext', 'discord.ApplicationContext'),
        
        # UI Components
        (r'discord\.ui\.TextInput', 'discord.ui.InputText'),
        
        # Bot initialization
        (r'commands\.Bot\(', 'discord.Bot('),
        (r'bot\.add_cog\((\w+)\(bot\)\)', r'bot.add_cog(\1(bot))'),
        
        # Context and options
        (r'@discord\.option\(', '@discord.option('),
        (r'discord\.Option\(', 'discord.Option('),
        
        # Views and interactions
        (r'discord\.ui\.View\(', 'discord.ui.View('),
        (r'discord\.ui\.Modal\(', 'discord.ui.Modal('),
        (r'discord\.ui\.button\(', 'discord.ui.button('),
        (r'@discord\.ui\.button', '@discord.ui.button'),
    ]
    
    changes_made = 0
    for old_pattern, new_pattern in conversions:
        new_content = re.sub(old_pattern, new_pattern, content)
        if new_content != content:
            changes_made += len(re.findall(old_pattern, content))
            content = new_content
    
    # Only write if changes were made
    if content != original_content:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed {changes_made} issues in {filepath}")
            return True
        except Exception as e:
            print(f"Error writing {filepath}: {e}")
            return False
    
    return False

def fix_codebase():
    """Fix Discord.py syntax across the entire codebase"""
    
    # Focus on the main bot files first
    priority_files = [
        'main.py',
        'bot/cogs/gambling_ultra_v2.py',
        'bot/cogs/economy.py',
        'bot/cogs/factions.py',
        'bot/cogs/stats.py',
        'bot/cogs/core.py',
        'bot/cogs/admin_channels.py',
        'bot/cogs/admin_batch.py',
        'bot/cogs/linking.py',
        'bot/cogs/bounties.py',
        'bot/cogs/automated_leaderboard.py',
        'bot/cogs/subscription_management.py',
        'bot/cogs/parsers.py',
        'bot/cogs/cache_management.py',
        'bot/cogs/leaderboards_fixed.py'
    ]
    
    fixed_files = 0
    total_changes = 0
    
    for filepath in priority_files:
        if os.path.exists(filepath):
            if fix_file_syntax(filepath):
                fixed_files += 1
    
    print(f"\nFixed {fixed_files} priority files")
    
    # Fix remaining bot files
    for root, dirs, files in os.walk('bot'):
        if '__pycache__' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if filepath not in [f"bot/{f.split('/')[-1]}" for f in priority_files]:
                    if fix_file_syntax(filepath):
                        fixed_files += 1
    
    print(f"Total files fixed: {fixed_files}")
    return fixed_files

if __name__ == "__main__":
    fix_codebase()