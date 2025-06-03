#!/usr/bin/env python3
"""
Fix Player State Accuracy - Clean up stale player states and implement proper state management
"""
import asyncio
import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_player_state_accuracy():
    """Fix critical player state accuracy issues"""
    try:
        # Connect to MongoDB
        mongo_client = AsyncIOMotorClient(os.environ.get('MONGO_URI'))
        db = mongo_client.emerald_killfeed
        
        guild_id = 1219706687980568769
        server_name = "Emerald EU"
        
        print(f"=== FIXING PLAYER STATE ACCURACY ===")
        
        # Step 1: Check current state
        current_sessions = await db.player_sessions.find({
            "guild_id": guild_id,
            "server_name": server_name
        }).to_list(length=None)
        
        print(f"Found {len(current_sessions)} player sessions")
        
        # Step 2: Clear all stale sessions (older than 1 hour should be considered disconnected)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        stale_sessions = await db.player_sessions.find({
            "guild_id": guild_id,
            "server_name": server_name,
            "state": "online",
            "last_updated": {"$lt": one_hour_ago}
        }).to_list(length=None)
        
        print(f"Found {len(stale_sessions)} stale 'online' sessions (older than 1 hour)")
        
        if stale_sessions:
            # Update stale sessions to offline
            result = await db.player_sessions.update_many(
                {
                    "guild_id": guild_id,
                    "server_name": server_name,
                    "state": "online",
                    "last_updated": {"$lt": one_hour_ago}
                },
                {
                    "$set": {
                        "state": "offline",
                        "last_updated": datetime.utcnow()
                    }
                }
            )
            print(f"Updated {result.modified_count} stale sessions to offline")
        
        # Step 3: Force all current sessions to offline (since we know from logs no one is actually connected)
        print(f"=== FORCING ALL SESSIONS OFFLINE (based on disconnect logs) ===")
        
        all_online = await db.player_sessions.update_many(
            {
                "guild_id": guild_id,
                "server_name": server_name,
                "state": {"$in": ["online", "queued"]}
            },
            {
                "$set": {
                    "state": "offline",
                    "last_updated": datetime.utcnow()
                }
            }
        )
        print(f"Forced {all_online.modified_count} sessions to offline state")
        
        # Step 4: Verify the fix
        final_count = await db.player_sessions.count_documents({
            "guild_id": guild_id,
            "server_name": server_name,
            "state": "online"
        })
        
        print(f"=== VERIFICATION ===")
        print(f"Final online player count: {final_count}")
        print(f"Voice channel should now show: {final_count}/50 players")
        
        # Step 5: Show all current states
        final_sessions = await db.player_sessions.find({
            "guild_id": guild_id,
            "server_name": server_name
        }).to_list(length=None)
        
        state_counts = {}
        for session in final_sessions:
            state = session.get('state', 'unknown')
            state_counts[state] = state_counts.get(state, 0) + 1
        
        print(f"\nFinal state distribution:")
        for state, count in state_counts.items():
            print(f"  {state}: {count}")
        
        mongo_client.close()
        print(f"\n=== PLAYER STATE ACCURACY FIXED ===")
        
    except Exception as e:
        logger.error(f"Failed to fix player state accuracy: {e}")

if __name__ == "__main__":
    asyncio.run(fix_player_state_accuracy())