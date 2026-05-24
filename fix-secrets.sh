#!/bin/bash

# This script will be sourced by git filter-branch
# to clean hardcoded passwords from test files

if [ "$GIT_COMMIT" != "" ]; then
  # Run sed replacement on the file if it exists in this commit
  if git show "$GIT_COMMIT:tests/test_validation_schemas.py" > /dev/null 2>&1; then
    git show "$GIT_COMMIT:tests/test_validation_schemas.py" | \
      sed "s/'password': *'secret'/'password': TEST_VALID_PASSWORD/g" | \
      sed "s/'password': *'pass123'/'password': TEST_VALID_PASSWORD/g" > /tmp/fixed_file.py
    
    # Update the file in the index
    cat /tmp/fixed_file.py | git hash-object -w --stdin > /tmp/blob_hash
    blob_hash=$(cat /tmp/blob_hash)
    
    # Update the tree entry
    git ls-tree -r "$GIT_COMMIT" | while read -r line; do
      if echo "$line" | grep -q "tests/test_validation_schemas.py"; then
        echo "$blob_hash"
      fi
    done
  fi
fi
