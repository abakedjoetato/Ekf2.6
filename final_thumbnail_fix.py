#!/usr/bin/env python3
"""
Final comprehensive thumbnail standardization fix
Addresses all remaining embed thumbnail issues across the entire codebase
"""

import os
import re
from pathlib import Path

def fix_gambling_cog():
    """Fix all remaining gambling.py thumbnail implementations"""
    file_path = "bot/cogs/gambling.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern 1: Simple thumbnail with immediate response
    pattern1 = r'(\s+)embed\.set_thumbnail\(url="attachment://Gamble\.png"\)\s*\n(\s+)await\s+(interaction\.response\.edit_message|ctx\.respond|ctx\.edit|ctx\.followup\.send)\(embed=embed\)'
    
    def replacement1(match):
        indent = match.group(1)
        await_indent = match.group(2)
        method = match.group(3)
        return f'{indent}gamble_file = discord.File("./assets/Gamble.png", filename="Gamble.png")\n{indent}embed.set_thumbnail(url="attachment://Gamble.png")\n{await_indent}await {method}(embed=embed, file=gamble_file)'
    
    content = re.sub(pattern1, replacement1, content, flags=re.MULTILINE)
    
    # Pattern 2: Thumbnail with view parameter
    pattern2 = r'(\s+)embed\.set_thumbnail\(url="attachment://Gamble\.png"\)\s*\n(\s+)await\s+(interaction\.response\.edit_message|ctx\.respond|ctx\.edit)\(embed=embed,\s*view=([^)]+)\)'
    
    def replacement2(match):
        indent = match.group(1)
        await_indent = match.group(2)
        method = match.group(3)
        view = match.group(4)
        return f'{indent}gamble_file = discord.File("./assets/Gamble.png", filename="Gamble.png")\n{indent}embed.set_thumbnail(url="attachment://Gamble.png")\n{await_indent}await {method}(embed=embed, file=gamble_file, view={view})'
    
    content = re.sub(pattern2, replacement2, content, flags=re.MULTILINE)
    
    # Pattern 3: Thumbnail with ephemeral parameter
    pattern3 = r'(\s+)embed\.set_thumbnail\(url="attachment://Gamble\.png"\)\s*\n(\s+)await\s+(ctx\.respond)\(embed=embed,\s*ephemeral=True\)'
    
    def replacement3(match):
        indent = match.group(1)
        await_indent = match.group(2)
        method = match.group(3)
        return f'{indent}gamble_file = discord.File("./assets/Gamble.png", filename="Gamble.png")\n{indent}embed.set_thumbnail(url="attachment://Gamble.png")\n{await_indent}await {method}(embed=embed, file=gamble_file, ephemeral=True)'
    
    content = re.sub(pattern3, replacement3, content, flags=re.MULTILINE)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def fix_admin_channels():
    """Fix admin_channels.py dynamic thumbnail implementation"""
    file_path = "bot/cogs/admin_channels.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Fix dynamic thumbnail with file creation
    pattern = r'(\s+)embed\.set_thumbnail\(url=f"attachment://\{thumbnails\[channel_type\]\}"\)\s*\n(\s+)await\s+(ctx\.respond)\(embed=embed\)'
    
    def replacement(match):
        indent = match.group(1)
        await_indent = match.group(2)
        method = match.group(3)
        return f'{indent}thumb_file = discord.File(f"./assets/{{thumbnails[channel_type]}}", filename=thumbnails[channel_type])\n{indent}embed.set_thumbnail(url=f"attachment://{{thumbnails[channel_type]}}")\n{await_indent}await {method}(embed=embed, file=thumb_file)'
    
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def fix_automated_leaderboard():
    """Fix automated_leaderboard.py thumbnail reference"""
    file_path = "bot/cogs/automated_leaderboard.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Fix thumbnail_url in leaderboard embed data
    content = re.sub(
        r"'thumbnail_url': 'attachment://Leaderboard\.png'",
        "'thumbnail_url': 'attachment://Leaderboard.png'",
        content
    )
    
    # If there are embed sends without file attachments, fix them
    pattern = r"(\s+)embed\['thumbnail_url'\] = 'attachment://Leaderboard\.png'\s*\n(\s+)await\s+(channel\.send)\(embed=embed\)"
    
    def replacement(match):
        indent = match.group(1)
        await_indent = match.group(2)
        method = match.group(3)
        return f'{indent}leaderboard_file = discord.File("./assets/Leaderboard.png", filename="Leaderboard.png")\n{indent}embed[\'thumbnail_url\'] = \'attachment://Leaderboard.png\'\n{await_indent}await {method}(embed=embed, file=leaderboard_file)'
    
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def check_and_fix_any_remaining():
    """Check for any remaining attachment references without proper files"""
    cog_files = [
        "bot/cogs/stats.py",
        "bot/cogs/leaderboards_fixed.py", 
        "bot/parsers/unified_log_parser.py"
    ]
    
    fixes_made = 0
    
    for file_path in cog_files:
        if not os.path.exists(file_path):
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Generic fix for any remaining attachment URLs without file attachments
        # Look for set_thumbnail with attachment:// followed by send without file=
        pattern = r'(\s+)embed\.set_thumbnail\(url="attachment://([^"]+)"\)\s*\n(\s+)await\s+(channel\.send|ctx\.respond|ctx\.followup\.send)\(embed=embed\)'
        
        def replacement(match):
            indent = match.group(1)
            asset_name = match.group(2)
            await_indent = match.group(3)
            method = match.group(4)
            var_name = asset_name.split('.')[0].lower() + '_file'
            return f'{indent}{var_name} = discord.File("./assets/{asset_name}", filename="{asset_name}")\n{indent}embed.set_thumbnail(url="attachment://{asset_name}")\n{await_indent}await {method}(embed=embed, file={var_name})'
        
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            fixes_made += 1
            print(f"  ✅ Fixed remaining thumbnails in {file_path}")
    
    return fixes_made

if __name__ == "__main__":
    print("Applying final comprehensive thumbnail fixes...")
    
    fixes = 0
    
    if fix_gambling_cog():
        print("  ✅ Fixed gambling.py thumbnails")
        fixes += 1
    else:
        print("  ⚡ No changes needed in gambling.py")
        
    if fix_admin_channels():
        print("  ✅ Fixed admin_channels.py thumbnails") 
        fixes += 1
    else:
        print("  ⚡ No changes needed in admin_channels.py")
        
    if fix_automated_leaderboard():
        print("  ✅ Fixed automated_leaderboard.py thumbnails")
        fixes += 1
    else:
        print("  ⚡ No changes needed in automated_leaderboard.py")
    
    additional_fixes = check_and_fix_any_remaining()
    fixes += additional_fixes
    
    print(f"\n🎉 Final thumbnail standardization complete! Applied {fixes} additional fixes.")