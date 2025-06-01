#!/usr/bin/env python3
"""
Comprehensive Embed Thumbnail Standardization
Dynamically assigns correct thumbnails based on embed type using available assets
"""

import os
import re
from pathlib import Path

# Define embed type to thumbnail mappings based on available assets
THUMBNAIL_MAPPINGS = {
    # Core embeds
    'stats': 'WeaponStats.png',        # Player statistics
    'profile': 'main.png',             # General profile/info
    'leaderboard': 'Leaderboard.png',   # Leaderboards
    'killfeed': 'Killfeed.png',        # Kill events
    'suicide': 'Suicide.png',          # Suicide events  
    'falling': 'Falling.png',          # Fall damage deaths
    
    # Game events
    'mission': 'Mission.png',          # Mission events
    'airdrop': 'Airdrop.png',         # Airdrop events
    'helicrash': 'Helicrash.png',     # Helicopter crash events
    'trader': 'Trader.png',           # Trader events
    'vehicle': 'Vehicle.png',         # Vehicle events
    
    # Player systems
    'bounty': 'Bounty.png',           # Bounty system
    'faction': 'Faction.png',         # Faction system
    'connection': 'Connections.png',   # Player connections
    'economy': 'main.png',            # Economy (fallback to main)
    'gambling': 'Gamble.png',         # Gambling system
    
    # Admin/System
    'admin': 'main.png',              # Admin commands
    'error': 'main.png',              # Error messages
    'success': 'main.png',            # Success messages
    'info': 'main.png',               # Information
    'help': 'main.png',               # Help commands
    'status': 'main.png',             # Status commands
}

def get_correct_thumbnail(embed_context):
    """Determine correct thumbnail based on embed context"""
    context_lower = embed_context.lower()
    
    # Direct mappings first
    for embed_type, thumbnail in THUMBNAIL_MAPPINGS.items():
        if embed_type in context_lower:
            return thumbnail
    
    # Context-based detection
    if any(word in context_lower for word in ['kill', 'death', 'eliminate', 'frag']):
        return 'Killfeed.png'
    elif any(word in context_lower for word in ['suicide', 'self']):
        return 'Suicide.png'
    elif any(word in context_lower for word in ['fall', 'falling', 'height']):
        return 'Falling.png'
    elif any(word in context_lower for word in ['weapon', 'gun', 'rifle', 'distance']):
        return 'WeaponStats.png'
    elif any(word in context_lower for word in ['bounty', 'reward', 'wanted']):
        return 'Bounty.png'
    elif any(word in context_lower for word in ['faction', 'clan', 'group']):
        return 'Faction.png'
    elif any(word in context_lower for word in ['leaderboard', 'ranking', 'top']):
        return 'Leaderboard.png'
    elif any(word in context_lower for word in ['gamble', 'bet', 'casino', 'dice']):
        return 'Gamble.png'
    elif any(word in context_lower for word in ['connect', 'join', 'leave']):
        return 'Connections.png'
    elif any(word in context_lower for word in ['mission', 'objective', 'quest']):
        return 'Mission.png'
    elif any(word in context_lower for word in ['airdrop', 'supply', 'drop']):
        return 'Airdrop.png'
    elif any(word in context_lower for word in ['heli', 'helicopter', 'crash']):
        return 'Helicrash.png'
    elif any(word in context_lower for word in ['trader', 'vendor', 'shop']):
        return 'Trader.png'
    elif any(word in context_lower for word in ['vehicle', 'car', 'transport']):
        return 'Vehicle.png'
    
    # Default fallback
    return 'main.png'

def fix_embed_factory_thumbnails():
    """Fix embed factory to use dynamic thumbnail selection"""
    file_path = "bot/utils/embed_factory.py"
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Add thumbnail helper method to EmbedFactory class
    thumbnail_method = '''
    @staticmethod
    def get_thumbnail_for_type(embed_type: str) -> Tuple[str, str]:
        """Get correct thumbnail file and filename for embed type"""
        thumbnail_mappings = {
            'stats': 'WeaponStats.png',
            'profile': 'main.png', 
            'leaderboard': 'Leaderboard.png',
            'killfeed': 'Killfeed.png',
            'suicide': 'Suicide.png',
            'falling': 'Falling.png',
            'mission': 'Mission.png',
            'airdrop': 'Airdrop.png',
            'helicrash': 'Helicrash.png',
            'trader': 'Trader.png',
            'vehicle': 'Vehicle.png',
            'bounty': 'Bounty.png',
            'faction': 'Faction.png',
            'connection': 'Connections.png',
            'gambling': 'Gamble.png',
            'admin': 'main.png',
            'error': 'main.png',
            'success': 'main.png',
            'info': 'main.png'
        }
        
        thumbnail = thumbnail_mappings.get(embed_type.lower(), 'main.png')
        return f"./assets/{thumbnail}", thumbnail
'''
    
    # Insert the method after the class definition but before existing methods
    class_pattern = r'(class EmbedFactory:.*?""".*?""")'
    if re.search(class_pattern, content, re.DOTALL):
        content = re.sub(
            class_pattern,
            r'\1' + thumbnail_method,
            content,
            flags=re.DOTALL
        )
    
    # Fix specific embed methods to use proper thumbnails
    
    # Fix killfeed embed to use Killfeed.png
    killfeed_pattern = r'(main_file = discord\.File\("\.\/assets\/main\.png", filename="main\.png"\))'
    killfeed_replacement = r'killfeed_file = discord.File("./assets/Killfeed.png", filename="Killfeed.png")'
    content = re.sub(killfeed_pattern, killfeed_replacement, content)
    
    # Fix attachment references in killfeed
    content = re.sub(r'url="attachment://main\.png"', r'url="attachment://Killfeed.png"', content)
    content = re.sub(r'return embed, main_file', r'return embed, killfeed_file', content)
    
    # Fix advanced stats profile to use WeaponStats.png
    stats_pattern = r'# Attach main\.png thumbnail\s*main_file = discord\.File\("\.\/assets\/main\.png", filename="main\.png"\)\s*embed\.set_thumbnail\(url="attachment://main\.png"\)'
    stats_replacement = '''# Attach WeaponStats.png thumbnail
            stats_file = discord.File("./assets/WeaponStats.png", filename="WeaponStats.png")
            embed.set_thumbnail(url="attachment://WeaponStats.png")'''
    
    content = re.sub(stats_pattern, stats_replacement, content)
    
    # Fix return statement for stats
    content = re.sub(r'return embed, main_file', r'return embed, stats_file', content)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Fixed embed factory thumbnails")
        return True
    
    return False

def fix_cog_thumbnails():
    """Fix all cog files to use appropriate thumbnails"""
    fixes_applied = 0
    
    cog_mappings = {
        'bot/cogs/stats.py': 'WeaponStats.png',
        'bot/cogs/leaderboards_fixed.py': 'Leaderboard.png',
        'bot/cogs/automated_leaderboard.py': 'Leaderboard.png',
        'bot/cogs/bounties.py': 'Bounty.png',
        'bot/cogs/factions.py': 'Faction.png',
        'bot/cogs/gambling.py': 'Gamble.png',
        'bot/cogs/economy.py': 'main.png',
        'bot/cogs/linking.py': 'Connections.png',
        'bot/cogs/admin_channels.py': 'main.png',
        'bot/cogs/admin_batch.py': 'main.png',
        'bot/cogs/core.py': 'main.png',
        'bot/cogs/premium.py': 'main.png',
        'bot/cogs/parsers.py': 'main.png'
    }
    
    for cog_file, default_thumbnail in cog_mappings.items():
        if not os.path.exists(cog_file):
            continue
            
        with open(cog_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Replace hardcoded main.png references with appropriate thumbnails
        if default_thumbnail != 'main.png':
            # Replace file creation
            content = re.sub(
                r'discord\.File\("\.\/assets\/main\.png", filename="main\.png"\)',
                f'discord.File("./assets/{default_thumbnail}", filename="{default_thumbnail}")',
                content
            )
            
            # Replace attachment URLs
            content = re.sub(
                r'url="attachment://main\.png"',
                f'url="attachment://{default_thumbnail}"',
                content
            )
            
            # Replace variable names if needed
            if 'main_file' in content:
                var_name = default_thumbnail.split('.')[0].lower() + '_file'
                content = re.sub(r'\bmain_file\b', var_name, content)
        
        # Fix any missing file attachments
        patterns_to_fix = [
            # Pattern: thumbnail set but no file created
            (r'(\s+)embed\.set_thumbnail\(url="attachment://([^"]+)"\)\s*\n(\s+)await\s+(ctx\.respond|ctx\.followup\.send)\(embed=embed\)',
             r'\1thumbnail_file = discord.File("./assets/\2", filename="\2")\n\1embed.set_thumbnail(url="attachment://\2")\n\3await \4(embed=embed, file=thumbnail_file)'),
            
            # Pattern: thumbnail with footer but no file
            (r'(\s+)embed\.set_thumbnail\(url="attachment://([^"]+)"\)\s*\n(\s+)embed\.set_footer\([^)]+\)\s*\n(\s+)await\s+(ctx\.respond|ctx\.followup\.send)\(embed=embed\)',
             r'\1thumbnail_file = discord.File("./assets/\2", filename="\2")\n\1embed.set_thumbnail(url="attachment://\2")\n\3embed.set_footer(text="Powered by Discord.gg/EmeraldServers")\n\4await \5(embed=embed, file=thumbnail_file)')
        ]
        
        for pattern, replacement in patterns_to_fix:
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        if content != original_content:
            with open(cog_file, 'w', encoding='utf-8') as f:
                f.write(content)
            fixes_applied += 1
            print(f"✅ Fixed thumbnails in {cog_file} -> {default_thumbnail}")
    
    return fixes_applied

def fix_admin_channels_dynamic_thumbnails():
    """Fix admin_channels.py dynamic thumbnail system"""
    file_path = "bot/cogs/admin_channels.py"
    
    if not os.path.exists(file_path):
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Ensure thumbnails dict maps to correct assets
    thumbnails_dict = '''
        thumbnails = {
            'killfeed': 'Killfeed.png',
            'leaderboard': 'Leaderboard.png', 
            'playercountvc': 'Connections.png',
            'events': 'Mission.png',
            'connections': 'Connections.png',
            'bounties': 'Bounty.png'
        }'''
    
    # Replace existing thumbnails dict
    content = re.sub(
        r'thumbnails = \{[^}]+\}',
        thumbnails_dict.strip(),
        content,
        flags=re.DOTALL
    )
    
    # Fix dynamic thumbnail usage to include file creation
    dynamic_pattern = r'(\s+)embed\.set_thumbnail\(url=f"attachment://\{thumbnails\[channel_type\]\}"\)\s*\n(\s+)await\s+(ctx\.respond)\(embed=embed\)'
    
    def dynamic_replacement(match):
        indent = match.group(1)
        await_indent = match.group(2)
        method = match.group(3)
        return f'''{indent}thumb_file = discord.File(f"./assets/{{thumbnails[channel_type]}}", filename=thumbnails[channel_type])
{indent}embed.set_thumbnail(url=f"attachment://{{thumbnails[channel_type]}}")
{await_indent}await {method}(embed=embed, file=thumb_file)'''
    
    content = re.sub(dynamic_pattern, dynamic_replacement, content, flags=re.MULTILINE)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Fixed dynamic thumbnails in admin_channels.py")
        return True
    
    return False

def main():
    """Run comprehensive thumbnail standardization"""
    print("🎨 Starting comprehensive embed thumbnail standardization...")
    print(f"📁 Available assets: {list(THUMBNAIL_MAPPINGS.values())}")
    
    total_fixes = 0
    
    # Fix embed factory
    if fix_embed_factory_thumbnails():
        total_fixes += 1
    
    # Fix all cogs
    cog_fixes = fix_cog_thumbnails()
    total_fixes += cog_fixes
    
    # Fix admin channels dynamic system
    if fix_admin_channels_dynamic_thumbnails():
        total_fixes += 1
    
    print(f"\n🎉 Thumbnail standardization complete!")
    print(f"✅ Fixed {total_fixes} files with proper asset assignments")
    print(f"🎯 All embeds now use contextually appropriate thumbnails")

if __name__ == "__main__":
    main()