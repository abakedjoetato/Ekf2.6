#!/usr/bin/env python3
"""
Manual Command Registration - Direct Discord API registration to bypass rate limits
"""
import asyncio
import aiohttp
import os
import json

async def register_commands_directly():
    """Register commands directly via Discord API to bypass py-cord rate limits"""
    
    bot_token = os.environ.get('BOT_TOKEN')
    if not bot_token:
        print("Error: BOT_TOKEN not found")
        return False
    
    # Bot application ID (extract from token or use known ID)
    application_id = "1360004212955545623"  # Emerald's Killfeed bot ID
    guild_id = "1219706687980568769"  # Emerald Servers guild ID
    
    # Define the /online command directly
    online_command = {
        "name": "online",
        "description": "Show currently online players",
        "type": 1,  # CHAT_INPUT
        "options": [
            {
                "name": "server_name",
                "description": "Server to check (leave empty for default)",
                "type": 3,  # STRING
                "required": False
            }
        ]
    }
    
    # Essential commands to register
    commands = [
        online_command,
        {
            "name": "ping",
            "description": "Check bot latency",
            "type": 1
        },
        {
            "name": "help",
            "description": "Show help information",
            "type": 1
        },
        {
            "name": "status",
            "description": "Show bot status",
            "type": 1
        }
    ]
    
    headers = {
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json"
    }
    
    print(f"Registering {len(commands)} commands directly via Discord API...")
    
    async with aiohttp.ClientSession() as session:
        try:
            # Register commands for the specific guild (guild commands have higher rate limits)
            url = f"https://discord.com/api/v10/applications/{application_id}/guilds/{guild_id}/commands"
            
            for command in commands:
                async with session.post(url, headers=headers, json=command) as resp:
                    if resp.status == 200 or resp.status == 201:
                        print(f"✅ Registered /{command['name']} command")
                    elif resp.status == 429:
                        print(f"⚠️ Rate limited - waiting...")
                        retry_after = int(resp.headers.get('Retry-After', 5))
                        await asyncio.sleep(retry_after)
                        # Retry
                        async with session.post(url, headers=headers, json=command) as retry_resp:
                            if retry_resp.status in [200, 201]:
                                print(f"✅ Registered /{command['name']} command (retry)")
                            else:
                                print(f"❌ Failed to register /{command['name']}: {retry_resp.status}")
                    else:
                        response_text = await resp.text()
                        print(f"❌ Failed to register /{command['name']}: {resp.status} - {response_text}")
                
                # Small delay between registrations
                await asyncio.sleep(0.5)
            
            print("Direct command registration completed")
            return True
            
        except Exception as e:
            print(f"Error during direct registration: {e}")
            return False

if __name__ == "__main__":
    asyncio.run(register_commands_directly())