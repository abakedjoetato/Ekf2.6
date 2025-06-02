#!/usr/bin/env python3
"""
Complete Database Rebuild - Phase 1
Wipes all existing collections and creates fresh schema for 10/10 bot
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

class DatabaseReconstructor:
    def __init__(self):
        self.client = AsyncIOMotorClient(os.getenv('MONGO_URI'))
        self.db = self.client.emerald_killfeed
        
    async def phase_1_complete_wipe(self):
        """Phase 1: Complete database wipe"""
        print("🔥 PHASE 1: Complete Database Wipe Starting...")
        
        # Get all collection names
        collections = await self.db.list_collection_names()
        print(f"📋 Found {len(collections)} existing collections: {collections}")
        
        # Drop all collections
        for collection_name in collections:
            await self.db[collection_name].drop()
            print(f"🗑️ Dropped collection: {collection_name}")
        
        print("✅ Phase 1 Complete: All collections wiped")
        
    async def phase_2_create_fresh_schema(self):
        """Phase 2: Create fresh schema with server-scoped premium"""
        print("🏗️ PHASE 2: Creating Fresh Schema...")
        
        # 1. Servers collection (primary entity - server-scoped premium)
        await self.db.servers.create_index([("server_id", 1)], unique=True)
        await self.db.servers.create_index([("guild_id", 1), ("server_id", 1)])
        await self.db.servers.create_index([("premium_status", 1)])
        print("✅ Created servers collection with indexes")
        
        # 2. Premium subscriptions (server-scoped)
        await self.db.premium_subscriptions.create_index([("server_id", 1)], unique=True)
        await self.db.premium_subscriptions.create_index([("guild_id", 1)])
        await self.db.premium_subscriptions.create_index([("expires_at", 1)])
        print("✅ Created premium_subscriptions collection")
        
        # 3. Guild features (unlocked by premium servers)
        await self.db.guild_features.create_index([("guild_id", 1)], unique=True)
        await self.db.guild_features.create_index([("premium_servers", 1)])
        print("✅ Created guild_features collection")
        
        # 4. Kills (cross-guild, server-scoped)
        await self.db.kills.create_index([("server_id", 1), ("timestamp", -1)])
        await self.db.kills.create_index([("killer", 1), ("timestamp", -1)])
        await self.db.kills.create_index([("victim", 1), ("timestamp", -1)])
        await self.db.kills.create_index([("weapon", 1)])
        print("✅ Created kills collection (cross-guild)")
        
        # 5. Players (cross-guild, server sessions)
        await self.db.players.create_index([("player_name", 1), ("server_id", 1)])
        await self.db.players.create_index([("steam_id", 1)])
        print("✅ Created players collection")
        
        # 6. Player sessions (server-scoped)
        await self.db.player_sessions.create_index([("server_id", 1), ("player_name", 1)])
        await self.db.player_sessions.create_index([("guild_id", 1)])
        await self.db.player_sessions.create_index([("is_online", 1)])
        await self.db.player_sessions.create_index([("last_seen", -1)])
        print("✅ Created player_sessions collection")
        
        # 7. Guild analytics (premium servers only)
        await self.db.guild_analytics.create_index([("guild_id", 1), ("period", 1)])
        await self.db.guild_analytics.create_index([("generated_at", -1)])
        print("✅ Created guild_analytics collection")
        
        # 8. Economy (user wallets)
        await self.db.economy.create_index([("guild_id", 1), ("user_id", 1)], unique=True)
        await self.db.economy.create_index([("balance", -1)])
        print("✅ Created economy collection")
        
        # 9. Parser states (server-scoped)
        await self.db.parser_states.create_index([("server_id", 1)], unique=True)
        await self.db.parser_states.create_index([("last_parsed", -1)])
        print("✅ Created parser_states collection")
        
        # 10. Audit logs (system operations)
        await self.db.audit_logs.create_index([("guild_id", 1), ("timestamp", -1)])
        await self.db.audit_logs.create_index([("operation_type", 1)])
        print("✅ Created audit_logs collection")
        
        print("✅ Phase 2 Complete: Fresh schema created")
        
    async def phase_3_insert_base_data(self):
        """Phase 3: Insert base configuration data"""
        print("📊 PHASE 3: Inserting Base Data...")
        
        # Insert current guild configuration
        guild_config = {
            "guild_id": 1219706687980568769,
            "name": "Emerald Servers",
            "premium_servers": [],  # Will be populated when servers become premium
            "features_enabled": [],  # Will be enabled when first premium server added
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        await self.db.guild_features.insert_one(guild_config)
        print("✅ Inserted base guild configuration")
        
        # Insert existing server (currently free)
        server_config = {
            "server_id": 7020,
            "server_name": "Enerald EU",  # Note: keeping existing typo for consistency
            "guild_id": 1219706687980568769,
            "premium_status": False,
            "premium_tier": None,
            "ssh_config": {
                "host": "79.127.236.1",
                "port": 8822,
                "username": "baked",
                "log_path": "/home/baked/server/logs/latest.log"
            },
            "features": {
                "killfeed_enabled": True,
                "analytics_enabled": False,  # Only enabled for premium
                "leaderboards_enabled": False  # Only enabled for premium
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        await self.db.servers.insert_one(server_config)
        print("✅ Inserted base server configuration")
        
        print("✅ Phase 3 Complete: Base data inserted")
        
    async def execute_complete_rebuild(self):
        """Execute complete database rebuild"""
        try:
            await self.phase_1_complete_wipe()
            await self.phase_2_create_fresh_schema()
            await self.phase_3_insert_base_data()
            
            print("\n🎉 DATABASE REBUILD COMPLETE!")
            print("✅ Fresh schema created with server-scoped premium")
            print("✅ Cross-guild kill data support enabled") 
            print("✅ Guild analytics from premium servers only")
            print("✅ Free server limitation to killfeed only")
            
        except Exception as e:
            print(f"❌ Database rebuild failed: {e}")
            raise

async def main():
    reconstructor = DatabaseReconstructor()
    await reconstructor.execute_complete_rebuild()

if __name__ == "__main__":
    asyncio.run(main())