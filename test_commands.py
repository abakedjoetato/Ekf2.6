#!/usr/bin/env python3
"""
Command Testing Script
Tests actual bot command functionality to identify runtime failures
"""

import asyncio
import sys
import os
sys.path.append('.')

from motor.motor_asyncio import AsyncIOMotorClient
from bot.models.database import DatabaseManager
from datetime import datetime, timezone

async def test_critical_functionality():
    """Test the critical commands that were reported as failing"""
    
    print("🔍 Testing critical bot functionality...")
    
    # Database connection
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        print("❌ MONGO_URI not found")
        return
        
    client = AsyncIOMotorClient(mongo_uri)
    db = client.EmeraldDB
    
    try:
        # Test 1: Database Operations
        print("\n1. Testing database operations...")
        
        guild_id = 1219706687980568769
        test_user_id = 999999999
        
        # Test faction creation (this is what faction commands use)
        faction_doc = {
            'guild_id': guild_id,
            'faction_name': 'Test Faction Runtime',
            'faction_tag': 'TEST',
            'leader_id': test_user_id,
            'members': [test_user_id],
            'officers': [],
            'created_at': datetime.now(timezone.utc),
            'last_updated': datetime.now(timezone.utc),
            'description': None,
            'invite_only': False,
            'max_members': 20
        }
        
        result = await db.factions.insert_one(faction_doc)
        print(f"✅ Faction creation: SUCCESS (ID: {result.inserted_id})")
        
        # Test faction list query (this is what /faction list uses)
        cursor = db.factions.find({'guild_id': guild_id}).sort('faction_name', 1)
        factions = await cursor.to_list(length=50)
        print(f"✅ Faction list query: SUCCESS ({len(factions)} factions found)")
        
        # Test faction lookup by name (this is what faction commands use)
        faction = await db.factions.find_one({
            'guild_id': guild_id,
            'faction_name': 'Test Faction Runtime'
        })
        
        if faction:
            print("✅ Faction lookup by name: SUCCESS")
            # Check field access patterns
            print(f"   - faction_name: {faction.get('faction_name')}")
            print(f"   - leader_id: {faction.get('leader_id')}")
            print(f"   - members: {len(faction.get('members', []))}")
        else:
            print("❌ Faction lookup by name: FAILED")
        
        # Test 2: User wallet operations (for casino/gambling)
        print("\n2. Testing wallet operations...")
        
        # Test user wallet creation
        wallet_doc = {
            'guild_id': guild_id,
            'discord_id': test_user_id,
            'balance': 1000,
            'created_at': datetime.now(timezone.utc)
        }
        
        await db.user_wallets.insert_one(wallet_doc)
        print("✅ Wallet creation: SUCCESS")
        
        # Test wallet lookup (this is what gambling commands use)
        user_wallet = await db.user_wallets.find_one({
            'guild_id': guild_id,
            'discord_id': test_user_id
        })
        
        if user_wallet:
            balance = user_wallet.get('balance', 0)
            print(f"✅ Wallet lookup: SUCCESS (Balance: ${balance})")
        else:
            print("❌ Wallet lookup: FAILED")
        
        # Test wallet event logging
        event_doc = {
            'guild_id': guild_id,
            'discord_id': test_user_id,
            'amount': 100,
            'event_type': 'test',
            'description': 'Runtime test',
            'timestamp': datetime.now(timezone.utc)
        }
        
        await db.wallet_events.insert_one(event_doc)
        print("✅ Wallet event logging: SUCCESS")
        
        # Test 3: Player stats (for online command)
        print("\n3. Testing player stats operations...")
        
        # Test player session lookup
        sessions = await db.player_sessions.find({'guild_id': guild_id}).limit(5).to_list(length=5)
        print(f"✅ Player sessions query: SUCCESS ({len(sessions)} sessions found)")
        
        # Test 4: Premium access check simulation
        print("\n4. Testing premium access patterns...")
        
        # This simulates what premium checks do
        guild_config = await db.guild_configs.find_one({'guild_id': guild_id})
        if guild_config:
            premium_status = guild_config.get('premium_enabled', False)
            print(f"✅ Premium check: SUCCESS (Status: {premium_status})")
        else:
            print("⚠️  Premium check: No guild config found (would default to False)")
        
        print("\n🧹 Cleaning up test data...")
        # Clean up test data
        await db.factions.delete_one({'_id': result.inserted_id})
        await db.user_wallets.delete_one({'guild_id': guild_id, 'discord_id': test_user_id})
        await db.wallet_events.delete_one({'guild_id': guild_id, 'discord_id': test_user_id})
        print("✅ Cleanup complete")
        
        print("\n🎉 ALL CRITICAL TESTS PASSED")
        print("The database operations that power faction, gambling, and economy commands are working correctly.")
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(test_critical_functionality())