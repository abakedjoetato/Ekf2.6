#!/usr/bin/env python3
"""
Test Online Command Functionality
Creates test player sessions and verifies /online command works
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

async def create_test_player_sessions():
    """Create test player sessions to verify /online command"""
    
    # Connect to MongoDB
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        print("Error: MONGO_URI environment variable not set")
        return
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client.emerald_killfeed
    
    guild_id = 1219706687980568769  # Emerald Servers
    server_id = "7020"  # Emerald EU
    
    # Test player sessions
    test_sessions = [
        {
            'guild_id': guild_id,
            'server_id': server_id,
            'player_id': '76561198123456789',
            'player_name': 'TestPlayer1',
            'character_name': 'TestPlayer1',
            'platform': 'PC',
            'status': 'online',
            'joined_at': datetime.now(timezone.utc).isoformat(),
            'last_seen': datetime.now(timezone.utc),
            'session_start': datetime.now(timezone.utc)
        },
        {
            'guild_id': guild_id,
            'server_id': server_id,
            'player_id': '76561198987654321',
            'player_name': 'TestPlayer2',
            'character_name': 'TestPlayer2', 
            'platform': 'PC',
            'status': 'online',
            'joined_at': datetime.now(timezone.utc).isoformat(),
            'last_seen': datetime.now(timezone.utc),
            'session_start': datetime.now(timezone.utc)
        },
        {
            'guild_id': guild_id,
            'server_id': server_id,
            'player_id': '76561198555666777',
            'player_name': 'TestPlayer3',
            'character_name': 'TestPlayer3',
            'platform': 'Console',
            'status': 'online', 
            'joined_at': datetime.now(timezone.utc).isoformat(),
            'last_seen': datetime.now(timezone.utc),
            'session_start': datetime.now(timezone.utc)
        }
    ]
    
    try:
        # Clear existing test sessions first
        await db.player_sessions.delete_many({
            'guild_id': guild_id,
            'player_name': {'$regex': '^TestPlayer'}
        })
        
        # Insert test sessions
        result = await db.player_sessions.insert_many(test_sessions)
        
        print(f"✅ Created {len(result.inserted_ids)} test player sessions")
        print(f"✅ Guild ID: {guild_id}")
        print(f"✅ Server ID: {server_id}")
        print("✅ Test players:")
        for session in test_sessions:
            print(f"  • {session['player_name']} ({session['platform']}) - {session['status']}")
        
        # Verify the sessions were created
        count = await db.player_sessions.count_documents({
            'guild_id': guild_id,
            'server_id': server_id,
            'status': 'online'
        })
        
        print(f"✅ Total online players in database: {count}")
        print("✅ You can now test /online command in Discord")
        
    except Exception as e:
        print(f"❌ Error creating test sessions: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(create_test_player_sessions())