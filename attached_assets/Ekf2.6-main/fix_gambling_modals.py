#!/usr/bin/env python3
"""
Fix gambling modals for py-cord 2.6.1 compatibility
The runtime errors show TextInput doesn't exist in discord.ui
"""

import re

def fix_gambling_modals():
    """Fix the modal implementations that are causing runtime errors"""
    
    with open('bot/cogs/gambling_ultra_v2.py', 'r') as f:
        content = f.read()
    
    # The actual issue: TextInput doesn't exist in py-cord, should be InputText
    # But the fix I made earlier wasn't complete - need to check all modal definitions
    
    # Find all modal classes and their InputText definitions
    modal_pattern = r'class \w+Modal\(discord\.ui\.Modal\):'
    input_pattern = r'discord\.ui\.InputText\('
    
    modals = re.findall(modal_pattern, content)
    inputs = re.findall(input_pattern, content)
    
    print(f"Found {len(modals)} modal classes")
    print(f"Found {len(inputs)} InputText instances")
    
    # Check if all are properly converted
    if 'discord.ui.TextInput' in content:
        print("ERROR: Still has TextInput references!")
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if 'discord.ui.TextInput' in line:
                print(f"Line {i}: {line.strip()}")
    else:
        print("All TextInput references appear to be fixed")
    
    # Check for null safety issues that cause the .value errors
    value_access_pattern = r'self\.\w+\.value\.'
    unsafe_accesses = re.findall(value_access_pattern, content)
    
    if unsafe_accesses:
        print(f"Found {len(unsafe_accesses)} potentially unsafe value accesses")
    
    return True

if __name__ == "__main__":
    fix_gambling_modals()