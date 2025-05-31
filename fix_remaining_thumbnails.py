#!/usr/bin/env python3
"""
Fix remaining thumbnail implementations in gambling.py and other cogs
"""

import os
import re

def fix_gambling_thumbnails():
    """Fix all gambling.py thumbnail implementations"""
    
    file_path = "bot/cogs/gambling.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Replace all standalone Gamble.png thumbnail references
    # Pattern: Look for embed.set_thumbnail followed by response/send without file attachment
    
    # Simple pattern for most cases
    pattern1 = r'(\s+)embed\.set_thumbnail\(url="attachment://Gamble\.png"\)\s*\n(\s+)await\s+(interaction\.response\.edit_message|ctx\.respond|ctx\.edit|ctx\.followup\.send)\(embed=embed\)'
    
    def replacement1(match):
        indent = match.group(1)
        await_indent = match.group(2)
        send_method = match.group(3)
        return f'{indent}gamble_file = discord.File("./assets/Gamble.png", filename="Gamble.png")\n{indent}embed.set_thumbnail(url="attachment://Gamble.png")\n{await_indent}await {send_method}(embed=embed, file=gamble_file)'
    
    content = re.sub(pattern1, replacement1, content, flags=re.MULTILINE)
    
    # Pattern with view parameter  
    pattern2 = r'(\s+)embed\.set_thumbnail\(url="attachment://Gamble\.png"\)\s*\n(\s+)await\s+(interaction\.response\.edit_message|ctx\.respond|ctx\.edit|ctx\.followup\.send)\(embed=embed,\s*view=([^)]+)\)'
    
    def replacement2(match):
        indent = match.group(1)
        await_indent = match.group(2)
        send_method = match.group(3)
        view_param = match.group(4)
        return f'{indent}gamble_file = discord.File("./assets/Gamble.png", filename="Gamble.png")\n{indent}embed.set_thumbnail(url="attachment://Gamble.png")\n{await_indent}await {send_method}(embed=embed, file=gamble_file, view={view_param})'
    
    content = re.sub(pattern2, replacement2, content, flags=re.MULTILINE)
    
    # Pattern with ephemeral parameter
    pattern3 = r'(\s+)embed\.set_thumbnail\(url="attachment://Gamble\.png"\)\s*\n(\s+)await\s+(ctx\.respond)\(embed=embed,\s*ephemeral=True\)'
    
    def replacement3(match):
        indent = match.group(1)
        await_indent = match.group(2)
        send_method = match.group(3)
        return f'{indent}gamble_file = discord.File("./assets/Gamble.png", filename="Gamble.png")\n{indent}embed.set_thumbnail(url="attachment://Gamble.png")\n{await_indent}await {send_method}(embed=embed, file=gamble_file, ephemeral=True)'
    
    content = re.sub(pattern3, replacement3, content, flags=re.MULTILINE)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Fixed gambling thumbnails in {file_path}")
        return True
    else:
        print(f"⚡ No changes needed in {file_path}")
        return False

def fix_admin_channels_thumbnails():
    """Fix admin_channels.py thumbnail implementations"""
    
    file_path = "bot/cogs/admin_channels.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Look for the dynamic thumbnail assignment
    pattern = r'(\s+)embed\.set_thumbnail\(url=f"attachment://\{thumbnails\[channel_type\]\}"\)\s*\n(\s+)await\s+(ctx\.respond)\(embed=embed\)'
    
    def replacement(match):
        indent = match.group(1)
        await_indent = match.group(2)
        send_method = match.group(3)
        # Add file creation based on channel_type
        return f'{indent}thumb_file = discord.File(f"./assets/{{thumbnails[channel_type]}}", filename=thumbnails[channel_type])\n{indent}embed.set_thumbnail(url=f"attachment://{{thumbnails[channel_type]}}")\n{await_indent}await {send_method}(embed=embed, file=thumb_file)'
    
    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Fixed admin_channels thumbnails in {file_path}")
        return True
    else:
        print(f"⚡ No changes needed in {file_path}")
        return False

if __name__ == "__main__":
    print("Fixing remaining thumbnail implementations...")
    
    fixes = 0
    if fix_gambling_thumbnails():
        fixes += 1
    if fix_admin_channels_thumbnails():
        fixes += 1
    
    print(f"\n🎉 Additional thumbnail fixes complete! Fixed {fixes} more files.")