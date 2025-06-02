#!/usr/bin/env python3
"""
Check Leaderboard Data
Direct database query to see what's actually available for the leaderboard
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
    """Check what data is available for leaderboards"""
    try:
        mongo_uri = os.getenv('MONGO_URI')
        client = AsyncIOMotorClient(mongo_uri)
        db = client.killfeed_db
        
        guild_id = 1219706687980568769
        
        logger.info("=== LEADERBOARD DATA CHECK ===")
        
        # Check PVP data for top killers
        logger.info("\n1. TOP KILLERS:")
        pvp_cursor = db.pvp_data.find({"guild_id": guild_id, "kills": {"$gt": 0}}).sort("kills", -1).limit(5)
        top_killers = await pvp_cursor.to_list(length=None)
        
        if top_killers:
            for i, player in enumerate(top_killers, 1):
                logger.info(f"  {i}. {player.get('player_name', 'Unknown')} - {player.get('kills', 0)} kills")
        else:
            logger.info("  No kill data found")
        
        # Check for KDR data
        logger.info("\n2. TOP KDR:")
        all_players = await db.pvp_data.find({"guild_id": guild_id, "kills": {"$gte": 1}}).to_list(length=None)
        
        kdr_players = []
        for player in all_players:
            kills = player.get('kills', 0)
            deaths = player.get('deaths', 0)
            kdr = kills / max(deaths, 1) if deaths > 0 else float(kills)
            player['kdr'] = kdr
            kdr_players.append(player)
        
        kdr_players.sort(key=lambda x: x['kdr'], reverse=True)
        top_kdr = kdr_players[:3]
        
        if top_kdr:
            for i, player in enumerate(top_kdr, 1):
                logger.info(f"  {i}. {player.get('player_name', 'Unknown')} - {player.get('kdr', 0):.2f} KDR")
        else:
            logger.info("  No KDR data found")
        
        # Check distance data
        logger.info("\n3. LONGEST SHOTS:")
        distance_cursor = db.pvp_data.find({"guild_id": guild_id, "personal_best_distance": {"$gt": 0}}).sort("personal_best_distance", -1).limit(3)
        top_distance = await distance_cursor.to_list(length=None)
        
        if top_distance:
            for i, player in enumerate(top_distance, 1):
                distance = player.get('personal_best_distance', 0)
                logger.info(f"  {i}. {player.get('player_name', 'Unknown')} - {distance}m")
        else:
            logger.info("  No distance data found")
        
        # Check streaks
        logger.info("\n4. BEST STREAKS:")
        streak_cursor = db.pvp_data.find({"guild_id": guild_id, "longest_streak": {"$gt": 0}}).sort("longest_streak", -1).limit(3)
        top_streaks = await streak_cursor.to_list(length=None)
        
        if top_streaks:
            for i, player in enumerate(top_streaks, 1):
                streak = player.get('longest_streak', 0)
                logger.info(f"  {i}. {player.get('player_name', 'Unknown')} - {streak} streak")
        else:
            logger.info("  No streak data found")
        
        # Check weapons
        logger.info("\n5. TOP WEAPONS:")
        kill_events_cursor = db.kill_events.find({"guild_id": guild_id})
        kill_events = await kill_events_cursor.to_list(length=None)
        
        weapon_stats = {}
        for event in kill_events:
            weapon = event.get('weapon', 'Unknown')
            if weapon != 'Unknown':
                if weapon not in weapon_stats:
                    weapon_stats[weapon] = {'kills': 0, 'top_user': event.get('killer', 'Unknown')}
                weapon_stats[weapon]['kills'] += 1
        
        sorted_weapons = sorted(weapon_stats.items(), key=lambda x: x[1]['kills'], reverse=True)[:3]
        
        if sorted_weapons:
            for i, (weapon, stats) in enumerate(sorted_weapons, 1):
                logger.info(f"  {i}. {weapon} - {stats['kills']} kills (Top: {stats['top_user']})")
        else:
            logger.info("  No weapon data found")
        
        # Check factions
        logger.info("\n6. TOP FACTIONS:")
        factions_cursor = db.factions.find({"guild_id": guild_id}).sort("kills", -1).limit(1)
        top_factions = await factions_cursor.to_list(length=None)
        
        if top_factions:
            faction = top_factions[0]
            logger.info(f"  1. {faction.get('faction_name', 'Unknown')} - {faction.get('kills', 0)} kills")
        else:
            logger.info("  No faction data found")
        
        logger.info("\n=== DATA CHECK COMPLETE ===")
        
    except Exception as e:
        logger.error(f"Error checking data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())