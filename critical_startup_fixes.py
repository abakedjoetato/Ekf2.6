#!/usr/bin/env python3
"""
Critical Startup Fixes - Resolves syntax errors preventing bot startup
"""
import re

def fix_database_issues():
    """Fix critical database syntax issues"""
    filepath = "bot/models/database.py"
    
    with open(filepath, 'r') as file:
        content = file.read()
    
    # Fix database collection references that were corrupted
    fixes = [
        # Fix bot_config and premium_limits references back to collections
        (r'getattr\(self, "bot_config", \{\}\)\.replace_one', 'self.bot_config.replace_one'),
        (r'getattr\(self, "bot_config", \{\}\)\.find_one', 'self.bot_config.find_one'),
        (r'getattr\(self, "premium_limits", \{\}\)\.update_one', 'self.premium_limits.update_one'),
        (r'getattr\(self, "premium_limits", \{\}\)\.find_one', 'self.premium_limits.find_one'),
        
        # Fix None assignments to datetime parameters
        (r'updated_at=datetime\.now\(timezone\.utc\)', 'updated_at=datetime.now(timezone.utc)'),
        
        # Fix missing arguments
        (r'self\.increment_player_kill\(killer, victim, datetime\.now\(timezone\.utc\)\)', 
         'self.increment_player_kill(killer, victim, datetime.now(timezone.utc))'),
    ]
    
    for old, new in fixes:
        content = re.sub(old, new, content)
    
    # Add missing collections initialization if not present
    if 'self.bot_config = self.db.bot_config' not in content:
        content = content.replace(
            'self.leaderboard_messages = self.db.leaderboard_messages',
            'self.leaderboard_messages = self.db.leaderboard_messages\n        self.bot_config = self.db.bot_config\n        self.premium_limits = self.db.premium_limits'
        )
    
    with open(filepath, 'w') as file:
        file.write(content)
    
    print("✅ Fixed database.py")

def fix_premium_modal_values():
    """Fix premium cog modal value access"""
    filepath = "bot/cogs/premium.py"
    
    with open(filepath, 'r') as file:
        content = file.read()
    
    # Revert problematic modal value fixes to simpler working versions
    fixes = [
        # Fix modal value access
        (r'serverid = getattr\(modal\.children\[0\], "value", ""\)\.strip\(\) if modal\.children and len\(modal\.children\) > 0 else ""',
         'serverid = modal.children[0].value.strip() if modal.children and len(modal.children) > 0 and modal.children[0].value else ""'),
        (r'name = getattr\(modal\.children\[1\], "value", ""\)\.strip\(\) if modal\.children and len\(modal\.children\) > 1 else ""',
         'name = modal.children[1].value.strip() if modal.children and len(modal.children) > 1 and modal.children[1].value else ""'),
        (r'host_port = getattr\(modal\.children\[2\], "value", ""\)\.strip\(\) if modal\.children and len\(modal\.children\) > 2 else ""',
         'host_port = modal.children[2].value.strip() if modal.children and len(modal.children) > 2 and modal.children[2].value else ""'),
        (r'username = getattr\(modal\.children\[3\], "value", ""\)\.strip\(\) if modal\.children and len\(modal\.children\) > 3 else ""',
         'username = modal.children[3].value.strip() if modal.children and len(modal.children) > 3 and modal.children[3].value else ""'),
        (r'password = getattr\(modal\.children\[4\], "value", ""\)\.strip\(\) if modal\.children and len\(modal\.children\) > 4 else ""',
         'password = modal.children[4].value.strip() if modal.children and len(modal.children) > 4 and modal.children[4].value else ""'),
    ]
    
    for old, new in fixes:
        content = re.sub(old, new, content)
    
    with open(filepath, 'w') as file:
        file.write(content)
    
    print("✅ Fixed premium.py")

def fix_parsers_cog():
    """Fix parsers cog undefined variables"""
    filepath = "bot/cogs/parsers.py"
    
    with open(filepath, 'r') as file:
        content = file.read()
    
    # Fix undefined lines variable
    content = re.sub(
        r'for line in lines:',
        'lines = content.strip().split("\\n") if content else []\n        for line in lines:',
        content
    )
    
    with open(filepath, 'w') as file:
        file.write(content)
    
    print("✅ Fixed parsers.py")

def main():
    """Execute critical startup fixes"""
    print("🔧 Applying critical startup fixes...")
    
    try:
        fix_database_issues()
        fix_premium_modal_values()
        fix_parsers_cog()
        
        print("\n✅ Critical startup fixes completed!")
        print("🚀 Bot should now start successfully")
        
    except Exception as e:
        print(f"❌ Error during fixes: {e}")
        raise

if __name__ == "__main__":
    main()