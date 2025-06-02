#!/usr/bin/env python3
"""
Check Weapon Data in Database
Find where the weapon data is actually stored
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
    """Check where weapon data is actually stored"""
    try:
        mongo_uri = os.getenv('MONGO_URI')
        client = AsyncIOMotorClient(mongo_uri)
        db = client.killfeed_db
        
        guild_id = 1219706687980568769
        
        logger.info("=== SEARCHING FOR WEAPON DATA ===")
        
        # List all collections
        collections = await db.list_collection_names()
        logger.info(f"All collections: {collections}")
        
        # Search for weapon data in all collections
        for collection_name in collections:
            collection = db[collection_name]
            
            # Search for documents containing weapon fields
            weapon_docs = await collection.find({"weapon": {"$exists": True}}).limit(5).to_list(length=None)
            if weapon_docs:
                logger.info(f"\n{collection_name} contains weapon data:")
                for doc in weapon_docs:
                    weapon = doc.get('weapon', 'Unknown')
                    logger.info(f"  Weapon: {weapon}")
                    logger.info(f"  Doc keys: {list(doc.keys())}")
            
            # Also check for any documents with guild_id
            guild_docs = await collection.count_documents({"guild_id": guild_id})
            if guild_docs > 0:
                logger.info(f"\n{collection_name}: {guild_docs} documents for guild {guild_id}")
                
                # Get a sample
                sample = await collection.find_one({"guild_id": guild_id})
                if sample:
                    logger.info(f"  Sample keys: {list(sample.keys())}")
                    if 'weapon' in sample:
                        logger.info(f"  Contains weapon: {sample.get('weapon')}")
        
        # Check for any collection that might contain combat data
        for collection_name in collections:
            collection = db[collection_name]
            
            # Look for kill-related data
            kill_terms = ['kill', 'death', 'weapon', 'killer', 'victim']
            for term in kill_terms:
                docs = await collection.find({term: {"$exists": True}}).limit(1).to_list(length=None)
                if docs:
                    logger.info(f"\n{collection_name} contains '{term}' field")
        
        logger.info("\n=== WEAPON DATA SEARCH COMPLETE ===")
        
    except Exception as e:
        logger.error(f"Error checking weapon data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())