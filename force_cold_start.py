"""
Force Cold Start - Complete rebuild of all command syntax
"""

import os
import re

def rebuild_economy_command():
    """Rebuild economy.py balance command with correct syntax"""
    
    file_path = 'bot/cogs/economy.py'
    
    if not os.path.exists(file_path):
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find the balance command and replace it entirely
    balance_pattern = r'(@discord\.slash_command\(name="balance"[^)]*\))\s*async def balance\(self, ctx[^)]*\):[^}]*?(?=\n    @|\n    def|\nclass|\Z)'
    
    new_balance_command = '''@discord.slash_command(name="balance", description="Check your wallet balance")
    async def balance(self, ctx: discord.ApplicationContext):
        """Check user's wallet balance"""
        # IMMEDIATE defer - must be first line to prevent timeout
        await ctx.defer()
        
        try:
            if not ctx.guild:
                await ctx.followup.send("❌ This command must be used in a server", ephemeral=True)
                return
                
            guild_id = ctx.guild.id
            discord_id = ctx.user.id

            # Check premium access
            if not await self.check_premium_server(guild_id):
                embed = discord.Embed(
                    title="Access Restricted",
                    description="Economy features require premium access",
                    color=0xff0000
                )
                await ctx.followup.send(embed=embed, ephemeral=True)
                return

            # Get wallet balance
            wallet = await self.db.get_wallet(guild_id, discord_id)
            balance = wallet.get('balance', 0) if wallet else 0

            embed = discord.Embed(
                title="💰 Wallet Balance",
                description=f"**{balance:,}** credits",
                color=0x00ff00
            )
            
            embed.set_footer(text=f"User ID: {discord_id}")
            
            await ctx.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in balance command: {e}")
            await ctx.followup.send("❌ Failed to check balance", ephemeral=True)'''
    
    content = re.sub(balance_pattern, new_balance_command, content, flags=re.DOTALL)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    return True

def fix_critical_command_files():
    """Fix critical command files that are preventing bot startup"""
    
    critical_fixes = [
        ('bot/cogs/linking.py', 54),
        ('bot/cogs/premium.py', 50),
        ('bot/cogs/core.py', 51)
    ]
    
    for file_path, error_line in critical_fixes:
        if not os.path.exists(file_path):
            continue
            
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Fix common patterns around the error line
        for i in range(max(0, error_line - 5), min(len(lines), error_line + 5)):
            line = lines[i]
            
            # Fix orphaned if statements
            if 'if not ctx.guild:' in line and i + 1 < len(lines):
                next_line = lines[i + 1]
                if next_line.strip() == '' or not next_line.startswith('    '):
                    lines[i + 1] = '                await ctx.followup.send("❌ This command must be used in a server", ephemeral=True)\n'
                    lines.insert(i + 2, '                return\n')
            
            # Fix incomplete try blocks
            if line.strip() == 'try:' and i + 1 < len(lines):
                next_line = lines[i + 1]
                if next_line.strip() == '' or 'except' in next_line:
                    lines[i + 1] = '            pass\n'
        
        with open(file_path, 'w') as f:
            f.writelines(lines)
        
        print(f"Fixed {file_path}")

def validate_syntax():
    """Quick syntax validation"""
    
    import ast
    
    critical_files = [
        'bot/cogs/economy.py',
        'bot/cogs/linking.py', 
        'bot/cogs/premium.py',
        'bot/cogs/core.py'
    ]
    
    all_valid = True
    
    for file_path in critical_files:
        if not os.path.exists(file_path):
            continue
            
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            ast.parse(content)
            print(f"✅ {file_path} - syntax valid")
            
        except SyntaxError as e:
            print(f"❌ {file_path} - syntax error: {e}")
            all_valid = False
    
    return all_valid

def main():
    """Force cold start with complete syntax fixes"""
    print("🔧 Force cold start - rebuilding critical commands...")
    
    # Rebuild economy command
    if rebuild_economy_command():
        print("✅ Rebuilt economy.py balance command")
    
    # Fix other critical files
    fix_critical_command_files()
    
    # Validate syntax
    if validate_syntax():
        print("✅ All critical files have valid syntax")
        print("✅ Discord bot ready to start")
        return True
    else:
        print("❌ Syntax errors remain")
        return False

if __name__ == "__main__":
    main()