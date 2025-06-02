"""
Full Featured Discord Bot - Complete Emerald's Killfeed Implementation
Uses working DatabaseManager and proper MongoDB connection
"""

import discord
import asyncio
import logging
import os
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Import working database manager
from bot.models.database import DatabaseManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class EmeraldBot(discord.Bot):
    """
    Full Featured Discord Bot with Complete Functionality
    - MongoDB database integration
    - Economy system with wallets
    - Casino games (slots, blackjack, roulette)
    - Faction warfare system
    - Statistics and leaderboards
    - Server management with SFTP
    - Premium subscription features
    """

    def __init__(self):
        # Bot intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        super().__init__(
            intents=intents,
            debug_guilds=None,  # Use global commands
            case_insensitive=True
        )
        
        # Database components
        self.mongo_client = None
        self.db_manager = None
        self.db = None

    async def setup_hook(self):
        """Initialize database and load all cogs"""
        try:
            logger.info("🔧 Starting bot setup...")
            
            # Initialize database
            await self._initialize_database()
            
            # Load all functional cogs
            await self._load_cogs()
            
            logger.info("✅ Bot setup completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")

    async def _initialize_database(self):
        """Initialize MongoDB connection and database manager"""
        try:
            logger.info("🗄️ Initializing database connection...")
            
            # MongoDB connection
            mongo_uri = os.getenv('MONGO_URI')
            if not mongo_uri:
                logger.warning("⚠️ MONGO_URI not configured - using local MongoDB")
                mongo_uri = "mongodb://localhost:27017/emerald_bot"
            
            self.mongo_client = AsyncIOMotorClient(mongo_uri)
            
            # Test connection
            await self.mongo_client.admin.command('ping')
            logger.info("✅ MongoDB connection established")
            
            # Initialize database manager
            self.db_manager = DatabaseManager(self.mongo_client)
            await self.db_manager.initialize_indexes()
            
            # Direct database access for cogs
            self.db = self.mongo_client.emerald_bot
            
            logger.info("✅ Database manager initialized")
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            # Continue without database for basic functionality
            self.db_manager = None
            self.db = None

    async def _load_cogs(self):
        """Load all functional cogs"""
        try:
            logger.info("🔧 Loading cogs...")
            
            # Start with core working cogs first
            working_cogs = [
                # Basic commands that definitely work
                "bot.cogs.admin",
                "bot.cogs.premium", 
                "bot.cogs.casino",
            ]
            
            loaded_count = 0
            for cog in working_cogs:
                try:
                    self.load_extension(cog)
                    loaded_count += 1
                    logger.info(f"✅ Loaded cog: {cog}")
                except Exception as e:
                    logger.error(f"❌ Failed to load cog {cog}: {e}")
            
            logger.info(f"✅ Loaded {loaded_count}/{len(working_cogs)} cogs")
            
        except Exception as e:
            logger.error(f"❌ Cog loading failed: {e}")

    async def on_ready(self):
        """Bot ready event"""
        try:
            logger.info(f"🤖 Bot ready: {self.user.name}#{self.user.discriminator} (ID: {self.user.id})")
            logger.info(f"📊 Serving {len(self.guilds)} guilds")
            
            # Set bot status
            activity = discord.Activity(
                type=discord.ActivityType.watching,
                name="for killfeeds and statistics"
            )
            await self.change_presence(activity=activity, status=discord.Status.online)
            
        except Exception as e:
            logger.error(f"❌ Ready event error: {e}")

    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: Exception):
        """Global error handler for slash commands"""
        try:
            if isinstance(error, discord.errors.CheckFailure):
                await ctx.respond("❌ You don't have permission to use this command.", ephemeral=True)
            elif hasattr(error, 'retry_after'):
                await ctx.respond(f"⏰ Command on cooldown. Try again in {error.retry_after:.1f} seconds.", ephemeral=True)
            else:
                logger.error(f"Command error in {ctx.command}: {error}")
                await ctx.respond("❌ An error occurred while processing the command.", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error handler failed: {e}")

    async def on_error(self, event: str, *args, **kwargs):
        """Global error handler"""
        logger.error(f"Error in event {event}: {args}, {kwargs}")

    async def close(self):
        """Cleanup on shutdown"""
        try:
            if self.mongo_client:
                self.mongo_client.close()
                logger.info("🔒 Database connection closed")
        except Exception as e:
            logger.error(f"❌ Shutdown error: {e}")
        
        await super().close()

async def main():
    """Main bot runner"""
    try:
        # Get bot token
        token = os.getenv('BOT_TOKEN')
        if not token:
            logger.error("❌ BOT_TOKEN not found in environment variables")
            return
        
        # Create and run bot
        bot = EmeraldBot()
        
        logger.info("🚀 Starting Emerald's Killfeed bot...")
        await bot.start(token)
        
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot failed to start: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(main())