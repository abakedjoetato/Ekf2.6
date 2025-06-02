#!/usr/bin/env python3
"""
Debug Missing Leaderboard Data
Check what's actually in the database for weapons and streaks
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Debug missing weapons and streaks data"""
    try:
        mongo_uri = os.getenv('MONGO_URI')
        client = AsyncIOMotorClient(mongo_uri)
        db = client.killfeed_db
        
        guild_id = 1219706687980568769
        
        logger.info("=== DEBUGGING MISSING DATA ===")
        
        # Check streak data specifically
        logger.info("\n1. CHECKING STREAK DATA:")
        streak_query = {"guild_id": guild_id, "longest_streak": {"$gt": 0}}
        streak_count = await db.pvp_data.count_documents(streak_query)
        logger.info(f"Documents with streaks > 0: {streak_count}")
        
        if streak_count > 0:
            top_streak = await db.pvp_data.find_one(streak_query, sort=[("longest_streak", -1)])
            logger.info(f"Top streak player: {top_streak.get('player_name')} - {top_streak.get('longest_streak')} streak")
        
        # Check all pvp data for any streak fields
        all_pvp = await db.pvp_data.find({"guild_id": guild_id}).limit(5).to_list(length=None)
        logger.info(f"\nSample PVP data fields:")
        for player in all_pvp:
            fields = list(player.keys())
            logger.info(f"Player {player.get('player_name', 'Unknown')}: {fields}")
            if 'longest_streak' in player:
                logger.info(f"  Longest streak: {player.get('longest_streak')}")
        
        # Check weapon data in kill_events
        logger.info("\n2. CHECKING WEAPON DATA:")
        weapon_count = await db.kill_events.count_documents({"guild_id": guild_id})
        logger.info(f"Total kill events: {weapon_count}")
        
        if weapon_count > 0:
            # Sample some kill events
            sample_events = await db.kill_events.find({"guild_id": guild_id}).limit(5).to_list(length=None)
            logger.info("Sample kill events:")
            for event in sample_events:
                weapon = event.get('weapon', 'Unknown')
                killer = event.get('killer', 'Unknown')
                logger.info(f"  {killer} used {weapon}")
        
        # Check weapons aggregation
        logger.info("\n3. TESTING WEAPON AGGREGATION:")
        pipeline = [
            {"$match": {"guild_id": guild_id}},
            {"$group": {
                "_id": "$weapon",
                "kills": {"$sum": 1},
                "top_user": {"$first": "$killer"}
            }},
            {"$sort": {"kills": -1}},
            {"$limit": 3}
        ]
        
        weapon_results = await db.kill_events.aggregate(pipeline).to_list(length=None)
        logger.info(f"Weapon aggregation results: {len(weapon_results)} weapons found")
        for weapon in weapon_results:
            logger.info(f"  {weapon['_id']}: {weapon['kills']} kills (top: {weapon['top_user']})")
        
        logger.info("\n=== DEBUG COMPLETE ===")
        
    except Exception as e:
        logger.error(f"Error debugging data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())