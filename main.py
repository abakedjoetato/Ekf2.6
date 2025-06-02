#!/usr/bin/env python3
"""
Advanced Main Bot - 10/10 py-cord 2.6.1 Implementation
Complete reconstruction with server-scoped premium and guild feature unlocking
"""

import os
import sys
import logging
import asyncio
import traceback
from datetime import datetime
from typing import Optional, List, Dict, Any

import discord
from discord.ext import commands, tasks
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Advanced imports
from bot.models.advanced_database import AdvancedDatabaseManager

# Configure advanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AdvancedEmeraldBot(discord.Bot):
    """
    Advanced 10/10 Discord Bot using py-cord 2.6.1
    - Server-scoped premium subscriptions
    - Guild feature unlocking (1+ premium server enables guild features)
    - Cross-guild kill data with proper isolation
    - Real-time analytics from premium servers only
    - Free server killfeed-only limitation
    """
    
    def __init__(self):
        # Advanced bot configuration
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        intents.voice_states = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            description="Emerald's Killfeed - Advanced 10/10 Discord Bot",
            help_command=None,
            case_insensitive=True,
            strip_after_prefix=True,
            owner_id=718157721609625610  # Bot owner ID
        )
        
        # Core systems
        self.db_manager: Optional[AdvancedDatabaseManager] = None
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.unified_parser = None
        self.killfeed_parser = None
        self.channel_router = None
        
        # Advanced caching
        self._guild_cache: Dict[int, Dict] = {}
        self._premium_cache: Dict[int, bool] = {}
        self._startup_complete = False
        
        # Performance tracking
        self._command_stats = {}
        self._error_count = 0
        
    async def setup_hook(self):
        """Advanced setup hook with comprehensive initialization"""
        logger.info("🚀 Starting advanced bot initialization...")
        
        try:
            # Phase 1: Database initialization
            await self._initialize_database()
            
            # Phase 2: Parser systems
            await self._initialize_parsers()
            
            # Phase 3: Load cogs
            await self._load_all_cogs()
            
            # Phase 4: Background tasks
            await self._start_background_tasks()
            
            # Phase 5: Sync slash commands
            await self._sync_commands()
            
            self._startup_complete = True
            logger.info("✅ Advanced bot initialization complete!")
            
        except Exception as e:
            logger.error(f"❌ Bot initialization failed: {e}")
            logger.error(traceback.format_exc())
            await self.close()
            raise
    
    async def _initialize_database(self):
        """Initialize advanced database manager"""
        logger.info("📊 Initializing advanced database manager...")
        
        self.db_manager = AdvancedDatabaseManager()
        success = await self.db_manager.initialize()
        
        if not success:
            raise Exception("Database initialization failed")
        
        logger.info("✅ Advanced database manager initialized")
    
    async def _initialize_parsers(self):
        """Initialize parser systems"""
        logger.info("📜 Initializing parser systems...")
        
        try:
            # Initialize channel router
            from bot.utils.channel_router import ChannelRouter
            self.channel_router = ChannelRouter(self.db_manager)
            
            # Initialize advanced unified parser
            from bot.parsers.advanced_unified_parser import AdvancedUnifiedParser
            self.unified_parser = AdvancedUnifiedParser(self.db_manager, self.channel_router)
            
            # Initialize killfeed parser
            from bot.parsers.killfeed_parser import KillfeedParser
            self.killfeed_parser = KillfeedParser(self.db_manager, self.channel_router)
            
            logger.info("✅ Parser systems initialized")
        except Exception as e:
            logger.warning(f"⚠️ Parser initialization skipped: {e}")
            # Continue without parsers for now
    
    async def _load_all_cogs(self):
        """Load all cogs with advanced error handling"""
        logger.info("🔧 Loading advanced cogs...")
        
        cog_modules = [
            "bot.cogs.advanced_premium",     # Advanced premium system
            "bot.cogs.advanced_casino",      # Casino with premium validation
        ]
        
        # Optional cogs - load if available
        optional_cogs = [
            "bot.cogs.admin_channels",       # Admin tools with guild isolation
            "bot.cogs.autocomplete",         # Advanced autocomplete
            "bot.cogs.automated_leaderboard", # Premium-only leaderboards
            "bot.cogs.parsers",              # Parser management
            "bot.cogs.economy",              # Economy with guild isolation
            "bot.cogs.help",                 # Advanced help system
            "bot.cogs.info",                 # Server info with premium features
            "bot.cogs.leaderboards",         # Premium leaderboards
            "bot.cogs.player_lookup",        # Cross-guild player lookup
            "bot.cogs.server_management",    # Premium server management
            "bot.cogs.stats",                # Premium-only stats
            "bot.cogs.weapons",              # Weapon statistics
            "bot.cogs.voice_channel_sync"    # Real-time voice sync
        ]
        
        loaded_count = 0
        failed_cogs = []
        
        # Load core cogs first
        for cog_module in cog_modules:
            try:
                await self.load_extension(cog_module)
                loaded_count += 1
                logger.info(f"✅ Loaded: {cog_module}")
                
            except Exception as e:
                failed_cogs.append((cog_module, str(e)))
                logger.error(f"❌ Failed to load {cog_module}: {e}")
        
        # Load optional cogs
        for cog_module in optional_cogs:
            try:
                await self.load_extension(cog_module)
                loaded_count += 1
                logger.info(f"✅ Loaded: {cog_module}")
                
            except Exception as e:
                failed_cogs.append((cog_module, str(e)))
                logger.warning(f"⚠️ Optional cog failed: {cog_module}: {e}")
        
        logger.info(f"🎯 Loaded {loaded_count}/{len(cog_modules) + len(optional_cogs)} cogs successfully")
        
        if failed_cogs:
            logger.warning("⚠️ Failed cogs:")
            for cog, error in failed_cogs:
                logger.warning(f"  - {cog}: {error}")
    
    async def _start_background_tasks(self):
        """Start background tasks with scheduler"""
        logger.info("⏰ Starting background tasks...")
        
        self.scheduler = AsyncIOScheduler()
        
        # Only add parser tasks if parsers are available
        if self.unified_parser:
            self.scheduler.add_job(
                self.unified_parser.run_log_parser,
                trigger=IntervalTrigger(seconds=180),
                id="unified_parser",
                name="Unified Log Parser"
            )
        
        if self.killfeed_parser:
            self.scheduler.add_job(
                self.killfeed_parser.run_killfeed_parser,
                trigger=IntervalTrigger(seconds=300),
                id="killfeed_parser",
                name="Killfeed Parser"
            )
        
        # Database cleanup (every hour)
        if self.db_manager:
            self.scheduler.add_job(
                self.db_manager.cleanup_stale_sessions,
                trigger=IntervalTrigger(seconds=3600),
                id="db_cleanup",
                name="Database Cleanup"
            )
        
        # Cache cleanup (every 10 minutes)
        self.scheduler.add_job(
            self._cleanup_caches,
            trigger=IntervalTrigger(seconds=600),
            id="cache_cleanup",
            name="Cache Cleanup"
        )
        
        self.scheduler.start()
        logger.info("✅ Background tasks started")
        
        # Trigger initial parser run if available (delayed to avoid loop conflicts)
        if self.unified_parser:
            def delayed_parser_start():
                asyncio.create_task(self.unified_parser.run_log_parser())
            
            self.scheduler.add_job(
                delayed_parser_start,
                trigger=IntervalTrigger(seconds=10),
                id="initial_parser_run",
                name="Initial Parser Run",
                max_instances=1
            )
    
    async def _sync_commands(self):
        """Sync slash commands with advanced error handling"""
        try:
            logger.info("🔄 Syncing slash commands...")
            synced = await self.sync_commands()
            if synced:
                logger.info(f"✅ Synced {len(synced)} slash commands")
            else:
                logger.info("✅ No commands to sync")
            
        except Exception as e:
            logger.error(f"❌ Failed to sync commands: {e}")
    
    async def _cleanup_caches(self):
        """Clean up expired cache entries"""
        try:
            # Clear expired caches
            self._guild_cache.clear()
            self._premium_cache.clear()
            logger.debug("🧹 Cache cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Cache cleanup failed: {e}")
    
    async def on_ready(self):
        """Advanced ready event with comprehensive logging"""
        if not self._startup_complete:
            return
        
        logger.info(f"✅ Bot logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"✅ Connected to {len(self.guilds)} guilds")
        
        for guild in self.guilds:
            logger.info(f"📡 Bot connected to: {guild.name} (ID: {guild.id})")
            
            # Initialize guild in database if needed
            await self._ensure_guild_initialized(guild.id, guild.name)
        
        # Set advanced bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="emerald servers | /premium status"
        )
        await self.change_presence(activity=activity, status=discord.Status.online)
        
        logger.info("🎉 Advanced bot startup completed successfully!")
    
    async def _ensure_guild_initialized(self, guild_id: int, guild_name: str):
        """Ensure guild is properly initialized in database"""
        try:
            if not self.db_manager:
                return
                
            # Check if guild features exist
            guild_features = await self.db_manager.db.guild_features.find_one({"guild_id": guild_id})
            
            if not guild_features:
                # Initialize guild
                guild_config = {
                    "guild_id": guild_id,
                    "name": guild_name,
                    "premium_servers": [],
                    "features_enabled": [],
                    "analytics_enabled": False,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                await self.db_manager.db.guild_features.insert_one(guild_config)
                logger.info(f"✅ Initialized guild: {guild_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize guild {guild_id}: {e}")
    
    async def on_guild_join(self, guild: discord.Guild):
        """Handle new guild joining"""
        logger.info(f"📥 Joined new guild: {guild.name} (ID: {guild.id})")
        await self._ensure_guild_initialized(guild.id, guild.name)
    
    async def on_guild_remove(self, guild: discord.Guild):
        """Handle guild removal"""
        logger.info(f"📤 Left guild: {guild.name} (ID: {guild.id})")
        # Note: We don't delete guild data to preserve it if they re-add the bot
    
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: Exception):
        """Advanced error handling for slash commands"""
        self._error_count += 1
        
        # Log error with context
        logger.error(f"❌ Command error in {ctx.command.qualified_name}: {error}")
        logger.error(f"   Guild: {ctx.guild.id if ctx.guild else 'DM'}")
        logger.error(f"   User: {ctx.author.id}")
        logger.error(traceback.format_exc())
        
        # User-friendly error responses
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.respond(
                f"⏰ Command is on cooldown. Try again in {error.retry_after:.1f} seconds.",
                ephemeral=True
            )
        elif isinstance(error, commands.MissingPermissions):
            await ctx.respond(
                "❌ You don't have permission to use this command.",
                ephemeral=True
            )
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.respond(
                "❌ I don't have the required permissions to execute this command.",
                ephemeral=True
            )
        else:
            # Generic error response
            await ctx.respond(
                "❌ An error occurred while processing your command. Please try again.",
                ephemeral=True
            )
    
    async def on_error(self, event: str, *args, **kwargs):
        """Advanced global error handler"""
        self._error_count += 1
        logger.error(f"❌ Unhandled error in {event}: {sys.exc_info()[1]}")
        logger.error(traceback.format_exc())
    
    async def close(self):
        """Advanced cleanup on bot shutdown"""
        logger.info("🔄 Starting bot shutdown...")
        
        try:
            # Stop scheduler
            if self.scheduler and self.scheduler.running:
                self.scheduler.shutdown(wait=False)
                logger.info("✅ Scheduler stopped")
            
            # Close database connection
            if self.db_manager:
                await self.db_manager.close()
                logger.info("✅ Database connection closed")
            
            # Call parent close
            await super().close()
            logger.info("✅ Bot shutdown complete")
            
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")

# Advanced bot instance and runner
bot = AdvancedEmeraldBot()

async def main():
    """Advanced main function with comprehensive error handling"""
    try:
        # Verify environment variables
        bot_token = os.getenv('BOT_TOKEN')
        mongo_uri = os.getenv('MONGO_URI')
        
        if not bot_token:
            logger.error("❌ BOT_TOKEN environment variable not found")
            return
        
        if not mongo_uri:
            logger.error("❌ MONGO_URI environment variable not found")
            return
        
        logger.info("🚀 Starting advanced Emerald's Killfeed bot...")
        
        # Start the bot
        await bot.start(bot_token)
        
    except discord.LoginFailure:
        logger.error("❌ Invalid bot token")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        logger.error(traceback.format_exc())
    finally:
        if not bot.is_closed():
            await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        sys.exit(1)