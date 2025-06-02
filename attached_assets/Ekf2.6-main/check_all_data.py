#!/usr/bin/env python3
"""
Check All Database Collections
See what data actually exists for the leaderboards
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Check all collections for any data"""
    try:
        mongo_uri = os.getenv('MONGO_URI')
        client = AsyncIOMotorClient(mongo_uri)
        db = client.killfeed_db
        
        guild_id = 1219706687980568769
        
        logger.info("=== CHECKING ALL DATABASE COLLECTIONS ===")
        
        # List all collections
        collections = await db.list_collection_names()
        logger.info(f"Available collections: {collections}")
        
        # Check each relevant collection
        for collection_name in ['pvp_data', 'kill_events', 'factions', 'players']:
            if collection_name in collections:
                count = await db[collection_name].count_documents({"guild_id": guild_id})
                logger.info(f"\n{collection_name}: {count} documents")
                
                if count > 0:
                    sample = await db[collection_name].find_one({"guild_id": guild_id})
                    if sample:
                        fields = list(sample.keys())
                        logger.info(f"  Sample fields: {fields}")
            else:
                logger.info(f"\n{collection_name}: Collection doesn't exist")
        
        # Check if there's any data at all for this guild
        total_pvp = await db.pvp_data.count_documents({"guild_id": guild_id})
        total_kills = await db.kill_events.count_documents({"guild_id": guild_id})
        
        logger.info(f"\nSUMMARY FOR GUILD {guild_id}:")
        logger.info(f"PVP Data: {total_pvp} records")
        logger.info(f"Kill Events: {total_kills} records")
        
        if total_pvp == 0 and total_kills == 0:
            logger.info("NO COMBAT DATA FOUND - Leaderboards will show 'No data available' message")
        
    except Exception as e:
        logger.error(f"Error checking data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())