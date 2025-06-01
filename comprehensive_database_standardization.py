#!/usr/bin/env python3
"""
Comprehensive Database Access Standardization
Fixes all fragmented database access patterns across the entire codebase
"""

import os
import re
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

class DatabaseStandardizationFixer:
    """Comprehensive database access pattern standardization"""
    
    def __init__(self):
        self.fixed_files = []
        self.errors = []
        
    def fix_all_casino_database_access(self):
        """Fix all casino files to use unified database access"""
        casino_files = [
            'bot/cogs/professional_casino.py',
            'bot/cogs/gambling.py',
            'bot/cogs/gambling_advanced.py',
            'bot/cogs/gambling_ultra.py',
            'bot/cogs/gambling_ultra_v2.py',
            'bot/cogs/casino_redesign.py',
            'bot/cogs/ultra_casino_clean.py',
            'bot/cogs/ultra_casino_v3.py'
        ]
        
        for filepath in casino_files:
            if os.path.exists(filepath):
                self._fix_database_access_patterns(filepath)
                
    def fix_all_premium_validation(self):
        """Standardize premium validation across all cogs"""
        cog_files = [
            'bot/cogs/core.py',
            'bot/cogs/admin_channels.py',
            'bot/cogs/admin_batch.py',
            'bot/cogs/linking.py',
            'bot/cogs/stats.py',
            'bot/cogs/leaderboards_fixed.py',
            'bot/cogs/automated_leaderboard.py',
            'bot/cogs/economy.py',
            'bot/cogs/bounties.py',
            'bot/cogs/factions.py',
            'bot/cogs/subscription_management.py',
            'bot/cogs/cache_management.py'
        ]
        
        for filepath in cog_files:
            if os.path.exists(filepath):
                self._fix_premium_validation_patterns(filepath)
                
    def _fix_database_access_patterns(self, filepath):
        """Fix database access patterns in a single file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Fix direct MongoDB access patterns
            content = re.sub(
                r'self\.bot\.db\.([a-zA-Z_]+)\.find_one\(',
                r'await self.bot.db_manager.\1.find_one(',
                content
            )
            
            # Fix wallet access patterns
            content = re.sub(
                r'self\.bot\.db\.economy\.find_one\({[^}]*guild_id[^}]*}\)',
                r'await self.bot.db_manager.get_wallet(guild_id, user_id)',
                content
            )
            
            # Fix premium config access
            content = re.sub(
                r'self\.bot\.db\.guild_configs\.find_one\({[^}]*guild_id[^}]*}\)',
                r'await self.bot.db_manager.get_guild(guild_id)',
                content
            )
            
            # Fix balance updates
            content = re.sub(
                r'self\.bot\.db\.economy\.update_one\(',
                r'await self.bot.db_manager.update_wallet(',
                content
            )
            
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.fixed_files.append(filepath)
                print(f"✅ Fixed database access patterns in {filepath}")
            
        except Exception as e:
            self.errors.append(f"Error fixing {filepath}: {e}")
            print(f"❌ Error fixing {filepath}: {e}")
            
    def _fix_premium_validation_patterns(self, filepath):
        """Standardize premium validation patterns"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Add unified premium check method if missing
            if 'async def check_premium_access(self, guild_id: int)' not in content:
                # Find the class definition
                class_match = re.search(r'class (\w+)\(discord\.Cog\):', content)
                if class_match:
                    # Find the __init__ method
                    init_match = re.search(r'def __init__\(self, bot\):[^}]*?self\.bot = bot', content, re.DOTALL)
                    if init_match:
                        # Insert the premium check method after __init__
                        premium_method = '''
    
    async def check_premium_access(self, guild_id: int) -> bool:
        """Check if guild has premium access - unified validation"""
        try:
            if hasattr(self.bot, 'premium_manager_v2'):
                return await self.bot.premium_manager_v2.has_premium_access(guild_id)
            elif hasattr(self.bot, 'db_manager') and hasattr(self.bot.db_manager, 'has_premium_access'):
                return await self.bot.db_manager.has_premium_access(guild_id)
            else:
                return False
        except Exception as e:
            logger.error(f"Premium access check failed: {e}")
            return False'''
            
                        content = content[:init_match.end()] + premium_method + content[init_match.end():]
            
            # Fix existing premium validation calls to use unified method
            content = re.sub(
                r'await self\.bot\.db_manager\.guild_configs\.find_one\({[^}]*guild_id[^}]*}\)',
                r'await self.bot.db_manager.get_guild(guild_id)',
                content
            )
            
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.fixed_files.append(filepath)
                print(f"✅ Fixed premium validation in {filepath}")
                
        except Exception as e:
            self.errors.append(f"Error fixing premium validation in {filepath}: {e}")
            print(f"❌ Error fixing premium validation in {filepath}: {e}")
    
    def remove_duplicate_casino_files(self):
        """Remove duplicate casino implementations"""
        duplicate_files = [
            'bot/cogs/gambling.py',
            'bot/cogs/gambling_advanced.py', 
            'bot/cogs/gambling_ultra.py',
            'bot/cogs/gambling_ultra_v2.py',
            'bot/cogs/casino_redesign.py',
            'bot/cogs/ultra_casino_clean.py',
            'bot/cogs/ultra_casino_v3.py'
        ]
        
        for filepath in duplicate_files:
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    print(f"🗑️ Removed duplicate casino file: {filepath}")
                except Exception as e:
                    self.errors.append(f"Error removing {filepath}: {e}")
                    
    def fix_economy_data_consistency(self):
        """Fix economy system data consistency issues"""
        economy_files = [
            'bot/cogs/economy.py',
            'bot/cogs/bounties.py',
            'bot/cogs/admin_batch.py',
            'bot/cogs/stats.py'
        ]
        
        for filepath in economy_files:
            if os.path.exists(filepath):
                self._fix_economy_wallet_access(filepath)
                
    def _fix_economy_wallet_access(self, filepath):
        """Fix wallet access patterns in economy-related files"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Ensure all wallet operations use db_manager
            content = re.sub(
                r'self\.bot\.db\.economy\.',
                r'self.bot.db_manager.',
                content
            )
            
            # Fix direct balance access to use get_wallet
            content = re.sub(
                r'balance\s*=\s*await\s+self\.bot\.db\.economy\.find_one\([^)]+\)',
                r'wallet = await self.bot.db_manager.get_wallet(guild_id, user_id)\nbalance = wallet.get("balance", 0)',
                content
            )
            
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.fixed_files.append(filepath)
                print(f"✅ Fixed economy wallet access in {filepath}")
                
        except Exception as e:
            self.errors.append(f"Error fixing economy in {filepath}: {e}")
            print(f"❌ Error fixing economy in {filepath}: {e}")
    
    def validate_database_consistency(self):
        """Validate that all database access is now consistent"""
        print("\n🔍 Validating database access consistency...")
        
        # Check for remaining direct database access
        problematic_patterns = [
            r'self\.bot\.db\.[a-zA-Z_]+\.find_one\(',
            r'self\.bot\.db\.[a-zA-Z_]+\.update_one\(',
            r'self\.bot\.database\.',
            r'self\.mongo_client\.'
        ]
        
        issues_found = 0
        
        for pattern in problematic_patterns:
            for root, dirs, files in os.walk('bot'):
                for file in files:
                    if file.endswith('.py'):
                        filepath = os.path.join(root, file)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            matches = re.findall(pattern, content)
                            if matches:
                                print(f"⚠️ Found {len(matches)} problematic database access patterns in {filepath}")
                                issues_found += len(matches)
                        except:
                            pass
        
        if issues_found == 0:
            print("✅ All database access patterns are now consistent!")
        else:
            print(f"⚠️ Found {issues_found} remaining issues that need manual review")
    
    def execute_comprehensive_fixes(self):
        """Execute all database standardization fixes"""
        print("🚀 Starting comprehensive database access standardization...")
        
        # Phase 1: Fix casino database access
        print("\n📊 Phase 1: Fixing casino database access patterns...")
        self.fix_all_casino_database_access()
        
        # Phase 2: Fix premium validation
        print("\n🔒 Phase 2: Standardizing premium validation...")
        self.fix_all_premium_validation()
        
        # Phase 3: Fix economy data consistency  
        print("\n💰 Phase 3: Fixing economy data consistency...")
        self.fix_economy_data_consistency()
        
        # Phase 4: Remove duplicate casino files
        print("\n🗑️ Phase 4: Removing duplicate casino implementations...")
        self.remove_duplicate_casino_files()
        
        # Phase 5: Validate consistency
        print("\n✅ Phase 5: Validating fixes...")
        self.validate_database_consistency()
        
        # Summary
        print(f"\n📋 SUMMARY:")
        print(f"✅ Fixed files: {len(self.fixed_files)}")
        print(f"❌ Errors: {len(self.errors)}")
        
        if self.fixed_files:
            print(f"\n📁 Fixed files:")
            for filepath in self.fixed_files:
                print(f"  • {filepath}")
        
        if self.errors:
            print(f"\n⚠️ Errors encountered:")
            for error in self.errors:
                print(f"  • {error}")

def main():
    """Execute comprehensive database standardization"""
    fixer = DatabaseStandardizationFixer()
    fixer.execute_comprehensive_fixes()

if __name__ == "__main__":
    main()