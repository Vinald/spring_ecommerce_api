#!/usr/bin/env python3
import sys
import re

def callback(blob, metadata):
    """Callback function for git-filter-repo to remove hardcoded passwords."""
    if metadata['filename'].decode() == 'tests/test_validation_schemas.py':
        content = blob.data.decode('utf-8')
        
        # Replace hardcoded passwords with variable references
        content = re.sub(r"'password':\s*'secret'", r"'password': TEST_VALID_PASSWORD", content)
        content = re.sub(r"'password':\s*'pass123'", r"'password': TEST_VALID_PASSWORD", content)
        content = re.sub(r"'password':\s*'x'", r"'password': TEST_PASSWORD_SHORT", content)
        
        # Ensure os import is present
        if 'import os' not in content:
            # Add after docstring
            if '"""' in content:
                parts = content.split('"""')
                if len(parts) >= 3:
                    content = parts[0] + '"""' + parts[1] + '"""\nimport os\n' + '"""'.join(parts[2:])
        
        # Ensure constants are defined
        if 'TEST_VALID_PASSWORD = ' not in content and 'validate_request' in content:
            # Add constants after imports
            lines = content.split('\n')
            last_import = 0
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    last_import = i
            
            if last_import > 0:
                const_section = (
                    "\n# Test data constants - placeholder values for testing only\n"
                    "TEST_VALID_PASSWORD = os.environ.get('TEST_PASSWORD', 'TestPass123!')\n"
                    "TEST_WEAK_PASSWORD = 'weak'\n"
                    "TEST_PASSWORD_SHORT = 'x'\n"
                )
                lines.insert(last_import + 1, const_section)
                content = '\n'.join(lines)
        
        blob.data = content.encode('utf-8')

if __name__ == '__main__':
    # This will be imported by git-filter-repo
    pass
