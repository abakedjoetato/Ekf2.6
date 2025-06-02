#!/usr/bin/env python3
"""
Check Economy Collection Status
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def check_economy_status():
    client = AsyncIOMotorClient(os.getenv('MONGO_URI'))
    db = client.EmeraldDB
    
    guild_id = 1219706687980568769
    
    print("Checking economy collection...")
    
    # Check economy collection
    economy_count = await db.economy.count_documents({'guild_id': guild_id})
    print(f'Economy records for guild: {economy_count}')
    
    if economy_count > 0:
        wallets = await db.economy.find({'guild_id': guild_id}).to_list(length=10)
        for wallet in wallets:
            discord_id = wallet.get('discord_id', 'Unknown')
            balance = wallet.get('balance', 0)
            print(f'User {discord_id}: ${balance}')
    else:
        print('No economy records found for this guild')
        print('Users need to use /work command to create initial wallet')
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_economy_status())