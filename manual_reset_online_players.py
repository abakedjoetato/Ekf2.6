#!/usr/bin/env python3
"""
Manual Reset Online Players
Resets all players to offline for clean cold start
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

async def manual_reset_online_players():
    """Manually reset all players to offline for clean cold start"""
    
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        print("Error: MONGO_URI environment variable not set")
        return
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client.emerald_killfeed
    
    guild_id = 1219706687980568769  # Emerald Servers
    
    try:
        print("🔄 Manually resetting all players to offline...")
        
        # Reset ALL players for this guild to offline
        reset_result = await db.player_sessions.update_many(
            {'guild_id': guild_id},
            {
                '$set': {
                    'status': 'offline',
                    'last_seen': datetime.now(timezone.utc),
                    'cleanup_reason': 'Manual cold start reset',
                    'disconnected_at': datetime.now(timezone.utc)
                },
                '$unset': {
                    'updated_at': ''
                }
            }
        )
        
        print(f"✅ Reset {reset_result.modified_count} players to offline")
        
        # Verify reset
        online_count = await db.player_sessions.count_documents({
            'guild_id': guild_id,
            'status': 'online'
        })
        
        print(f"📊 Online players after reset: {online_count}")
        
        if online_count == 0:
            print("✅ Clean slate achieved - next parser run will rebuild accurate state")
        else:
            print("⚠️  Some players still online - may need database refresh")
        
    except Exception as e:
        print(f"Error resetting players: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(manual_reset_online_players())