"""
Create Rate Limit Cooldown Files - Stop excessive Discord API calls
This creates cooldown files to prevent the bot from making too many API requests
"""
import time
import os

def create_cooldowns():
    """Create cooldown files to prevent excessive Discord API calls"""
    current_time = time.time()
    
    # Create 1-hour cooldowns for different API endpoints
    cooldown_files = {
        'command_sync_cooldown.txt': current_time + 3600,  # 1 hour
        'global_sync_cooldown.txt': current_time + 3600,   # 1 hour
        'channel_message_cooldown.txt': current_time + 1800,  # 30 minutes
        'voice_channel_cooldown.txt': current_time + 3600     # 1 hour
    }
    
    for filename, until_time in cooldown_files.items():
        with open(filename, 'w') as f:
            f.write(str(until_time))
        print(f"Created {filename} with cooldown until {time.ctime(until_time)}")
    
    print("✅ All rate limit cooldowns created - bot will reduce API calls")

if __name__ == "__main__":
    create_cooldowns()