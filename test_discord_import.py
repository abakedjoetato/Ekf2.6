#!/usr/bin/env python3
"""Test py-cord import"""

try:
    import discord
    print(f"✅ Discord imported successfully")
    
    from discord.ext import commands
    print("✅ Commands imported successfully")
    
    # Test creating a bot instance
    bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())
    print("✅ Bot instance created successfully")
    
    print("✅ py-cord 2.6.1 is working correctly")
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")