#!/usr/bin/env python3
"""
Premium System Migration Script
Migrates existing guild and server data to work with the new premium system
"""

import asyncio
import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_premium_system():
    """Main migration function"""
    
    # Get MongoDB connection
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        logger.error("MONGO_URI environment variable not set")
        return False
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client.emerald_killfeed
    
    try:
        logger.info("Starting premium system migration...")
        
        # Step 1: Check existing guilds
        guilds = await db.guilds.find({}).to_list(length=None)
        logger.info(f"Found {len(guilds)} existing guilds")
        
        for guild in guilds:
            guild_id = guild.get('guild_id')
            if not guild_id:
                logger.warning(f"Guild missing guild_id: {guild.get('_id')}")
                continue
                
            logger.info(f"Processing guild {guild_id}")
            
            # Step 2: Create premium limit for each guild (default to 1)
            await db.premium_limits.update_one(
                {"guild_id": guild_id},
                {
                    "$set": {
                        "guild_id": guild_id,
                        "limit": 1,
                        "created_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc)
                    },
                    "$setOnInsert": {
                        "history": [{
                            "action": "migration",
                            "amount": 1,
                            "by": 0,  # System migration
                            "reason": "Initial migration to new premium system",
                            "timestamp": datetime.now(timezone.utc)
                        }]
                    }
                },
                upsert=True
            )
            
            # Step 3: Check servers for this guild
            servers = guild.get('servers', [])
            if isinstance(servers, dict):
                # Convert dict format to list format
                server_list = []
                for server_id, server_config in servers.items():
                    server_config['_id'] = server_id
                    server_config['server_id'] = server_id
                    server_list.append(server_config)
                servers = server_list
                
                # Update guild document with new format
                await db.guilds.update_one(
                    {"_id": guild["_id"]},
                    {"$set": {"servers": servers}}
                )
                logger.info(f"Converted servers dict to list format for guild {guild_id}")
            
            # Step 4: Activate premium for all existing servers (migration)
            for server in servers:
                server_id = server.get('_id') or server.get('server_id')
                server_name = server.get('name', 'Unknown Server')
                
                if server_id:
                    await db.server_premium_status.update_one(
                        {"guild_id": guild_id, "server_id": str(server_id)},
                        {
                            "$set": {
                                "guild_id": guild_id,
                                "server_id": str(server_id),
                                "is_active": True,
                                "activated_by": 0,  # System migration
                                "activated_at": datetime.now(timezone.utc),
                                "reason": "Migration from legacy system",
                                "expires_at": None
                            }
                        },
                        upsert=True
                    )
                    logger.info(f"Activated premium for server {server_name} ({server_id})")
        
        # Step 5: Create indexes for new collections
        await db.premium_limits.create_index("guild_id", unique=True)
        await db.server_premium_status.create_index([("guild_id", 1), ("server_id", 1)], unique=True)
        await db.bot_config.create_index("type", unique=True)
        
        logger.info("Premium system migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False
    finally:
        client.close()

async def check_migration_status():
    """Check if migration is needed and show current status"""
    
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        logger.error("MONGO_URI environment variable not set")
        return
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client.emerald_killfeed
    
    try:
        # Check existing data
        guild_count = await db.guilds.count_documents({})
        premium_limit_count = await db.premium_limits.count_documents({})
        premium_server_count = await db.server_premium_status.count_documents({})
        
        logger.info(f"Current database status:")
        logger.info(f"  Guilds: {guild_count}")
        logger.info(f"  Premium limits: {premium_limit_count}")
        logger.info(f"  Premium servers: {premium_server_count}")
        
        if guild_count > 0 and premium_limit_count == 0:
            logger.info("Migration needed: No premium data found for existing guilds")
            return True
        else:
            logger.info("Migration not needed or already completed")
            return False
            
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return False
    finally:
        client.close()

if __name__ == "__main__":
    async def main():
        # Check if migration is needed
        needs_migration = await check_migration_status()
        
        if needs_migration:
            logger.info("Starting migration...")
            success = await migrate_premium_system()
            if success:
                logger.info("Migration completed successfully!")
            else:
                logger.error("Migration failed!")
        else:
            logger.info("No migration needed")
    
    asyncio.run(main())