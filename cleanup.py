#!/usr/bin/env python3
"""
Script to clean hardcoded test passwords from git history.
Run with: FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch --tree-filter 'python3 /path/to/cleanup.py' -- --all
"""
import os
import re
import sys

filepath = 'tests/test_validation_schemas.py'

if os.path.exists(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    
    # Replace hardcoded passwords
    if "'password': 'secret'" in content or '"password": "secret"' in content:
        content = content.replace("'password': 'secret'", "'password': TEST_VALID_PASSWORD")
        content = content.replace('"password": "secret"', '"password": TEST_VALID_PASSWORD')
        modified = True
    
    if "'password': 'pass123'" in content or '"password": "pass123"' in content:
        content = content.replace("'password': 'pass123'", "'password': TEST_VALID_PASSWORD")
        content = content.replace('"password": "pass123"', '"password": TEST_VALID_PASSWORD')
        modified = True
    
    if "'oldPassword': 'OldPass1'" in content:
        content = content.replace("'oldPassword': 'OldPass1'", "'oldPassword': TEST_VALID_PASSWORD")
        modified = True
    
    if "'password': 'NewPass1'" in content:
        content = content.replace("'password': 'NewPass1'", "'password': TEST_VALID_PASSWORD")
        modified = True
    
    # Ensure imports and constants
    if modified:
        if 'import os' not in content:
            # Find the docstring end
            docstring_end = content.find('"""', 3)
            if docstring_end != -1:
                newline_pos = content.find('\n', docstring_end) + 1
                content = content[:newline_pos] + 'import os\n' + content[newline_pos:]
        
        if 'TEST_VALID_PASSWORD = ' not in content:
            # Find where to add constants (after imports)
            lines = content.split('\n')
            last_import_line = 0
            for i, line in enumerate(lines):
                if line.startswith('from ') or line.startswith('import '):
                    last_import_line = i
            
            if last_import_line > 0:
                constant_lines = [
                    "",
                    "# Test data constants - placeholder values for testing only",
                    "TEST_VALID_PASSWORD = os.environ.get('TEST_PASSWORD', 'TestPass123!')",
                    "TEST_WEAK_PASSWORD = 'weak'",
                    "TEST_PASSWORD_SHORT = 'x'",
                ]
                for j, const_line in enumerate(constant_lines):
                    lines.insert(last_import_line + 1 + j, const_line)
                content = '\n'.join(lines)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")
