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
from bot.parsers.killfeed_parser import KillfeedParser
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
            activity=discord.Game(name="Emerald's Killfeed v2.0")
        )

        # Initialize variables
        self.db_manager = None
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
        """Load all cogs with comprehensive error handling"""
        cog_files = [
            'bot.cogs.core',
            'bot.cogs.admin_channels',
            'bot.cogs.admin_batch',
            'bot.cogs.linking',
            'bot.cogs.stats',
            'bot.cogs.leaderboards_fixed',
            'bot.cogs.automated_leaderboard',
            'bot.cogs.economy',
            'bot.cogs.gambling',
            'bot.cogs.bounties',
            'bot.cogs.factions',
            'bot.cogs.premium',
            'bot.cogs.parsers'
        ]

        loaded_count = 0
        failed_cogs = []

        for cog in cog_files:
            try:
                self.load_extension(cog)
                logger.info(f"✅ Successfully loaded cog: {cog}")
                loaded_count += 1
            except Exception as e:
                logger.error(f"❌ Failed to load cog {cog}: {e}")
                logger.error(f"Cog error traceback: {traceback.format_exc()}")
                failed_cogs.append(cog)

        logger.info(f"📊 Loaded {loaded_count}/{len(cog_files)} cogs successfully")

        # Log command count
        total_commands = len(self.pending_application_commands)
        logger.info(f"📊 Total slash commands registered: {total_commands} (via pending_application_commands)")

        # Log command names (first 10)
        if self.pending_application_commands:
            command_names = [cmd.name for cmd in self.pending_application_commands[:10]]
            logger.info(f"🔍 Commands found: {', '.join(command_names)}...")

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
        Production-ready sync logic:
        - Avoids redundant syncs with command fingerprinting
        - Caches command hash to prevent unnecessary syncs
        - Falls back to per-guild on global sync failure
        - Applies intelligent rate limit cooldowns
        """
        try:
            # Get all commands
            all_commands = []
            if hasattr(self, 'application_commands') and self.application_commands:
                all_commands = list(self.application_commands)
            elif hasattr(self, 'pending_application_commands') and self.pending_application_commands:
                all_commands = list(self.pending_application_commands)

            if not all_commands:
                logger.warning("⚠️ No commands found for syncing")
                return

            # Calculate current command fingerprint
            current_fingerprint = self.calculate_command_fingerprint(all_commands)
            if not current_fingerprint:
                logger.error("❌ Failed to calculate command fingerprint")
                return

            hash_file = "command_hash.txt"
            cooldown_file = "command_sync_cooldown.txt"
            cooldown_secs = 1800  # 30 minutes

            # Check for rate-limit cooldown
            if os.path.exists(cooldown_file):
                try:
                    with open(cooldown_file, 'r') as f:
                        until = float(f.read().strip())
                        if time.time() < until:
                            remaining = int(until - time.time())
                            logger.warning(f"⏳ Command sync on cooldown for {remaining}s. Skipping.")
                            return
                        else:
                            os.remove(cooldown_file)
                            logger.info("✅ Rate limit cooldown expired")
                except Exception:
                    pass

            # Check for command changes
            old_fingerprint = None
            if os.path.exists(hash_file):
                try:
                    with open(hash_file, 'r') as f:
                        old_fingerprint = f.read().strip()
                except Exception:
                    pass

            # Force sync override for development
            force_sync = os.getenv('FORCE_SYNC', 'false').lower() == 'true'

            # Temporarily force sync to fix missing commands
            if current_fingerprint == old_fingerprint and not force_sync:
                logger.info("🔄 Forcing sync to fix missing Discord commands...")
                # Comment out the return to force sync
                # return

            logger.info(f"🔄 Command structure changed - syncing {len(all_commands)} commands")

            # Attempt global sync
            try:
                logger.info("🌍 Performing global command sync...")
                await asyncio.wait_for(self.sync_commands(), timeout=30)
                logger.info("✅ Global sync complete")

                # Save successful fingerprint
                with open(hash_file, 'w') as f:
                    f.write(current_fingerprint)
                with open("global_sync_success.txt", 'w') as f:
                    f.write(str(time.time()))
                return

            except Exception as e:
                error_msg = str(e).lower()
                if "429" in error_msg or "rate limit" in error_msg:
                    logger.warning(f"❌ Global sync rate limited: {e}")
                    # Set cooldown
                    with open(cooldown_file, 'w') as f:
                        f.write(str(time.time() + cooldown_secs))
                else:
                    logger.warning(f"⚠️ Global sync failed: {e}")

            # Per-guild fallback
            logger.info(f"🏠 Performing per-guild sync fallback for {len(self.guilds)} guilds...")
            success_count = 0

            for guild in self.guilds:
                try:
                    await asyncio.wait_for(self.sync_commands(guild_ids=[guild.id]), timeout=15)
                    success_count += 1
                    logger.info(f"✅ Guild sync: {guild.name}")
                    await asyncio.sleep(1.5)  # Rate limit prevention

                except Exception as ge:
                    error_msg = str(ge).lower()
                    if "429" in error_msg or "rate limit" in error_msg:
                        logger.warning(f"🛑 Hit rate limit on guild sync - halting further syncs.")
                        with open(cooldown_file, 'w') as f:
                            f.write(str(time.time() + cooldown_secs))
                        break
                    else:
                        logger.warning(f"❌ Guild sync failed for {guild.name}: {ge}")

            if success_count > 0:
                # Save successful fingerprint even on partial success
                with open(hash_file, 'w') as f:
                    f.write(current_fingerprint)
                logger.info(f"✅ Per-guild sync completed: {success_count}/{len(self.guilds)} successful")
            else:
                logger.warning("⚠️ All sync methods failed")

        except Exception as e:
            logger.error(f"❌ Command sync logic failed: {e}")
            import traceback
            logger.error(f"Sync traceback: {traceback.format_exc()}")

    async def cleanup_connections(self):
        """Clean up AsyncSSH connections on shutdown with enhanced error recovery"""
        try:
            cleanup_tasks = []

            # Killfeed parser cleanup
            if hasattr(self, 'killfeed_parser') and self.killfeed_parser:
                cleanup_tasks.append(self._cleanup_parser_connections(self.killfeed_parser, "killfeed"))

            # Unified log parser cleanup  
            if hasattr(self, 'unified_log_parser') and self.unified_log_parser:
                cleanup_tasks.append(self._cleanup_parser_connections(self.unified_log_parser, "unified_log"))

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
                self.unified_log_parser.reset_parser_state()

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

            # Initialize database manager with PHASE 1 architecture
            from bot.models.database import DatabaseManager
            self.db_manager = DatabaseManager(self.mongo_client)
            # Ensure consistent access pattern
            self.database = self.db_manager  # Legacy compatibility

            # Test connection
            await self.mongo_client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")

            # Initialize database indexes
            await self.db_manager.initialize_indexes()
            logger.info("Database architecture initialized (PHASE 1)")

            # Initialize batch sender for rate limit management
            from bot.utils.batch_sender import BatchSender
            self.batch_sender = BatchSender(self)

            # Initialize advanced rate limiter
            from bot.utils.advanced_rate_limiter import AdvancedRateLimiter
            self.advanced_rate_limiter = AdvancedRateLimiter(self)

            # Initialize parsers (PHASE 2) - Data parsers for killfeed & log events
            self.killfeed_parser = KillfeedParser(self)
            self.historical_parser = HistoricalParser(self)
            self.unified_log_parser = UnifiedLogParser(self)
            # Ensure consistent parser access
            self.log_parser = self.unified_log_parser  # Legacy compatibility
            logger.info("Parsers initialized (PHASE 2) + Unified Log Parser + Advanced Rate Limiter + Batch Sender")

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

            # STEP 2: Verify commands are actually registered
            command_count = 0
            if hasattr(self, 'pending_application_commands'):
                command_count = len(self.pending_application_commands)
            elif hasattr(self, 'application_commands'):
                command_count = len(self.application_commands)

            if command_count == 0:
                logger.error("❌ CRITICAL: No commands found after cog loading - fix required")
                return

            logger.info(f"✅ {command_count} commands registered and ready for sync")

            # STEP 3: Command sync - simplified and robust
            logger.info("🔧 Starting command sync...")
            try:
                await self.register_commands_safely()
                logger.info("✅ Command sync completed")
            except Exception as sync_error:
                logger.error(f"❌ Command sync failed: {sync_error}")

            # STEP 4: Database setup with graceful degradation
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
                self.killfeed_parser.schedule_killfeed_parser()
                logger.info("📡 Killfeed parser scheduled")

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
        """Called when bot is removed from a guild"""
        logger.info("Left guild: %s (ID: %s)", guild.name, guild.id)

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

                self.mongo_client.close()
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

            if hasattr(self, 'mongo_client') and self.mongo_client:
                self.mongo_client.close()
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

        # Initialize database manager
        bot.db_manager = DatabaseManager(bot.mongo_client)

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