#!/usr/bin/env python3
"""
Comprehensive thumbnail standardization script for Emerald's Killfeed Discord Bot
Fixes all embed thumbnail implementations to use proper file attachments
"""

import os
import re
from pathlib import Path

def fix_thumbnail_implementations():
    """Fix all thumbnail implementations across all cog files"""
    
    # Define the cog files to process
    cog_files = [
        "bot/cogs/core.py",
        "bot/cogs/bounties.py", 
        "bot/cogs/economy.py",
        "bot/cogs/factions.py",
        "bot/cogs/linking.py",
        "bot/cogs/premium.py",
        "bot/cogs/parsers.py",
        "bot/cogs/gambling.py",
        "bot/cogs/stats.py",
        "bot/cogs/leaderboards_fixed.py",
        "bot/cogs/admin_channels.py",
        "bot/cogs/admin_batch.py",
        "bot/cogs/automated_leaderboard.py"
    ]
    
    # Asset mappings for proper thumbnails
    asset_mappings = {
        'main.png': 'main.png',
        'Bounty.png': 'Bounty.png', 
        'Faction.png': 'Faction.png',
        'Gamble.png': 'Gamble.png',
        'WeaponStats.png': 'WeaponStats.png',
        'Leaderboard.png': 'Leaderboard.png',
        'Connections.png': 'Connections.png'
    }
    
    fixes_applied = 0
    
    for cog_file in cog_files:
        if not os.path.exists(cog_file):
            continue
            
        print(f"Processing {cog_file}...")
        
        with open(cog_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix main.png thumbnails
        content = fix_main_thumbnails(content)
        
        # Fix bounty thumbnails  
        content = fix_bounty_thumbnails(content)
        
        # Fix faction thumbnails
        content = fix_faction_thumbnails(content)
        
        # Fix other asset thumbnails
        content = fix_other_thumbnails(content)
        
        # Write back if changes were made
        if content != original_content:
            with open(cog_file, 'w', encoding='utf-8') as f:
                f.write(content)
            fixes_applied += 1
            print(f"  ✅ Fixed thumbnails in {cog_file}")
        else:
            print(f"  ⚡ No changes needed in {cog_file}")
    
    print(f"\n🎉 Thumbnail standardization complete! Fixed {fixes_applied} files.")

def fix_main_thumbnails(content):
    """Fix main.png thumbnail implementations"""
    
    # Pattern 1: Basic main.png thumbnail without file attachment
    pattern1 = r'(\s+)embed\.set_thumbnail\(url="attachment://main\.png"\)\s*\n(\s+)embed\.set_footer\([^)]+\)\s*\n\s*await\s+(ctx\.respond|ctx\.followup\.send|channel\.send)\(embed=embed\)'
    
    def replacement1(match):
        indent = match.group(1)
        footer_indent = match.group(2) 
        send_method = match.group(3)
        return f'{indent}main_file = discord.File("./assets/main.png", filename="main.png")\n{indent}embed.set_thumbnail(url="attachment://main.png")\n{footer_indent}embed.set_footer(text="Powered by Discord.gg/EmeraldServers")\n\n{footer_indent}await {send_method}(embed=embed, file=main_file)'
    
    content = re.sub(pattern1, replacement1, content, flags=re.MULTILINE)
    
    # Pattern 2: Simple main.png cases
    pattern2 = r'(\s+)embed\.set_thumbnail\(url="attachment://main\.png"\)\s*\n\s*await\s+(ctx\.respond|ctx\.followup\.send)\(embed=embed\)'
    
    def replacement2(match):
        indent = match.group(1)
        send_method = match.group(2)
        return f'{indent}main_file = discord.File("./assets/main.png", filename="main.png")\n{indent}embed.set_thumbnail(url="attachment://main.png")\n\n{indent}await {send_method}(embed=embed, file=main_file)'
    
    content = re.sub(pattern2, replacement2, content, flags=re.MULTILINE)
    
    return content

def fix_bounty_thumbnails(content):
    """Fix Bounty.png thumbnail implementations"""
    
    # Pattern for bounty thumbnails
    pattern = r'(\s+)embed\.set_thumbnail\(url="attachment://Bounty\.png"\)\s*\n(\s+)embed\.set_footer\([^)]+\)\s*\n\s*await\s+(ctx\.respond|ctx\.followup\.send|channel\.send)\(embed=embed\)'
    
    def replacement(match):
        indent = match.group(1)
        footer_indent = match.group(2)
        send_method = match.group(3)
        return f'{indent}bounty_file = discord.File("./assets/Bounty.png", filename="Bounty.png")\n{indent}embed.set_thumbnail(url="attachment://Bounty.png")\n{footer_indent}embed.set_footer(text="Powered by Discord.gg/EmeraldServers")\n\n{footer_indent}await {send_method}(embed=embed, file=bounty_file)'
    
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    return content

def fix_faction_thumbnails(content):
    """Fix Faction.png thumbnail implementations"""
    
    # Pattern for faction thumbnails
    pattern = r'(\s+)embed\.set_thumbnail\(url="attachment://Faction\.png"\)\s*\n(\s+)embed\.set_footer\([^)]+\)\s*\n\s*await\s+(ctx\.respond|ctx\.followup\.send|channel\.send)\(embed=embed\)'
    
    def replacement(match):
        indent = match.group(1)
        footer_indent = match.group(2)
        send_method = match.group(3)
        return f'{indent}faction_file = discord.File("./assets/Faction.png", filename="Faction.png")\n{indent}embed.set_thumbnail(url="attachment://Faction.png")\n{footer_indent}embed.set_footer(text="Powered by Discord.gg/EmeraldServers")\n\n{footer_indent}await {send_method}(embed=embed, file=faction_file)'
    
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    return content

def fix_other_thumbnails(content):
    """Fix other asset thumbnail implementations"""
    
    # Handle remaining attachment references without proper files
    assets = ['Gamble.png', 'WeaponStats.png', 'Leaderboard.png', 'Connections.png']
    
    for asset in assets:
        asset_var = asset.split('.')[0].lower() + '_file'
        pattern = f'(\\s+)embed\\.set_thumbnail\\(url="attachment://{re.escape(asset)}"\\)\\s*\\n(\\s+)embed\\.set_footer\\([^)]+\\)\\s*\\n\\s*await\\s+(ctx\\.respond|ctx\\.followup\\.send|channel\\.send)\\(embed=embed\\)'
        
        def replacement(match):
            indent = match.group(1)
            footer_indent = match.group(2)
            send_method = match.group(3)
            return f'{indent}{asset_var} = discord.File("./assets/{asset}", filename="{asset}")\n{indent}embed.set_thumbnail(url="attachment://{asset}")\n{footer_indent}embed.set_footer(text="Powered by Discord.gg/EmeraldServers")\n\n{footer_indent}await {send_method}(embed=embed, file={asset_var})'
        
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    return content

if __name__ == "__main__":
    fix_thumbnail_implementations()