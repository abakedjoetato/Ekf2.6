#!/usr/bin/env python3
"""
Fix Stale Player Sessions
Marks old sessions as offline and implements proper session management
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta

async def fix_stale_sessions():
    """Clean up stale player sessions and mark them as offline"""
    
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        print("Error: MONGO_URI environment variable not set")
        return
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client.emerald_killfeed
    
    guild_id = 1219706687980568769  # Emerald Servers
    
    try:
        # Define session timeout (30 minutes of inactivity)
        timeout_threshold = datetime.now(timezone.utc) - timedelta(minutes=30)
        
        print(f"Checking for sessions older than: {timeout_threshold}")
        
        # Find stale sessions (older than 30 minutes and still marked online)
        stale_query = {
            'guild_id': guild_id,
            'status': 'online',
            '$or': [
                {'last_seen': {'$lt': timeout_threshold}},
                {'joined_at': {'$lt': timeout_threshold.isoformat()}},
                {'session_start': {'$lt': timeout_threshold}}
            ]
        }
        
        # Count stale sessions
        stale_count = await db.player_sessions.count_documents(stale_query)
        print(f"Found {stale_count} stale sessions to clean up")
        
        if stale_count > 0:
            # Mark stale sessions as offline
            update_result = await db.player_sessions.update_many(
                stale_query,
                {
                    '$set': {
                        'status': 'offline',
                        'disconnected_at': datetime.now(timezone.utc),
                        'cleanup_reason': 'session_timeout'
                    }
                }
            )
            
            print(f"✅ Marked {update_result.modified_count} stale sessions as offline")
        
        # Remove test players we created earlier
        test_cleanup = await db.player_sessions.delete_many({
            'guild_id': guild_id,
            'player_name': {'$regex': '^TestPlayer'}
        })
        
        if test_cleanup.deleted_count > 0:
            print(f"✅ Removed {test_cleanup.deleted_count} test player sessions")
        
        # Check current state
        current_online = await db.player_sessions.count_documents({
            'guild_id': guild_id,
            'status': 'online'
        })
        
        print(f"✅ Current online players after cleanup: {current_online}")
        
        # Show remaining online players if any
        if current_online > 0:
            print(f"\nRemaining online players:")
            cursor = db.player_sessions.find({
                'guild_id': guild_id,
                'status': 'online'
            }).limit(10)
            
            async for session in cursor:
                player_name = session.get('player_name', 'Unknown')
                server_id = session.get('server_id', 'Unknown')
                joined_at = session.get('joined_at', 'Unknown')
                last_seen = session.get('last_seen', 'Unknown')
                print(f"  • {player_name} | Server: {server_id} | Joined: {joined_at} | Last seen: {last_seen}")
        
    except Exception as e:
        print(f"Error cleaning up sessions: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(fix_stale_sessions())