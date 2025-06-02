"""
Complete Server Cleanup - Remove Emerald EU from all guilds and clean all data
Removes server ID 7020 / Emerald EU from all database collections
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def complete_server_cleanup():
    """Remove Emerald EU server from all guilds and clean all associated data"""
    
    mongo_uri = os.getenv('MONGO_URI')
    client = AsyncIOMotorClient(mongo_uri)
    db = client['emeralds_killfeed']
    
    server_id = "7020"
    server_name = "Emerald EU"
    
    print(f'=== Complete Cleanup for {server_name} (ID: {server_id}) ===')
    
    # 1. Remove server from all guild configurations
    print('\n1. Removing server from guild configurations...')
    
    # Remove from servers array in all guilds
    guild_result = await db.guilds.update_many(
        {},
        {"$pull": {"servers": {"$or": [
            {"_id": server_id},
            {"server_id": server_id},
            {"name": server_name}
        ]}}}
    )
    print(f'   ✓ Updated {guild_result.modified_count} guild configurations')
    
    # 2. Clean PvP data for this server
    print('\n2. Cleaning PvP data...')
    pvp_result = await db.pvp_data.delete_many({"server_id": server_id})
    print(f'   ✓ Removed {pvp_result.deleted_count} PvP records')
    
    # 3. Clean kill events for this server
    print('\n3. Cleaning kill events...')
    kill_result = await db.kill_events.delete_many({"server_id": server_id})
    print(f'   ✓ Removed {kill_result.deleted_count} kill events')
    
    # 4. Clean player sessions for this server
    print('\n4. Cleaning player sessions...')
    session_result = await db.player_sessions.delete_many({"server_id": server_id})
    print(f'   ✓ Removed {session_result.deleted_count} player sessions')
    
    # 5. Clean parser states for this server
    print('\n5. Cleaning parser states...')
    parser_result = await db.parser_states.delete_many({"server_id": server_id})
    print(f'   ✓ Removed {parser_result.deleted_count} parser states')
    
    # 6. Clean premium assignments for this server
    print('\n6. Cleaning premium assignments...')
    premium_result = await db.server_premium_status.delete_many({"server_id": server_id})
    print(f'   ✓ Removed {premium_result.deleted_count} premium assignments')
    
    # 7. Clean any faction data for this server
    print('\n7. Cleaning faction data...')
    faction_result = await db.factions.delete_many({"server_id": server_id})
    print(f'   ✓ Removed {faction_result.deleted_count} faction records')
    
    # 8. Clean any bounty data for this server
    print('\n8. Cleaning bounty data...')
    bounty_result = await db.bounties.delete_many({"server_id": server_id})
    print(f'   ✓ Removed {bounty_result.deleted_count} bounty records')
    
    # 9. Verify complete removal
    print('\n9. Verification - checking for any remaining data...')
    
    collections_to_check = [
        'guilds', 'pvp_data', 'kill_events', 'player_sessions', 
        'parser_states', 'server_premium_status', 'factions', 'bounties'
    ]
    
    remaining_data = False
    for collection_name in collections_to_check:
        collection = db[collection_name]
        
        if collection_name == 'guilds':
            # Check if server exists in any guild's servers array
            count = await collection.count_documents({
                "servers": {"$elemMatch": {"$or": [
                    {"_id": server_id},
                    {"server_id": server_id},
                    {"name": server_name}
                ]}}
            })
        else:
            count = await collection.count_documents({"server_id": server_id})
        
        if count > 0:
            print(f'   ⚠️  {collection_name}: {count} records still exist')
            remaining_data = True
        else:
            print(f'   ✓ {collection_name}: clean')
    
    if not remaining_data:
        print(f'\n✅ Complete cleanup successful - {server_name} (ID: {server_id}) fully removed')
    else:
        print(f'\n⚠️  Some data may still exist - manual review recommended')
    
    print(f'\n=== Cleanup Summary ===')
    print(f'Guild configs updated: {guild_result.modified_count}')
    print(f'PvP records removed: {pvp_result.deleted_count}')
    print(f'Kill events removed: {kill_result.deleted_count}')
    print(f'Player sessions removed: {session_result.deleted_count}')
    print(f'Parser states removed: {parser_result.deleted_count}')
    print(f'Premium assignments removed: {premium_result.deleted_count}')
    print(f'Faction records removed: {faction_result.deleted_count}')
    print(f'Bounty records removed: {bounty_result.deleted_count}')

if __name__ == "__main__":
    asyncio.run(complete_server_cleanup())