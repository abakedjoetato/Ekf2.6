"""
Test /online Command Fix - Verify the streamlined implementation
"""
import asyncio
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

async def test_online_command_fix():
    """Test the fixed /online command implementation"""
    try:
        # Import the database manager
        from bot.models.database import DatabaseManager
        
        db_manager = DatabaseManager()
        await db_manager.initialize()
        
        # Test the exact query used in the fixed /online command
        guild_id = 1219706687980568769  # Emerald Servers guild ID
        
        print("Testing fixed /online command database query...")
        
        # Simulate the exact query from the fixed command
        sessions = await db_manager.player_sessions.find(
            {'guild_id': guild_id, 'state': 'online'},
            {'character_name': 1, 'player_name': 1, 'server_name': 1, 'server_id': 1, '_id': 0}
        ).limit(50).to_list(length=50)
        
        print(f"✅ Query completed successfully - found {len(sessions)} online sessions")
        
        # Test embed creation logic
        if not sessions:
            print("✅ Empty state handling: No players online")
        else:
            # Group by server (simplified version)
            servers = {}
            for session in sessions:
                server_name = session.get('server_name', 'Unknown')
                player_name = session.get('character_name') or session.get('player_name', 'Unknown')
                if server_name not in servers:
                    servers[server_name] = []
                servers[server_name].append(player_name)
            
            print(f"✅ Grouping logic: {len(servers)} servers with players")
            for server_name, players in servers.items():
                print(f"   - {server_name}: {len(players)} players")
        
        await db_manager.close()
        print("✅ /online command fix test completed successfully")
        
    except Exception as e:
        print(f"❌ Error testing /online command fix: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_online_command_fix())
