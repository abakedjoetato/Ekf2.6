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
    
    server_id = "7020"
    server_name = "Emerald EU"
    server_host = "79.127.236.1"
    
    print(f'=== Complete Cleanup for {server_name} (ID: {server_id}) ===')
    
    # Get all databases
    databases = await client.list_database_names()
    databases = [db for db in databases if db not in ['admin', 'config', 'local']]
    
    total_removed = 0
    
    for db_name in databases:
        print(f'\n--- Processing database: {db_name} ---')
        db = client[db_name]
        collections = await db.list_collection_names()
        
        for coll_name in collections:
            collection = db[coll_name]
            
            # Delete all documents that reference this server
            query = {
                '$or': [
                    {'server_id': server_id},
                    {'host': server_host},
                    {'name': server_name},
                    {'server_name': server_name},
                    {'hostname': server_host},
                    {'servers.server_id': server_id},
                    {'servers.host': server_host},
                    {'servers.name': server_name},
                    {'servers.hostname': server_host}
                ]
            }
            
            # First try direct deletion
            try:
                result = await collection.delete_many(query)
                if result.deleted_count > 0:
                    print(f'  {coll_name}: deleted {result.deleted_count} documents')
                    total_removed += result.deleted_count
            except Exception as e:
                print(f'  {coll_name}: delete error - {e}')
            
            # Then try removing from arrays (for embedded server configs)
            try:
                update_result = await collection.update_many(
                    {'servers': {'$exists': True}},
                    {
                        '$pull': {
                            'servers': {
                                '$or': [
                                    {'server_id': server_id},
                                    {'_id': server_id},
                                    {'host': server_host},
                                    {'name': server_name},
                                    {'hostname': server_host}
                                ]
                            }
                        }
                    }
                )
                if update_result.modified_count > 0:
                    print(f'  {coll_name}: updated {update_result.modified_count} documents (removed from arrays)')
            except Exception as e:
                print(f'  {coll_name}: update error - {e}')
    
    print(f'\n=== Cleanup Summary ===')
    print(f'Total documents removed: {total_removed}')
    
    # Final verification
    print(f'\n=== Verification ===')
    remaining_count = 0
    
    for db_name in databases:
        db = client[db_name]
        collections = await db.list_collection_names()
        
        for coll_name in collections:
            collection = db[coll_name]
            
            query = {
                '$or': [
                    {'server_id': server_id},
                    {'host': server_host},
                    {'name': server_name},
                    {'servers.server_id': server_id},
                    {'servers.host': server_host}
                ]
            }
            
            try:
                count = await collection.count_documents(query)
                if count > 0:
                    remaining_count += count
                    print(f'  {db_name}.{coll_name}: {count} documents still contain server references')
            except Exception:
                pass
    
    if remaining_count == 0:
        print('✅ Server completely removed from all databases')
    else:
        print(f'⚠️  {remaining_count} references still remain')

if __name__ == "__main__":
    asyncio.run(complete_server_cleanup())