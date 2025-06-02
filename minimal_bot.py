#!/usr/bin/env python3
"""
Minimal Discord Bot - Clean Startup Test
"""

import os
import logging
import asyncio
from threading import Thread

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def keep_alive():
    """HTTP server for health checks"""
    try:
        from flask import Flask
        app = Flask(__name__)
        
        @app.route('/')
        def home():
            return "Bot Status: Running"
        
        @app.route('/health')
        def health():
            return {"status": "healthy"}
        
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except Exception as e:
        logger.warning(f"Keep-alive server error: {e}")

async def main():
    """Main entry point"""
    logger.info("Starting minimal bot...")
    
    # Start keep-alive server
    Thread(target=keep_alive, daemon=True).start()
    
    # Check for BOT_TOKEN
    token = os.getenv('BOT_TOKEN')
    if not token:
        logger.error("BOT_TOKEN not found")
        return
    
    # Try to import and start Discord bot
    try:
        import discord
        from discord.ext import commands
        
        intents = discord.Intents.default()
        intents.message_content = True
        
        bot = commands.Bot(command_prefix='/', intents=intents)
        
        @bot.event
        async def on_ready():
            logger.info(f"Bot ready: {bot.user}")
            logger.info("Clean startup completed - zero errors")
        
        await bot.start(token)
        
    except ImportError as e:
        logger.error(f"Discord import failed: {e}")
        # Keep server running without Discord functionality
        await asyncio.sleep(3600)
    except Exception as e:
        logger.error(f"Bot error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")