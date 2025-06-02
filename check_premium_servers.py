#!/usr/bin/env python3
"""
Check Premium Server Configuration
Examines actual premium server assignments for the guild
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

async def check_premium_servers():
    """Check current premium server configuration"""
    
    # Connect to MongoDB
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        print("Error: MONGO_URI environment variable not set")
        return
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client.EmeraldDB
    
    guild_id = 1219706687980568769  # Emerald Servers
    
    try:
        print(f"🔍 Checking premium configuration for guild {guild_id}")
        
        # Check guild_configs for servers with premium status
        guild_config = await db.guild_configs.find_one({'guild_id': guild_id})
        if guild_config:
            print(f"✅ Found guild config")
            servers = guild_config.get('servers', [])
            print(f"📋 Total servers configured: {len(servers)}")
            
            premium_servers = []
            for server in servers:
                server_id = server.get('_id') or server.get('server_id')
                server_name = server.get('name', 'Unknown')
                is_premium = server.get('premium', False)
                
                print(f"  🖥️ Server: {server_name} (ID: {server_id}) - Premium: {is_premium}")
                
                if is_premium:
                    premium_servers.append(server)
            
            print(f"💎 Premium servers found: {len(premium_servers)}")
            
            # Check new premium system collections
            premium_subscriptions = await db.premium_subscriptions.find({'guild_id': guild_id}).to_list(None)
            print(f"📋 Premium subscriptions in new system: {len(premium_subscriptions)}")
            
            premium_assignments = await db.premium_assignments.find_one({'guild_id': guild_id})
            if premium_assignments:
                print(f"🎯 Premium assignments found:")
                print(f"  Total slots: {premium_assignments.get('total_slots', 0)}")
                print(f"  Used slots: {premium_assignments.get('used_slots', 0)}")
                print(f"  Available slots: {premium_assignments.get('available_slots', 0)}")
            else:
                print("❌ No premium assignments found in new system")
            
            # Check server_premium_status collection
            server_statuses = await db.server_premium_status.find({'guild_id': guild_id}).to_list(None)
            print(f"🔧 Server premium statuses: {len(server_statuses)}")
            for status in server_statuses:
                server_id = status.get('server_id')
                is_active = status.get('is_premium', False)
                print(f"  🖥️ Server {server_id}: Premium active: {is_active}")
            
        else:
            print("❌ No guild config found")
            
    except Exception as e:
        print(f"❌ Error checking premium servers: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(check_premium_servers())