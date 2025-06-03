#!/usr/bin/env python3

"""
Test Complete Killfeed Pipeline
Verify that parsed events are successfully delivered to Discord channels
"""

import asyncio
import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bot.parsers.scalable_killfeed_parser import ScalableKillfeedParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockBot:
    def __init__(self):
        self.mongo_client = AsyncIOMotorClient(os.environ.get('MONGO_URI'))
        from bot.models.database import DatabaseManager
        self.db_manager = DatabaseManager(self.mongo_client)
        
        # Mock Discord bot methods
        self.guild_channels = {}
        
    def get_channel(self, channel_id):
        """Mock channel retrieval"""
        logger.info(f"Mock bot: Getting channel {channel_id}")
        return MockChannel(channel_id)

class MockChannel:
    def __init__(self, channel_id):
        self.id = channel_id
        
    async def send(self, content=None, embed=None, file=None):
        """Mock sending message to channel"""
        if embed:
            logger.info(f"✅ MOCK SEND to channel {self.id}: {embed.title or 'Killfeed Event'}")
            logger.info(f"   Description: {embed.description[:100]}...")
        else:
            logger.info(f"✅ MOCK SEND to channel {self.id}: {content}")
        return MockMessage()

class MockMessage:
    def __init__(self):
        self.id = 12345

async def test_complete_pipeline():
    """Test the complete killfeed pipeline from parsing to Discord delivery"""
    try:
        logger.info("=== Testing Complete Killfeed Pipeline ===")
        
        # Initialize with mock bot
        bot = MockBot()
        killfeed_parser = ScalableKillfeedParser(bot)
        
        # Force a complete killfeed processing run
        logger.info("Running complete killfeed pipeline...")
        
        await killfeed_parser.run_killfeed_parser()
        
        logger.info("Pipeline test completed - check logs for event delivery")
        
    except Exception as e:
        logger.error(f"Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_complete_pipeline())