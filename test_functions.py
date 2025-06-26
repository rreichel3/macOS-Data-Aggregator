#!/usr/bin/env python3
"""
Quick test script to verify the new functionality works
"""

import sys
from pathlib import Path

# Add the current directory to Python path to import our functions
sys.path.insert(0, str(Path(__file__).parent))

from collect_sdef_files import (
    get_application_name, 
    extract_code_signing_info, 
    extract_entitlements,
    extract_info_plist,
    analyze_sandbox_info
)

def test_single_app():
    """Test the functions on a single application"""
    # Test with a common system app
    test_app = Path("/System/Applications/Calculator.app")
    
    if not test_app.exists():
        print("Calculator.app not found, trying TextEdit...")
        test_app = Path("/System/Applications/TextEdit.app")
    
    if not test_app.exists():
        print("No test app found")
        return
    
    print(f"Testing with: {test_app}")
    print(f"App name: {get_application_name(test_app)}")
    
    # Test code signing (this should work without sudo for basic info)
    print("\n--- Code Signing Info ---")
    codesign_info = extract_code_signing_info(test_app)
    for key, value in codesign_info.items():
        print(f"{key}: {value}")
    
    # Test Info.plist extraction
    print("\n--- Info.plist (first 200 chars) ---")
    info_plist = extract_info_plist(test_app)
    if info_plist:
        print(info_plist[:200] + "..." if len(info_plist) > 200 else info_plist)
    else:
        print("No Info.plist found")
    
    # Test entitlements (might need sudo)
    print("\n--- Entitlements (first 200 chars) ---")
    entitlements = extract_entitlements(test_app)
    if entitlements:
        print(entitlements[:200] + "..." if len(entitlements) > 200 else entitlements)
    else:
        print("No entitlements found")
    
    # Test sandbox analysis
    print("\n--- Sandbox Analysis ---")
    sandbox_info = analyze_sandbox_info(test_app, info_plist, entitlements)
    for key, value in sandbox_info.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    test_single_app()
