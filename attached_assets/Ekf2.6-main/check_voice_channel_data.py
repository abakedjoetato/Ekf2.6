#!/usr/bin/env python3
"""
Check Voice Channel Data Source
Find where the voice channel gets its player count vs /online command
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def check_voice_channel_data():
    """Check what data source the voice channel uses vs /online command"""
    
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        print("Error: MONGO_URI environment variable not set")
        return
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client.emerald_killfeed
    
    guild_id = 1219706687980568769  # Emerald Servers
    
    try:
        print("🔍 Checking all possible data sources for player counts...")
        
        # Check all collections that might contain player data
        collections = await db.list_collection_names()
        
        for collection_name in collections:
            if any(keyword in collection_name.lower() for keyword in ['player', 'session', 'online', 'active', 'voice']):
                collection = db[collection_name]
                count = await collection.count_documents({'guild_id': guild_id})
                if count > 0:
                    print(f"\n📊 Collection: {collection_name} ({count} documents)")
                    
                    # Show sample documents
                    cursor = collection.find({'guild_id': guild_id}).limit(3)
                    async for doc in cursor:
                        # Remove sensitive data but show structure
                        safe_doc = {}
                        for key, value in doc.items():
                            if key in ['_id', 'guild_id', 'server_id']:
                                safe_doc[key] = value
                            elif 'name' in key.lower():
                                safe_doc[key] = str(value)[:20] + "..." if len(str(value)) > 20 else value
                            elif key in ['status', 'online', 'active', 'connected', 'is_online']:
                                safe_doc[key] = value
                            elif 'time' in key.lower() or 'date' in key.lower():
                                safe_doc[key] = str(value)[:19] if value else None
                            else:
                                safe_doc[key] = f"<{type(value).__name__}>"
                        
                        print(f"  Sample: {safe_doc}")
        
        # Check for any recent activity indicators
        print(f"\n🔍 Checking for recent activity indicators...")
        
        # Look for any documents with current timestamps
        from datetime import datetime, timezone, timedelta
        recent_time = datetime.now(timezone.utc) - timedelta(minutes=10)
        
        # Check parser_states for recent activity
        recent_parser = await db.parser_states.count_documents({
            'guild_id': guild_id,
            'last_processed': {'$gte': recent_time}
        })
        print(f"📊 Recent parser activity: {recent_parser}")
        
        # Check if there's a separate active players tracking
        recent_updates = await db.player_sessions.count_documents({
            'guild_id': guild_id,
            '$or': [
                {'last_seen': {'$gte': recent_time}},
                {'updated_at': {'$gte': recent_time}},
                {'modified': {'$gte': recent_time}}
            ]
        })
        print(f"📊 Recently updated sessions: {recent_updates}")
        
    except Exception as e:
        print(f"Error checking data: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(check_voice_channel_data())