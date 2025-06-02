"""
Comprehensive Database Access Standardization
Fixes all fragmented database access patterns across the entire codebase
"""

import os
import re
from pathlib import Path

class DatabaseStandardizationFixer:
    """Comprehensive database access pattern standardization"""
    
    def __init__(self):
        self.target_database = "emerald_killfeed"
        self.fixes_applied = 0
        self.files_processed = 0
        
    def fix_all_casino_database_access(self):
        """Fix all casino files to use unified database access"""
        casino_files = [
            "bot/cogs/professional_casino.py",
            "bot/cogs/economy.py",
            "bot/cogs/bounties.py",
            "bot/cogs/factions.py"
        ]
        
        for filepath in casino_files:
            if os.path.exists(filepath):
                print(f"Fixing database access in {filepath}")
                self._fix_database_access_patterns(filepath)
                
    def fix_all_premium_validation(self):
        """Standardize premium validation across all cogs"""
        premium_files = [
            "bot/cogs/premium.py",
            "bot/cogs/subscription_management.py",
            "bot/cogs/leaderboards_fixed.py",
            "bot/cogs/automated_leaderboard.py"
        ]
        
        for filepath in premium_files:
            if os.path.exists(filepath):
                print(f"Fixing premium validation in {filepath}")
                self._fix_premium_validation_patterns(filepath)
                
    def _fix_database_access_patterns(self, filepath):
        """Fix database access patterns in a single file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Fix database client access patterns
            patterns = [
                # Fix direct MongoDB client access
                (r'client\[[\'"](.*?)[\'"]\]', f'client.{self.target_database}'),
                (r'mongo_client\[[\'"](.*?)[\'"]\]', f'mongo_client.{self.target_database}'),
                
                # Fix database manager instantiation
                (r'DatabaseManager\(mongo_client\[[\'"](.*?)[\'"]\]\)', 'DatabaseManager(mongo_client)'),
                
                # Fix collection access patterns
                (r'self\.client\[[\'"](.*?)[\'"]\]\.(.*)', r'self.db.\2'),
                (r'db_manager\.client\[[\'"](.*?)[\'"]\]\.(.*)', r'db_manager.\2'),
                
                # Fix inconsistent database references
                (r'emerald_killfeed', self.target_database),
                (r'EmeraldDB', self.target_database),
                (r'pvp_stats_bot', self.target_database),
                (r'deadside_bot', self.target_database),
                (r'premium_bot', self.target_database)
            ]
            
            for pattern, replacement in patterns:
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    self.fixes_applied += 1
                content = new_content
                
            # Only write if changes were made
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  ✓ Updated database access patterns in {filepath}")
                self.files_processed += 1
                
        except Exception as e:
            print(f"  ✗ Error fixing {filepath}: {e}")
            
    def _fix_premium_validation_patterns(self, filepath):
        """Standardize premium validation patterns"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            original_content = content
            
            # Fix premium validation to use consistent server_id parameter
            patterns = [
                # Standardize premium check method calls
                (r'check_premium_server\(guild_id\)', 'check_premium_server(guild_id, "default")'),
                (r'is_server_premium\(guild_id\)', 'is_server_premium(guild_id, "default")'),
                (r'has_premium_access\(guild_id, None\)', 'has_premium_access(guild_id)'),
                
                # Fix server_id parameter handling
                (r'server_id = None', 'server_id = "default"'),
                (r'server_id: Optional\[str\] = None', 'server_id: str = "default"'),
                
                # Ensure guild isolation
                (r'guild_id = ctx\.guild\.id if ctx\.guild else 0', 'guild_id = ctx.guild.id')
            ]
            
            for pattern, replacement in patterns:
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    self.fixes_applied += 1
                content = new_content
                
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  ✓ Updated premium validation patterns in {filepath}")
                self.files_processed += 1
                
        except Exception as e:
            print(f"  ✗ Error fixing {filepath}: {e}")
            
    def remove_duplicate_casino_files(self):
        """Remove duplicate casino implementations"""
        duplicate_files = [
            "bot/cogs/casino.py",
            "bot/cogs/gambling.py",
            "bot/cogs/roulette.py",
            "bot/cogs/blackjack.py"
        ]
        
        for filepath in duplicate_files:
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    print(f"  ✓ Removed duplicate file: {filepath}")
                except Exception as e:
                    print(f"  ✗ Error removing {filepath}: {e}")
                    
    def fix_economy_data_consistency(self):
        """Fix economy system data consistency issues"""
        economy_files = [
            "bot/cogs/economy.py",
            "bot/cogs/professional_casino.py"
        ]
        
        for filepath in economy_files:
            if os.path.exists(filepath):
                print(f"Fixing economy consistency in {filepath}")
                self._fix_economy_wallet_access(filepath)
                
    def _fix_economy_wallet_access(self, filepath):
        """Fix wallet access patterns in economy-related files"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            original_content = content
            
            # Fix wallet access patterns
            patterns = [
                # Ensure proper guild_id and user_id validation
                (r'if not guild_id:', 'if not guild_id or guild_id == 0:'),
                (r'if not user_id:', 'if not user_id or user_id == 0:'),
                
                # Fix wallet collection access
                (r'self\.economy\.find_one', 'self.db_manager.economy.find_one'),
                (r'self\.economy\.update_one', 'self.db_manager.economy.update_one'),
                (r'self\.economy\.insert_one', 'self.db_manager.economy.insert_one'),
                
                # Ensure proper error handling
                (r'return \{\}', 'return {"balance": 0, "guild_id": guild_id, "user_id": user_id}')
            ]
            
            for pattern, replacement in patterns:
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    self.fixes_applied += 1
                content = new_content
                
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  ✓ Updated economy patterns in {filepath}")
                self.files_processed += 1
                
        except Exception as e:
            print(f"  ✗ Error fixing {filepath}: {e}")
            
    def validate_database_consistency(self):
        """Validate that all database access is now consistent"""
        print("\n=== Database Consistency Validation ===")
        
        # Check all Python files for inconsistent database access
        inconsistent_files = []
        
        for filepath in Path('.').rglob('*.py'):
            if 'bot/' in str(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Look for problematic patterns
                    problems = []
                    
                    if re.search(r'client\[[\'"]((?!' + self.target_database + r')[^\'\"]+)[\'"]\]', content):
                        problems.append("Direct client database access")
                        
                    if re.search(r'mongo_client\[[\'"]((?!' + self.target_database + r')[^\'\"]+)[\'"]\]', content):
                        problems.append("Direct mongo_client database access")
                        
                    if re.search(r'server_id = None', content):
                        problems.append("server_id defaults to None")
                        
                    if problems:
                        inconsistent_files.append((str(filepath), problems))
                        
                except Exception:
                    pass
                    
        if inconsistent_files:
            print("⚠️ Found inconsistent database access:")
            for filepath, problems in inconsistent_files:
                print(f"  {filepath}: {', '.join(problems)}")
        else:
            print("✅ All database access patterns are consistent")
            
    def execute_comprehensive_fixes(self):
        """Execute all database standardization fixes"""
        print("=== Comprehensive Database Standardization ===")
        
        print("\n1. Fixing casino database access...")
        self.fix_all_casino_database_access()
        
        print("\n2. Fixing premium validation...")
        self.fix_all_premium_validation()
        
        print("\n3. Removing duplicate casino files...")
        self.remove_duplicate_casino_files()
        
        print("\n4. Fixing economy data consistency...")
        self.fix_economy_data_consistency()
        
        print("\n5. Validating database consistency...")
        self.validate_database_consistency()
        
        print(f"\n=== Summary ===")
        print(f"Files processed: {self.files_processed}")
        print(f"Fixes applied: {self.fixes_applied}")
        print(f"Target database: {self.target_database}")

def main():
    """Execute comprehensive database standardization"""
    fixer = DatabaseStandardizationFixer()
    fixer.execute_comprehensive_fixes()

if __name__ == "__main__":
    main()