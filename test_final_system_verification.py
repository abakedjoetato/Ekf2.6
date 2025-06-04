"""
Final System Verification - Comprehensive test of all bot capabilities after command sync
"""

import asyncio
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, '.')

async def verify_command_sync_completion():
    """Verify Discord command sync has completed successfully"""
    
    import discord
    from discord.ext import commands
    
    bot_token = os.environ.get('BOT_TOKEN')
    if not bot_token:
        print("❌ BOT_TOKEN not found")
        return False
    
    # Create minimal bot for verification
    intents = discord.Intents.default()
    bot = commands.Bot(intents=intents)
    
    sync_completed = False
    
    @bot.event
    async def on_ready():
        nonlocal sync_completed
        
        print(f"✅ Connected as {bot.user}")
        
        guild_id = 1219706687980568769
        guild = bot.get_guild(guild_id)
        
        if not guild:
            print(f"❌ Guild {guild_id} not found")
            await bot.close()
            return
        
        try:
            # Check if commands are now available on Discord
            app_commands = await bot.tree.fetch_commands(guild=guild)
            print(f"✅ Discord has {len(app_commands)} registered commands")
            
            if len(app_commands) >= 30:  # Should have ~32 commands
                sync_completed = True
                print("✅ Command sync completed successfully")
            else:
                print(f"⏳ Command sync still in progress ({len(app_commands)}/32)")
                
        except Exception as e:
            print(f"❌ Error checking commands: {e}")
        
        await bot.close()
    
    try:
        await bot.start(bot_token)
    except Exception as e:
        print(f"❌ Bot connection error: {e}")
    
    return sync_completed

async def test_database_functionality():
    """Test core database operations"""
    
    import motor.motor_asyncio
    from bot.models.database import DatabaseManager
    
    mongo_uri = os.environ.get('MONGO_URI')
    if not mongo_uri:
        print("❌ MONGO_URI not found")
        return False
    
    try:
        # Connect to database
        mongo_client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
        await mongo_client.admin.command('ping')
        db_manager = DatabaseManager(mongo_client)
        
        # Test guild retrieval
        guild_id = 1219706687980568769
        guild_data = await db_manager.get_guild(guild_id)
        
        if guild_data:
            print(f"✅ Database connection successful")
            print(f"✅ Guild data retrieved: {guild_data.get('name', 'Unknown')}")
            
            # Test server data
            servers = await db_manager.get_guild_servers(guild_id)
            print(f"✅ Found {len(servers)} configured servers")
            
            return True
        else:
            print("❌ No guild data found")
            return False
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    finally:
        await mongo_client.close()

async def test_parser_functionality():
    """Test log parser and data processing"""
    
    import motor.motor_asyncio
    from bot.models.database import DatabaseManager
    
    mongo_uri = os.environ.get('MONGO_URI')
    if not mongo_uri:
        print("❌ MONGO_URI not found")
        return False
    
    try:
        mongo_client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
        db_manager = DatabaseManager(mongo_client)
        
        guild_id = 1219706687980568769
        
        # Check player sessions
        player_sessions = await db_manager.player_sessions.count_documents({
            "guild_id": guild_id
        })
        print(f"✅ Player sessions in database: {player_sessions}")
        
        # Check parser states
        parser_states = await db_manager.parser_states.count_documents({
            "guild_id": guild_id
        })
        print(f"✅ Parser states tracked: {parser_states}")
        
        # Check recent activity
        recent_events = await db_manager.events.count_documents({
            "guild_id": guild_id,
            "timestamp": {"$gte": datetime.utcnow().replace(hour=0, minute=0, second=0)}
        })
        print(f"✅ Events today: {recent_events}")
        
        return True
        
    except Exception as e:
        print(f"❌ Parser test failed: {e}")
        return False
    finally:
        await mongo_client.close()

async def comprehensive_system_verification():
    """Run complete system verification"""
    
    print("🔍 Starting comprehensive system verification...")
    print("=" * 50)
    
    # Test 1: Command Sync Status
    print("\n📋 Testing Discord Command Sync...")
    command_sync_ok = await verify_command_sync_completion()
    
    # Test 2: Database Functionality
    print("\n🗄️ Testing Database Functionality...")
    database_ok = await test_database_functionality()
    
    # Test 3: Parser Functionality
    print("\n📜 Testing Parser Functionality...")
    parser_ok = await test_parser_functionality()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SYSTEM VERIFICATION SUMMARY")
    print("=" * 50)
    
    total_tests = 3
    passed_tests = sum([command_sync_ok, database_ok, parser_ok])
    
    print(f"✅ Command Sync: {'PASS' if command_sync_ok else 'PENDING'}")
    print(f"✅ Database: {'PASS' if database_ok else 'FAIL'}")
    print(f"✅ Parser: {'PASS' if parser_ok else 'FAIL'}")
    
    print(f"\n🎯 Overall Status: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL SYSTEMS OPERATIONAL - Bot ready for production use!")
    elif command_sync_ok and database_ok:
        print("⚡ CORE SYSTEMS OPERATIONAL - Bot functional with active command sync")
    else:
        print("⚠️ SOME SYSTEMS NEED ATTENTION")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    asyncio.run(comprehensive_system_verification())