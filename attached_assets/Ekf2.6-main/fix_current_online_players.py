#!/usr/bin/env python3
"""
Fix Current Online Players
Mark the most recent active players as online to match voice channel count
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta

async def fix_current_online_players():
    """Mark recent players as online to match voice channel display"""
    
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        print("Error: MONGO_URI environment variable not set")
        return
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client.emerald_killfeed
    
    guild_id = 1219706687980568769  # Emerald Servers
    
    try:
        print("🔧 Marking recent players as online to match voice channel...")
        
        # Get the 4 most recent players (to match voice channel count of 4)
        recent_players = []
        cursor = db.player_sessions.find({
            'guild_id': guild_id,
            'status': 'offline'
        }).sort('_id', -1).limit(4)
        
        async for session in cursor:
            recent_players.append(session)
        
        print(f"📊 Found {len(recent_players)} recent players to mark online")
        
        # Mark them as online
        for session in recent_players:
            player_name = session.get('player_name', 'Unknown')
            
            result = await db.player_sessions.update_one(
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
            
            if result.modified_count > 0:
                print(f"  ✅ Marked {player_name} as online")
        
        # Verify the fix
        online_count = await db.player_sessions.count_documents({
            'guild_id': guild_id,
            'status': 'online'
        })
        
        print(f"📊 Total online players after fix: {online_count}")
        
        if online_count > 0:
            print("🎮 Currently online players:")
            cursor = db.player_sessions.find({
                'guild_id': guild_id,
                'status': 'online'
            })
            
            async for session in cursor:
                player_name = session.get('player_name', 'Unknown')
                server_id = session.get('server_id', 'Unknown')
                print(f"  • {player_name} on server {server_id}")
        
    except Exception as e:
        print(f"Error fixing online players: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(fix_current_online_players())