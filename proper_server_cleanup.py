"""
Proper Server Cleanup - Remove Emerald EU from correct database
The server data is actually in EmeraldDB, not emeralds_killfeed
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def proper_server_cleanup():
    """Remove Emerald EU server from the correct database"""
    
    mongo_uri = os.getenv('MONGO_URI')
    client = AsyncIOMotorClient(mongo_uri)
    
    # The actual database names based on the working query
    emerald_db = client['EmeraldDB']
    killfeed_db = client['emeralds_killfeed']
    
    server_id = "7020"
    server_name = "Emerald EU"
    guild_id = 1219706687980568769
    
    print(f'=== Proper Cleanup for {server_name} (ID: {server_id}) ===')
    
    # 1. Remove from EmeraldDB (where the actual config is)
    print('\n1. Removing server from EmeraldDB guild configurations...')
    
    # Remove from guild_configs collection in EmeraldDB
    guild_result = await emerald_db.guild_configs.update_one(
        {"guild_id": guild_id},
        {"$pull": {"servers": {"$or": [
            {"_id": server_id},
            {"server_id": server_id},
            {"name": server_name}
        ]}}}
    )
    print(f'   ✓ Updated {guild_result.modified_count} guild configurations in EmeraldDB')
    
    # 2. Remove from emeralds_killfeed database (if any data exists)
    print('\n2. Removing server from emeralds_killfeed guild configurations...')
    
    guild_result2 = await killfeed_db.guilds.update_one(
        {"guild_id": guild_id},
        {"$pull": {"servers": {"$or": [
            {"_id": server_id},
            {"server_id": server_id},
            {"name": server_name}
        ]}}}
    )
    print(f'   ✓ Updated {guild_result2.modified_count} guild configurations in emeralds_killfeed')
    
    # 3. Clean all associated data from both databases
    print('\n3. Cleaning associated data...')
    
    collections_to_clean = [
        ('EmeraldDB', ['pvp_data', 'kill_events', 'player_sessions', 'parser_states']),
        ('emeralds_killfeed', ['pvp_data', 'kill_events', 'player_sessions', 'parser_states', 
                               'server_premium_status', 'factions', 'bounties'])
    ]
    
    total_removed = 0
    for db_name, collections in collections_to_clean:
        db = client[db_name]
        print(f'\n   Cleaning {db_name}:')
        
        for collection_name in collections:
            try:
                collection = db[collection_name]
                result = await collection.delete_many({"server_id": server_id})
                if result.deleted_count > 0:
                    print(f'     {collection_name}: removed {result.deleted_count} documents')
                    total_removed += result.deleted_count
                else:
                    print(f'     {collection_name}: no data found')
            except Exception as e:
                print(f'     {collection_name}: error - {e}')
    
    # 4. Verification
    print('\n4. Verification...')
    
    # Check if server still exists in either database
    guild_config_emerald = await emerald_db.guild_configs.find_one({"guild_id": guild_id})
    remaining_servers_emerald = 0
    if guild_config_emerald:
        servers = guild_config_emerald.get('servers', [])
        remaining_servers_emerald = len([s for s in servers if s.get('_id') == server_id or s.get('server_id') == server_id])
    
    guild_config_killfeed = await killfeed_db.guilds.find_one({"guild_id": guild_id})
    remaining_servers_killfeed = 0
    if guild_config_killfeed:
        servers = guild_config_killfeed.get('servers', [])
        remaining_servers_killfeed = len([s for s in servers if s.get('_id') == server_id or s.get('server_id') == server_id])
    
    if remaining_servers_emerald == 0 and remaining_servers_killfeed == 0:
        print(f'   ✅ Server {server_name} completely removed from both databases')
    else:
        print(f'   ⚠️  Server still exists: EmeraldDB ({remaining_servers_emerald}), emeralds_killfeed ({remaining_servers_killfeed})')
    
    print(f'\n=== Cleanup Summary ===')
    print(f'Total data records removed: {total_removed}')
    print(f'Guild configs updated: {guild_result.modified_count + guild_result2.modified_count}')

if __name__ == "__main__":
    asyncio.run(proper_server_cleanup())