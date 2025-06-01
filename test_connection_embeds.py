#!/usr/bin/env python3
"""
Test script for new connection and disconnection embeds
"""

import asyncio
import sys
sys.path.append('.')

from bot.utils.embed_factory import EmbedFactory

async def test_embeds():
    """Test both connection and disconnection embeds"""
    
    print("🔍 Testing Connection and Disconnection Embeds")
    print("=" * 50)
    
    # Test connection embed
    print("\n📋 Testing Connection Embed:")
    try:
        embed_data = {
            'player_name': 'NoKnees2911',
            'platform': 'PC',
            'server_name': 'Emerald EU'
        }
        embed, file = await EmbedFactory.build('connection', embed_data)
        print(f"✅ Connection embed created successfully")
        print(f"   Title: {embed.title}")
        print(f"   Description: {embed.description}")
        print(f"   Color: #{embed.color:06x}")
        print(f"   Fields: {len(embed.fields)}")
        for i, field in enumerate(embed.fields):
            print(f"     Field {i+1}: {field.name} = {field.value}")
        print(f"   Thumbnail: {file.filename}")
    except Exception as e:
        print(f"❌ Connection embed failed: {e}")
    
    # Test disconnection embed  
    print("\n📋 Testing Disconnection Embed:")
    try:
        embed_data = {
            'player_name': 'NoKnees2911',
            'platform': 'PC',
            'server_name': 'Emerald EU'
        }
        embed, file = await EmbedFactory.build('disconnection', embed_data)
        print(f"✅ Disconnection embed created successfully")
        print(f"   Title: {embed.title}")
        print(f"   Description: {embed.description}")
        print(f"   Color: #{embed.color:06x}")
        print(f"   Fields: {len(embed.fields)}")
        for i, field in enumerate(embed.fields):
            print(f"     Field {i+1}: {field.name} = {field.value}")
        print(f"   Thumbnail: {file.filename}")
    except Exception as e:
        print(f"❌ Disconnection embed failed: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Embed testing completed!")

if __name__ == "__main__":
    asyncio.run(test_embeds())