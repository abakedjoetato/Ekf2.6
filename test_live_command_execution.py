"""
Test Live Command Execution - Simulate actual Discord command execution
to identify remaining blocking issues in the command chain
"""

import asyncio
import os
import sys
import traceback
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

# Add project root to path
sys.path.insert(0, '.')

async def test_live_command_execution():
    """Test actual command execution as Discord would invoke it"""
    print("🔍 TESTING LIVE COMMAND EXECUTION")
    print("=" * 50)
    
    try:
        # Import necessary modules
        from main import EmeraldKillfeedBot
        from bot.models.database import DatabaseManager
        import motor.motor_asyncio
        import discord
        
        print("✓ Modules imported successfully")
        
        # Set up database connection
        mongo_uri = os.environ.get('MONGO_URI')
        mongo_client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
        await mongo_client.admin.command('ping')
        
        # Create bot instance with direct database manager
        bot = EmeraldKillfeedBot()
        bot.mongo_client = mongo_client
        bot.db_manager = DatabaseManager(mongo_client)
        
        # Load cogs
        await bot.load_cogs()
        print(f"✓ Bot created with {len(bot.cogs)} cogs loaded")
        
        # Create mock Discord context that simulates real interaction
        class MockApplicationContext:
            def __init__(self):
                self.guild = MagicMock()
                self.guild.id = 1219706687980568769
                self.guild.name = "Emerald Servers"
                self.user = MagicMock()
                self.user.id = 123456789
                self.user.display_name = "TestUser"
                self.author = self.user
                self.deferred = False
                self.responded = False
                self.followup_sent = False
                
            async def defer(self, ephemeral=False):
                """Mock defer method"""
                print(f"    → ctx.defer() called (ephemeral={ephemeral})")
                await asyncio.sleep(0.01)  # Simulate network delay
                self.deferred = True
                
            async def respond(self, content=None, embed=None, ephemeral=False, file=None):
                """Mock respond method"""
                print(f"    → ctx.respond() called: {content or 'embed'}")
                await asyncio.sleep(0.01)  # Simulate network delay
                self.responded = True
                
            @property
            def followup(self):
                """Mock followup property"""
                return MockFollowup()
        
        class MockFollowup:
            async def send(self, content=None, embed=None, ephemeral=False, file=None):
                """Mock followup send method"""
                print(f"    → ctx.followup.send() called: {content or 'embed'}")
                await asyncio.sleep(0.01)  # Simulate network delay
                return True
        
        # Test critical commands that were failing
        test_commands = [
            ("online", "Stats", "online"),
            ("stats", "Stats", "stats"),  
            ("link", "Linking", "link"),
            ("setchannel", "AdminChannels", "set_channel"),
        ]
        
        print("\n🚀 SIMULATING DISCORD COMMAND EXECUTION")
        print("-" * 40)
        
        all_passed = True
        
        for command_name, cog_name, method_name in test_commands:
            print(f"\n🎯 Testing /{command_name} command:")
            
            # Get the cog and command method
            cog = bot.get_cog(cog_name)
            if not cog:
                print(f"❌ Cog {cog_name} not found")
                all_passed = False
                continue
            
            # Get the command method
            command_method = getattr(cog, method_name, None)
            if not command_method:
                print(f"❌ Method {method_name} not found in {cog_name}")
                all_passed = False
                continue
            
            # Create mock context
            ctx = MockApplicationContext()
            
            # Execute command with timeout
            start_time = datetime.now()
            try:
                # Special handling for different command signatures
                if command_name == "link":
                    await asyncio.wait_for(command_method(ctx, "TestCharacter"), timeout=5.0)
                elif command_name == "setchannel":
                    # Create mock channel
                    mock_channel = MagicMock()
                    mock_channel.id = 1361522248451756234
                    mock_channel.mention = "#test-channel"
                    mock_channel.type = discord.ChannelType.text
                    await asyncio.wait_for(command_method(ctx, "killfeed", mock_channel), timeout=5.0)
                else:
                    await asyncio.wait_for(command_method(ctx), timeout=5.0)
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                # Check if command completed properly
                if ctx.deferred or ctx.responded or ctx.followup_sent:
                    print(f"✓ Command completed in {execution_time:.3f}s")
                    if execution_time > 2.5:
                        print(f"  ⚠️ WARNING: Close to Discord timeout limit")
                else:
                    print(f"❌ Command executed but no response sent")
                    all_passed = False
                    
            except asyncio.TimeoutError:
                execution_time = (datetime.now() - start_time).total_seconds()
                print(f"❌ Command TIMEOUT after {execution_time:.3f}s")
                all_passed = False
                
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                print(f"❌ Command FAILED in {execution_time:.3f}s: {e}")
                print(f"    Error type: {type(e).__name__}")
                traceback.print_exc()
                all_passed = False
        
        # Test database operations during command execution
        print("\n📊 TESTING DATABASE OPERATIONS DURING EXECUTION")
        print("-" * 40)
        
        guild_id = 1219706687980568769
        concurrent_operations = [
            ("Session count", lambda: bot.db_manager.player_sessions.count_documents({'guild_id': guild_id})),
            ("Online players", lambda: bot.db_manager.player_sessions.find({'guild_id': guild_id, 'state': 'online'}).limit(5).to_list(length=5)),
            ("Guild data", lambda: bot.db_manager.get_guild(guild_id)),
        ]
        
        start_time = datetime.now()
        try:
            tasks = [op_func() for _, op_func in concurrent_operations]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = (datetime.now() - start_time).total_seconds()
            
            successful = sum(1 for r in results if not isinstance(r, Exception))
            print(f"✓ Database operations: {successful}/{len(tasks)} successful in {total_time:.3f}s")
            
            for i, (op_name, _) in enumerate(concurrent_operations):
                if isinstance(results[i], Exception):
                    print(f"  ❌ {op_name}: {results[i]}")
                    all_passed = False
                else:
                    print(f"  ✓ {op_name}: Success")
                    
        except Exception as e:
            print(f"❌ Database operation test failed: {e}")
            all_passed = False
        
        # Summary
        print("\n🎯 LIVE EXECUTION SUMMARY")
        print("=" * 50)
        
        if all_passed:
            print("✅ ALL COMMAND TESTS PASSED")
            print("   Commands execute properly within Discord timeout limits")
            print("   Database operations complete successfully")
            print("   Bot should respond to Discord slash commands")
        else:
            print("❌ SOME TESTS FAILED")
            print("   Commands may still have execution issues")
            print("   Additional debugging needed")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR in live test: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_live_command_execution())
    if result:
        print("\n✅ Commands should work in Discord")
    else:
        print("\n❌ Commands need additional fixes")