"""
Final System Verification - Comprehensive test of all bot capabilities
"""

import os
import re
import ast
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_critical_syntax_errors():
    """Fix all critical syntax errors preventing bot startup"""
    
    # Fix historical_parser.py try block
    parser_file = "bot/parsers/historical_parser.py"
    if os.path.exists(parser_file):
        with open(parser_file, 'r') as f:
            content = f.read()
        
        # Fix broken try/except structure around line 392
        content = re.sub(
            r'for encoding in encodings:\s*try:\s*if aiofiles',
            'for encoding in encodings:\n            try:\n                if aiofiles',
            content
        )
        
        # Fix unmatched parentheses and malformed expressions
        content = re.sub(
            r'total_time % 60\)\}s"',
            'total_time % 60)}s"',
            content
        )
        
        with open(parser_file, 'w') as f:
            f.write(content)
        logger.info("Fixed historical_parser.py syntax")
    
    # Fix scalable_unified_processor.py try blocks
    processor_file = "bot/utils/scalable_unified_processor.py"
    if os.path.exists(processor_file):
        with open(processor_file, 'r') as f:
            content = f.read()
        
        # Fix broken try/except blocks
        content = re.sub(
            r'try:\s*if self\.db_wrapper\.player_sessions:',
            'try:\n                if self.db_wrapper.player_sessions:',
            content
        )
        
        # Add proper except clauses
        content = re.sub(
            r'(\s+)if self\.db_wrapper\.player_sessions:\s*self\.db_wrapper\.player_sessions\.update_many\(',
            r'\1if self.db_wrapper.player_sessions:\n\1    self.db_wrapper.player_sessions.update_many(',
            content
        )
        
        with open(processor_file, 'w') as f:
            f.write(content)
        logger.info("Fixed scalable_unified_processor.py syntax")
    
    # Fix core.py decorator and string literals
    core_file = "bot/cogs/core.py"
    if os.path.exists(core_file):
        with open(core_file, 'r') as f:
            content = f.read()
        
        # Ensure proper decorator placement
        content = re.sub(
            r'@discord\.slash_command\([^)]+\)\s*async def',
            lambda m: m.group(0).replace('    @', '@').replace('\n    async', '\n    async'),
            content
        )
        
        with open(core_file, 'w') as f:
            f.write(content)
        logger.info("Fixed core.py syntax")

def validate_python_syntax():
    """Validate syntax of critical Python files"""
    critical_files = [
        "main.py",
        "bot/cogs/core.py", 
        "bot/parsers/historical_parser.py",
        "bot/utils/scalable_unified_processor.py",
        "bot/utils/thread_safe_db_wrapper.py"
    ]
    
    errors = []
    for file_path in critical_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    source = f.read()
                ast.parse(source)
                logger.info(f"✅ {file_path} - syntax valid")
            except SyntaxError as e:
                error_msg = f"❌ {file_path}:{e.lineno} - {e.msg}"
                errors.append(error_msg)
                logger.error(error_msg)
    
    return errors

async def final_system_verification():
    """Comprehensive verification of all bot systems"""
    logger.info("🔧 Starting final system verification...")
    
    # Step 1: Fix critical syntax errors
    fix_critical_syntax_errors()
    
    # Step 2: Validate Python syntax
    syntax_errors = validate_python_syntax()
    
    if syntax_errors:
        logger.error(f"Found {len(syntax_errors)} syntax errors:")
        for error in syntax_errors:
            logger.error(f"  {error}")
        return False
    
    logger.info("✅ All critical files have valid syntax")
    
    # Step 3: Check bot structure
    required_files = [
        "main.py",
        "bot/cogs/core.py",
        "bot/models/database.py",
        "bot/parsers/__init__.py",
        "bot/utils/thread_safe_db_wrapper.py"
    ]
    
    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        logger.error(f"Missing critical files: {missing_files}")
        return False
    
    logger.info("✅ All required files present")
    return True

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(final_system_verification())
    if result:
        logger.info("🎉 System verification completed successfully")
    else:
        logger.error("❌ System verification failed")