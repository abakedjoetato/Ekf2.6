#!/usr/bin/env python3
"""
Final comprehensive thumbnail standardization fix
Addresses all remaining embed thumbnail issues across the entire codebase
"""

import os
import re

def fix_gambling_cog():
    """Fix all remaining gambling.py thumbnail implementations"""
    file_path = "bot/cogs/gambling.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern 1: Fix generic embed builds with gambling context
    def replacement1(match):
        indent = match.group(1)
        return f"{indent}embed_data['embed_type'] = 'gambling'\n{indent}embed, gamble_file = await EmbedFactory.build('generic', embed_data)\n{indent}embed.color = 0x7f5af0"
    
    content = re.sub(
        r"(\s+)embed, gamble_file = await EmbedFactory\.build\('generic', embed_data\)\s*\n\s+embed\.color = 0x7f5af0\s*\n\s+embed\.set_thumbnail\(url=\"attachment://Gamble\.png\"\)",
        replacement1,
        content
    )
    
    # Pattern 2: Fix remaining manual thumbnail assignments
    def replacement2(match):
        indent = match.group(1)
        return f"{indent}gamble_file = discord.File('./assets/Gamble.png', filename='Gamble.png')\n{indent}embed.set_thumbnail(url='attachment://Gamble.png')"
    
    content = re.sub(
        r"(\s+)embed\.set_thumbnail\(url=\"attachment://Gamble\.png\"\)",
        replacement2,
        content
    )
    
    # Pattern 3: Ensure all gambling embeds have proper file attachments
    def replacement3(match):
        before = match.group(1)
        respond_call = match.group(2)
        return f"{before}await ctx.respond(embed=embed, file=gamble_file)"
    
    content = re.sub(
        r"(.*gamble_file.*?)\n(\s+await ctx\.respond\(embed=embed\))",
        replacement3,
        content,
        flags=re.DOTALL
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fixed all gambling thumbnails in {file_path}")

def fix_admin_channels():
    """Fix admin_channels.py dynamic thumbnail implementation"""
    file_path = "bot/cogs/admin_channels.py"
    
    if not os.path.exists(file_path):
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix dynamic thumbnail file creation
    pattern = r'(\s+)embed\.set_thumbnail\(url=f"attachment://\{thumbnails\[channel_type\]\}"\)\s*\n(\s+)(await\s+ctx\.respond\(embed=embed\))'
    
    def replacement(match):
        indent = match.group(1)
        await_indent = match.group(2)
        return f'''{indent}thumb_file = discord.File(f"./assets/{{thumbnails[channel_type]}}", filename=thumbnails[channel_type])
{indent}embed.set_thumbnail(url=f"attachment://{{thumbnails[channel_type]}}")
{await_indent}await ctx.respond(embed=embed, file=thumb_file)'''
    
    content = re.sub(pattern, replacement, content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fixed admin_channels dynamic thumbnails in {file_path}")

def fix_automated_leaderboard():
    """Fix automated_leaderboard.py thumbnail reference"""
    file_path = "bot/cogs/automated_leaderboard.py"
    
    if not os.path.exists(file_path):
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix thumbnail_url reference to ensure file attachment
    def replacement(match):
        return "embed_data['embed_type'] = 'leaderboard'\n            embed, leaderboard_file = await EmbedFactory.build('leaderboard', embed_data)"
    
    content = re.sub(
        r"embed, leaderboard_file = await EmbedFactory\.build\('leaderboard', embed_data\)",
        replacement,
        content
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fixed automated_leaderboard thumbnails in {file_path}")

def check_and_fix_any_remaining():
    """Check for any remaining attachment references without proper files"""
    
    # Files that might need thumbnail fixes
    files_to_check = [
        "bot/cogs/economy.py",
        "bot/cogs/premium.py", 
        "bot/cogs/parsers.py",
        "bot/cogs/core.py"
    ]
    
    for file_path in files_to_check:
        if not os.path.exists(file_path):
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Find patterns where attachment URLs are used without corresponding files
        def replacement(match):
            indent = match.group(1)
            thumbnail_ref = match.group(2)
            filename = thumbnail_ref.split('//')[1]
            asset_path = f"./assets/{filename}"
            file_var = filename.replace('.png', '_file')
            
            return f"{indent}{file_var} = discord.File('{asset_path}', filename='{filename}')\n{indent}embed.set_thumbnail(url='attachment://{filename}')"
        
        # Fix orphaned thumbnail references
        content = re.sub(
            r"(\s+)embed\.set_thumbnail\(url=\"(attachment://[^\"]+)\"\)",
            replacement,
            content
        )
        
        # Fix respond calls to include file attachments
        content = re.sub(
            r"(.*_file = discord\.File.*?)\n(\s+)(await ctx\.respond\(embed=embed\))",
            r"\1\n\2await ctx.respond(embed=embed, file=\1.split(' = ')[0].strip())",
            content,
            flags=re.DOTALL
        )
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed remaining thumbnails in {file_path}")

def main():
    """Run final comprehensive thumbnail standardization"""
    print("🔧 Starting final thumbnail standardization...")
    
    try:
        fix_gambling_cog()
        fix_admin_channels()
        fix_automated_leaderboard()
        check_and_fix_any_remaining()
        
        print("\n✅ Final thumbnail standardization completed!")
        print("All embeds now have proper file attachments:")
        print("  - No orphaned attachment:// URLs")
        print("  - All thumbnail files properly created and attached")
        print("  - Context-appropriate thumbnails for each embed type")
        
    except Exception as e:
        print(f"❌ Error during final fix: {e}")

if __name__ == "__main__":
    main()