"""
Premium Compatibility Layer
Bridges new premium manager commands with existing database structure
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import discord
from discord.ext import commands


class PremiumCompatibility:
    """
    Compatibility layer that provides new premium manager functionality
    while working with existing database structure
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db_manager if hasattr(bot, 'db_manager') else bot.database
        self._locks = {}
    
    def get_guild_lock(self, guild_id: int) -> asyncio.Lock:
        """Get or create a lock for guild operations to prevent race conditions"""
        if guild_id not in self._locks:
            self._locks[guild_id] = asyncio.Lock()
        return self._locks[guild_id]
    
    # =====================
    # HOME GUILD MANAGEMENT
    # =====================
    
    async def set_home_guild(self, guild_id: int, set_by: int) -> bool:
        """Set the Home Guild for premium management (Bot Owner only)"""
        try:
            await self.db.bot_config.update_one(
                {"config_type": "home_guild"},
                {
                    "$set": {
                        "guild_id": guild_id,
                        "set_by": set_by,
                        "set_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Error setting home guild: {e}")
            return False
    
    async def get_home_guild(self) -> Optional[int]:
        """Get the current Home Guild ID"""
        try:
            config = await self.db.bot_config.find_one({"config_type": "home_guild"})
            return config.get("guild_id") if config else None
        except Exception as e:
            print(f"Error getting home guild: {e}")
            return None
    
    # =====================
    # PREMIUM ACCESS CHECKS
    # =====================
    
    async def has_premium_access(self, guild_id: int, server_id: str = None) -> bool:
        """
        Check if guild has premium access
        
        For server-specific features: checks if specific server is premium
        For guild-wide features: checks if ANY server in guild is premium
        """
        try:
            if server_id:
                # Server-specific check
                return await self.is_server_premium(guild_id, server_id)
            else:
                # Guild-wide check - any premium server in guild
                guild_doc = await self.db.guild_configs.find_one({"guild_id": guild_id})
                if not guild_doc:
                    return False
                
                servers = guild_doc.get('servers', [])
                for server_config in servers:
                    if server_config.get('premium', False):
                        return True
                return False
        except Exception as e:
            print(f"Error checking premium access: {e}")
            return False
    
    async def is_server_premium(self, guild_id: int, server_id: str) -> bool:
        """Check if a specific server is premium"""
        try:
            guild_doc = await self.db.guild_configs.find_one({"guild_id": guild_id})
            if not guild_doc:
                return False
            
            servers = guild_doc.get('servers', [])
            for server_config in servers:
                if server_config.get('server_id', 'default') == server_id:
                    return server_config.get('premium', False)
            return False
        except Exception as e:
            print(f"Error checking server premium status: {e}")
            return False
    
    # =====================
    # PREMIUM LIMIT MANAGEMENT
    # =====================
    
    async def add_premium_limit(self, guild_id: int, added_by: int, reason: str = None) -> bool:
        """Add 1 to the premium server limit for a guild"""
        async with self.get_guild_lock(guild_id):
            try:
                current_limit = await self.get_premium_limit(guild_id)
                new_limit = current_limit + 1
                
                # Update the limit in bot_config collection
                await self.db.bot_config.update_one(
                    {"config_type": "premium_limits", "guild_id": guild_id},
                    {
                        "$set": {
                            "guild_id": guild_id,
                            "max_premium_servers": new_limit,
                            "last_modified_by": added_by,
                            "last_modified_at": datetime.utcnow()
                        },
                        "$push": {
                            "limit_history": {
                                "action": "add",
                                "from_limit": current_limit,
                                "to_limit": new_limit,
                                "by": added_by,
                                "at": datetime.utcnow(),
                                "reason": reason or "Premium limit increased"
                            }
                        }
                    },
                    upsert=True
                )
                return True
            except Exception as e:
                print(f"Error adding premium limit: {e}")
                return False
    
    async def remove_premium_limit(self, guild_id: int, removed_by: int, reason: str = None, auto_deactivate: bool = True) -> Tuple[bool, List[str]]:
        """
        Remove 1 from the premium server limit for a guild
        Returns (success, list_of_deactivated_servers)
        """
        async with self.get_guild_lock(guild_id):
            try:
                current_limit = await self.get_premium_limit(guild_id)
                if current_limit <= 0:
                    return False, []
                
                new_limit = current_limit - 1
                deactivated_servers = []
                
                if auto_deactivate:
                    # Count current premium servers
                    current_count = await self.count_premium_servers(guild_id)
                    if current_count > new_limit:
                        # Need to deactivate servers
                        excess = current_count - new_limit
                        deactivated_servers = await self._auto_deactivate_servers(guild_id, excess, removed_by, reason or "Limit reduction")
                
                # Update the limit
                await self.db.bot_config.update_one(
                    {"config_type": "premium_limits", "guild_id": guild_id},
                    {
                        "$set": {
                            "guild_id": guild_id,
                            "max_premium_servers": new_limit,
                            "last_modified_by": removed_by,
                            "last_modified_at": datetime.utcnow()
                        },
                        "$push": {
                            "limit_history": {
                                "action": "remove",
                                "from_limit": current_limit,
                                "to_limit": new_limit,
                                "by": removed_by,
                                "at": datetime.utcnow(),
                                "reason": reason or "Premium limit decreased",
                                "auto_deactivated_servers": deactivated_servers
                            }
                        }
                    }
                )
                return True, deactivated_servers
                
            except Exception as e:
                print(f"Error removing premium limit: {e}")
                return False, []
    
    async def get_premium_limit(self, guild_id: int) -> int:
        """Get current premium server limit for guild"""
        try:
            limit_doc = await self.db.bot_config.find_one({"config_type": "premium_limits", "guild_id": guild_id})
            return limit_doc.get("max_premium_servers", 0) if limit_doc else 0
        except Exception as e:
            print(f"Error getting premium limit: {e}")
            return 0
    
    async def get_premium_usage(self, guild_id: int) -> Dict[str, int]:
        """Get premium usage statistics for guild"""
        try:
            limit = await self.get_premium_limit(guild_id)
            used = await self.count_premium_servers(guild_id)
            return {
                "limit": limit,
                "used": used,
                "available": max(0, limit - used),
                "active_premium_servers": used
            }
        except Exception as e:
            print(f"Error getting premium usage: {e}")
            return {"limit": 0, "used": 0, "available": 0, "active_premium_servers": 0}
    
    async def count_premium_servers(self, guild_id: int) -> int:
        """Count active premium servers for guild"""
        try:
            guild_doc = await self.db.guild_configs.find_one({"guild_id": guild_id})
            if not guild_doc:
                return 0
            
            count = 0
            servers = guild_doc.get('servers', [])
            for server_config in servers:
                if server_config.get('premium', False):
                    count += 1
            return count
        except Exception as e:
            print(f"Error counting premium servers: {e}")
            return 0
    
    # =====================
    # SERVER MANAGEMENT
    # =====================
    
    async def activate_server_premium(self, guild_id: int, server_id: str, activated_by: int, reason: str = None) -> Tuple[bool, str]:
        """
        Activate premium for a server
        Returns (success, message)
        """
        async with self.get_guild_lock(guild_id):
            try:
                # Check if already premium
                if await self.is_server_premium(guild_id, server_id):
                    return False, "Server is already premium"
                
                # Check limits
                usage = await self.get_premium_usage(guild_id)
                if usage["used"] >= usage["limit"]:
                    return False, f"Premium server limit reached ({usage['used']}/{usage['limit']})"
                
                # Update server to premium in guild_configs
                await self.db.guild_configs.update_one(
                    {"guild_id": guild_id, "servers.server_id": server_id},
                    {
                        "$set": {
                            "servers.$.premium": True,
                            "servers.$.premium_activated_by": activated_by,
                            "servers.$.premium_activated_at": datetime.utcnow()
                        }
                    }
                )
                
                return True, f"Server {server_id} activated as premium ({usage['used'] + 1}/{usage['limit']})"
                
            except Exception as e:
                print(f"Error activating server premium: {e}")
                return False, "Database error occurred"
    
    async def deactivate_server_premium(self, guild_id: int, server_id: str, deactivated_by: int, reason: str = None) -> Tuple[bool, str]:
        """
        Deactivate premium for a server
        Returns (success, message)
        """
        async with self.get_guild_lock(guild_id):
            try:
                # Check if premium
                if not await self.is_server_premium(guild_id, server_id):
                    return False, "Server is not premium"
                
                # Update server to non-premium in guild_configs
                await self.db.guild_configs.update_one(
                    {"guild_id": guild_id, "servers.server_id": server_id},
                    {
                        "$set": {
                            "servers.$.premium": False,
                            "servers.$.premium_deactivated_by": deactivated_by,
                            "servers.$.premium_deactivated_at": datetime.utcnow()
                        }
                    }
                )
                
                usage = await self.get_premium_usage(guild_id)
                return True, f"Server {server_id} deactivated from premium ({usage['used']}/{usage['limit']})"
                
            except Exception as e:
                print(f"Error deactivating server premium: {e}")
                return False, "Database error occurred"
    
    async def list_premium_servers(self, guild_id: int) -> List[Dict[str, str]]:
        """List all premium servers for guild with names"""
        try:
            guild_doc = await self.db.guild_configs.find_one({"guild_id": guild_id})
            if not guild_doc:
                return []
            
            premium_servers = []
            servers = guild_doc.get('servers', [])
            for server_config in servers:
                if server_config.get('premium', False):
                    premium_servers.append({
                        "server_id": server_config.get('server_id', 'default'),
                        "name": server_config.get('name', 'Unknown Server')
                    })
            return premium_servers
        except Exception as e:
            print(f"Error listing premium servers: {e}")
            return []
    
    async def _auto_deactivate_servers(self, guild_id: int, count: int, deactivated_by: int, reason: str) -> List[str]:
        """Auto-deactivate oldest premium servers"""
        try:
            guild_doc = await self.db.guild_configs.find_one({"guild_id": guild_id})
            if not guild_doc:
                return []
            
            deactivated = []
            servers = guild_doc.get('servers', [])
            premium_servers = [s for s in servers if s.get('premium', False)]
            
            # Sort by activation date (oldest first)
            premium_servers.sort(key=lambda x: x.get('premium_activated_at', datetime.min))
            
            for i in range(min(count, len(premium_servers))):
                server_id = premium_servers[i].get('server_id', 'default')
                success, _ = await self.deactivate_server_premium(guild_id, server_id, deactivated_by, reason)
                if success:
                    deactivated.append(server_id)
            
            return deactivated
        except Exception as e:
            print(f"Error auto-deactivating servers: {e}")
            return []
    
    # =====================
    # PERMISSION HELPERS
    # =====================
    
    async def is_bot_owner(self, user_id: int, bot) -> bool:
        """Check if user is bot owner"""
        try:
            app_info = await bot.application_info()
            return user_id == app_info.owner.id
        except:
            return False
    
    async def is_home_guild_admin(self, user_id: int, bot) -> bool:
        """Check if user is admin in Home Guild"""
        try:
            home_guild_id = await self.get_home_guild()
            if not home_guild_id:
                return False
            
            home_guild = bot.get_guild(home_guild_id)
            if not home_guild:
                return False
            
            member = home_guild.get_member(user_id)
            if not member:
                return False
            
            return member.guild_permissions.administrator
        except:
            return False
    
    async def can_manage_premium_limits(self, user_id: int, bot) -> bool:
        """Check if user can manage premium limits (bot owner or home guild admin)"""
        return await self.is_bot_owner(user_id, bot) or await self.is_home_guild_admin(user_id, bot)
    
    async def is_guild_admin(self, user_id: int, guild_id: int, bot) -> bool:
        """Check if user is admin in specific guild"""
        try:
            guild = bot.get_guild(guild_id)
            if not guild:
                return False
            
            member = guild.get_member(user_id)
            if not member:
                return False
            
            return member.guild_permissions.administrator
        except:
            return False
    
    # Legacy compatibility method
    async def check_premium_access(self, guild_id: int, server_id: str = None) -> bool:
        """Legacy compatibility method - same as has_premium_access"""
        return await self.has_premium_access(guild_id, server_id)