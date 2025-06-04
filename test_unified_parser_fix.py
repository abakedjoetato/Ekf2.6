"""
Test Unified Parser Fix - Verify the parser is now properly fetching and processing logs
"""

import asyncio
import logging
from bot.models.database import DatabaseManager
from bot.parsers.scalable_unified_parser import ScalableUnifiedParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockBot:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
    def get_guild(self, guild_id):
        return None  # Simplified for testing

async def test_unified_parser():
    """Test the unified parser with actual database connection"""
    try:
        # Initialize database
        db_manager = DatabaseManager()
        await db_manager.initialize()
        
        # Create mock bot
        bot = MockBot(db_manager)
        
        # Initialize unified parser
        parser = ScalableUnifiedParser(bot)
        
        # Test guild configuration retrieval
        guild_configs = await parser._get_all_guild_configs()
        print(f"Found guild configurations: {len(guild_configs)}")
        
        for guild_id, servers in guild_configs.items():
            print(f"Guild {guild_id}: {len(servers)} servers")
            for server in servers:
                print(f"  Server: {server.get('name')} - Enabled: {server.get('enabled', False)}")
        
        # Test manual processing for the guild
        if guild_configs:
            guild_id = list(guild_configs.keys())[0]
            print(f"\nTesting manual processing for guild {guild_id}...")
            
            result = await parser.process_guild_manual(guild_id)
            print(f"Manual processing result: {result}")
        
        # Check current player sessions
        player_count = await db_manager.player_sessions.count_documents({'state': 'online'})
        print(f"Current online players: {player_count}")
        
        # Check all player sessions
        all_sessions = await db_manager.player_sessions.count_documents({})
        print(f"Total player sessions: {all_sessions}")
        
        # List some recent sessions
        recent_sessions = await db_manager.player_sessions.find({}).limit(5).to_list(length=5)
        print(f"\nRecent sessions:")
        for session in recent_sessions:
            print(f"  {session.get('character_name')} - {session.get('state')} - {session.get('last_seen')}")
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_unified_parser())