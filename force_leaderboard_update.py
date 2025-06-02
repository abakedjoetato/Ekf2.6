#!/usr/bin/env python3
"""
Force Leaderboard Update - Manual Test
Creates and posts the consolidated leaderboard immediately
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from bot.models.database import DatabaseManager
from bot.cogs.automated_leaderboard import AutomatedLeaderboard
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockBot:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.user = type('MockUser', (), {'id': 1360004212955545623})()

async def main():
    """Force update the automated leaderboard"""
    try:
        # Connect to database
        mongo_uri = os.getenv('MONGO_URI')
        if not mongo_uri:
            logger.error("MONGO_URI not found in environment variables")
            return

        client = AsyncIOMotorClient(mongo_uri)
        db_manager = DatabaseManager(client)
        
        # Create mock bot
        bot = MockBot(db_manager)
        
        # Create automated leaderboard instance
        auto_lb = AutomatedLeaderboard(bot)
        
        # Get guild ID
        guild_id = 1219706687980568769
        
        logger.info("Creating consolidated leaderboard...")
        
        # Create consolidated leaderboard
        embed, file_attachment = await auto_lb.create_consolidated_leaderboard(
            guild_id, None, "All Servers"
        )
        
        if embed:
            logger.info("✅ Embed created successfully!")
            logger.info(f"Title: {embed.title}")
            logger.info(f"Description: {embed.description}")
            logger.info(f"Color: {embed.color}")
            logger.info(f"Fields: {len(embed.fields)}")
            
            for i, field in enumerate(embed.fields):
                logger.info(f"Field {i+1}: {field.name}")
                logger.info(f"Value length: {len(field.value)}")
                logger.info(f"First 200 chars: {field.value[:200]}...")
        else:
            logger.error("❌ Failed to create embed")
            
        # Check database content
        logger.info("\nChecking database content...")
        
        # Check PVP data
        pvp_count = await db_manager.pvp_data.count_documents({"guild_id": guild_id})
        logger.info(f"PVP data documents: {pvp_count}")
        
        if pvp_count > 0:
            top_killer = await db_manager.pvp_data.find_one(
                {"guild_id": guild_id, "kills": {"$gt": 0}},
                sort=[("kills", -1)]
            )
            if top_killer:
                logger.info(f"Top killer: {top_killer.get('player_name')} with {top_killer.get('kills')} kills")
        
        # Check kill events
        kill_events_count = await db_manager.kill_events.count_documents({"guild_id": guild_id})
        logger.info(f"Kill events: {kill_events_count}")
        
        logger.info("Force leaderboard update completed!")
        
    except Exception as e:
        logger.error(f"Error in force update: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())