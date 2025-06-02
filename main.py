#!/usr/bin/env python3
"""
Production Discord Bot - Clean py-cord 2.6.1 Implementation
Optimized for performance and reliability
"""

import os
import sys
import logging
import asyncio
from datetime import datetime
from typing import Optional

import discord
from motor.motor_asyncio import AsyncIOMotorClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class EmeraldBot(discord.Bot):
    """Production Discord Bot with server-scoped premium system"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(
            intents=intents,
            debug_guilds=[1219706687980568769]  # Your guild ID
        )
        
        self.db_client: Optional[AsyncIOMotorClient] = None
        self.db = None
        
    async def setup_hook(self):
        """Initialize database and load cogs"""
        try:
            # Initialize database
            mongo_uri = os.getenv('MONGO_URI')
            if not mongo_uri:
                raise ValueError("MONGO_URI environment variable not set")
                
            self.db_client = AsyncIOMotorClient(mongo_uri)
            self.db = self.db_client.emerald_killfeed
            
            # Test connection
            await self.db.admin.command('ping')
            logger.info("✅ Database connected successfully")
            
            # Load essential cogs
            await self.load_extension('bot.cogs.premium')
            await self.load_extension('bot.cogs.casino')
            await self.load_extension('bot.cogs.admin')
            logger.info("✅ Essential cogs loaded")
            
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            raise
    
    async def on_ready(self):
        """Bot ready event"""
        logger.info(f"🤖 Bot ready: {self.user} (ID: {self.user.id})")
        logger.info(f"📊 Serving {len(self.guilds)} guilds")
        
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: Exception):
        """Global error handler"""
        logger.error(f"Command error in {ctx.command}: {error}")
        
        if isinstance(error, discord.CheckFailure):
            await ctx.respond("❌ You don't have permission to use this command.", ephemeral=True)
        elif isinstance(error, discord.CommandOnCooldown):
            await ctx.respond(f"⏰ Command on cooldown. Try again in {error.retry_after:.1f}s", ephemeral=True)
        else:
            await ctx.respond("❌ An error occurred while processing your command.", ephemeral=True)
    
    async def close(self):
        """Cleanup on shutdown"""
        if self.db_client:
            self.db_client.close()
        await super().close()

async def main():
    """Main bot runner"""
    try:
        bot_token = os.getenv('BOT_TOKEN')
        if not bot_token:
            raise ValueError("BOT_TOKEN environment variable not set")
        
        bot = EmeraldBot()
        await bot.start(bot_token)
        
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested")
    except Exception as e:
        logger.error(f"Bot failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())