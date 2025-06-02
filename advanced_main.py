"""
Advanced Production Bot - Complete 10-Phase Reconstruction
Emerald's Killfeed with py-cord 2.6.1 and advanced UI components
"""

import discord
import asyncio
import logging
import os
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Import database manager
from bot.models.database import DatabaseManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_advanced.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class AdvancedEmeraldBot(discord.Bot):
    """
    Advanced Discord Bot - Complete 10-Phase Implementation
    - Advanced py-cord 2.6.1 UI components
    - Server-scoped premium with guild feature unlocking
    - Cross-character aggregation with main/alt linking
    - Dual-layer faction management
    - Complete audit trails for admin actions
    - Enhanced parser system preservation
    """

    def __init__(self):
        # Bot intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        super().__init__(
            intents=intents,
            debug_guilds=None  # Remove debug restriction for production
        )
        
        # Initialize components
        self.db_manager = None
        self.mongo_client = None
        self.start_time = datetime.now(timezone.utc)
        
        logger.info("🚀 Advanced Emerald Bot initialized")

    async def setup_hook(self):
        """Advanced setup hook with comprehensive initialization"""
        try:
            logger.info("🔧 Starting advanced setup hook...")
            
            # Initialize database connection
            logger.info("📋 Step 1: Initializing database...")
            await self._initialize_advanced_database()
            
            # Load all advanced cogs
            logger.info("📋 Step 2: Loading cogs...")
            await self._load_advanced_cogs()
            
            # Initialize parsers (preserved from original)
            logger.info("📋 Step 3: Initializing parsers...")
            await self._initialize_parser_systems()
            
            # Sync commands
            logger.info("📋 Step 4: Syncing commands...")
            await self._sync_commands()
            
            logger.info("✅ Advanced setup hook completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Setup hook failed: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

    async def _initialize_advanced_database(self):
        """Initialize advanced database with complete schema"""
        try:
            logger.info("🗄️ Initializing advanced database connection...")
            
            # MongoDB connection
            mongo_uri = os.getenv('MONGO_URI')
            if not mongo_uri:
                logger.warning("⚠️ MONGO_URI not configured - using fallback database")
                # Use a simple in-memory fallback for testing
                self.db_manager = None
                return
            
            self.mongo_client = AsyncIOMotorClient(mongo_uri)
            
            # Test connection
            await self.mongo_client.admin.command('ping')
            logger.info("✅ MongoDB connection established")
            
            # Initialize database manager
            self.db_manager = DatabaseManager(self.mongo_client)
            
            # Initialize database schema
            await self.db_manager.initialize_database()
            
            logger.info("✅ Advanced database manager initialized")
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            logger.error(f"Error details: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            logger.info("🔄 Continuing without database for testing purposes")
            self.db_manager = None

    async def _load_advanced_cogs(self):
        """Load all advanced cogs with error handling"""
        try:
            logger.info("🔧 Loading advanced cogs...")
            
            # Streamlined cog system - no redundancies
            advanced_cogs = [
                # Core enhanced systems
                "bot.cogs.admin_channels_enhanced",    # Enhanced channel configuration
                "bot.cogs.admin_server_management",    # SFTP server management
                "bot.cogs.statistics_enhanced",        # Enhanced player statistics
                "bot.cogs.core",                       # Core functionality
                
                # Administrative systems  
                "bot.cogs.admin_batch",                # Batch management
                "bot.cogs.advanced_premium",           # Premium management
                "bot.cogs.subscription_management_fixed", # Subscription management
                "bot.cogs.cache_management",           # Cache management
                
                # Gaming ecosystem
                "bot.cogs.advanced_casino",            # Consolidated casino system
                "bot.cogs.economy",                    # Economy system
                "bot.cogs.bounties",                   # Bounty system
                "bot.cogs.factions",                   # Faction management
                
                # Player features
                "bot.cogs.linking",                    # Character linking
                "bot.cogs.automated_leaderboard",      # Consolidated leaderboards
                
                # System features
                "bot.cogs.parsers",                    # Parser management
                "bot.cogs.autocomplete",               # Enhanced autocomplete
            ]
            
            loaded_count = 0
            for cog in advanced_cogs:
                try:
                    self.load_extension(cog)
                    loaded_count += 1
                    logger.info(f"✅ Loaded cog: {cog}")
                except Exception as e:
                    logger.error(f"❌ Failed to load cog {cog}: {e}")
            
            logger.info(f"✅ Loaded {loaded_count}/{len(advanced_cogs)} advanced cogs")
            
        except Exception as e:
            logger.error(f"❌ Cog loading failed: {e}")
            raise

    async def _initialize_parser_systems(self):
        """Initialize parser systems with enhanced channel routing"""
        try:
            logger.info("📜 Initializing parser systems...")
            
            # Initialize channel router
            from bot.utils.channel_router import ChannelRouter
            self.channel_router = ChannelRouter(self.db_manager)
            logger.info("✅ Channel router initialized")
            
            # Import preserved parsers
            try:
                from bot.parsers.killfeed_parser import KillfeedParser
                from bot.parsers.unified_log_parser import UnifiedLogParser
                from bot.parsers.historical_parser import HistoricalParser
                
                # Initialize parsers with database manager only (channel router added later)
                self.killfeed_parser = KillfeedParser(self.db_manager)
                self.unified_parser = UnifiedLogParser(self.db_manager)
                self.historical_parser = HistoricalParser(self.db_manager)
                
                # Add channel router to parsers
                if hasattr(self.killfeed_parser, 'set_channel_router'):
                    self.killfeed_parser.set_channel_router(self.channel_router)
                if hasattr(self.unified_parser, 'set_channel_router'):
                    self.unified_parser.set_channel_router(self.channel_router)
                if hasattr(self.historical_parser, 'set_channel_router'):
                    self.historical_parser.set_channel_router(self.channel_router)
                
                logger.info("✅ Parser systems initialized with channel routing")
                
            except ImportError as e:
                logger.warning(f"⚠️ Some parsers not available: {e}")
                logger.info("✅ Bot will continue without full parser integration")
            
        except Exception as e:
            logger.error(f"❌ Parser initialization failed: {e}")
            # Continue without parsers for now

    async def _sync_commands(self):
        """Sync slash commands"""
        try:
            logger.info("🔄 Syncing slash commands...")
            
            # Sync commands globally
            await self.sync_commands()
            
            logger.info("✅ Slash commands synced successfully")
            
        except Exception as e:
            logger.error(f"❌ Command sync failed: {e}")

    async def on_ready(self):
        """Enhanced ready event with comprehensive logging"""
        try:
            logger.info(f"🤖 Advanced bot ready: {self.user} (ID: {self.user.id})")
            logger.info(f"📊 Serving {len(self.guilds)} guilds")
            logger.info(f"⏱️ Startup time: {(datetime.now(timezone.utc) - self.start_time).total_seconds():.2f}s")
            
            # Force database initialization if it wasn't done in setup_hook
            if not self.db_manager:
                logger.info("🔄 Database not initialized, attempting initialization now...")
                await self._initialize_advanced_database()
            
            # Load cogs if they weren't loaded in setup_hook
            if self.db_manager and len(self.cogs) == 0:
                logger.info("🔄 Cogs not loaded, loading now...")
                await self._load_advanced_cogs()
                
                # Sync commands after loading cogs
                logger.info("🔄 Syncing slash commands...")
                await self._sync_commands()
            
            # Initialize guilds in database
            if self.db_manager:
                for guild in self.guilds:
                    try:
                        await self.db_manager.ensure_guild_initialized(guild.id, guild.name)
                        logger.debug(f"✅ Guild initialized: {guild.name}")
                    except Exception as e:
                        logger.error(f"❌ Failed to initialize guild {guild.name}: {e}")
                
                logger.info("✅ All guilds initialized in database")
            else:
                logger.info("⚠️ Database not available - skipping guild initialization")
            
            # Set bot status
            activity = discord.Activity(
                type=discord.ActivityType.watching,
                name="for advanced gaming stats | /help"
            )
            await self.change_presence(status=discord.Status.online, activity=activity)
            
            logger.info("🚀 Advanced Emerald Bot fully operational")
            
        except Exception as e:
            logger.error(f"❌ Ready event failed: {e}")

    async def on_guild_join(self, guild: discord.Guild):
        """Handle new guild joining with advanced initialization"""
        try:
            logger.info(f"🆕 Joined new guild: {guild.name} (ID: {guild.id})")
            
            # Initialize guild in database
            success = await self.db_manager.ensure_guild_initialized(guild.id, guild.name)
            
            if success:
                logger.info(f"✅ Guild {guild.name} initialized successfully")
                
                # Send welcome message if possible
                if guild.system_channel:
                    embed = discord.Embed(
                        title="🎉 Welcome to Emerald's Killfeed!",
                        description="Advanced Discord bot for gaming server management with comprehensive features.",
                        color=0x00FF00
                    )
                    
                    embed.add_field(
                        name="🚀 Getting Started",
                        value="• Use `/help` for command overview\n• Use `/admin` for server configuration\n• Contact administrators for premium features",
                        inline=False
                    )
                    
                    try:
                        await guild.system_channel.send(embed=embed)
                    except:
                        logger.warning(f"Could not send welcome message to {guild.name}")
            else:
                logger.error(f"❌ Failed to initialize guild {guild.name}")
                
        except Exception as e:
            logger.error(f"❌ Guild join handling failed for {guild.name}: {e}")

    async def on_guild_remove(self, guild: discord.Guild):
        """Handle guild removal"""
        logger.info(f"👋 Left guild: {guild.name} (ID: {guild.id})")
        # Note: We don't delete guild data to preserve user statistics

    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: Exception):
        """Advanced error handling for slash commands"""
        try:
            logger.error(f"Command error in {ctx.command.name}: {error}")
            
            # User-friendly error messages
            if isinstance(error, discord.errors.CheckFailure):
                await ctx.respond(
                    "❌ You don't have permission to use this command.",
                    ephemeral=True
                )
            elif isinstance(error, discord.errors.CommandOnCooldown):
                await ctx.respond(
                    f"⏳ Command is on cooldown. Try again in {error.retry_after:.1f} seconds.",
                    ephemeral=True
                )
            else:
                await ctx.respond(
                    "❌ An unexpected error occurred. Please try again later.",
                    ephemeral=True
                )
                
        except Exception as e:
            logger.error(f"Error in error handler: {e}")

    async def on_error(self, event: str, *args, **kwargs):
        """Advanced global error handler"""
        logger.error(f"Unhandled error in {event}: {args}")

    async def close(self):
        """Advanced cleanup on bot shutdown"""
        try:
            logger.info("🔄 Starting bot shutdown sequence...")
            
            # Close database connection
            if self.mongo_client:
                self.mongo_client.close()
                logger.info("✅ Database connection closed")
            
            # Close parsers if they exist
            for parser_name in ['killfeed_parser', 'unified_parser', 'historical_parser']:
                if hasattr(self, parser_name):
                    parser = getattr(self, parser_name)
                    if hasattr(parser, 'close'):
                        try:
                            await parser.close()
                            logger.info(f"✅ {parser_name} closed")
                        except:
                            pass
            
            await super().close()
            logger.info("✅ Bot shutdown completed")
            
        except Exception as e:
            logger.error(f"❌ Shutdown error: {e}")

async def main():
    """Advanced main function with comprehensive error handling"""
    try:
        logger.info("🚀 Starting Advanced Emerald Bot...")
        
        # Get bot token
        bot_token = os.getenv('BOT_TOKEN')
        if not bot_token:
            raise ValueError("BOT_TOKEN environment variable not set")
        
        # Create and run bot
        bot = AdvancedEmeraldBot()
        
        try:
            await bot.start(bot_token)
        except KeyboardInterrupt:
            logger.info("👋 Bot shutdown requested by user")
        except Exception as e:
            logger.error(f"❌ Bot runtime error: {e}")
            raise
        finally:
            await bot.close()
            
    except Exception as e:
        logger.error(f"❌ Critical error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Application terminated by user")
    except Exception as e:
        logger.error(f"❌ Application error: {e}")
        exit(1)