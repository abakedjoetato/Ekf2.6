#!/usr/bin/env python3
"""
Fix All Premium Checks Across The Codebase
Systematically implements cached premium validation for all commands that need it
"""

import os
import re

def fix_all_premium_validation():
    """Fix premium validation across all cogs that need it"""
    
    # Files that need premium check fixes
    cog_files = [
        'bot/cogs/automated_leaderboard.py',
        'bot/cogs/bounties.py', 
        'bot/cogs/economy.py',
        'bot/cogs/factions.py',
        'bot/cogs/leaderboards_fixed.py',
        'bot/cogs/premium.py',
        'bot/cogs/professional_casino.py',
        'bot/cogs/stats.py',
        'bot/cogs/subscription_management.py'
    ]
    
    premium_cache_init = '''        # Premium cache to avoid database calls during commands
        self.premium_cache = {}
    
    @discord.Cog.listener()
    async def on_ready(self):
        """Initialize premium cache when bot is ready"""
        for guild in self.bot.guilds:
            await self.refresh_premium_cache(guild.id)
    
    async def refresh_premium_cache(self, guild_id: int):
        """Refresh premium status from database and cache it"""
        try:
            guild_config = await self.bot.db_manager.guilds.find_one({"guild_id": guild_id})
            if guild_config:
                has_premium_access = guild_config.get('premium_access', False)
                has_premium_servers = bool(guild_config.get('premium_servers', []))
                self.premium_cache[guild_id] = has_premium_access or has_premium_servers
            else:
                self.premium_cache[guild_id] = False
        except Exception as e:
            logger.error(f"Failed to refresh premium cache: {e}")
            self.premium_cache[guild_id] = False

    def check_premium_access(self, guild_id: int) -> bool:
        """Check premium access from cache (no database calls)"""
        return self.premium_cache.get(guild_id, False)'''

    for file_path in cog_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Skip if already has premium cache
                if 'premium_cache' in content:
                    print(f"✅ {file_path} already has premium cache")
                    continue
                
                # Add premium cache system after __init__
                init_pattern = r'(def __init__\(self, bot\):.*?self\.bot = bot)'
                if re.search(init_pattern, content, re.DOTALL):
                    content = re.sub(
                        init_pattern,
                        r'\1\n' + premium_cache_init,
                        content,
                        flags=re.DOTALL
                    )
                    
                    # Replace database premium checks with cached checks
                    premium_check_patterns = [
                        (r'await\s+self\.bot\.db_manager\.guilds\.find_one\([^)]*guild_id[^)]*\)[^}]*premium[^}]*', 
                         'has_premium = self.check_premium_access(guild_id)'),
                        (r'guild_config\s*=\s*await\s+self\.bot\.db_manager\.guilds\.find_one[^}]*premium[^}]*',
                         'has_premium = self.check_premium_access(guild_id)'),
                        (r'has_premium_access\s*=\s*guild_config\.get\([\'"]premium_access[\'"][^}]*',
                         'has_premium = self.check_premium_access(guild_id)'),
                    ]
                    
                    for pattern, replacement in premium_check_patterns:
                        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                    
                    # Add premium restriction embeds where needed
                    premium_embed = '''embed = discord.Embed(
                        title="Premium Feature Required",
                        description="This feature requires premium subscription!",
                        color=0xFF6B6B,
                        timestamp=datetime.now(timezone.utc)
                    )
                    await ctx.respond(embed=embed, ephemeral=True)
                    return'''
                    
                    # Replace simple premium error responses with embeds
                    content = re.sub(
                        r'await ctx\.respond\([\'"].*Premium.*required.*[\'"][^)]*ephemeral=True\)',
                        premium_embed,
                        content
                    )
                    
                    with open(file_path, 'w') as f:
                        f.write(content)
                    
                    print(f"✅ Fixed premium validation in {file_path}")
                else:
                    print(f"⚠️  Could not find __init__ method in {file_path}")
                    
            except Exception as e:
                print(f"❌ Error fixing {file_path}: {e}")
        else:
            print(f"⚠️  File not found: {file_path}")

if __name__ == "__main__":
    fix_all_premium_validation()
    print("🎉 Premium validation fixes completed")