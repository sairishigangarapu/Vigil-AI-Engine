#!/usr/bin/env python3
"""
Debug script to test file operations and diagnose "no such file or directory" errors.
"""

import os
import sys

print("="*80)
print("FILE OPERATIONS DEBUG SCRIPT")
print("="*80)
print()

# Check current working directory
print(f"Current working directory: {os.getcwd()}")
print()

# Check backend directory
backend_dir = os.path.dirname(__file__)
print(f"Backend directory: {backend_dir}")
print(f"Backend exists: {os.path.exists(backend_dir)}")
print()

# Check analysis directory
analysis_dir = os.path.join(backend_dir, "analysis")
print(f"Analysis directory: {analysis_dir}")
print(f"Analysis exists: {os.path.exists(analysis_dir)}")

if not os.path.exists(analysis_dir):
    print("⚠️  Analysis directory does not exist!")
    print("   Creating it now...")
    try:
        os.makedirs(analysis_dir, exist_ok=True)
        print("✅ Created analysis directory")
    except Exception as e:
        print(f"❌ Failed to create: {e}")
else:
    print("✅ Analysis directory exists")
    # List contents
    try:
        contents = os.listdir(analysis_dir)
        print(f"   Contents ({len(contents)} items):")
        for item in contents[:10]:  # Show first 10
            item_path = os.path.join(analysis_dir, item)
            item_type = "DIR" if os.path.isdir(item_path) else "FILE"
            print(f"   - [{item_type}] {item}")
        if len(contents) > 10:
            print(f"   ... and {len(contents) - 10} more")
    except Exception as e:
        print(f"❌ Failed to list contents: {e}")

print()

# Check temp_media directory
temp_media_dir = os.path.join(backend_dir, "temp_media")
print(f"temp_media directory: {temp_media_dir}")
print(f"temp_media exists: {os.path.exists(temp_media_dir)}")

if not os.path.exists(temp_media_dir):
    print("⚠️  temp_media directory does not exist!")
    print("   Creating it now...")
    try:
        os.makedirs(temp_media_dir, exist_ok=True)
        print("✅ Created temp_media directory")
    except Exception as e:
        print(f"❌ Failed to create: {e}")
else:
    print("✅ temp_media directory exists")

print()

# Test file write operation
test_dir = os.path.join(backend_dir, "analysis", "test_session")
print(f"Testing file write to: {test_dir}")

try:
    # Create test directory
    os.makedirs(test_dir, exist_ok=True)
    print("✅ Created test directory")
    
    # Try to write a file
    test_file = os.path.join(test_dir, "test.txt")
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("Test content")
    print(f"✅ Successfully wrote to: {test_file}")
    
    # Try to read it back
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"✅ Successfully read back: '{content}'")
    
    # Clean up
    os.remove(test_file)
    os.rmdir(test_dir)
    print("✅ Cleaned up test files")
    
except Exception as e:
    print(f"❌ File operation failed: {e}")
    import traceback
    print("Stack trace:")
    traceback.print_exc()

print()
print("="*80)
print("DIAGNOSTIC COMPLETE")
print("="*80)
