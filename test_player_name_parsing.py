#!/usr/bin/env python3
"""
Test player name parsing with spaces
"""

import re
import sys
sys.path.append('.')

def test_player_name_regex():
    """Test the fixed player name regex pattern"""
    
    # The fixed regex pattern
    pattern = re.compile(
        r'LogNet: Join request: /Game/Maps/world_\d+/World_\d+\?.*?eosid=\|([a-f0-9]+).*?Name=([^&\?]+?)(?:&|\?|$).*?(?:platformid=([^&\?\s]+))?',
        re.IGNORECASE
    )
    
    # Test cases
    test_logs = [
        'LogNet: Join request: /Game/Maps/world_1/World_1?eosid=|abc123def456?Name=A Baked Joetato&platformid=PC:123456789',
        'LogNet: Join request: /Game/Maps/world_1/World_1?eosid=|def789ghi012?Name=TestPlayer&platformid=PS5:987654321',
        'LogNet: Join request: /Game/Maps/world_2/World_2?eosid=|abcdef123456?Name=Player With Spaces&platformid=Xbox:555666777',
        'LogNet: Join request: /Game/Maps/world_1/World_1?eosid=|fff111222333?Name=SingleName&platformid=PC:111222333',
        'LogNet: Join request: /Game/Maps/world_3/World_3?eosid=|aaa999bbb888?Name=Very Long Player Name Here?platformid=Steam:444555666'
    ]
    
    print("Testing Player Name Parsing")
    print("=" * 40)
    
    for i, log_line in enumerate(test_logs, 1):
        match = pattern.search(log_line)
        if match:
            groups = match.groups()
            player_id = groups[0]
            player_name = groups[1] if len(groups) > 1 else "Unknown"
            platform = groups[2] if len(groups) > 2 and groups[2] else "Unknown"
            
            print(f"Test {i}:")
            print(f"  Player ID: {player_id}")
            print(f"  Player Name: '{player_name}'")
            print(f"  Platform: {platform}")
            print()
        else:
            print(f"Test {i}: NO MATCH")
            print()

if __name__ == "__main__":
    test_player_name_regex()