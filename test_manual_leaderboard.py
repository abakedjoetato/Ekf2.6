"""
Manual Leaderboard Test
Triggers automated leaderboard creation immediately
"""

import asyncio
import os
import discord
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import logging

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_manual_leaderboard():
    """Manually trigger leaderboard creation"""
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(os.getenv('MONGO_URI'))
        db = client['emerald_killfeed']
        
        guild_id = 1219706687980568769
        server_id = "7020"
        
        # Get guild config
        guild_config = await db['guilds'].find_one({'guild_id': guild_id})
        if not guild_config:
            print("No guild config found")
            return
            
        # Get channel ID
        leaderboard_channel_id = guild_config.get('server_channels', {}).get('default', {}).get('leaderboard')
        if not leaderboard_channel_id:
            leaderboard_channel_id = guild_config.get('channels', {}).get('leaderboard')
            
        if not leaderboard_channel_id:
            print("No leaderboard channel configured")
            return
            
        print(f"Leaderboard channel ID: {leaderboard_channel_id}")
        
        # Get top players data
        pvp_data = db['pvp_data']
        top_kills = await pvp_data.find({
            "guild_id": guild_id,
            "server_id": server_id,
            "kills": {"$gt": 0}
        }).sort("kills", -1).limit(10).to_list(length=None)
        
        print(f"Found {len(top_kills)} players with kills")
        for i, player in enumerate(top_kills[:5], 1):
            print(f"{i}. {player.get('player_name', 'Unknown')} - {player.get('kills', 0)} kills")
            
        client.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_manual_leaderboard())