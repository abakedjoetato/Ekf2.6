#!/usr/bin/env python3
"""
Fix Player Session Tracking
Ensure players are properly marked as online when active on servers
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

async def fix_player_session_tracking():
    """Fix player session tracking to show currently online players"""
    
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        print("Error: MONGO_URI environment variable not set")
        return
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client.emerald_killfeed
    
    guild_id = 1219706687980568769  # Emerald Servers
    
    try:
        print("🔧 Fixing player session tracking...")
        
        # Find recent sessions that should be online
        from datetime import timedelta
        recent_time = datetime.now(timezone.utc) - timedelta(minutes=30)
        
        # Look for players who joined recently but are marked offline
        recent_joiners_query = {
            'guild_id': guild_id,
            'joined_at': {'$gte': recent_time.isoformat()},
            'status': 'offline'
        }
        
        recent_joiners = []
        cursor = db.player_sessions.find(recent_joiners_query)
        async for session in cursor:
            recent_joiners.append(session)
        
        print(f"📊 Found {len(recent_joiners)} recent joiners marked as offline")
        
        if recent_joiners:
            print("🔄 Marking recent joiners as online...")
            
            for session in recent_joiners:
                player_name = session.get('player_name', 'Unknown')
                joined_at = session.get('joined_at')
                
                # Update to online status
                update_result = await db.player_sessions.update_one(
                    {'_id': session['_id']},
                    {
                        '$set': {
                            'status': 'online',
                            'last_seen': datetime.now(timezone.utc),
                            'updated_at': datetime.now(timezone.utc)
                        },
                        '$unset': {
                            'cleanup_reason': '',
                            'disconnected_at': ''
                        }
                    }
                )
                
                if update_result.modified_count > 0:
                    print(f"  ✅ Marked {player_name} as online (joined: {joined_at})")
        
        # Check current online count after fixes
        online_count = await db.player_sessions.count_documents({
            'guild_id': guild_id,
            'status': 'online'
        })
        
        print(f"📊 Current online players after fix: {online_count}")
        
        # Show online players
        if online_count > 0:
            print("🎮 Currently online players:")
            cursor = db.player_sessions.find({
                'guild_id': guild_id,
                'status': 'online'
            })
            
            async for session in cursor:
                player_name = session.get('player_name', 'Unknown')
                server_id = session.get('server_id', 'Unknown')
                joined_at = session.get('joined_at', 'Unknown')
                print(f"  • {player_name} on server {server_id} (joined: {joined_at})")
        
    except Exception as e:
        print(f"Error fixing sessions: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(fix_player_session_tracking())