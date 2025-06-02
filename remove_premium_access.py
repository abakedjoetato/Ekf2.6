#!/usr/bin/env python3
"""
Remove Premium Access from Guild
Removes premium_access and premium_servers from the specified guild for testing premium gating
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def remove_premium_access():
    """Remove premium access from the guild to test premium restrictions"""
    
    # Connect to MongoDB
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        print("❌ MONGO_URI environment variable not found")
        return
        
    client = AsyncIOMotorClient(mongo_uri)
    db = client['emeralds_killfeed']
    
    guild_id = 1219706687980568769  # Emerald Servers
    
    try:
        # Remove premium access and premium servers
        result = await db.guilds.update_one(
            {"guild_id": guild_id},
            {"$unset": {"premium_access": "", "premium_servers": ""}}
        )
        
        if result.modified_count > 0:
            print(f"✅ Removed premium access from guild {guild_id}")
            print("   Now you can test the premium restriction messages")
        else:
            print(f"ℹ️  Guild {guild_id} already has no premium access")
            
        # Verify the change
        guild_config = await db.guilds.find_one({"guild_id": guild_id})
        if guild_config:
            has_premium_access = guild_config.get('premium_access', False)
            has_premium_servers = bool(guild_config.get('premium_servers', []))
            print(f"📊 Current status: premium_access={has_premium_access}, premium_servers={has_premium_servers}")
        else:
            print("📊 No guild configuration found")
            
    except Exception as e:
        print(f"❌ Error removing premium access: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(remove_premium_access())