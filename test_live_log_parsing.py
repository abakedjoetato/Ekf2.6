#!/usr/bin/env python3
"""
Test Live Log Parsing
Check what player connection patterns are actually in the current server logs
"""

import asyncio
import asyncssh
import re
from datetime import datetime

async def test_live_log_parsing():
    """Test what's actually in the current server logs"""
    
    try:
        # Connect to the same server as the parser
        host = "79.127.236.1"
        port = 8822
        username = "baked"
        
        print(f"🔍 Connecting to {host}:{port} to analyze current logs...")
        
        async with asyncssh.connect(host, port=port, username=username, known_hosts=None) as conn:
            # Read the current log file
            async with conn.start_sftp_client() as sftp:
                log_path = "/home/baked/.steam/steamapps/common/Deadside Dedicated Server/Engine/Binaries/Linux/Logs/Deadside.log"
                
                try:
                    log_data = await sftp.get(log_path)
                    log_content = log_data.decode('utf-8', errors='ignore')
                    
                    # Get the last 100 lines to see recent activity
                    lines = log_content.split('\n')
                    recent_lines = lines[-100:]
                    
                    print(f"📊 Analyzing last 100 log lines...")
                    
                    # Look for connection patterns
                    connection_patterns = [
                        r'LogNet.*Login.*',
                        r'LogNet.*Join.*',
                        r'LogNet.*Connect.*',
                        r'LogOnline.*Login.*',
                        r'LogOnline.*Join.*',
                        r'LogWorld.*Possess.*',
                        r'LogTemp.*Login.*',
                        r'LogTemp.*Join.*',
                        r'LogGameMode.*Login.*',
                        r'LogGameMode.*Join.*'
                    ]
                    
                    # Look for disconnection patterns
                    disconnection_patterns = [
                        r'LogNet.*Logout.*',
                        r'LogNet.*Disconnect.*',
                        r'LogNet.*Close.*',
                        r'LogOnline.*Logout.*',
                        r'LogOnline.*Disconnect.*',
                        r'LogWorld.*UnPossess.*',
                        r'LogTemp.*Logout.*',
                        r'LogTemp.*Disconnect.*',
                        r'LogGameMode.*Logout.*',
                        r'LogGameMode.*Disconnect.*'
                    ]
                    
                    print(f"\n🔍 Searching for player connection events:")
                    connection_found = False
                    for i, line in enumerate(recent_lines):
                        for pattern in connection_patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                print(f"  ✅ CONNECTION: {line.strip()}")
                                connection_found = True
                    
                    if not connection_found:
                        print("  ❌ No connection events found in recent logs")
                    
                    print(f"\n🔍 Searching for player disconnection events:")
                    disconnection_found = False
                    for i, line in enumerate(recent_lines):
                        for pattern in disconnection_patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                print(f"  ✅ DISCONNECTION: {line.strip()}")
                                disconnection_found = True
                    
                    if not disconnection_found:
                        print("  ❌ No disconnection events found in recent logs")
                    
                    # Look for any lines with player names or IDs
                    print(f"\n🔍 Looking for any player-related activity:")
                    player_activity = False
                    for line in recent_lines:
                        if any(keyword in line.lower() for keyword in ['player', 'user', 'character', 'pawn']):
                            if not any(skip in line.lower() for skip in ['spawn', 'destroy', 'create', 'delete']):
                                print(f"  🎮 PLAYER ACTIVITY: {line.strip()}")
                                player_activity = True
                    
                    if not player_activity:
                        print("  ❌ No obvious player activity found")
                    
                    # Show most recent 10 lines for manual inspection
                    print(f"\n📄 Most recent 10 log lines:")
                    for line in recent_lines[-10:]:
                        if line.strip():
                            print(f"  {line.strip()}")
                    
                except Exception as e:
                    print(f"❌ Error reading log file: {e}")
        
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(test_live_log_parsing())