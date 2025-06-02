#!/usr/bin/env python3
"""
Advanced Database Manager - 10/10 Bot Architecture
Complete reconstruction using advanced py-cord 2.6.1 patterns
Server-scoped premium with guild feature unlocking
"""

import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import asyncio
from typing import Optional, Dict, Any, List, Union, Tuple
import pymongo
import discord
from discord.ext import commands
import json
from dataclasses import dataclass, asdict

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class ServerConfig:
    """Server configuration dataclass"""
    server_id: int
    server_name: str
    guild_id: int
    premium_status: bool
    premium_tier: Optional[str]
    ssh_config: Dict[str, Any]
    features: Dict[str, bool]
    created_at: datetime
    updated_at: datetime

@dataclass
class PremiumSubscription:
    """Premium subscription dataclass"""
    server_id: int
    guild_id: int
    tier: str
    expires_at: datetime
    features: List[str]
    created_at: datetime
    is_active: bool

@dataclass
class GuildFeatures:
    """Guild features unlocked by premium servers"""
    guild_id: int
    name: str
    premium_servers: List[int]
    features_enabled: List[str]
    analytics_enabled: bool
    created_at: datetime
    updated_at: datetime

class AdvancedDatabaseManager:
    """
    Advanced Database Manager for 10/10 Discord Bot
    - Server-scoped premium subscriptions
    - Guild feature unlocking (1+ premium server enables guild features)
    - Cross-guild kill data with proper isolation
    - Premium server analytics aggregation
    - Free server killfeed-only limitation
    """
    
    def __init__(self):
        self.client = AsyncIOMotorClient(os.getenv('MONGO_URI'))
        self.db = self.client.emerald_killfeed
        self.logger = logging.getLogger(__name__)
        
        # Advanced caching system
        self._premium_cache = {}
        self._guild_cache = {}
        self._server_cache = {}
        self._cache_ttl = 300  # 5 minutes
        
    async def initialize(self):
        """Initialize database with health checks"""
        try:
            # Verify connection
            await self.client.admin.command('ping')
            self.logger.info("✅ MongoDB connection established")
            
            # Verify collections exist
            collections = await self.db.list_collection_names()
            required_collections = [
                'servers', 'premium_subscriptions', 'guild_features',
                'kills', 'players', 'player_sessions', 'guild_analytics',
                'economy', 'parser_states', 'audit_logs'
            ]
            
            for collection in required_collections:
                if collection not in collections:
                    self.logger.warning(f"Collection {collection} missing - will be created on first use")
            
            self.logger.info(f"✅ Database initialized with {len(collections)} collections")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Database initialization failed: {e}")
            return False
    
    # =================== SERVER MANAGEMENT ===================
    
    async def get_server_config(self, server_id: int) -> Optional[ServerConfig]:
        """Get server configuration with caching"""
        cache_key = f"server_{server_id}"
        
        # Check cache
        if cache_key in self._server_cache:
            cached_data, timestamp = self._server_cache[cache_key]
            if datetime.utcnow().timestamp() - timestamp < self._cache_ttl:
                return ServerConfig(**cached_data)
        
        # Query database
        server_doc = await self.db.servers.find_one({"server_id": server_id})
        if not server_doc:
            return None
        
        # Convert to dataclass
        server_config = ServerConfig(
            server_id=server_doc['server_id'],
            server_name=server_doc['server_name'],
            guild_id=server_doc['guild_id'],
            premium_status=server_doc['premium_status'],
            premium_tier=server_doc.get('premium_tier'),
            ssh_config=server_doc['ssh_config'],
            features=server_doc['features'],
            created_at=server_doc['created_at'],
            updated_at=server_doc['updated_at']
        )
        
        # Cache result
        self._server_cache[cache_key] = (asdict(server_config), datetime.utcnow().timestamp())
        
        return server_config
    
    async def update_server_premium_status(self, server_id: int, premium_status: bool, tier: Optional[str] = None) -> bool:
        """Update server premium status and refresh guild features"""
        try:
            update_data = {
                "premium_status": premium_status,
                "premium_tier": tier,
                "updated_at": datetime.utcnow()
            }
            
            # Update server
            result = await self.db.servers.update_one(
                {"server_id": server_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                # Get server to find guild
                server = await self.get_server_config(server_id)
                if server:
                    # Refresh guild features
                    await self._refresh_guild_features(server.guild_id)
                    
                    # Clear cache
                    self._invalidate_cache(f"server_{server_id}")
                    self._invalidate_cache(f"guild_{server.guild_id}")
                    
                self.logger.info(f"✅ Server {server_id} premium status updated to {premium_status}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update server premium status: {e}")
            return False
    
    # =================== PREMIUM SYSTEM ===================
    
    async def check_server_premium(self, server_id: int) -> bool:
        """Check if specific server has premium access"""
        cache_key = f"premium_{server_id}"
        
        # Check cache
        if cache_key in self._premium_cache:
            cached_result, timestamp = self._premium_cache[cache_key]
            if datetime.utcnow().timestamp() - timestamp < self._cache_ttl:
                return cached_result
        
        # Check database
        subscription = await self.db.premium_subscriptions.find_one({
            "server_id": server_id,
            "is_active": True,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        
        result = subscription is not None
        
        # Cache result
        self._premium_cache[cache_key] = (result, datetime.utcnow().timestamp())
        
        return result
    
    async def check_guild_features_enabled(self, guild_id: int) -> bool:
        """Check if guild has any premium servers (enables guild features)"""
        cache_key = f"guild_features_{guild_id}"
        
        # Check cache
        if cache_key in self._guild_cache:
            cached_result, timestamp = self._guild_cache[cache_key]
            if datetime.utcnow().timestamp() - timestamp < self._cache_ttl:
                return cached_result
        
        # Check if guild has any premium servers
        premium_count = await self.db.servers.count_documents({
            "guild_id": guild_id,
            "premium_status": True
        })
        
        result = premium_count > 0
        
        # Cache result
        self._guild_cache[cache_key] = (result, datetime.utcnow().timestamp())
        
        return result
    
    async def get_guild_premium_servers(self, guild_id: int) -> List[int]:
        """Get list of premium servers in guild"""
        cursor = self.db.servers.find({
            "guild_id": guild_id,
            "premium_status": True
        }, {"server_id": 1})
        
        return [doc["server_id"] async for doc in cursor]
    
    async def add_premium_subscription(self, server_id: int, guild_id: int, tier: str, duration_days: int) -> bool:
        """Add premium subscription for server"""
        try:
            expires_at = datetime.utcnow() + timedelta(days=duration_days)
            
            subscription = {
                "server_id": server_id,
                "guild_id": guild_id,
                "tier": tier,
                "expires_at": expires_at,
                "features": self._get_tier_features(tier),
                "created_at": datetime.utcnow(),
                "is_active": True
            }
            
            # Upsert subscription
            await self.db.premium_subscriptions.replace_one(
                {"server_id": server_id},
                subscription,
                upsert=True
            )
            
            # Update server premium status
            await self.update_server_premium_status(server_id, True, tier)
            
            # Log audit
            await self._log_audit(guild_id, "premium_added", {
                "server_id": server_id,
                "tier": tier,
                "expires_at": expires_at.isoformat()
            })
            
            self.logger.info(f"✅ Premium subscription added for server {server_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to add premium subscription: {e}")
            return False
    
    # =================== KILL DATA (CROSS-GUILD) ===================
    
    async def record_kill(self, server_id: int, killer: str, victim: str, weapon: str, 
                         additional_data: Optional[Dict] = None) -> bool:
        """Record kill event (cross-guild accessible)"""
        try:
            kill_event = {
                "server_id": server_id,
                "killer": killer,
                "victim": victim,
                "weapon": weapon,
                "timestamp": datetime.utcnow(),
                "additional_data": additional_data or {}
            }
            
            await self.db.kills.insert_one(kill_event)
            
            # Update player statistics if from premium server
            server_config = await self.get_server_config(server_id)
            if server_config and server_config.premium_status:
                await self._update_player_stats(server_config.guild_id, killer, victim, weapon)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to record kill: {e}")
            return False
    
    async def get_cross_guild_kills(self, player_name: str, limit: int = 100) -> List[Dict]:
        """Get kills for player across all guilds"""
        cursor = self.db.kills.find({
            "$or": [
                {"killer": player_name},
                {"victim": player_name}
            ]
        }).sort("timestamp", -1).limit(limit)
        
        return await cursor.to_list(length=limit)
    
    # =================== GUILD ANALYTICS (PREMIUM ONLY) ===================
    
    async def generate_guild_analytics(self, guild_id: int) -> Optional[Dict]:
        """Generate analytics from premium servers only"""
        try:
            # Check if guild has premium access
            if not await self.check_guild_features_enabled(guild_id):
                return None
            
            # Get premium servers for this guild
            premium_servers = await self.get_guild_premium_servers(guild_id)
            if not premium_servers:
                return None
            
            # Aggregate data from premium servers only
            pipeline = [
                {"$match": {"server_id": {"$in": premium_servers}}},
                {"$group": {
                    "_id": None,
                    "total_kills": {"$sum": 1},
                    "unique_killers": {"$addToSet": "$killer"},
                    "unique_victims": {"$addToSet": "$victim"},
                    "weapon_stats": {"$push": "$weapon"}
                }}
            ]
            
            cursor = self.db.kills.aggregate(pipeline)
            result = await cursor.to_list(length=1)
            
            if result:
                analytics = result[0]
                analytics["guild_id"] = guild_id
                analytics["premium_servers"] = premium_servers
                analytics["generated_at"] = datetime.utcnow()
                
                # Store analytics
                await self.db.guild_analytics.replace_one(
                    {"guild_id": guild_id, "period": "current"},
                    analytics,
                    upsert=True
                )
                
                return analytics
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Failed to generate guild analytics: {e}")
            return None
    
    # =================== ECONOMY SYSTEM ===================
    
    async def get_wallet(self, guild_id: int, user_id: int) -> Dict[str, Any]:
        """Get user wallet (guild-scoped)"""
        wallet = await self.db.economy.find_one({
            "guild_id": guild_id,
            "user_id": user_id
        })
        
        if not wallet:
            # Create new wallet
            wallet = {
                "guild_id": guild_id,
                "user_id": user_id,
                "balance": 1000,  # Starting balance
                "total_earned": 0,
                "total_spent": 0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await self.db.economy.insert_one(wallet)
        
        return wallet
    
    async def update_balance(self, guild_id: int, user_id: int, amount: int, 
                           transaction_type: str, description: str) -> bool:
        """Update user balance with transaction logging"""
        try:
            # Get current wallet
            wallet = await self.get_wallet(guild_id, user_id)
            new_balance = wallet['balance'] + amount
            
            if new_balance < 0:
                return False  # Insufficient funds
            
            # Update wallet
            update_data = {
                "balance": new_balance,
                "updated_at": datetime.utcnow()
            }
            
            if amount > 0:
                update_data["total_earned"] = wallet.get('total_earned', 0) + amount
            else:
                update_data["total_spent"] = wallet.get('total_spent', 0) + abs(amount)
            
            await self.db.economy.update_one(
                {"guild_id": guild_id, "user_id": user_id},
                {"$set": update_data}
            )
            
            # Log transaction
            await self._log_audit(guild_id, "economy_transaction", {
                "user_id": user_id,
                "amount": amount,
                "type": transaction_type,
                "description": description,
                "balance_before": wallet['balance'],
                "balance_after": new_balance
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update balance: {e}")
            return False
    
    # =================== HELPER METHODS ===================
    
    async def _refresh_guild_features(self, guild_id: int):
        """Refresh guild features based on premium servers"""
        try:
            premium_servers = await self.get_guild_premium_servers(guild_id)
            features_enabled = []
            
            if premium_servers:
                features_enabled = [
                    "cross_server_analytics",
                    "guild_leaderboards", 
                    "advanced_admin_tools",
                    "custom_configurations",
                    "export_capabilities"
                ]
            
            await self.db.guild_features.update_one(
                {"guild_id": guild_id},
                {
                    "$set": {
                        "premium_servers": premium_servers,
                        "features_enabled": features_enabled,
                        "analytics_enabled": len(premium_servers) > 0,
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
        except Exception as e:
            self.logger.error(f"❌ Failed to refresh guild features: {e}")
    
    def _get_tier_features(self, tier: str) -> List[str]:
        """Get features for premium tier"""
        features = {
            "basic": ["analytics", "leaderboards", "killfeed_customization"],
            "premium": ["analytics", "leaderboards", "killfeed_customization", "advanced_stats", "export"],
            "enterprise": ["analytics", "leaderboards", "killfeed_customization", "advanced_stats", "export", "api_access", "priority_support"]
        }
        return features.get(tier, [])
    
    def _invalidate_cache(self, cache_key: str):
        """Invalidate specific cache entry"""
        for cache_dict in [self._premium_cache, self._guild_cache, self._server_cache]:
            cache_dict.pop(cache_key, None)
    
    async def _log_audit(self, guild_id: int, operation_type: str, data: Dict[str, Any]):
        """Log audit event"""
        try:
            audit_log = {
                "guild_id": guild_id,
                "operation_type": operation_type,
                "data": data,
                "timestamp": datetime.utcnow()
            }
            await self.db.audit_logs.insert_one(audit_log)
        except Exception as e:
            self.logger.error(f"❌ Failed to log audit: {e}")
    
    async def _update_player_stats(self, guild_id: int, killer: str, victim: str, weapon: str):
        """Update player statistics for premium guild"""
        # This would implement detailed stat tracking for premium servers
        pass
    
    async def cleanup_stale_sessions(self):
        """Cleanup stale player sessions"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            result = await self.db.player_sessions.update_many(
                {"last_seen": {"$lt": cutoff_time}, "is_online": True},
                {"$set": {"is_online": False}}
            )
            
            if result.modified_count > 0:
                self.logger.info(f"✅ Cleaned up {result.modified_count} stale sessions")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to cleanup stale sessions: {e}")
    
    async def close(self):
        """Close database connection"""
        if hasattr(self, 'client'):
            self.client.close()
            self.logger.info("✅ Database connection closed")