"""
Test Complete Killfeed Pipeline
Verify that parsed events are successfully delivered to Discord channels
"""
import asyncio
import logging
from bot.utils.simple_killfeed_processor import SimpleKillfeedProcessor
from bot.utils.connection_pool import connection_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockBot:
    def __init__(self):
        self.channels = {}
        self.messages_sent = []
    
    def get_channel(self, channel_id):
        """Mock channel retrieval with detailed logging"""
        logger.info(f"Bot.get_channel called for channel {channel_id}")
        if channel_id not in self.channels:
            self.channels[channel_id] = MockChannel(channel_id)
        return self.channels[channel_id]

class MockChannel:
    def __init__(self, channel_id):
        self.id = channel_id
        self.name = f"channel-{channel_id}"
        
    async def send(self, content=None, embed=None, file=None):
        """Mock sending message to channel"""
        logger.info(f"📤 KILLFEED MESSAGE SENT to channel {self.id}")
        if content:
            logger.info(f"  Content: {content}")
        if embed:
            logger.info(f"  Embed title: {embed.title}")
            logger.info(f"  Embed description: {embed.description}")
        
        # Track the message
        mock_bot.messages_sent.append({
            'channel_id': self.id,
            'content': content,
            'embed': embed,
            'file': file
        })
        
        return MockMessage()

class MockMessage:
    def __init__(self):
        self.id = 12345

async def test_complete_pipeline():
    """Test the complete killfeed pipeline from parsing to Discord delivery"""
    global mock_bot
    mock_bot = MockBot()
    
    logger.info("=== Testing Complete Killfeed Pipeline ===")
    
    server_config = {
        'name': 'Emerald EU',
        'host': '79.127.236.1',
        'port': 8822,
        'username': 'baked',
        'server_id': '7020',
        '_id': '7020'
    }
    
    # Create processor with mock bot
    processor = SimpleKillfeedProcessor(1219706687980568769, server_config, bot=mock_bot)
    
    try:
        await connection_manager.start()
        
        # Test processing
        logger.info("🔍 Starting killfeed processing...")
        result = await processor.process_server_killfeed()
        
        logger.info(f"📊 Processing result: {result}")
        
        if result['success']:
            logger.info(f"✅ Processed {result['events_processed']} events")
            
            if result['events_processed'] > 0:
                logger.info(f"📨 Messages sent to Discord: {len(mock_bot.messages_sent)}")
                
                for i, msg in enumerate(mock_bot.messages_sent):
                    logger.info(f"  Message {i+1}: Channel {msg['channel_id']}")
                    if msg['embed']:
                        logger.info(f"    Embed: {msg['embed'].title}")
            else:
                logger.info("ℹ️ No events processed - CSV may contain only already-processed data")
        else:
            logger.error(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"❌ Pipeline test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        try:
            await connection_manager.stop()
        except Exception as e:
            logger.warning(f"Connection cleanup warning: {e}")

if __name__ == "__main__":
    asyncio.run(test_complete_pipeline())