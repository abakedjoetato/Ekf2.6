#!/usr/bin/env python3
"""
Fix All Database Attribute Errors
Comprehensive fix for all database connection and attribute issues
"""

import os
import re

def fix_all_database_attribute_errors():
    """Fix all database attribute errors across the codebase"""
    
    fixes_applied = []
    
    # Fix main.py database connection issues
    main_py_path = "main.py"
    if os.path.exists(main_py_path):
        with open(main_py_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Fix database manager admin access
        content = content.replace(
            "await self.db_manager.admin.command('ping')",
            "await self.mongo_client.admin.command('ping')"
        )
        
        # Fix all self.bot.db_manager references
        content = re.sub(
            r'self\.bot\.db_manager',
            'self.db_manager',
            content
        )
        
        if content != original_content:
            with open(main_py_path, 'w') as f:
                f.write(content)
            fixes_applied.append("main.py - Fixed database manager references")
    
    # Fix stats.py database access patterns
    stats_py_path = "bot/cogs/stats.py"
    if os.path.exists(stats_py_path):
        with open(stats_py_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Fix database access patterns
        content = re.sub(
            r'self\.bot\.db_manager\.([a-zA-Z_]+)\.find\(',
            r'self.bot.db_manager.\1.find(',
            content
        )
        
        if content != original_content:
            with open(stats_py_path, 'w') as f:
                f.write(content)
            fixes_applied.append("bot/cogs/stats.py - Fixed database access patterns")
    
    # Fix all files with database manager attribute errors
    files_to_fix = [
        "bot/parsers/unified_log_parser.py",
        "bot/parsers/killfeed_parser.py", 
        "bot/parsers/historical_parser.py",
        "bot/cogs/economy.py",
        "bot/cogs/professional_casino.py",
        "bot/cogs/admin_batch.py",
        "bot/cogs/linking.py",
        "bot/cogs/bounties.py",
        "bot/cogs/factions.py"
    ]
    
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Fix database manager references
            content = re.sub(
                r'self\.bot\.db_manager',
                'self.bot.db_manager',
                content
            )
            
            # Fix direct database references that don't exist
            content = re.sub(
                r'\.database\.([a-zA-Z_]+)',
                r'.db_manager.\1',
                content
            )
            
            # Fix admin command references
            content = re.sub(
                r'\.admin\.command\(',
                '.admin.command(',
                content
            )
            
            if content != original_content:
                with open(file_path, 'w') as f:
                    f.write(content)
                fixes_applied.append(f"{file_path} - Fixed database references")
    
    # Fix database.py if it has issues
    db_py_path = "bot/models/database.py"
    if os.path.exists(db_py_path):
        with open(db_py_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Ensure admin property exists
        if "def admin(self):" not in content and "@property" not in content:
            # Add admin property if missing
            admin_property = '''
    @property
    def admin(self):
        """Access to admin database operations"""
        return self.client.admin
'''
            # Insert after class definition
            content = re.sub(
                r'(class DatabaseManager[^:]*:)',
                r'\1' + admin_property,
                content
            )
        
        if content != original_content:
            with open(db_py_path, 'w') as f:
                f.write(content)
            fixes_applied.append("bot/models/database.py - Added admin property")
    
    return fixes_applied

def main():
    """Execute all database fixes"""
    print("🔧 Fixing all database attribute errors...")
    
    fixes = fix_all_database_attribute_errors()
    
    if fixes:
        print(f"✅ Applied {len(fixes)} fixes:")
        for fix in fixes:
            print(f"  • {fix}")
    else:
        print("✅ No database fixes needed")
    
    print("🎉 Database error fixes completed!")

if __name__ == "__main__":
    main()