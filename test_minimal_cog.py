#!/usr/bin/env python3
"""
Create a minimal cog to test basic functionality
"""

import discord
from discord.ext import commands

class TestCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @discord.slash_command(name="test", description="Simple test command")
    async def test_command(self, ctx):
        await ctx.respond("Test command working!")

def setup(bot):
    bot.add_cog(TestCog(bot))