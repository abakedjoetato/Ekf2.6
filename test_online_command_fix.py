"""
Test Online Command Fix - Check if /online command now works properly
"""

import asyncio
import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bot.models.database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_online_command():
    """Test the /online command functionality"""
    try:
        # Connect to database using same method as main bot
        mongo_uri = os.getenv('MONGO_URI')
        if not mongo_uri:
            print("❌ MONGO_URI environment variable not found")
            return
        
        client = AsyncIOMotorClient(mongo_uri)
        db_manager = DatabaseManager(client)
        await db_manager.initialize()
        
        # Check current player sessions
        guild_id = 1219706687980568769  # Emerald Servers
        
        # Count total sessions
        total_sessions = await db_manager.player_sessions.count_documents({'guild_id': guild_id})
        print(f"Total player sessions for guild {guild_id}: {total_sessions}")
        
        # Count online sessions
        online_sessions = await db_manager.player_sessions.count_documents({
            'guild_id': guild_id,
            'state': 'online'
        })
        print(f"Online player sessions: {online_sessions}")
        
        # List all sessions
        all_sessions = await db_manager.player_sessions.find({'guild_id': guild_id}).to_list(length=50)
        print(f"\nAll player sessions:")
        for session in all_sessions:
            print(f"  {session.get('character_name')} - {session.get('state')} - Server: {session.get('server_name')} - Last seen: {session.get('last_seen')}")
        
        # Test the guild configuration
        guild_config = await db_manager.get_guild(guild_id)
        if guild_config:
            print(f"\nGuild configuration found:")
            print(f"  Servers: {len(guild_config.get('servers', []))}")
            for server in guild_config.get('servers', []):
                print(f"    {server.get('name')} - Enabled: {server.get('enabled', False)}")
        else:
            print(f"❌ No guild configuration found for {guild_id}")
        
        # Check if SSH credentials are available
        ssh_host = os.getenv('SSH_HOST')
        ssh_user = os.getenv('SSH_USERNAME')
        ssh_pass = os.getenv('SSH_PASSWORD')
        
        print(f"\nSSH Configuration:")
        print(f"  Host: {'✅' if ssh_host else '❌'} {ssh_host or 'Not set'}")
        print(f"  Username: {'✅' if ssh_user else '❌'} {ssh_user or 'Not set'}")
        print(f"  Password: {'✅' if ssh_pass else '❌'} {'Set' if ssh_pass else 'Not set'}")
        
        await client.close()
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_online_command())