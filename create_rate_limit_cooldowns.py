"""
Create Rate Limit Cooldown Files - Stop excessive Discord API calls
This creates cooldown files to prevent the bot from making too many API requests
"""
import time

def create_cooldowns():
    """Create cooldown files to prevent excessive Discord API calls"""
    current_time = time.time()
    
    # Create a 30-minute cooldown for command syncing
    command_sync_cooldown = current_time + (30 * 60)  # 30 minutes
    with open("command_sync_cooldown.txt", "w") as f:
        f.write(str(command_sync_cooldown))
    
    # Create a 30-minute cooldown for global syncing
    global_sync_cooldown = current_time + (30 * 60)  # 30 minutes
    with open("global_sync_cooldown.txt", "w") as f:
        f.write(str(global_sync_cooldown))
    
    print("✅ Created rate limit cooldown files")
    print("Bot will stop trying to sync commands for 30 minutes")
    print("Commands are already loaded and functional in bot memory")

if __name__ == "__main__":
    create_cooldowns()