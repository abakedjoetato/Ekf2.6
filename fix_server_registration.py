#!/usr/bin/env python3
"""
Fix Server Registration Issue
Properly registers existing servers that are connecting but not in database
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

async def fix_server_registration():
    """Fix the server registration issue for Emerald Servers guild"""
    
    # Connect to MongoDB
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        print("Error: MONGO_URI environment variable not set")
        return
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client.EmeraldDB
    
    guild_id = 1219706687980568769  # Emerald Servers
    
    try:
        print(f"🔧 Fixing server registration for guild {guild_id}")
        
        # Define the servers that should be registered based on parser connections
        # From the logs, we can see Emerald EU (ID: 7020, Host: 79.127.236.1)
        servers_to_register = [
            {
                "_id": "7020",
                "server_id": "7020", 
                "name": "Emerald EU",
                "host": "79.127.236.1",
                "port": 8822,
                "username": "baked",  # From the SSH logs
                "premium": True,  # This should be a premium server
                "active": True,
                "region": "EU",
                "added_date": datetime.now(timezone.utc),
                "last_seen": datetime.now(timezone.utc)
            }
        ]
        
        # Get current guild config
        guild_config = await db.guild_configs.find_one({'guild_id': guild_id})
        if not guild_config:
            print("Creating new guild configuration...")
            guild_config = {
                'guild_id': guild_id,
                'servers': [],
                'premium_enabled': True,
                'created_at': datetime.now(timezone.utc)
            }
        
        current_servers = guild_config.get('servers', [])
        print(f"Current servers in database: {len(current_servers)}")
        
        # Add missing servers
        for server in servers_to_register:
            # Check if server already exists
            server_exists = any(
                s.get('_id') == server['_id'] or s.get('server_id') == server['server_id'] 
                for s in current_servers
            )
            
            if not server_exists:
                current_servers.append(server)
                print(f"✅ Added server: {server['name']} (ID: {server['_id']})")
            else:
                print(f"⚠️ Server already exists: {server['name']} (ID: {server['_id']})")
        
        # Update guild configuration
        await db.guild_configs.update_one(
            {'guild_id': guild_id},
            {
                '$set': {
                    'servers': current_servers,
                    'premium_enabled': True,
                    'updated_at': datetime.now(timezone.utc)
                }
            },
            upsert=True
        )
        
        print(f"✅ Guild configuration updated with {len(current_servers)} servers")
        
        # Create premium assignments for the new system
        premium_servers = [s for s in current_servers if s.get('premium', False)]
        if premium_servers:
            assignment_doc = {
                'guild_id': guild_id,
                'total_slots': len(premium_servers),
                'used_slots': len(premium_servers),
                'available_slots': 0,
                'assigned_by': 0,  # System
                'assigned_at': datetime.now(timezone.utc),
                'history': [{
                    'action': 'auto_registered',
                    'slots': len(premium_servers),
                    'by': 0,
                    'at': datetime.now(timezone.utc),
                    'reason': 'Auto-registration of existing premium servers'
                }]
            }
            
            await db.premium_assignments.update_one(
                {'guild_id': guild_id},
                {'$set': assignment_doc},
                upsert=True
            )
            
            print(f"✅ Premium assignments created: {len(premium_servers)} slots")
        
        # Create server premium status records
        for server in premium_servers:
            server_id = server.get('_id') or server.get('server_id')
            await db.server_premium_status.update_one(
                {'guild_id': guild_id, 'server_id': server_id},
                {
                    '$set': {
                        'guild_id': guild_id,
                        'server_id': server_id,
                        'is_premium': True,
                        'activated_at': datetime.now(timezone.utc),
                        'activated_by': 0,
                        'reason': 'Auto-registration of existing premium server'
                    }
                },
                upsert=True
            )
            
            print(f"✅ Premium status set for server {server_id}")
        
        # Verify the changes
        updated_config = await db.guild_configs.find_one({'guild_id': guild_id})
        final_servers = updated_config.get('servers', [])
        final_premium = [s for s in final_servers if s.get('premium', False)]
        
        print(f"\n🎯 Final Results:")
        print(f"Total servers registered: {len(final_servers)}")
        print(f"Premium servers: {len(final_premium)}")
        
        for server in final_premium:
            print(f"  💎 {server.get('name')} (ID: {server.get('_id')})")
        
        print(f"\n✅ Server registration fix complete!")
        print(f"✅ Premium access should now work correctly")
        
    except Exception as e:
        print(f"❌ Error fixing server registration: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(fix_server_registration())