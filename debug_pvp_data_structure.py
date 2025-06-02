#!/usr/bin/env python3
"""
Debug PVP Data Structure
Check the actual structure of player statistics in the database
"""
import asyncio
import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

async def debug_pvp_data():
    """Debug the actual structure of pvp_data collection"""
    try:
        # Connect to MongoDB
        mongo_uri = os.getenv('MONGO_URI')
        client = AsyncIOMotorClient(mongo_uri)
        db = client.emerald_killfeed
        
        guild_id = 1219706687980568769
        
        logger.info("=== DEBUGGING PVP DATA STRUCTURE ===")
        
        # Get first 5 players from pvp_data
        pvp_cursor = db.pvp_data.find({"guild_id": guild_id}).limit(5)
        players = await pvp_cursor.to_list(length=None)
        
        logger.info(f"Found {len(players)} sample players")
        
        for i, player in enumerate(players, 1):
            logger.info(f"\nPlayer {i} structure:")
            for key, value in player.items():
                if key != '_id':  # Skip ObjectId for readability
                    logger.info(f"  {key}: {value} (type: {type(value).__name__})")
        
        # Check for players with any kills > 0
        high_kill_cursor = db.pvp_data.find({"guild_id": guild_id, "kills": {"$gt": 0}})
        high_kill_players = await high_kill_cursor.to_list(length=None)
        logger.info(f"\nPlayers with kills > 0: {len(high_kill_players)}")
        
        # Check total kills in collection
        total_stats = await db.pvp_data.aggregate([
            {"$match": {"guild_id": guild_id}},
            {"$group": {
                "_id": None,
                "total_kills": {"$sum": "$kills"},
                "total_deaths": {"$sum": "$deaths"},
                "max_kills": {"$max": "$kills"},
                "min_kills": {"$min": "$kills"}
            }}
        ]).to_list(length=None)
        
        if total_stats:
            stats = total_stats[0]
            logger.info(f"\nCollection statistics:")
            logger.info(f"  Total kills across all players: {stats.get('total_kills', 0)}")
            logger.info(f"  Total deaths across all players: {stats.get('total_deaths', 0)}")
            logger.info(f"  Max kills by single player: {stats.get('max_kills', 0)}")
            logger.info(f"  Min kills by single player: {stats.get('min_kills', 0)}")
        
        # Sample some kill_events too
        logger.info(f"\n=== SAMPLE KILL EVENTS ===")
        kill_cursor = db.kill_events.find({"guild_id": guild_id}).limit(3)
        kills = await kill_cursor.to_list(length=None)
        
        for i, kill in enumerate(kills, 1):
            logger.info(f"\nKill {i}:")
            logger.info(f"  Killer: {kill.get('killer')}")
            logger.info(f"  Victim: {kill.get('victim')}")
            logger.info(f"  Weapon: {kill.get('weapon')}")
            logger.info(f"  Distance: {kill.get('distance')}")
            logger.info(f"  Is Suicide: {kill.get('is_suicide')}")
        
        client.close()
        
    except Exception as e:
        logger.error(f"Error debugging pvp data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_pvp_data())