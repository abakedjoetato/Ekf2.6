#!/usr/bin/env python3
"""
Check Real Data in MongoDB Collections
See what the parsers have actually stored
"""
import asyncio
import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

async def check_real_data():
    """Check what data actually exists in MongoDB"""
    try:
        # Connect to MongoDB
        mongo_uri = os.getenv('MONGO_URI')
        if not mongo_uri:
            logger.error("MONGO_URI not found in environment")
            return
            
        client = AsyncIOMotorClient(mongo_uri)
        db = client.emerald_killfeed
        
        guild_id = 1219706687980568769
        
        logger.info("=== CHECKING REAL MONGODB DATA ===")
        
        # List all collections
        collections = await db.list_collection_names()
        logger.info(f"Available collections: {collections}")
        
        # Check each collection for guild data
        for collection_name in collections:
            collection = db[collection_name]
            count = await collection.count_documents({"guild_id": guild_id})
            logger.info(f"\n{collection_name}: {count} documents for guild {guild_id}")
            
            if count > 0:
                # Get a sample document
                sample = await collection.find_one({"guild_id": guild_id})
                if sample:
                    logger.info(f"  Sample keys: {list(sample.keys())}")
                    
                    # If it looks like kill data, show more details
                    if any(key in sample for key in ['killer', 'victim', 'weapon', 'distance']):
                        logger.info(f"  Killer: {sample.get('killer')}")
                        logger.info(f"  Victim: {sample.get('victim')}")
                        logger.info(f"  Weapon: {sample.get('weapon')}")
                        logger.info(f"  Distance: {sample.get('distance')}")
                        
                    # If it looks like player stats, show more details  
                    if any(key in sample for key in ['kills', 'deaths', 'kdr']):
                        logger.info(f"  Player: {sample.get('player_name')}")
                        logger.info(f"  Kills: {sample.get('kills')}")
                        logger.info(f"  Deaths: {sample.get('deaths')}")
                        logger.info(f"  KDR: {sample.get('kdr')}")
                        
        # Check for any collection with significant data
        logger.info("\n=== COLLECTIONS WITH MOST DATA ===")
        for collection_name in collections:
            collection = db[collection_name]
            total_count = await collection.count_documents({})
            if total_count > 100:
                logger.info(f"{collection_name}: {total_count} total documents")
                
                # Show sample from large collections
                sample = await collection.find_one({})
                if sample:
                    logger.info(f"  Sample structure: {list(sample.keys())}")
        
        await client.close()
        
    except Exception as e:
        logger.error(f"Error checking real data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_real_data())