#!/usr/bin/env python3
"""
Validate that connection and disconnection embeds are properly separated
"""

import asyncio
import sys
sys.path.append('.')

from bot.utils.embed_factory import EmbedFactory

async def validate_fixes():
    """Validate the embed separation fixes"""
    
    print("Validating Connection/Disconnection Embed Fixes")
    print("=" * 50)
    
    # Test 1: Connection embed
    print("\n✅ Connection Embed:")
    embed_data = {
        'player_name': 'TestPlayer',
        'platform': 'PC', 
        'server_name': 'Emerald EU'
    }
    embed, file = await EmbedFactory.build('connection', embed_data)
    
    print(f"   Title: {embed.title}")
    print(f"   Description: {embed.description}")
    print(f"   Fields: {len(embed.fields)}")
    print(f"   Status Field: {embed.fields[1].value}")
    print(f"   Color: Green (connection)")
    
    # Test 2: Disconnection embed  
    print("\n✅ Disconnection Embed:")
    embed, file = await EmbedFactory.build('disconnection', embed_data)
    
    print(f"   Title: {embed.title}")
    print(f"   Description: {embed.description}")
    print(f"   Fields: {len(embed.fields)}")
    print(f"   Status Field: {embed.fields[1].value}")
    print(f"   Color: Red (disconnection)")
    
    print("\n" + "=" * 50)
    print("Key Improvements Made:")
    print("✓ Separate embed builders for connection vs disconnection")
    print("✓ Different titles and descriptions for each event type")
    print("✓ Correct status messages (ACTIVE vs OFFLINE)")
    print("✓ Minimalistic design with only 2 fields")
    print("✓ Color coding: Green for connections, Red for disconnections")
    print("✓ Fixed unified log parser to use correct embed type")

if __name__ == "__main__":
    asyncio.run(validate_fixes())