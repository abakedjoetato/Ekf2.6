"""
Centralized Premium Manager
Handles all premium feature access control and validation
"""

import discord
from typing import Dict, Optional
from datetime import datetime

class PremiumManager:
    """Centralized premium feature management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.premium_cache: Dict[int, Dict] = {}
        
    async def check_feature_access(self, guild_id: int, feature: str) -> bool:
        """Check if guild has access to premium feature"""
        try:
            guild_config = await self._get_guild_premium_config(guild_id)
            if not guild_config:
                return False
                
            return guild_config.get('features', {}).get(feature, False)
            
        except Exception as e:
            print(f"Premium check failed: {e}")
            return False
            
    async def get_guild_limits(self, guild_id: int) -> Dict[str, int]:
        """Get resource limits for guild"""
        config = await self._get_guild_premium_config(guild_id)
        
        if config and config.get('premium', False):
            return {
                'max_servers': 10,
                'max_channels': 50,
                'max_players_tracked': 1000,
                'max_leaderboard_entries': 100
            }
        else:
            return {
                'max_servers': 3,
                'max_channels': 10,
                'max_players_tracked': 100,
                'max_leaderboard_entries': 25
            }
            
    async def validate_server_premium(self, guild_id: int, server_id: str) -> bool:
        """Validate premium status for specific server"""
        config = await self._get_guild_premium_config(guild_id)
        
        if not config or not config.get('premium', False):
            return False
            
        premium_servers = config.get('premium_servers', [])
        return server_id in premium_servers or config.get('premium_all_servers', False)
        
    async def _get_guild_premium_config(self, guild_id: int) -> Optional[Dict]:
        """Get guild premium configuration from database"""
        try:
            if hasattr(self.bot, 'db_manager'):
                guild_doc = await self.bot.db_manager.guilds.find_one({"guild_id": guild_id})
                return guild_doc.get('premium_config', {}) if guild_doc else None
        except Exception as e:
            print(f"Failed to get premium config: {e}")
        return None

# Premium feature decorator
def premium_required(feature: str):
    """Decorator to require premium feature access"""
    def decorator(func):
        async def wrapper(self, ctx: discord.ApplicationContext, *args, **kwargs):
            if hasattr(self.bot, 'premium_manager'):
                has_access = await self.bot.premium_manager.check_feature_access(
                    ctx.guild_id, feature
                )
                if not has_access:
                    embed = discord.Embed(
                        title="Premium Required",
                        description=f"This feature requires premium access: {feature}",
                        color=0xff0000
                    )
                    await ctx.respond(embed=embed, ephemeral=True)
                    return
            
            return await func(self, ctx, *args, **kwargs)
        return wrapper
    return decorator
