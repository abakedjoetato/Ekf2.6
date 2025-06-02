"""
Test what commands are actually registered with Discord
"""
import asyncio
import os
import discord
from discord.ext import commands

async def check_discord_commands():
    """Check what commands Discord actually has registered"""
    
    # Create a simple bot to check commands
    bot = discord.Bot(intents=discord.Intents.default())
    
    @bot.event
    async def on_ready():
        print(f"Bot connected as {bot.user}")
        
        # Get global commands
        try:
            global_commands = await bot.http.get_global_commands(bot.user.id)
            print(f"\n=== GLOBAL COMMANDS ({len(global_commands)}) ===")
            for cmd in global_commands:
                print(f"- {cmd['name']}: {cmd.get('description', 'No description')}")
        except Exception as e:
            print(f"Error getting global commands: {e}")
        
        # Get guild commands
        for guild in bot.guilds:
            try:
                guild_commands = await bot.http.get_guild_commands(bot.user.id, guild.id)
                print(f"\n=== GUILD COMMANDS for {guild.name} ({len(guild_commands)}) ===")
                for cmd in guild_commands:
                    print(f"- {cmd['name']}: {cmd.get('description', 'No description')}")
            except Exception as e:
                print(f"Error getting guild commands for {guild.name}: {e}")
        
        await bot.close()
    
    # Run the bot
    token = os.getenv('BOT_TOKEN')
    if token:
        await bot.start(token)
    else:
        print("BOT_TOKEN not found")

if __name__ == "__main__":
    asyncio.run(check_discord_commands())