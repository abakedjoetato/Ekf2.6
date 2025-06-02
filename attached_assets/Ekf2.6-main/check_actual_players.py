#!/usr/bin/env python3
"""
Check Actual Player Sessions in Database
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

async def check_player_sessions():
    """Check what's actually in the player_sessions collection"""
    
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        print("Error: MONGO_URI environment variable not set")
        return
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client.emerald_killfeed
    
    guild_id = 1219706687980568769  # Emerald Servers
    
    try:
        # Check total documents
        total_count = await db.player_sessions.count_documents({})
        print(f"Total player_sessions documents: {total_count}")
        
        # Check for this guild
        guild_count = await db.player_sessions.count_documents({'guild_id': guild_id})
        print(f"Player sessions for guild {guild_id}: {guild_count}")
        
        # Check online players for this guild
        online_count = await db.player_sessions.count_documents({
            'guild_id': guild_id,
            'status': 'online'
        })
        print(f"Online players for guild {guild_id}: {online_count}")
        
        # Check by server
        server_counts = {}
        cursor = db.player_sessions.find({'guild_id': guild_id})
        async for session in cursor:
            server_id = session.get('server_id', 'unknown')
            status = session.get('status', 'unknown')
            key = f"{server_id}_{status}"
            server_counts[key] = server_counts.get(key, 0) + 1
        
        print(f"\nBreakdown by server and status:")
        for key, count in server_counts.items():
            print(f"  {key}: {count}")
        
        # Show some actual session examples
        print(f"\nActual session examples:")
        cursor = db.player_sessions.find({'guild_id': guild_id}).limit(5)
        async for session in cursor:
            player_name = session.get('player_name', session.get('character_name', 'Unknown'))
            server_id = session.get('server_id', 'Unknown')
            status = session.get('status', 'Unknown')
            joined_at = session.get('joined_at', 'Unknown')
            print(f"  • {player_name} | Server: {server_id} | Status: {status} | Joined: {joined_at}")
        
    except Exception as e:
        print(f"Error checking sessions: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(check_player_sessions())