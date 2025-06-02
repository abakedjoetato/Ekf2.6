"""
Advanced Database Manager - Phase 1: Complete Schema Implementation
Implements comprehensive 10-phase reconstruction with py-cord 2.6.1 UI support
"""

import logging
import asyncio
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING
import discord

logger = logging.getLogger(__name__)

class AdvancedDatabaseManager:
    """
    Advanced Database Manager implementing complete 10-phase architecture
    - Server-scoped premium subscriptions with guild feature unlocking
    - Cross-character aggregation with main/alt linking
    - Dual-layer faction management (user + admin controls)
    - Complete audit trails for administrative actions
    - UI preference storage for py-cord 2.6.1 components
    """

    def __init__(self, mongo_client: AsyncIOMotorClient):
        self.client = mongo_client
        self.db: AsyncIOMotorDatabase = mongo_client.emerald_killfeed_v2
        
        # Core Collections - Phase 1 Schema
        self.guilds = self.db.guilds
        self.pvp_data = self.db.pvp_data
        self.kill_events = self.db.kill_events
        self.players = self.db.players
        self.factions = self.db.factions
        self.economy_config = self.db.economy_config
        self.premium_allocation = self.db.premium_allocation
        
        # Advanced Collections
        self.user_sessions = self.db.user_sessions
        self.ui_preferences = self.db.ui_preferences
        self.audit_logs = self.db.audit_logs
        self.bounties = self.db.bounties
        self.achievements = self.db.achievements
        
        # Parser Collections (Preserved)
        self.parser_states = self.db.parser_states
        self.log_processing = self.db.log_processing
        
        # Cache for premium status
        self._premium_cache = {}
        self._cache_expiry = {}

    async def initialize_complete_schema(self):
        """Initialize complete database schema with all collections and indexes"""
        try:
            logger.info("🚀 Initializing Complete Database Schema - Phase 1")
            
            # Create all indexes
            await self._create_core_indexes()
            await self._create_advanced_indexes()
            await self._create_ui_indexes()
            
            # Initialize default configurations
            await self._initialize_default_configs()
            
            logger.info("✅ Complete database schema initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Database schema initialization failed: {e}")
            raise

    async def _create_core_indexes(self):
        """Create core collection indexes"""
        try:
            # Guilds collection
            await self.guilds.create_index("guild_id", unique=True)
            await self.guilds.create_index([("guild_id", 1), ("servers.server_id", 1)])
            
            # PvP data collection (server-scoped)
            await self.pvp_data.create_index([
                ("guild_id", 1), ("server_id", 1), ("player_name", 1)
            ], unique=True)
            await self.pvp_data.create_index([("guild_id", 1), ("server_id", 1), ("kills", -1)])
            await self.pvp_data.create_index([("guild_id", 1), ("server_id", 1), ("kdr", -1)])
            await self.pvp_data.create_index([("guild_id", 1), ("faction_id", 1)])
            
            # Kill events collection (server-scoped)
            await self.kill_events.create_index([
                ("guild_id", 1), ("server_id", 1), ("timestamp", -1)
            ])
            await self.kill_events.create_index([("guild_id", 1), ("server_id", 1), ("killer", 1)])
            await self.kill_events.create_index([("guild_id", 1), ("server_id", 1), ("victim", 1)])
            await self.kill_events.create_index([("timestamp", -1)])
            
            # Players collection (guild-scoped)
            await self.players.create_index([("guild_id", 1), ("discord_id", 1)], unique=True)
            await self.players.create_index([("guild_id", 1), ("linked_characters", 1)])
            await self.players.create_index([("guild_id", 1), ("main_character", 1)])
            await self.players.create_index([("guild_id", 1), ("faction_id", 1)])
            
            # Factions collection (guild-scoped)
            await self.factions.create_index([("guild_id", 1), ("faction_id", 1)], unique=True)
            await self.factions.create_index([("guild_id", 1), ("name", 1)], unique=True)
            await self.factions.create_index([("guild_id", 1), ("leader_id", 1)])
            await self.factions.create_index([("guild_id", 1), ("members", 1)])
            
            logger.info("✅ Core indexes created successfully")
            
        except Exception as e:
            logger.error(f"❌ Core index creation failed: {e}")
            raise

    async def _create_advanced_indexes(self):
        """Create advanced feature indexes"""
        try:
            # Economy config collection (guild-scoped)
            await self.economy_config.create_index("guild_id", unique=True)
            
            # Premium allocation collection
            await self.premium_allocation.create_index("home_guild_id", unique=True)
            await self.premium_allocation.create_index([("allocated_slots.guild_id", 1)])
            
            # Bounties collection (guild-scoped)
            await self.bounties.create_index([("guild_id", 1), ("target_player", 1)])
            await self.bounties.create_index([("guild_id", 1), ("creator_id", 1)])
            await self.bounties.create_index([("guild_id", 1), ("amount", -1)])
            await self.bounties.create_index("expires_at")
            
            # Achievements collection (guild-scoped)
            await self.achievements.create_index([("guild_id", 1), ("discord_id", 1)])
            await self.achievements.create_index([("guild_id", 1), ("achievement_type", 1)])
            
            # Audit logs collection
            await self.audit_logs.create_index([("guild_id", 1), ("timestamp", -1)])
            await self.audit_logs.create_index([("guild_id", 1), ("admin_id", 1), ("timestamp", -1)])
            await self.audit_logs.create_index([("guild_id", 1), ("action_type", 1), ("timestamp", -1)])
            
            logger.info("✅ Advanced indexes created successfully")
            
        except Exception as e:
            logger.error(f"❌ Advanced index creation failed: {e}")
            raise

    async def _create_ui_indexes(self):
        """Create UI and session indexes"""
        try:
            # User sessions collection
            await self.user_sessions.create_index([("guild_id", 1), ("discord_id", 1)])
            await self.user_sessions.create_index("expires_at")
            
            # UI preferences collection
            await self.ui_preferences.create_index([("guild_id", 1), ("discord_id", 1)], unique=True)
            
            # Parser states (preserved from original)
            await self.parser_states.create_index([
                ("guild_id", 1), ("server_id", 1), ("parser_type", 1)
            ], unique=True)
            
            logger.info("✅ UI and session indexes created successfully")
            
        except Exception as e:
            logger.error(f"❌ UI index creation failed: {e}")
            raise

    async def _initialize_default_configs(self):
        """Initialize default configurations for new system"""
        try:
            # Default economy configuration template
            default_economy = {
                "currency_name": "Credits",
                "currency_symbol": "💎",
                "currency_emoji": "💎",
                "kill_rewards": {
                    "base_kill": 100,
                    "headshot_bonus": 50,
                    "suicide_penalty": -25,
                    "streak_multipliers": {
                        "5": 1.5,
                        "10": 2.0,
                        "15": 3.0,
                        "20": 5.0
                    },
                    "platform_bonuses": {
                        "PC": 1.0,
                        "Xbox": 1.2,
                        "PS5": 1.2
                    },
                    "distance_bonuses": {
                        "close_range": {"min": 0, "max": 50, "multiplier": 1.0},
                        "medium_range": {"min": 51, "max": 200, "multiplier": 1.2},
                        "long_range": {"min": 201, "max": 500, "multiplier": 1.5},
                        "extreme_range": {"min": 501, "max": 9999, "multiplier": 2.0}
                    }
                },
                "betting_limits": {
                    "casino_min": 10,
                    "casino_max": 10000,
                    "bounty_min": 100,
                    "bounty_max": 50000,
                    "daily_earning_cap": 100000
                },
                "auto_bounty_config": {
                    "enabled": True,
                    "cooldown_hours": 24,
                    "threat_multipliers": {
                        "low": 1.0,
                        "medium": 2.0,
                        "high": 4.0,
                        "elite": 8.0
                    },
                    "trigger_thresholds": {
                        "streak_trigger": 10,
                        "kd_trigger": 3.0,
                        "faction_leader_bonus": 2.0
                    }
                }
            }
            
            self._default_economy_config = default_economy
            logger.info("✅ Default configurations initialized")
            
        except Exception as e:
            logger.error(f"❌ Default config initialization failed: {e}")
            raise

    # Guild Management Methods
    async def ensure_guild_initialized(self, guild_id: int, guild_name: str) -> bool:
        """Ensure guild is properly initialized with complete schema"""
        try:
            existing_guild = await self.guilds.find_one({"guild_id": guild_id})
            
            if not existing_guild:
                guild_doc = {
                    "guild_id": guild_id,
                    "guild_name": guild_name,
                    "servers": [],
                    "channels": {
                        "killfeed": {},
                        "leaderboard": {},
                        "events": {},
                        "missions": {},
                        "playercountvc": {},
                        "connections": {},
                        "bounties": {}
                    },
                    "ui_preferences": {
                        "embed_style": "default",
                        "button_layout": "matrix",
                        "pagination_size": 10,
                        "modal_themes": {}
                    },
                    "created_at": datetime.now(timezone.utc)
                }
                
                await self.guilds.insert_one(guild_doc)
                
                # Initialize default economy config for new guild
                economy_doc = dict(self._default_economy_config)
                economy_doc["guild_id"] = guild_id
                await self.economy_config.insert_one(economy_doc)
                
                logger.info(f"✅ Initialized new guild: {guild_name} ({guild_id})")
                return True
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Guild initialization failed for {guild_id}: {e}")
            return False

    # Server Management Methods
    async def add_server_to_guild(self, guild_id: int, server_data: Dict[str, Any]) -> bool:
        """Add server to guild with validation"""
        try:
            result = await self.guilds.update_one(
                {"guild_id": guild_id},
                {"$push": {"servers": server_data}}
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Added server {server_data.get('name')} to guild {guild_id}")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to add server to guild {guild_id}: {e}")
            return False

    async def get_guild_servers(self, guild_id: int) -> List[Dict[str, Any]]:
        """Get all servers for a guild"""
        try:
            guild_doc = await self.guilds.find_one({"guild_id": guild_id})
            if guild_doc:
                return guild_doc.get("servers", [])
            return []
            
        except Exception as e:
            logger.error(f"❌ Failed to get servers for guild {guild_id}: {e}")
            return []

    # Player Management Methods
    async def link_character_to_player(self, guild_id: int, discord_id: int, character_name: str, is_main: bool = False) -> bool:
        """Link character to player with main/alt support"""
        try:
            player_doc = await self.players.find_one({
                "guild_id": guild_id,
                "discord_id": discord_id
            })
            
            if not player_doc:
                # Create new player
                new_player = {
                    "guild_id": guild_id,
                    "discord_id": discord_id,
                    "linked_characters": [character_name],
                    "main_character": character_name if is_main else None,
                    "wallet_balance": 0,
                    "casino_stats": {
                        "total_wagered": 0,
                        "total_won": 0,
                        "games_played": 0,
                        "biggest_win": 0
                    },
                    "faction_id": None,
                    "linking_history": [{
                        "action": "linked",
                        "character": character_name,
                        "admin_id": None,
                        "timestamp": datetime.now(timezone.utc),
                        "reason": "User self-link"
                    }],
                    "balance_history": [],
                    "created_at": datetime.now(timezone.utc)
                }
                
                await self.players.insert_one(new_player)
                logger.info(f"✅ Created new player {discord_id} with character {character_name}")
                return True
                
            else:
                # Add character to existing player
                if character_name not in player_doc.get("linked_characters", []):
                    update_data = {
                        "$addToSet": {"linked_characters": character_name},
                        "$push": {
                            "linking_history": {
                                "action": "linked",
                                "character": character_name,
                                "admin_id": None,
                                "timestamp": datetime.now(timezone.utc),
                                "reason": "User self-link"
                            }
                        }
                    }
                    
                    if is_main or not player_doc.get("main_character"):
                        update_data["$set"] = {"main_character": character_name}
                    
                    await self.players.update_one(
                        {"guild_id": guild_id, "discord_id": discord_id},
                        update_data
                    )
                    
                    logger.info(f"✅ Added character {character_name} to player {discord_id}")
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to link character {character_name} to player {discord_id}: {e}")
            return False

    async def get_player_characters(self, guild_id: int, discord_id: int) -> Dict[str, Any]:
        """Get all linked characters for a player"""
        try:
            player_doc = await self.players.find_one({
                "guild_id": guild_id,
                "discord_id": discord_id
            })
            
            if player_doc:
                return {
                    "linked_characters": player_doc.get("linked_characters", []),
                    "main_character": player_doc.get("main_character"),
                    "faction_id": player_doc.get("faction_id"),
                    "wallet_balance": player_doc.get("wallet_balance", 0)
                }
                
            return {
                "linked_characters": [],
                "main_character": None,
                "faction_id": None,
                "wallet_balance": 0
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get characters for player {discord_id}: {e}")
            return {"linked_characters": [], "main_character": None, "faction_id": None, "wallet_balance": 0}

    # Faction Management Methods
    async def create_faction(self, guild_id: int, faction_name: str, creator_id: int, description: str = None) -> Optional[str]:
        """Create new faction with user as leader"""
        try:
            faction_id = f"faction_{guild_id}_{int(datetime.now(timezone.utc).timestamp())}"
            
            faction_doc = {
                "guild_id": guild_id,
                "faction_id": faction_id,
                "name": faction_name,
                "display_name": faction_name,
                "description": description or f"Faction {faction_name}",
                "color": "#3498DB",  # Default blue
                "leader_id": creator_id,
                "officers": [],
                "members": [creator_id],
                "treasury": 0,
                "faction_history": [{
                    "action": "created",
                    "target_user": creator_id,
                    "admin_id": None,
                    "timestamp": datetime.now(timezone.utc),
                    "details": f"Faction created by user"
                }],
                "created_at": datetime.now(timezone.utc),
                "created_by": creator_id
            }
            
            await self.factions.insert_one(faction_doc)
            
            # Update player's faction
            await self.players.update_one(
                {"guild_id": guild_id, "discord_id": creator_id},
                {"$set": {"faction_id": faction_id}}
            )
            
            logger.info(f"✅ Created faction {faction_name} with leader {creator_id}")
            return faction_id
            
        except Exception as e:
            logger.error(f"❌ Failed to create faction {faction_name}: {e}")
            return None

    async def get_faction_by_id(self, guild_id: int, faction_id: str) -> Optional[Dict[str, Any]]:
        """Get faction by ID"""
        try:
            return await self.factions.find_one({
                "guild_id": guild_id,
                "faction_id": faction_id
            })
            
        except Exception as e:
            logger.error(f"❌ Failed to get faction {faction_id}: {e}")
            return None

    async def get_user_faction_role(self, guild_id: int, discord_id: int, faction_id: str) -> Optional[str]:
        """Get user's role in faction"""
        try:
            faction = await self.get_faction_by_id(guild_id, faction_id)
            if not faction:
                return None
                
            if faction.get("leader_id") == discord_id:
                return "leader"
            elif discord_id in faction.get("officers", []):
                return "officer"
            elif discord_id in faction.get("members", []):
                return "member"
                
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get faction role for user {discord_id}: {e}")
            return None

    # Premium Management Methods
    async def check_server_premium(self, guild_id: int, server_id: str) -> bool:
        """Check if specific server has premium access"""
        try:
            cache_key = f"{guild_id}_{server_id}"
            now = datetime.now(timezone.utc)
            
            # Check cache first
            if cache_key in self._premium_cache and cache_key in self._cache_expiry:
                if now < self._cache_expiry[cache_key]:
                    return self._premium_cache[cache_key]
            
            # Check guild's servers for premium status
            guild_doc = await self.guilds.find_one({"guild_id": guild_id})
            if guild_doc:
                for server in guild_doc.get("servers", []):
                    if str(server.get("server_id")) == str(server_id):
                        premium_status = server.get("premium_status", False)
                        if premium_status:
                            # Check expiry
                            expires = server.get("premium_expires")
                            if expires and isinstance(expires, datetime):
                                premium_status = expires > now
                        
                        # Cache result for 5 minutes
                        self._premium_cache[cache_key] = premium_status
                        self._cache_expiry[cache_key] = now + timedelta(minutes=5)
                        
                        return premium_status
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to check premium for server {server_id}: {e}")
            return False

    async def check_guild_premium_features(self, guild_id: int) -> bool:
        """Check if guild has premium features enabled (1+ premium server)"""
        try:
            cache_key = f"guild_{guild_id}"
            now = datetime.now(timezone.utc)
            
            # Check cache first
            if cache_key in self._premium_cache and cache_key in self._cache_expiry:
                if now < self._cache_expiry[cache_key]:
                    return self._premium_cache[cache_key]
            
            # Check if any server in guild has premium
            guild_doc = await self.guilds.find_one({"guild_id": guild_id})
            if guild_doc:
                for server in guild_doc.get("servers", []):
                    if server.get("premium_status", False):
                        expires = server.get("premium_expires")
                        if not expires or (isinstance(expires, datetime) and expires > now):
                            # Cache positive result
                            self._premium_cache[cache_key] = True
                            self._cache_expiry[cache_key] = now + timedelta(minutes=5)
                            return True
            
            # Cache negative result
            self._premium_cache[cache_key] = False
            self._cache_expiry[cache_key] = now + timedelta(minutes=5)
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to check guild premium features for {guild_id}: {e}")
            return False

    # Administrative Methods
    async def log_admin_action(self, guild_id: int, admin_id: int, action_type: str, target_data: Dict[str, Any], reason: str = None):
        """Log administrative action for audit trail"""
        try:
            audit_doc = {
                "guild_id": guild_id,
                "admin_id": admin_id,
                "action_type": action_type,
                "target_data": target_data,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc)
            }
            
            await self.audit_logs.insert_one(audit_doc)
            logger.info(f"✅ Logged admin action: {action_type} by {admin_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to log admin action: {e}")

    # Economy Methods
    async def get_economy_config(self, guild_id: int) -> Dict[str, Any]:
        """Get economy configuration for guild"""
        try:
            config = await self.economy_config.find_one({"guild_id": guild_id})
            return config if config else self._default_economy_config
            
        except Exception as e:
            logger.error(f"❌ Failed to get economy config for guild {guild_id}: {e}")
            return self._default_economy_config

    async def update_player_balance(self, guild_id: int, discord_id: int, amount: int, reason: str = "System", admin_id: int = None) -> bool:
        """Update player balance with history tracking"""
        try:
            player_doc = await self.players.find_one({
                "guild_id": guild_id,
                "discord_id": discord_id
            })
            
            if not player_doc:
                return False
            
            current_balance = player_doc.get("wallet_balance", 0)
            new_balance = max(0, current_balance + amount)  # Prevent negative balances
            
            balance_entry = {
                "action": "add" if amount > 0 else "remove",
                "amount": abs(amount),
                "new_balance": new_balance,
                "admin_id": admin_id,
                "timestamp": datetime.now(timezone.utc),
                "reason": reason
            }
            
            await self.players.update_one(
                {"guild_id": guild_id, "discord_id": discord_id},
                {
                    "$set": {"wallet_balance": new_balance},
                    "$push": {"balance_history": balance_entry}
                }
            )
            
            logger.info(f"✅ Updated balance for player {discord_id}: {current_balance} -> {new_balance}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update balance for player {discord_id}: {e}")
            return False

    # Statistics Methods
    async def get_player_stats(self, guild_id: int, character_name: str, server_id: str = None) -> Optional[Dict[str, Any]]:
        """Get comprehensive player statistics"""
        try:
            query = {"guild_id": guild_id, "player_name": character_name}
            if server_id:
                query["server_id"] = server_id
            
            stats = await self.pvp_data.find_one(query)
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get stats for player {character_name}: {e}")
            return None

    async def get_cross_character_stats(self, guild_id: int, discord_id: int) -> Dict[str, Any]:
        """Get aggregated statistics across all linked characters"""
        try:
            player_doc = await self.get_player_characters(guild_id, discord_id)
            characters = player_doc.get("linked_characters", [])
            
            if not characters:
                return {}
            
            # Aggregate stats across all characters
            pipeline = [
                {
                    "$match": {
                        "guild_id": guild_id,
                        "player_name": {"$in": characters}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_kills": {"$sum": "$kills"},
                        "total_deaths": {"$sum": "$deaths"},
                        "total_suicides": {"$sum": "$suicides"},
                        "total_distance": {"$sum": "$total_distance"},
                        "longest_streak": {"$max": "$longest_streak"},
                        "best_distance": {"$max": "$personal_best_distance"},
                        "servers_played": {"$addToSet": "$server_id"}
                    }
                }
            ]
            
            result = await self.pvp_data.aggregate(pipeline).to_list(length=1)
            if result:
                stats = result[0]
                stats["kdr"] = stats["total_kills"] / max(stats["total_deaths"], 1)
                stats["characters"] = characters
                stats["server_count"] = len(stats.get("servers_played", []))
                return stats
                
            return {}
            
        except Exception as e:
            logger.error(f"❌ Failed to get cross-character stats for player {discord_id}: {e}")
            return {}