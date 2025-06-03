#!/usr/bin/env python3
"""
Test Online Command Working Now - Direct verification using bot's database connection
"""
import asyncio
import os
import sys
import discord
from discord.ext import commands
from datetime import datetime, timezone

# Add the bot directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import bot components
from bot.models.database import DatabaseManager

async def test_online_command_now():
    """Test online command using bot's exact database connection"""
    print("=== TESTING /ONLINE COMMAND WITH BOT'S DATABASE CONNECTION ===")
    
    # Initialize database manager exactly like the bot does
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    guild_id = 1219706687980568769
    
    # 1. Check current database state
    print("\n1. Current Database State:")
    total_sessions = await db_manager.player_sessions.count_documents({'guild_id': guild_id})
    online_sessions = await db_manager.player_sessions.count_documents({'guild_id': guild_id, 'state': 'online'})
    print(f"  Total sessions: {total_sessions}")
    print(f"  Online sessions: {online_sessions}")
    
    # 2. Test /online command queries directly
    print("\n2. /online Command Queries:")
    
    # All servers query (what /online with no args would do)
    all_servers_query = {'guild_id': guild_id, 'state': 'online'}
    all_servers_count = await db_manager.player_sessions.count_documents(all_servers_query)
    print(f"  /online (all servers): {all_servers_count} players")
    
    # Specific server query (what /online Emerald EU would do)
    emerald_query = {'guild_id': guild_id, 'server_name': 'Emerald EU', 'state': 'online'}
    emerald_count = await db_manager.player_sessions.count_documents(emerald_query)
    print(f"  /online Emerald EU: {emerald_count} players")
    
    # 3. Show actual player data if found
    if emerald_count > 0:
        print("\n3. Current Online Players:")
        async for session in db_manager.player_sessions.find(emerald_query).limit(10):
            player_name = session.get('player_name', session.get('character_name', 'Unknown'))
            player_id = session.get('player_id', '')
            joined_at = session.get('joined_at', 'Unknown')
            platform = session.get('platform', 'Unknown')
            
            print(f"    {player_name}")
            print(f"      ID: {player_id[:8]}...")
            print(f"      Joined: {joined_at}")
            print(f"      Platform: {platform}")
    
    # 4. Test the exact format the /online command would use
    print("\n4. /online Command Format Test:")
    
    if emerald_count > 0:
        print("  Sample /online Emerald EU response:")
        player_list = []
        async for session in db_manager.player_sessions.find(emerald_query).limit(5):
            player_name = session.get('player_name', session.get('character_name', 'Unknown'))
            joined_at = session.get('joined_at')
            platform = session.get('platform', 'Unknown')
            
            # Format join time like the actual command does
            join_time_display = "Unknown"
            if joined_at:
                if isinstance(joined_at, str):
                    try:
                        join_time = datetime.fromisoformat(joined_at.replace('Z', '+00:00'))
                        time_diff = datetime.now(timezone.utc) - join_time
                        hours = int(time_diff.total_seconds() // 3600)
                        minutes = int((time_diff.total_seconds() % 3600) // 60)
                        if hours > 0:
                            join_time_display = f"Online {hours}h {minutes}m"
                        else:
                            join_time_display = f"Online {minutes}m"
                    except:
                        join_time_display = "Recent"
            
            player_list.append(f"    {player_name} ({join_time_display})")
        
        for player in player_list:
            print(player)
    else:
        print("  No players online - /online command would show empty")
    
    # 5. Final verdict
    print(f"\n=== FINAL VERDICT ===")
    if emerald_count > 0:
        print(f"✅ SUCCESS: /online command should work correctly")
        print(f"   Shows {emerald_count} players on Emerald EU")
        print(f"   Shows {all_servers_count} total players across all servers")
        print(f"   Database queries are functional")
    else:
        print(f"❌ ISSUE: No online players found")
        print(f"   /online command will show empty results")
        print(f"   Cold start data may not have persisted")
    
    # Close database connection
    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(test_online_command_now())