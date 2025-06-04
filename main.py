#!/usr/bin/env python3
"""
Emerald's Killfeed - Discord Bot for Deadside PvP Engine
Full production-grade bot with killfeed parsing, stats, economy, and premium features
"""

import asyncio
import logging
import os
import sys
import json
import hashlib
import re
import time
import traceback
from pathlib import Path

# Clean up any conflicting discord modules before importing
for module_name in list(sys.modules.keys()):
    if module_name == 'discord' or module_name.startswith('discord.'):
        del sys.modules[module_name]

# Import py-cord v2.6.1
try:
    import discord
    from discord.ext import commands
    print(f"✅ Successfully imported py-cord")
except ImportError as e:
    print(f"❌ Error importing py-cord: {e}")
    print("Please ensure py-cord 2.6.1 is installed")
    sys.exit(1)

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bot.models.database import DatabaseManager

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

try:
    from bot.parsers.killfeed_parser import KillfeedParser
except Exception as e:
    logger.error(f"Failed to import KillfeedParser: {e}")
    raise
from bot.parsers.historical_parser import HistoricalParser
from bot.parsers.unified_log_parser import UnifiedLogParser

# Load environment variables (optional for Railway)
load_dotenv()

# Detect Railway environment
RAILWAY_ENV = os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_STATIC_URL")
if RAILWAY_ENV:
    print(f"🚂 Running on Railway environment")
else:
    print("🖥️ Running in local/development environment")

# Import Railway keep-alive server
from keep_alive import keep_alive

# Set runtime mode to production
MODE = os.getenv("MODE", "production")
print(f"Runtime mode set to: {MODE}")

# Start keep-alive server for Railway deployment
if MODE == "production" or RAILWAY_ENV:
    print("🚀 Starting Railway keep-alive server...")
    keep_alive()

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

class EmeraldKillfeedBot(commands.Bot):
    """Main bot class for Emerald's Killfeed"""

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
            status=discord.Status.online,
            activity=discord.Game(name="Emerald's Killfeed v2.0"),
            auto_sync_commands=False  # Disable automatic command syncing
        )

        # Initialize variables
        self.db_manager = None
        self.premium_sync = None
        self.scheduler = AsyncIOScheduler()
        self.killfeed_parser = None
        self.log_parser = None
        self.historical_parser = None
        self.unified_log_parser = None
        self.ssh_connections = []

        # Missing essential properties
        self.assets_path = Path('./assets')
        self.dev_data_path = Path('./dev_data')
        self.dev_mode = os.getenv('DEV_MODE', 'false').lower() == 'true'

        logger.info("Bot initialized in production mode")

    async def load_cogs(self):
        """Load all cogs with direct registration (py-cord 2.6.1 compatible)"""
        from bot.cogs.core import Core
        from bot.cogs.admin_channels import AdminChannels
        from bot.cogs.admin_batch import AdminBatch
        from bot.cogs.linking import Linking
        from bot.cogs.stats import Stats
        from bot.cogs.leaderboards_fixed import LeaderboardsFixed
        from bot.cogs.automated_leaderboard import AutomatedLeaderboard
        from bot.cogs.economy import Economy
        from bot.cogs.professional_casino import ProfessionalCasino
        from bot.cogs.bounties import Bounties
        from bot.cogs.factions import Factions
        from bot.cogs.subscription_management import SubscriptionManagement
        from bot.cogs.premium import Premium
        from bot.cogs.parsers import Parsers
        from bot.cogs.cache_management import CacheManagement

        cog_classes = [
            ('Core', Core),
            ('AdminChannels', AdminChannels),
            ('AdminBatch', AdminBatch),
            ('Linking', Linking),
            ('Stats', Stats),
            ('LeaderboardsFixed', LeaderboardsFixed),
            ('AutomatedLeaderboard', AutomatedLeaderboard),
            ('Economy', Economy),
            ('ProfessionalCasino', ProfessionalCasino),
            ('Bounties', Bounties),
            ('Factions', Factions),
            ('SubscriptionManagement', SubscriptionManagement),
            ('Premium', Premium),
            ('Parsers', Parsers),
            ('CacheManagement', CacheManagement)
        ]

        loaded_count = 0
        failed_cogs = []

        for name, cog_class in cog_classes:
            try:
                cog_instance = cog_class(self)
                self.add_cog(cog_instance)
                logger.info(f"✅ Successfully loaded cog: {name}")
                loaded_count += 1
            except Exception as e:
                logger.error(f"❌ Failed to load cog {name}: {e}")
                logger.error(f"Cog error traceback: {traceback.format_exc()}")
                failed_cogs.append(name)

        logger.info(f"📊 Loaded {loaded_count}/{len(cog_classes)} cogs successfully")

        # Log command count (py-cord 2.6.1 compatible)
        total_commands = 0
        command_names = []
        
        # py-cord 2.6.1 command discovery - comprehensive approach
        all_commands = []
        if hasattr(self, 'pending_application_commands') and self.pending_application_commands:
            all_commands = list(self.pending_application_commands)
        elif hasattr(self, 'application_commands') and self.application_commands:
            all_commands = list(self.application_commands)
        
        total_commands = len(all_commands)
        command_names = [getattr(cmd, 'name', 'Unknown') for cmd in all_commands[:10]]
        
        logger.info(f"📊 Total slash commands registered: {total_commands}")
        if command_names:
            logger.info(f"🔍 Commands found: {', '.join(command_names[:10])}...")
        
        logger.info("✅ Cog loading: Complete")
        logger.info(f"✅ {total_commands} commands registered and ready for sync")

        if failed_cogs:
            logger.error(f"❌ Failed cogs: {failed_cogs}")
            # Don't abort on cog failures in production - continue with available functionality
            logger.warning("⚠️ Some cogs failed to load but continuing with available functionality")

        return loaded_count, failed_cogs

    def calculate_command_fingerprint(self, commands):
        """Generates a stable hash for the current command structure."""
        try:
            command_data = []
            for c in commands:
                cmd_dict = {
                    'name': c.name,
                    'description': c.description,
                }
                # Handle options safely by converting to basic types
                if hasattr(c, 'options') and c.options:
                    options_data = []
                    for opt in c.options:
                        opt_dict = {
                            'name': getattr(opt, 'name', ''),
                            'description': getattr(opt, 'description', ''),
                            'type': str(getattr(opt, 'type', '')),
                            'required': getattr(opt, 'required', False)
                        }
                        options_data.append(opt_dict)
                    cmd_dict['options'] = options_data
                else:
                    cmd_dict['options'] = []
                command_data.append(cmd_dict)

            # Sort by name for consistent hashing
            command_data = sorted(command_data, key=lambda x: x['name'])
            return hashlib.sha256(json.dumps(command_data, sort_keys=True).encode()).hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate command fingerprint: {e}")
            return None

    async def register_commands_safely(self):
        """
        DISABLED: All Discord command sync operations disabled to prevent rate limiting
        Commands are loaded and functional in bot memory without requiring Discord sync
        """
        logger.info("Command sync disabled - commands functional without Discord API sync")
        return

    async def cleanup_connections(self):
        """Clean up AsyncSSH connections on shutdown with enhanced error recovery"""
        try:
            cleanup_tasks = []

            # Scalable killfeed parser cleanup
            if hasattr(self, 'killfeed_parser') and self.killfeed_parser:
                if hasattr(self.killfeed_parser, 'cleanup_killfeed_connections'):
                    cleanup_tasks.append(self.killfeed_parser.cleanup_killfeed_connections())
                else:
                    cleanup_tasks.append(self._cleanup_parser_connections(self.killfeed_parser, "killfeed"))

            # Scalable unified parser cleanup  
            if hasattr(self, 'unified_log_parser') and self.unified_log_parser:
                if hasattr(self.unified_log_parser, 'cleanup_unified_connections'):
                    cleanup_tasks.append(self.unified_log_parser.cleanup_unified_connections())
                else:
                    cleanup_tasks.append(self._cleanup_parser_connections(self.unified_log_parser, "unified_log"))
            
            # Scalable historical parser cleanup
            if hasattr(self, 'historical_parser') and self.historical_parser:
                if hasattr(self.historical_parser, 'stop_connection_manager'):
                    cleanup_tasks.append(self.historical_parser.stop_connection_manager())

            # Execute all cleanup tasks with timeout
            if cleanup_tasks:
                await asyncio.wait_for(
                    asyncio.gather(*cleanup_tasks, return_exceptions=True),
                    timeout=30
                )

            # Force cleanup of any remaining connections
            await self._force_cleanup_all_connections()

            logger.info("Cleaned up all SFTP connections")

        except asyncio.TimeoutError:
            logger.warning("Connection cleanup timed out after 30 seconds")
        except Exception as e:
            logger.error(f"Failed to cleanup connections: {e}")

    async def _force_cleanup_all_connections(self):
        """Force cleanup of any remaining connections"""
        try:
            import gc

            # Clear any remaining parser state
            if hasattr(self, 'unified_log_parser') and self.unified_log_parser:
                # Clear internal state without requiring guild_id/server_id
                if hasattr(self.unified_log_parser, 'connections'):
                    self.unified_log_parser.connections.clear()
                if hasattr(self.unified_log_parser, 'parser_states'):
                    self.unified_log_parser.parser_states.clear()

            # Force garbage collection
            gc.collect()

        except Exception as e:
            logger.error(f"Error in force cleanup: {e}")

    async def _cleanup_parser_connections(self, parser, parser_name: str):
        """Clean up connections for a specific parser"""
        try:
            if hasattr(parser, 'cleanup_sftp_connections'):
                await parser.cleanup_sftp_connections()
            elif hasattr(parser, 'sftp_connections'):
                # Generic cleanup for parsers with sftp_connections
                for pool_key, conn in list(parser.sftp_connections.items()):
                    try:
                        if hasattr(conn, 'is_closed') and not conn.is_closed():
                            conn.close()
                    except Exception as e:
                        logger.debug(f"Error closing connection {pool_key}: {e}")
                parser.sftp_connections.clear()

            logger.debug(f"Cleaned up {parser_name} parser connections")

        except Exception as e:
            logger.error(f"Failed to cleanup {parser_name} parser connections: {e}")

    async def setup_database(self):
        """Setup MongoDB connection"""
        mongo_uri = os.getenv('MONGODB_URI') or os.getenv('MONGO_URI')
        if not mongo_uri:
            logger.error("MongoDB URI not found in environment variables")
            return False

        try:
            self.mongo_client = AsyncIOMotorClient(mongo_uri)
            self.database = self.mongo_client.emerald_killfeed

            # Initialize database manager without caching to prevent command registration issues
            from bot.models.database import DatabaseManager
            
            # Create direct database manager
            self.db_manager = DatabaseManager(self.mongo_client)
            
            # Ensure consistent access pattern
            self.database = self.db_manager  # Legacy compatibility

            # Test connection
            await self.mongo_client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")

            # Initialize database indexes
            await self.db_manager.initialize_indexes()
            logger.info("Database architecture initialized (PHASE 1)")
            
            # Premium system initialization handled by premium_manager_v2

            # Initialize batch sender for rate limit management
            from bot.utils.batch_sender import BatchSender
            self.batch_sender = BatchSender(self)

            # Initialize advanced rate limiter
            from bot.utils.advanced_rate_limiter import AdvancedRateLimiter
            self.advanced_rate_limiter = AdvancedRateLimiter(self)

            # Initialize channel router
            from bot.utils.channel_router import ChannelRouter
            self.channel_router = ChannelRouter(self)
            
            # Initialize embed factory
            from bot.utils.embed_factory import EmbedFactory
            self.embed_factory = EmbedFactory()
            
            # Initialize voice channel batcher to prevent rate limiting
            from bot.utils.voice_channel_batch import VoiceChannelBatcher
            self.voice_channel_batcher = VoiceChannelBatcher(self)

            # Initialize premium manager v2 with cached database
            from bot.utils.premium_manager_v2 import PremiumManagerV2
            self.premium_manager_v2 = PremiumManagerV2(self.db_manager)
            
            # Legacy compatibility for existing code
            self.premium_manager = self.premium_manager_v2

            # Initialize connection manager for scalable parsing
            from bot.utils.connection_pool import connection_manager
            await connection_manager.start()
            logger.info("Connection pool manager started for scalable parsing")

            # Initialize shared parser state management
            from bot.utils.shared_parser_state import initialize_shared_state_manager
            initialize_shared_state_manager(self.db_manager)
            logger.info("Shared parser state manager initialized")

            # Initialize parsers (PHASE 2) - Data parsers for killfeed & log events
            from bot.parsers.scalable_killfeed_parser import ScalableKillfeedParser
            self.killfeed_parser = ScalableKillfeedParser(self)
            from bot.parsers.scalable_historical_parser import ScalableHistoricalParser
            self.historical_parser = ScalableHistoricalParser(self)
            from bot.parsers.scalable_unified_parser import ScalableUnifiedParser
            self.unified_log_parser = ScalableUnifiedParser(self)
            # Ensure consistent parser access
            self.log_parser = self.unified_log_parser  # Legacy compatibility
            logger.info("Parsers initialized (PHASE 2) + Scalable Killfeed Parser + Scalable Historical Parser + Scalable Unified Parser + Advanced Rate Limiter + Batch Sender + Channel Router")

            return True

        except Exception as e:
            logger.error("Failed to connect to MongoDB: %s", e)
            return False

    def setup_scheduler(self):
        """Setup background job scheduler"""
        try:
            self.scheduler.start()
            logger.info("Background job scheduler started")
            return True
        except Exception as e:
            logger.error("Failed to start scheduler: %s", e)
            return False

    async def on_ready(self):
        """Called when bot is ready and connected to Discord"""
        # Only run setup once
        if hasattr(self, '_setup_complete'):
            return

        logger.info("🚀 Bot is ready! Starting bulletproof setup...")

        try:
            # STEP 1: Load cogs with proper async loading
            logger.info("🔧 Loading cogs for command registration...")
            cogs_success = await self.load_cogs()

            if not cogs_success:
                logger.error("❌ Cog loading failed - aborting setup")
                return

            logger.info("✅ Cog loading: Complete")

            # STEP 2: Verify commands are actually registered (py-cord 2.6.1 compatible)
            command_count = 0
            all_commands = []
            
            # Try different command attribute names for py-cord 2.6.1
            if hasattr(self, 'pending_application_commands') and self.pending_application_commands:
                command_count = len(self.pending_application_commands)
                all_commands = list(self.pending_application_commands)
            elif hasattr(self, 'application_commands') and self.application_commands:
                command_count = len(self.application_commands)
                all_commands = list(self.application_commands)
            else:
                # Fallback: count commands from cogs directly
                for cog_name, cog in self.cogs.items():
                    if hasattr(cog, 'get_commands'):
                        cog_commands = cog.get_commands()
                        command_count += len(cog_commands)
                        all_commands.extend(cog_commands)
                    # Also check for slash commands specifically
                    for attr_name in dir(cog):
                        attr = getattr(cog, attr_name)
                        if hasattr(attr, '__discord_app_commands_is_command__'):
                            command_count += 1

            if command_count == 0:
                logger.error("❌ CRITICAL: No commands found after cog loading - fix required")
                logger.error("❌ Check cog definitions and @discord.slash_command decorators")
                return

            logger.info(f"✅ {command_count} commands registered and ready for sync")

            # STEP 3: Command sync - disabled to prevent rate limiting
            # Commands are already loaded and functional in bot memory
            # Sync only when commands actually change, not on every startup
            logger.info("✅ Commands loaded and ready (sync bypassed to prevent rate limits)")

            # STEP 4: Set cold start flag for unified parser
            logger.info("🔄 Setting cold start flag for bot restart...")
            if hasattr(self, 'db_manager') and self.db_manager:
                try:
                    # Set global cold start flag in database
                    await self.db_manager.guild_configs.update_many(
                        {},  # All guilds
                        {'$set': {'cold_start_required': True}},
                        upsert=False
                    )
                    logger.info("✅ Cold start flag set for all guilds")
                except Exception as flag_error:
                    logger.warning(f"Failed to set cold start flag: {flag_error}")
            
            # STEP 5: Database setup with graceful degradation
            logger.info("🚀 Starting database and parser setup...")
            db_success = await self.setup_database()
            if not db_success:
                logger.error("❌ Database setup failed - operating in limited mode")
                # Continue with limited functionality rather than failing completely
                self._limited_mode = True
            else:
                logger.info("✅ Database setup: Success")
                self._limited_mode = False

            # STEP 5: Scheduler setup
            scheduler_success = self.setup_scheduler()
            if not scheduler_success:
                logger.error("❌ Scheduler setup failed")
                return
            logger.info("✅ Scheduler setup: Success")

            # STEP 6: Schedule parsers
            if self.killfeed_parser:
                self.scheduler.add_job(
                    self.killfeed_parser.run_killfeed_parser,
                    'interval',
                    minutes=5,
                    id='scalable_killfeed_parser'
                )
                logger.info("📡 Scalable killfeed parser scheduled")

            if self.unified_log_parser:
                try:
                    # Remove existing job if it exists
                    try:
                        self.scheduler.remove_job('unified_log_parser')
                    except:
                        pass

                    self.scheduler.add_job(
                        self.unified_log_parser.run_log_parser,
                        'interval',
                        seconds=180,
                        id='unified_log_parser',
                        max_instances=1,
                        coalesce=True
                    )
                    logger.info("📜 Unified log parser scheduled (180s interval)")

                    # Run initial parse
                    asyncio.create_task(self.unified_log_parser.run_log_parser())
                    logger.info("🔥 Initial unified log parser run triggered")

                except Exception as e:
                    logger.error(f"Failed to schedule unified log parser: {e}")

            # STEP 7: Final status
            if self.user:
                logger.info("✅ Bot logged in as %s (ID: %s)", self.user.name, self.user.id)
            logger.info("✅ Connected to %d guilds", len(self.guilds))

            for guild in self.guilds:
                logger.info(f"📡 Bot connected to: {guild.name} (ID: {guild.id})")

            # Verify assets exist with detailed validation
            if self.assets_path.exists():
                assets = list(self.assets_path.glob('*.png'))
                logger.info("📁 Found %d asset files", len(assets))

                # Validate required assets
                required_assets = ['main.png', 'Killfeed.png', 'Mission.png', 'Connections.png']
                missing_assets = []
                for asset in required_assets:
                    asset_path = self.assets_path / asset
                    if not asset_path.exists():
                        missing_assets.append(asset)

                if missing_assets:
                    logger.warning(f"⚠️ Missing required assets: {missing_assets}")
                else:
                    logger.info("✅ All required assets found")
            else:
                logger.warning("⚠️ Assets directory not found - creating default structure")
                self.assets_path.mkdir(exist_ok=True)

            logger.info("🎉 Bot setup completed successfully!")
            self._setup_complete = True

        except Exception as e:
            logger.error(f"❌ Critical error in bot setup: {e}")
            import traceback
            logger.error(f"Setup error traceback: {traceback.format_exc()}")
            raise

    async def on_guild_join(self, guild):
        """Called when bot joins a new guild - NO SYNC to prevent rate limits"""
        logger.info("Joined guild: %s (ID: %s)", guild.name, guild.id)
        logger.info("Commands will be available after next restart (bulletproof mode)")

    async def on_guild_remove(self, guild):
        """Called when bot is removed from a guild - Clean up all data"""
        logger.info("Left guild: %s (ID: %s)", guild.name, guild.id)
        
        try:
            # Comprehensive cleanup of all guild-related data
            guild_id = guild.id
            
            # Remove guild configuration
            result = await self.database.db.guilds.delete_one({"guild_id": guild_id})
            logger.info("Cleaned guild config: %d documents", result.deleted_count)
            
            # Remove premium data
            result = await self.database.db.premium_limits.delete_one({"guild_id": guild_id})
            logger.info("Cleaned premium limits: %d documents", result.deleted_count)
            
            result = await self.database.db.server_premium_status.delete_many({"guild_id": guild_id})
            logger.info("Cleaned premium servers: %d documents", result.deleted_count)
            
            # Remove user data (stats, economy, linking)
            result = await self.database.db.user_stats.delete_many({"guild_id": guild_id})
            logger.info("Cleaned user stats: %d documents", result.deleted_count)
            
            result = await self.database.db.user_wallets.delete_many({"guild_id": guild_id})
            logger.info("Cleaned user wallets: %d documents", result.deleted_count)
            
            result = await self.database.db.wallet_events.delete_many({"guild_id": guild_id})
            logger.info("Cleaned wallet events: %d documents", result.deleted_count)
            
            result = await self.database.db.user_linking.delete_many({"guild_id": guild_id})
            logger.info("Cleaned user linking: %d documents", result.deleted_count)
            
            # Remove faction data
            result = await self.database.db.faction_members.delete_many({"guild_id": guild_id})
            logger.info("Cleaned faction members: %d documents", result.deleted_count)
            
            result = await self.database.db.factions.delete_many({"guild_id": guild_id})
            logger.info("Cleaned factions: %d documents", result.deleted_count)
            
            # Remove bounty data
            result = await self.database.db.bounties.delete_many({"guild_id": guild_id})
            logger.info("Cleaned bounties: %d documents", result.deleted_count)
            
            # Remove parser and session data
            result = await self.database.db.parser_states.delete_many({"guild_id": guild_id})
            logger.info("Cleaned parser states: %d documents", result.deleted_count)
            
            result = await self.database.db.player_sessions.delete_many({"guild_id": guild_id})
            logger.info("Cleaned player sessions: %d documents", result.deleted_count)
            
            # Remove leaderboard data
            result = await self.database.db.leaderboard_messages.delete_many({"guild_id": guild_id})
            logger.info("Cleaned leaderboard messages: %d documents", result.deleted_count)
            
            logger.info("Complete cleanup finished for guild %d", guild_id)
            
        except Exception as e:
            logger.error("Failed to clean up guild data: %s", e)

    async def close(self):
        """Clean shutdown"""
        logger.info("Shutting down bot...")

        # Clean up SFTP connections
        await self.cleanup_connections()

        # Flush advanced rate limiter if it exists
        if hasattr(self, 'advanced_rate_limiter'):
            await self.advanced_rate_limiter.flush_all_queues()
            logger.info("Advanced rate limiter flushed")

        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")

        # Proper MongoDB cleanup
        if hasattr(self, 'mongo_client') and self.mongo_client:
            try:
                # Close all database operations gracefully
                if hasattr(self, 'db_manager'):
                    # Cancel any pending database operations
                    await asyncio.sleep(0.1)

                if hasattr(self, 'db_manager') and self.db_manager and hasattr(self.db_manager, 'close'):
                    self.db_manager.close()
                    logger.info("MongoDB connection closed")
            except Exception as e:
                logger.error(f"Error closing MongoDB connection: {e}")

        await super().close()
        logger.info("Bot shutdown complete")

    async def shutdown(self):
        """Graceful shutdown"""
        try:
            # Flush any remaining batched messages
            if hasattr(self, 'batch_sender'):
                logger.info("Flushing remaining batched messages...")
                await self.batch_sender.flush_all_queues()
                logger.info("Batch sender flushed")

            # Flush advanced rate limiter
            if hasattr(self, 'advanced_rate_limiter'):
                logger.info("Flushing advanced rate limiter...")
                await self.advanced_rate_limiter.flush_all_queues()
                logger.info("Advanced rate limiter flushed")

            # Clean up SFTP connections
            await self.cleanup_connections()

            if self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("Scheduler stopped")

            if hasattr(self, 'db_manager') and self.db_manager and hasattr(self.db_manager, 'close'):
                self.db_manager.close()
                logger.info("MongoDB connection closed")

            await super().close()
            logger.info("Bot shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

async def main():
    """Main entry point"""
    # Check required environment variables for Railway deployment
    bot_token = os.getenv('BOT_TOKEN') or os.getenv('DISCORD_TOKEN')
    mongo_uri = os.getenv('MONGO_URI') or os.getenv('MONGODB_URI')
    tip4serv_key = os.getenv('TIP4SERV_KEY')  # Optional service key

    # Railway environment detection
    railway_env = os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RAILWAY_STATIC_URL')
    if railway_env:
        print(f"✅ Railway environment detected")

    # Validate required secrets
    if not bot_token:
        logger.error("❌ BOT_TOKEN not found in environment variables")
        logger.error("Please set BOT_TOKEN in your Railway environment variables")
        return

    if not mongo_uri:
        logger.error("❌ MONGO_URI not found in environment variables") 
        logger.error("Please set MONGO_URI in your Railway environment variables")
        return

    # Log startup success
    logger.info(f"✅ Bot starting with token: {'*' * 20}...{bot_token[-4:] if bot_token else 'MISSING'}")
    logger.info(f"✅ MongoDB URI configured: {'*' * 20}...{mongo_uri[-10:] if mongo_uri else 'MISSING'}")
    if tip4serv_key:
        logger.info(f"✅ TIP4SERV_KEY configured: {'*' * 10}...{tip4serv_key[-4:]}")
    else:
        logger.info("ℹ️ TIP4SERV_KEY not configured (optional)")

    # Create and run bot
    print("Creating bot instance...")
    bot = EmeraldKillfeedBot()

    try:
        # Initialize database and parsers
        logger.info("🚀 Starting database and parser setup...")

        # Connect to database
        bot.mongo_client = AsyncIOMotorClient(mongo_uri)
        await bot.mongo_client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")

        # Initialize database manager with caching
        from bot.utils.unified_cache import initialize_cache
        from bot.utils.cache_integration import create_cached_database_manager
        from bot.utils.premium_manager_v2 import PremiumManagerV2
        
        # Initialize cache system
        await initialize_cache()
        
        # Create base database manager
        base_db_manager = DatabaseManager(bot.mongo_client)
        
        # Use direct database manager to avoid cache blocking issues
        bot.db_manager = base_db_manager
        
        # Store cached version separately for parsers
        bot.cached_db_manager = create_cached_database_manager(base_db_manager)
        
        # Initialize premium manager v2 with cached database
        bot.premium_manager_v2 = PremiumManagerV2(bot.db_manager)
        bot.premium_manager = bot.premium_manager_v2

        # Perform database cleanup and initialization
        logger.info("🧹 Performing database cleanup and initialization...")
        await bot.db_manager.initialize_indexes()
        logger.info("Database architecture initialized (PHASE 1)")

        await bot.start(bot_token)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error("Error in bot execution: %s", e)
        raise
    finally:
        if not bot.is_closed():
            await bot.close()

if __name__ == "__main__":
    # Run the bot
    print("Starting main bot execution...")
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Critical error in main execution: {e}")
        import traceback
        traceback.print_exc()