"""
Comprehensive System Fix - Complete error resolution for production readiness
Fixes all syntax errors, LSP issues, and threading problems systematically
"""

import os
import re

def fix_core_cog_syntax():
    """Fix critical syntax errors in core.py"""
    
    content = '''"""
Emerald's Killfeed - Core System Commands (REFACTORED)
Essential bot information and system status commands
Uses py-cord 2.6.1 syntax with proper error handling
"""

import discord
from discord.ext import commands
import logging
from datetime import datetime, timezone
import platform
import psutil
import asyncio

logger = logging.getLogger(__name__)

class Core(discord.Cog):
    """Core system commands for bot information and status"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("Core cog initialized")

    async def check_premium_access(self, guild_id: int) -> bool:
        """Check if guild has premium access - unified validation"""
        try:
            premium_data = await self.bot.db_manager.premium_guilds.find_one({"guild_id": guild_id})
            return premium_data is not None and premium_data.get("active", False)
        except Exception as e:
            logger.error(f"Error checking premium access: {e}")
            return False

    @discord.slash_command(name="info", description="Show bot information")
    async def info(self, ctx: discord.ApplicationContext):
        """Display bot information and statistics"""
        # Immediate defer to prevent Discord timeout
        try:
            await ctx.defer()
        except discord.errors.NotFound:
            return
        except Exception as e:
            logger.error(f"Failed to defer interaction: {e}")
            return
            
        try:
            # Create bot info embed manually for reliability
            embed = discord.Embed(
                title="🤖 Emerald's Killfeed Bot",
                description="Advanced Discord bot for Deadside server monitoring",
                color=0x00d38a,
                timestamp=datetime.now(timezone.utc)
            )

            # Add bot information fields
            embed.add_field(
                name="📊 Statistics",
                value=f"Servers: {len(self.bot.guilds)}\\nLatency: {round(self.bot.latency * 1000)}ms",
                inline=True
            )

            embed.add_field(
                name="💾 System",
                value=f"Python: {platform.python_version()}\\nPy-cord: {discord.__version__}",
                inline=True
            )

            embed.add_field(
                name="🔗 Links",
                value="[Discord Server](https://discord.gg/EmeraldServers)\\n[Support](https://discord.gg/EmeraldServers)",
                inline=False
            )

            # Set thumbnail using main logo
            try:
                main_file = discord.File("./assets/main.png", filename="main.png")
                embed.set_thumbnail(url="attachment://main.png")
                embed.set_footer(text="Powered by Discord.gg/EmeraldServers")
                
                await ctx.followup.send(embed=embed, file=main_file)
            except FileNotFoundError:
                embed.set_footer(text="Powered by Discord.gg/EmeraldServers")
                await ctx.followup.send(embed=embed)
            except discord.errors.NotFound:
                pass  # Interaction expired
            except Exception as e:
                logger.error(f"Failed to show bot info: {e}")
                try:
                    await ctx.followup.send("Failed to retrieve bot information.", ephemeral=True)
                except discord.errors.NotFound:
                    pass  # Interaction expired
                    
        except Exception as e:
            logger.error(f"Error in info command: {e}")
            try:
                await ctx.followup.send("An error occurred while retrieving bot information.", ephemeral=True)
            except:
                pass

    @discord.slash_command(name="ping", description="Check bot latency")
    async def ping(self, ctx: discord.ApplicationContext):
        """Check bot response time and latency"""
        # Immediate defer to prevent Discord timeout
        try:
            await ctx.defer()
        except discord.errors.NotFound:
            return
        except Exception as e:
            logger.error(f"Failed to defer interaction: {e}")
            return
            
        try:
            latency = round(self.bot.latency * 1000)
            
            embed = discord.Embed(
                title="🏓 Pong!",
                description=f"Bot latency: **{latency}ms**",
                color=0x00FF00 if latency < 100 else 0xFFAA00 if latency < 200 else 0xFF0000
            )
            
            await ctx.followup.send(embed=embed)
            
        except discord.errors.NotFound:
            pass  # Interaction expired
        except Exception as e:
            logger.error(f"Error in ping command: {e}")
            try:
                await ctx.followup.send("Failed to check latency.", ephemeral=True)
            except:
                pass

    @discord.slash_command(name="status", description="Show bot system status")
    async def status(self, ctx: discord.ApplicationContext):
        """Display detailed bot system status"""
        # Immediate defer to prevent Discord timeout
        try:
            await ctx.defer()
        except discord.errors.NotFound:
            return
        except Exception as e:
            logger.error(f"Failed to defer interaction: {e}")
            return
            
        try:
            # Get system information
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            embed = discord.Embed(
                title="📊 Bot System Status",
                color=0x00d38a,
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(
                name="🖥️ CPU Usage",
                value=f"{cpu_percent:.1f}%",
                inline=True
            )
            
            embed.add_field(
                name="💾 Memory Usage",
                value=f"{memory.percent:.1f}%\\n({memory.used // 1024 // 1024}MB / {memory.total // 1024 // 1024}MB)",
                inline=True
            )
            
            embed.add_field(
                name="💿 Disk Usage",
                value=f"{disk.percent:.1f}%\\n({disk.used // 1024 // 1024 // 1024}GB / {disk.total // 1024 // 1024 // 1024}GB)",
                inline=True
            )
            
            embed.add_field(
                name="🌐 Network",
                value=f"Latency: {round(self.bot.latency * 1000)}ms\\nGuilds: {len(self.bot.guilds)}",
                inline=True
            )
            
            await ctx.followup.send(embed=embed)
            
        except discord.errors.NotFound:
            pass  # Interaction expired
        except Exception as e:
            logger.error(f"Error in status command: {e}")
            try:
                await ctx.followup.send("Failed to retrieve system status.", ephemeral=True)
            except:
                pass

def setup(bot):
    """Load the Core cog"""
    bot.add_cog(Core(bot))
    logger.info("Core cog loaded")
'''
    
    with open('bot/cogs/core.py', 'w') as f:
        f.write(content)
    print("✅ Fixed core.py syntax errors")

def fix_thread_safe_wrapper():
    """Add missing methods to thread-safe database wrapper"""
    
    wrapper_path = 'bot/utils/threaded_parser_wrapper.py'
    if not os.path.exists(wrapper_path):
        return
        
    with open(wrapper_path, 'r') as f:
        content = f.read()
    
    # Add missing close method
    if 'def close(' not in content:
        close_method = '''
    def close(self):
        """Close database connections safely"""
        try:
            if hasattr(self.db_manager, 'close'):
                self.db_manager.close()
        except Exception as e:
            logger.error(f"Error closing database: {e}")
'''
        content = content.replace('class ThreadSafeDatabaseWrapper:', 
                                f'class ThreadSafeDatabaseWrapper:{close_method}')
        
        with open(wrapper_path, 'w') as f:
            f.write(content)
        print("✅ Fixed thread-safe wrapper missing methods")

def fix_historical_parser_errors():
    """Fix critical errors in historical parser"""
    
    parser_path = 'bot/parsers/historical_parser.py'
    if not os.path.exists(parser_path):
        return
        
    with open(parser_path, 'r') as f:
        content = f.read()
    
    # Fix split method parameter
    content = re.sub(r'\.split\(sep="/"\)', '.split("/")', content)
    
    # Fix None context manager issues
    content = re.sub(r'with sftp_client:', 'if sftp_client:\n            with sftp_client:', content)
    
    # Fix disabled attribute assignment
    content = re.sub(r'server_doc\["disabled"\] = True', 'await self.db_manager.servers.update_one({"_id": server_doc["_id"]}, {"$set": {"disabled": True}})', content)
    
    with open(parser_path, 'w') as f:
        f.write(content)
    print("✅ Fixed historical parser errors")

def fix_unified_processor_none_checks():
    """Fix None context manager issues in unified processor"""
    
    processor_path = 'bot/utils/scalable_unified_processor.py'
    if not os.path.exists(processor_path):
        return
        
    with open(processor_path, 'r') as f:
        content = f.read()
    
    # Add None checks before context managers
    content = re.sub(
        r'with (sftp_client|client):',
        r'if \1 is not None:\n            with \1:',
        content
    )
    
    # Fix asyncio await issues
    content = re.sub(
        r'await ([^(]+\([^)]+\))(?!\s*\()',
        r'result = \1\nif asyncio.iscoroutine(result):\n    await result',
        content
    )
    
    with open(processor_path, 'w') as f:
        f.write(content)
    print("✅ Fixed unified processor None checks")

def fix_main_py_database_close():
    """Fix database close method issues in main.py"""
    
    with open('main.py', 'r') as f:
        content = f.read()
    
    # Replace problematic database close calls
    content = re.sub(
        r'await self\.db_manager\.close\(\)',
        '''try:
            if hasattr(self.db_manager, 'close'):
                await self.db_manager.close()
        except Exception as e:
            logger.error(f"Error closing database: {e}")''',
        content
    )
    
    # Fix bot.database references
    content = re.sub(r'self\.database\.', 'self.db_manager.', content)
    
    with open('main.py', 'w') as f:
        f.write(content)
    print("✅ Fixed main.py database close issues")

def validate_syntax_across_codebase():
    """Validate syntax of all Python files"""
    
    python_files = [
        'main.py',
        'bot/cogs/core.py',
        'bot/cogs/stats.py',
        'bot/cogs/linking.py',
        'bot/cogs/admin_channels.py',
        'bot/cogs/premium.py'
    ]
    
    syntax_errors = []
    
    for file_path in python_files:
        if not os.path.exists(file_path):
            continue
            
        try:
            with open(file_path, 'r') as f:
                source = f.read()
            compile(source, file_path, 'exec')
            print(f"✅ {file_path} syntax valid")
        except SyntaxError as e:
            syntax_errors.append(f"{file_path}: {e}")
            print(f"❌ {file_path} has syntax error: {e}")
    
    return syntax_errors

def main():
    """Execute comprehensive system fixes"""
    print("🔧 Starting comprehensive system fix...")
    
    fix_core_cog_syntax()
    fix_thread_safe_wrapper()
    fix_historical_parser_errors() 
    fix_unified_processor_none_checks()
    fix_main_py_database_close()
    
    print("\n🔍 Validating syntax across codebase...")
    syntax_errors = validate_syntax_across_codebase()
    
    if syntax_errors:
        print(f"\n❌ Found {len(syntax_errors)} syntax errors:")
        for error in syntax_errors:
            print(f"  - {error}")
    else:
        print("\n✅ All critical files have valid syntax")
    
    print("\n🎯 Comprehensive system fix completed")

if __name__ == "__main__":
    main()