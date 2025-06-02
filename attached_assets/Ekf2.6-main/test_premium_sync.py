#!/usr/bin/env python3
"""
Test Premium Sync System
Validates that guild premium flags sync correctly with server premium status
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

async def test_premium_sync():
    """Test the premium sync system"""
    
    # Connect to MongoDB
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        print("Error: MONGO_URI environment variable not set")
        return
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client.EmeraldDB
    
    guild_id = 1219706687980568769  # Emerald Servers
    
    try:
        print(f"🧪 Testing premium sync for guild {guild_id}")
        
        # Get current guild config
        guild_config = await db.guild_configs.find_one({'guild_id': guild_id})
        if not guild_config:
            print("❌ No guild config found")
            return
        
        servers = guild_config.get('servers', [])
        premium_flag = guild_config.get('premium_enabled', False)
        
        print(f"📋 Current state:")
        print(f"  Premium flag: {premium_flag}")
        print(f"  Total servers: {len(servers)}")
        
        premium_servers = [s for s in servers if s.get('premium', False)]
        print(f"  Premium servers: {len(premium_servers)}")
        
        for server in premium_servers:
            print(f"    💎 {server.get('name')} (ID: {server.get('_id')})")
        
        # Test the logic
        should_have_premium = len(premium_servers) > 0
        is_synced = premium_flag == should_have_premium
        
        print(f"\n🔍 Sync Analysis:")
        print(f"  Should have premium: {should_have_premium}")
        print(f"  Currently has premium flag: {premium_flag}")
        print(f"  Is synchronized: {is_synced}")
        
        if is_synced:
            print("✅ Premium flag is correctly synchronized")
        else:
            print("⚠️ Premium flag needs synchronization")
            
            # Show what the sync would do
            action = "enable" if should_have_premium else "disable"
            print(f"  Sync would {action} premium access")
        
        # Test casino access logic
        print(f"\n🎰 Casino Access Test:")
        
        # Method 1: Premium flag check
        method1_access = premium_flag
        print(f"  Method 1 (premium_enabled flag): {method1_access}")
        
        # Method 2: Server premium check
        method2_access = len(premium_servers) > 0
        print(f"  Method 2 (server premium status): {method2_access}")
        
        # Method 3: Combined check (what the casino actually uses)
        method3_access = premium_flag or len(premium_servers) > 0
        print(f"  Method 3 (combined check): {method3_access}")
        
        if method1_access and method2_access and method3_access:
            print("✅ Casino should be accessible via all methods")
        elif method3_access:
            print("✅ Casino should be accessible via combined check")
        else:
            print("❌ Casino would not be accessible")
        
        print(f"\n📊 Summary:")
        print(f"  Guild has {len(premium_servers)} premium server(s)")
        print(f"  Premium flag is {'set' if premium_flag else 'not set'}")
        print(f"  Casino access: {'✅ Granted' if method3_access else '❌ Denied'}")
        
    except Exception as e:
        print(f"❌ Error testing premium sync: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(test_premium_sync())