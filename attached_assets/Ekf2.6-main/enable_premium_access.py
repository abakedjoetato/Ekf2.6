#!/usr/bin/env python3
"""
Enable Premium Access for Guild
Updates MongoDB to enable premium features for testing
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

async def enable_premium_access():
    """Enable premium access for the guild"""
    
    # Connect to MongoDB
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        print("Error: MONGO_URI environment variable not set")
        return
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client.EmeraldDB
    
    guild_id = 1219706687980568769  # Emerald Servers
    
    try:
        # Update guild config to enable premium
        result = await db.guild_configs.update_one(
            {'guild_id': guild_id},
            {
                '$set': {
                    'premium_enabled': True,
                    'premium_updated': datetime.now(timezone.utc),
                    'features_enabled': {
                        'ultra_casino': True,
                        'advanced_gambling': True,
                        'quantum_slots': True,
                        'premium_stats': True
                    }
                }
            },
            upsert=True
        )
        
        if result.upserted_id or result.modified_count > 0:
            print(f"✅ Premium access enabled for guild {guild_id}")
            print("✅ Ultra-advanced casino system is now accessible")
            print("✅ Use /casino command in Discord to test the system")
        else:
            print("⚠️ No changes made - premium may already be enabled")
            
        # Verify the update
        guild_config = await db.guild_configs.find_one({'guild_id': guild_id})
        if guild_config and guild_config.get('premium_enabled', False):
            print("✅ Premium status verified in database")
        else:
            print("❌ Failed to verify premium status")
            
    except Exception as e:
        print(f"❌ Error enabling premium access: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(enable_premium_access())