#!/usr/bin/env python3
"""
Create Test Wallet for Casino Integration Testing
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def create_test_wallet():
    client = AsyncIOMotorClient(os.getenv('MONGO_URI'))
    db = client.EmeraldDB
    
    guild_id = 1219706687980568769
    user_id = 123456789  # Test user ID
    
    # Create initial wallet with funds for testing
    initial_balance = 5000
    
    wallet_data = {
        'guild_id': guild_id,
        'discord_id': user_id,
        'balance': initial_balance,
        'last_work': None,
        'created_at': '2025-06-01T20:50:00Z',
        'updated_at': '2025-06-01T20:50:00Z'
    }
    
    result = await db.user_wallets.update_one(
        {'guild_id': guild_id, 'discord_id': user_id},
        {'$set': wallet_data},
        upsert=True
    )
    
    print(f'Test wallet created for user {user_id}: ${initial_balance}')
    
    # Verify creation
    wallet_check = await db.user_wallets.find_one({'guild_id': guild_id, 'discord_id': user_id})
    if wallet_check:
        print(f'Verified - wallet balance: ${wallet_check["balance"]}')
    else:
        print('Error - wallet not found after creation')
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_test_wallet())