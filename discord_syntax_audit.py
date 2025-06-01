#!/usr/bin/env python3
"""
Discord.py to py-cord 2.6.1 Syntax Audit and Conversion Tool
Systematically finds and fixes Discord.py syntax across the entire codebase
"""

import os
import re
from pathlib import Path

# Common Discord.py patterns that need conversion for py-cord 2.6.1
SYNTAX_CONVERSIONS = {
    # UI Components
    r'discord\.ui\.TextInput': 'discord.ui.InputText',
    r'discord\.ui\.Select': 'discord.ui.Select',
    r'discord\.ui\.button\(': 'discord.ui.button(',
    r'@discord\.ui\.button': '@discord.ui.button',
    
    # Application Commands (these are correct in py-cord)
    r'@commands\.slash_command': '@discord.slash_command',
    r'@bot\.slash_command': '@discord.slash_command',
    
    # Context and Interaction types
    r'discord\.ApplicationContext': 'discord.ApplicationContext',
    r'discord\.Interaction': 'discord.Interaction',
    
    # Option decorators
    r'@discord\.option': '@discord.option',
    r'discord\.Option': 'discord.Option',
    
    # Button styles (these should be correct)
    r'discord\.ButtonStyle': 'discord.ButtonStyle',
    
    # Embed types
    r'discord\.Embed': 'discord.Embed',
    
    # File handling
    r'discord\.File': 'discord.File',
}

# Problematic patterns that need manual review
PROBLEMATIC_PATTERNS = [
    r'commands\.Bot\(',  # Should be discord.Bot for py-cord
    r'commands\.Cog',    # Should be discord.Cog for py-cord
    r'@commands\.',      # Most should be @discord.
    r'\.add_cog\(',      # Method signature might differ
    r'\.slash_command',  # Check if using proper py-cord syntax
]

def audit_file(filepath):
    """Audit a single Python file for Discord.py syntax issues"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return []
    
    issues = []
    lines = content.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        # Check for Discord.py patterns
        for old_pattern, new_pattern in SYNTAX_CONVERSIONS.items():
            if re.search(old_pattern, line):
                issues.append({
                    'file': filepath,
                    'line': line_num,
                    'issue': f"Discord.py syntax: {old_pattern}",
                    'current': line.strip(),
                    'suggested': re.sub(old_pattern, new_pattern, line.strip())
                })
        
        # Check for problematic patterns
        for pattern in PROBLEMATIC_PATTERNS:
            if re.search(pattern, line):
                issues.append({
                    'file': filepath,
                    'line': line_num,
                    'issue': f"Needs review: {pattern}",
                    'current': line.strip(),
                    'suggested': "Manual review required"
                })
    
    return issues

def audit_codebase():
    """Audit the entire codebase for Discord.py syntax issues"""
    python_files = []
    
    # Find all Python files
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        if any(skip in root for skip in ['.git', '__pycache__', '.venv', 'node_modules']):
            continue
            
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"Found {len(python_files)} Python files to audit")
    
    all_issues = []
    for filepath in python_files:
        issues = audit_file(filepath)
        all_issues.extend(issues)
    
    # Group issues by type
    syntax_issues = [i for i in all_issues if "Discord.py syntax" in i['issue']]
    review_issues = [i for i in all_issues if "Needs review" in i['issue']]
    
    print(f"\n=== DISCORD.PY SYNTAX AUDIT RESULTS ===")
    print(f"Total issues found: {len(all_issues)}")
    print(f"Automatic fixes available: {len(syntax_issues)}")
    print(f"Manual review required: {len(review_issues)}")
    
    if syntax_issues:
        print(f"\n=== AUTOMATIC FIXES ===")
        for issue in syntax_issues[:10]:  # Show first 10
            print(f"File: {issue['file']}:{issue['line']}")
            print(f"  Current: {issue['current']}")
            print(f"  Fix: {issue['suggested']}")
            print()
    
    if review_issues:
        print(f"\n=== MANUAL REVIEW REQUIRED ===")
        for issue in review_issues[:10]:  # Show first 10
            print(f"File: {issue['file']}:{issue['line']}")
            print(f"  Issue: {issue['issue']}")
            print(f"  Line: {issue['current']}")
            print()
    
    return all_issues

if __name__ == "__main__":
    audit_codebase()