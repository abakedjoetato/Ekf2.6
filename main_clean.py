#!/usr/bin/env python3
"""
Minimal Clean Discord Bot - Zero Errors Startup
Production-ready bot with clean error-free initialization
"""

import os
import sys
import logging
import asyncio
from threading import Thread

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Verify py-cord installation
try:
    import discord
    from discord.ext import commands
    logger.info("✅ Successfully imported py-cord")
except ImportError as e:
    logger.error(f"❌ Error importing py-cord: {e}")
    logger.error("Please ensure py-cord 2.6.1 is installed")
    sys.exit(1)

# Import other dependencies
try:
    from dotenv import load_dotenv
    import motor.motor_asyncio
    logger.info("✅ All dependencies imported successfully")
except ImportError as e:
    logger.error(f"❌ Error importing dependencies: {e}")
    sys.exit(1)

# Load environment variables
load_dotenv()

class CleanEmeraldBot(commands.Bot):
    """Clean minimal bot for error-free startup"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True
        
        super().__init__(
            command_prefix='/',
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
        
        self.db_client = None
        self.database = None
        
    async def setup_database(self):
        """Setup MongoDB connection"""
        try:
            mongo_uri = os.getenv('MONGO_URI')
            if mongo_uri:
                self.db_client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
                self.database = self.db_client.emerald_killfeed
                logger.info("✅ Database connection established")
            else:
                logger.info("ℹ️ No MongoDB URI provided - running without database")
        except Exception as e:
            logger.warning(f"⚠️ Database connection failed: {e}")
    
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f"✅ Bot is ready! Logged in as {self.user}")
        logger.info(f"✅ Connected to {len(self.guilds)} guilds")
        logger.info("✅ Clean startup completed - zero errors")
        
        # Setup database
        await self.setup_database()
        
        logger.info("🚀 Emerald's Killfeed - Ready for production")
    
    async def close(self):
        """Clean shutdown"""
        if self.db_client:
            self.db_client.close()
        await super().close()
        logger.info("✅ Clean shutdown completed")

# Keep-alive server for Railway deployment
def keep_alive():
    """Simple HTTP server for health checks"""
    try:
        from flask import Flask
        app = Flask(__name__)
        
        @app.route('/')
        def home():
            return "✅ Emerald's Killfeed - Running"
        
        @app.route('/health')
        def health():
            return {"status": "healthy", "service": "emerald-killfeed"}
        
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except Exception as e:
        logger.warning(f"Keep-alive server failed: {e}")

async def main():
    """Main entry point"""
    # Start keep-alive server in background
    Thread(target=keep_alive, daemon=True).start()
    
    # Get bot token
    token = os.getenv('BOT_TOKEN')
    if not token:
        logger.error("❌ BOT_TOKEN not found in environment variables")
        return
    
    # Create and run bot
    bot = CleanEmeraldBot()
    
    try:
        logger.info("🚀 Starting Emerald's Killfeed Bot...")
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("👋 Received shutdown signal")
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")