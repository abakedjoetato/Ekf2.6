#!/usr/bin/env python3
"""
Test Working Leaderboards with Real Data
Test actual leaderboard functionality with the confirmed data structure
"""
import asyncio
import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

async def test_working_leaderboards():
    """Test leaderboards with the actual data structure"""
    try:
        # Connect to MongoDB
        mongo_uri = os.getenv('MONGO_URI')
        client = AsyncIOMotorClient(mongo_uri)
        db = client.emerald_killfeed
        
        guild_id = 1219706687980568769
        
        logger.info("=== TESTING WORKING LEADERBOARDS ===")
        
        # 1. TOP KILLERS (using confirmed data structure)
        logger.info("\n1. TOP KILLERS:")
        kills_cursor = db.pvp_data.find({"guild_id": guild_id, "kills": {"$gt": 0}}).sort("kills", -1).limit(5)
        top_killers = await kills_cursor.to_list(length=None)
        
        if top_killers:
            for i, player in enumerate(top_killers, 1):
                logger.info(f"  {i}. {player.get('player_name')} - {player.get('kills')} kills")
        else:
            logger.info("  No kill data found")
        
        # 2. TOP KDR
        logger.info("\n2. TOP KDR:")
        kdr_cursor = db.pvp_data.find({"guild_id": guild_id, "deaths": {"$gt": 0}}).sort("kdr", -1).limit(5)
        top_kdr = await kdr_cursor.to_list(length=None)
        
        if top_kdr:
            for i, player in enumerate(top_kdr, 1):
                logger.info(f"  {i}. {player.get('player_name')} - {player.get('kdr'):.2f} KDR")
        else:
            logger.info("  No KDR data found")
        
        # 3. LONGEST SHOTS
        logger.info("\n3. LONGEST SHOTS:")
        distance_cursor = db.pvp_data.find({"guild_id": guild_id, "personal_best_distance": {"$gt": 0}}).sort("personal_best_distance", -1).limit(5)
        top_distances = await distance_cursor.to_list(length=None)
        
        if top_distances:
            for i, player in enumerate(top_distances, 1):
                logger.info(f"  {i}. {player.get('player_name')} - {player.get('personal_best_distance')}m")
        else:
            logger.info("  No distance data found")
        
        # 4. BEST STREAKS
        logger.info("\n4. BEST STREAKS:")
        streak_cursor = db.pvp_data.find({"guild_id": guild_id, "longest_streak": {"$gt": 0}}).sort("longest_streak", -1).limit(5)
        top_streaks = await streak_cursor.to_list(length=None)
        
        if top_streaks:
            for i, player in enumerate(top_streaks, 1):
                logger.info(f"  {i}. {player.get('player_name')} - {player.get('longest_streak')} streak")
        else:
            logger.info("  No streak data found")
        
        # 5. TOP WEAPONS (from kill_events)
        logger.info("\n5. TOP WEAPONS:")
        weapon_pipeline = [
            {"$match": {"guild_id": guild_id, "is_suicide": False}},
            {"$group": {"_id": "$weapon", "kills": {"$sum": 1}, "top_user": {"$first": "$killer"}}},
            {"$sort": {"kills": -1}},
            {"$limit": 5}
        ]
        weapon_cursor = db.kill_events.aggregate(weapon_pipeline)
        top_weapons = await weapon_cursor.to_list(length=None)
        
        if top_weapons:
            for i, weapon in enumerate(top_weapons, 1):
                logger.info(f"  {i}. {weapon.get('_id')} - {weapon.get('kills')} kills (Top: {weapon.get('top_user')})")
        else:
            logger.info("  No weapon data found")
        
        # 6. SUMMARY STATS
        logger.info("\n6. SUMMARY:")
        total_players = await db.pvp_data.count_documents({"guild_id": guild_id})
        active_players = await db.pvp_data.count_documents({"guild_id": guild_id, "kills": {"$gt": 0}})
        total_events = await db.kill_events.count_documents({"guild_id": guild_id})
        
        logger.info(f"  Total Players: {total_players}")
        logger.info(f"  Active Players: {active_players}")
        logger.info(f"  Total Kill Events: {total_events}")
        
        client.close()
        logger.info("\n=== LEADERBOARD TEST COMPLETE ===")
        
    except Exception as e:
        logger.error(f"Error testing leaderboards: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_working_leaderboards())