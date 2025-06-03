#!/usr/bin/env python3
"""
Force Cold Start Implementation
Manually triggers a complete cold start by resetting all parser states and forcing full log reprocessing
"""

import asyncio
import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def force_cold_start():
    """Force a complete cold start by resetting all parser states"""
    try:
        # Initialize MongoDB connection directly
        mongo_client = AsyncIOMotorClient(os.environ.get("MONGO_URI"))
        db = mongo_client.EmeraldDB
        
        logger.info("🔄 FORCING COLD START - Resetting all parser states")
        
        # Delete all parser states to force cold start
        result = await db.parser_states.delete_many({})
        logger.info(f"🗑️ Deleted {result.deleted_count} parser states")
        
        # Reset all player sessions to offline
        player_result = await db.player_sessions.update_many(
            {},
            {"$set": {"state": "offline"}}
        )
        logger.info(f"⬇️ Reset {player_result.modified_count} player sessions to offline")
        
        logger.info("✅ Cold start preparation complete - next parser run will be COLD START")
        logger.info("🔄 The parser will now:")
        logger.info("   - Start from log position 0")
        logger.info("   - Parse entire log file")
        logger.info("   - Skip embed outputs during processing")
        logger.info("   - Update all player states accurately")
        
    except Exception as e:
        logger.error(f"❌ Failed to force cold start: {e}")

if __name__ == "__main__":
    asyncio.run(force_cold_start())