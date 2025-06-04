"""
Fix Server Path Configuration - Remove hardcoded log_path to use dynamic pattern
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def fix_server_path():
    """Remove hardcoded log_path from server configuration to use dynamic pattern"""
    try:
        # Connect to database
        mongo_uri = os.getenv('MONGO_URI')
        if not mongo_uri:
            print("Missing MONGO_URI environment variable")
            return
        
        client = AsyncIOMotorClient(mongo_uri)
        db = client.EmeraldDB
        
        guild_id = 1219706687980568769  # Emerald Servers
        
        # Remove log_path field so dynamic pattern is used
        result = await db.guilds.update_one(
            {'guild_id': guild_id},
            {
                '$unset': {'servers.0.log_path': 1}
            }
        )
        
        if result.modified_count > 0:
            print("✅ Removed hardcoded log_path from server configuration")
            print("   Dynamic path pattern will now be used: ./79.127.236.1_7020/Logs/Deadside.log")
        else:
            print("❌ Failed to update server configuration")
        
        # Verify the configuration
        guild_config = await db.guilds.find_one({'guild_id': guild_id})
        if guild_config and guild_config.get('servers'):
            server = guild_config['servers'][0]
            print(f"\n📊 Current server configuration:")
            print(f"   Name: {server.get('name')}")
            print(f"   Server ID: {server.get('server_id')}")
            print(f"   Host: {server.get('host')}")
            print(f"   Log path: {server.get('log_path', 'Will use dynamic pattern')}")
        
        client.close()
        
    except Exception as e:
        print(f"Configuration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_server_path())