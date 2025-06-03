#!/usr/bin/env python3
"""
Test Online Command Fix - Verify /online command functionality
"""
import asyncio
import os
import sys
from datetime import datetime

# Add the bot directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bot'))

from bot.models.database import DatabaseManager
import motor.motor_asyncio

async def test_online_command_fix():
    """Test the online command database queries"""
    
    print("🔍 Testing Online Command Database Queries")
    print("=" * 50)
    
    # Initialize database connection
    mongo_client = motor.motor_asyncio.AsyncIOMotorClient(os.environ.get('MONGO_URI'))
    db_manager = DatabaseManager(mongo_client)
    await db_manager.initialize()
    
    guild_id = 1315008007830650941
    
    try:
        # Test query for online players
        print(f"\n📊 Testing player sessions query for guild {guild_id}")
        
        query = {
            'guild_id': guild_id,
            'status': 'online'
        }
        
        cursor = db_manager.player_sessions.find(query)
        online_players = []
        
        async for session in cursor:
            server_name = session.get('server_name', 'Unknown')
            player_name = session.get('player_name', session.get('character_name', 'Unknown'))
            status = session.get('status', 'Unknown')
            joined_at = session.get('joined_at')
            
            online_players.append({
                'server_name': server_name,
                'player_name': player_name,
                'status': status,
                'joined_at': joined_at
            })
            
            print(f"   Player: {player_name} on {server_name} (Status: {status})")
        
        print(f"\n📈 Found {len(online_players)} online players")
        
        # Test server-specific query
        print(f"\n📊 Testing server-specific query for 'Emerald EU'")
        
        server_query = {
            'guild_id': guild_id,
            'server_name': 'Emerald EU',
            'status': 'online'
        }
        
        server_cursor = db_manager.player_sessions.find(server_query)
        server_players = []
        
        async for session in server_cursor:
            player_name = session.get('player_name', session.get('character_name', 'Unknown'))
            status = session.get('status', 'Unknown')
            joined_at = session.get('joined_at')
            
            server_players.append({
                'player_name': player_name,
                'status': status,
                'joined_at': joined_at
            })
            
            print(f"   Player: {player_name} (Status: {status})")
        
        print(f"\n📈 Found {len(server_players)} online players on Emerald EU")
        
        # Verify database structure
        print(f"\n🗄️ Database Structure Verification:")
        
        # Get one sample document to check structure
        sample_doc = await db_manager.player_sessions.find_one({'guild_id': guild_id})
        if sample_doc:
            print(f"   Sample document fields: {list(sample_doc.keys())}")
            print(f"   Guild ID type: {type(sample_doc.get('guild_id'))}")
            print(f"   Server name: {sample_doc.get('server_name')}")
            print(f"   Status: {sample_doc.get('status')}")
        else:
            print("   No sample document found")
        
        # Count total sessions
        total_sessions = await db_manager.player_sessions.count_documents({'guild_id': guild_id})
        print(f"   Total sessions for guild: {total_sessions}")
        
        online_count = await db_manager.player_sessions.count_documents({
            'guild_id': guild_id,
            'status': 'online'
        })
        print(f"   Online sessions: {online_count}")
        
        print(f"\n✅ Online command database queries working correctly")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        mongo_client.close()

if __name__ == "__main__":
    asyncio.run(test_online_command_fix())