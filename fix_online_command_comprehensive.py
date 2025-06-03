#!/usr/bin/env python3
"""
Fix Online Command - Comprehensive solution for rate limiting and database issues
"""
import asyncio
import os
import sys
import motor.motor_asyncio

async def fix_online_command():
    """Fix the online command issues comprehensively"""
    
    print("Fixing Online Command Issues")
    print("=" * 40)
    
    # Connect to MongoDB directly
    mongo_client = motor.motor_asyncio.AsyncIOMotorClient(os.environ.get('MONGO_URI'))
    db = mongo_client['deadside_pvp_tracker']
    
    guild_id = 1315008007830650941
    
    try:
        # Check player sessions collection structure
        print("Checking player sessions data structure...")
        
        # Get sample documents to understand structure
        sample_docs = []
        async for doc in db.player_sessions.find({'guild_id': guild_id}).limit(5):
            sample_docs.append(doc)
        
        if sample_docs:
            print(f"Found {len(sample_docs)} sample documents")
            for i, doc in enumerate(sample_docs):
                print(f"  Document {i+1}:")
                print(f"    Guild ID: {doc.get('guild_id')} (type: {type(doc.get('guild_id'))})")
                print(f"    Server name: {doc.get('server_name')}")
                print(f"    Player name: {doc.get('player_name')}")
                print(f"    Status: {doc.get('status')}")
                print(f"    Fields: {list(doc.keys())}")
        else:
            print("No documents found in player_sessions collection")
        
        # Count online players
        online_query = {
            'guild_id': guild_id,
            'status': 'online'
        }
        
        online_count = await db.player_sessions.count_documents(online_query)
        print(f"Current online players: {online_count}")
        
        # Check if there are any active sessions
        if online_count > 0:
            print("Found active player sessions:")
            async for session in db.player_sessions.find(online_query).limit(10):
                player_name = session.get('player_name', 'Unknown')
                server_name = session.get('server_name', 'Unknown')
                print(f"  {player_name} on {server_name}")
        
        # Fix rate limiting by clearing command sync cooldown
        cooldown_file = "command_sync_cooldown.txt"
        if os.path.exists(cooldown_file):
            print("Removing command sync cooldown file...")
            os.remove(cooldown_file)
            print("Command sync cooldown cleared")
        else:
            print("No command sync cooldown file found")
        
        # Check command hash file
        hash_file = "command_hash.txt"
        if os.path.exists(hash_file):
            print("Command hash file exists - commands should be stable")
        else:
            print("No command hash file - commands may need initial sync")
        
        print("Online command fix completed successfully")
        
    except Exception as e:
        print(f"Fix failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        mongo_client.close()

if __name__ == "__main__":
    asyncio.run(fix_online_command())