#!/usr/bin/env python3
"""
Debug Online Command Database Query
Check what's actually in player_sessions vs what the command queries
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

async def debug_online_command():
    """Debug why /online shows 0 when voice channel shows 4"""
    
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        print("Error: MONGO_URI environment variable not set")
        return
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client.emerald_killfeed
    
    guild_id = 1219706687980568769  # Emerald Servers
    
    try:
        print("🔍 Debugging /online command database queries...")
        
        # Query 1: What the /online command currently queries
        online_query = {
            'guild_id': guild_id,
            'status': 'online'
        }
        
        online_count = await db.player_sessions.count_documents(online_query)
        print(f"📊 Online players (command query): {online_count}")
        
        # Query 2: All recent sessions (last hour)
        from datetime import timedelta
        recent_time = datetime.now(timezone.utc) - timedelta(hours=1)
        
        recent_query = {
            'guild_id': guild_id,
            '$or': [
                {'joined_at': {'$gte': recent_time.isoformat()}},
                {'session_start': {'$gte': recent_time}},
                {'last_seen': {'$gte': recent_time}}
            ]
        }
        
        recent_sessions = []
        cursor = db.player_sessions.find(recent_query)
        async for session in cursor:
            recent_sessions.append(session)
        
        print(f"📊 Recent sessions (last hour): {len(recent_sessions)}")
        
        # Query 3: Check all current session statuses
        all_sessions_query = {'guild_id': guild_id}
        status_counts = {}
        
        cursor = db.player_sessions.find(all_sessions_query)
        async for session in cursor:
            status = session.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Show recent sessions
            joined_at = session.get('joined_at', 'Unknown')
            last_seen = session.get('last_seen', 'Unknown')
            player_name = session.get('player_name', 'Unknown')
            
            if status == 'online' or any(recent in str(joined_at) for recent in ['2025-06-01']):
                print(f"  🎮 {player_name}: {status} | Joined: {joined_at} | Last seen: {last_seen}")
        
        print(f"\n📊 Session status breakdown:")
        for status, count in status_counts.items():
            print(f"  {status}: {count}")
        
        # Query 4: Check for any sessions with recent activity
        active_query = {
            'guild_id': guild_id,
            '$or': [
                {'status': 'online'},
                {'status': 'active'},
                {'status': 'connected'},
                {'connected': True},
                {'is_online': True}
            ]
        }
        
        active_count = await db.player_sessions.count_documents(active_query)
        print(f"📊 Active players (broad query): {active_count}")
        
        # Query 5: Check if there are any collections we're missing
        collections = await db.list_collection_names()
        player_collections = [c for c in collections if 'player' in c.lower() or 'session' in c.lower()]
        print(f"\n📊 Player-related collections: {player_collections}")
        
        # Query 6: Check the most recent entries in player_sessions
        print(f"\n🔍 Most recent player_sessions entries:")
        cursor = db.player_sessions.find({'guild_id': guild_id}).sort('_id', -1).limit(5)
        async for session in cursor:
            player_name = session.get('player_name', 'Unknown')
            status = session.get('status', 'Unknown')
            timestamp = session.get('_id').generation_time if session.get('_id') else 'Unknown'
            print(f"  • {player_name}: {status} (created: {timestamp})")
        
    except Exception as e:
        print(f"Error debugging: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(debug_online_command())