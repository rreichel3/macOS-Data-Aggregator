#!/usr/bin/env python3
"""
SDEF File Collector for macOS

This script searches for all .sdef files on a Mac system and organizes them
in a directory structure: data/<ApplicationName>/<original_sdef_file_name>
"""

import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
import re
from typing import Optional, Set
import logging
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_sdef_files() -> Set[Path]:
    """
    Find all .sdef files on the system using multiple search strategies.
    
    Returns:
        Set of Path objects pointing to .sdef files
    """
    sdef_files = set()
    
    # Common locations where .sdef files are typically found
    search_paths = [
        "/System/Library/ScriptingDefinitions",
        "/Library/ScriptingDefinitions", 
        "/Applications",
        "/System/Applications",
        "/Developer/Applications",
        "~/Applications",
    ]
    
    logger.info("Searching for .sdef files in common locations...")
    
    # Search in common directories
    for search_path in search_paths:
        expanded_path = Path(search_path).expanduser()
        if expanded_path.exists():
            logger.info(f"Searching in: {expanded_path}")
            try:
                # Use find command for better performance on large directories
                result = subprocess.run([
                    'find', str(expanded_path), '-name', '*.sdef', '-type', 'f'
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            sdef_files.add(Path(line))
            except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
                logger.warning(f"Error searching {expanded_path}: {e}")
                # Fallback to Python's glob
                try:
                    for sdef_file in expanded_path.rglob("*.sdef"):
                        if sdef_file.is_file():
                            sdef_files.add(sdef_file)
                except PermissionError:
                    logger.warning(f"Permission denied accessing {expanded_path}")
    
    # Also search inside application bundles specifically
    logger.info("Searching inside application bundles...")
    app_paths = ["/Applications", "/System/Applications", Path.home() / "Applications"]
    
    for app_dir in app_paths:
        app_dir = Path(app_dir)
        if app_dir.exists():
            try:
                for app_bundle in app_dir.glob("*.app"):
                    if app_bundle.is_dir():
                        # Look for sdef files in Resources and other common locations
                        for sdef_file in app_bundle.rglob("*.sdef"):
                            if sdef_file.is_file():
                                sdef_files.add(sdef_file)
            except PermissionError:
                logger.warning(f"Permission denied accessing {app_dir}")
    
    logger.info(f"Found {len(sdef_files)} .sdef files")
    return sdef_files

def extract_application_name(sdef_path: Path) -> Optional[str]:
    """
    Extract the application name from an .sdef file.
    
    First tries to parse the XML and get the name from the dictionary element,
    then falls back to extracting from the file path.
    
    Args:
        sdef_path: Path to the .sdef file
        
    Returns:
        Application name or None if not found
    """
    try:
        # Try to parse the XML and extract the application name
        tree = ET.parse(sdef_path)
        root = tree.getroot()
        
        # Look for dictionary element with name attribute
        dictionary = root.find('dictionary')
        if dictionary is not None and 'title' in dictionary.attrib:
            app_name = dictionary.attrib['title']
            # Clean up the name for use as directory name
            app_name = re.sub(r'[<>:"/\\|?*]', '_', app_name)
            return app_name
            
        # Look for suite elements with name attributes as fallback
        suite = root.find('suite')
        if suite is not None and 'name' in suite.attrib:
            app_name = suite.attrib['name']
            app_name = re.sub(r'[<>:"/\\|?*]', '_', app_name)
            return app_name
            
    except (ET.ParseError, PermissionError, OSError) as e:
        logger.debug(f"Could not parse XML from {sdef_path}: {e}")
    
    # Fallback: extract from file path
    path_parts = sdef_path.parts
    
    # Look for .app bundle in the path
    for i, part in enumerate(path_parts):
        if part.endswith('.app'):
            app_name = part[:-4]  # Remove .app extension
            app_name = re.sub(r'[<>:"/\\|?*]', '_', app_name)
            return app_name
    
    # If no .app found, try to get from parent directory names
    if len(path_parts) > 1:
        # Skip common directory names
        skip_dirs = {'ScriptingDefinitions', 'Resources', 'Contents', 'Library', 'System', 'Applications'}
        for part in reversed(path_parts[:-1]):  # Exclude the filename
            if part not in skip_dirs and not part.startswith('.'):
                app_name = re.sub(r'[<>:"/\\|?*]', '_', part)
                return app_name
    
    # Last resort: use the filename without extension
    return sdef_path.stem

def copy_sdef_file(sdef_path: Path, data_dir: Path) -> bool:
    """
    Copy an .sdef file to the organized directory structure.
    
    Args:
        sdef_path: Source .sdef file path
        data_dir: Base data directory
        
    Returns:
        True if successful, False otherwise
    """
    try:
        app_name = extract_application_name(sdef_path)
        if not app_name:
            logger.warning(f"Could not determine application name for {sdef_path}")
            app_name = "Unknown"
        
        # Create application directory
        app_dir = data_dir / app_name
        app_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine destination filename
        dest_path = app_dir / sdef_path.name
        
        # Handle filename conflicts
        counter = 1
        original_dest = dest_path
        while dest_path.exists():
            name_parts = original_dest.stem, counter, original_dest.suffix
            dest_path = app_dir / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
            counter += 1
        
        # Copy the file
        shutil.copy2(sdef_path, dest_path)
        logger.info(f"Copied: {sdef_path} -> {dest_path}")
        return True
        
    except (OSError, PermissionError) as e:
        logger.error(f"Failed to copy {sdef_path}: {e}")
        return False

def main():
    """Main function to orchestrate the SDEF file collection."""
    # Check if running with sudo privileges
    if os.geteuid() != 0:
        logger.error("This script requires sudo privileges to access system .sdef files.")
        logger.error("Please run with: sudo python3 collect_sdef_files.py")
        sys.exit(1)
    
    script_dir = Path(__file__).parent
    data_dir = script_dir / "data"
    
    logger.info("Starting SDEF file collection...")
    logger.info(f"Output directory: {data_dir}")
    
    # Create data directory
    data_dir.mkdir(exist_ok=True)
    
    # Find all .sdef files
    sdef_files = find_sdef_files()
    
    if not sdef_files:
        logger.warning("No .sdef files found!")
        return
    
    # Copy files to organized structure
    success_count = 0
    for sdef_file in sdef_files:
        if copy_sdef_file(sdef_file, data_dir):
            success_count += 1
    
    logger.info(f"Successfully copied {success_count} out of {len(sdef_files)} .sdef files")
    logger.info(f"Files organized in: {data_dir}")
    
    # Print summary
    if success_count > 0:
        print(f"\n✅ Collection complete!")
        print(f"📁 Found and organized {success_count} .sdef files")
        print(f"📂 Output directory: {data_dir}")
        print(f"\nDirectory structure created:")
        
        # Show the directory structure
        for app_dir in sorted(data_dir.iterdir()):
            if app_dir.is_dir():
                sdef_count = len(list(app_dir.glob("*.sdef")))
                print(f"  📱 {app_dir.name}/ ({sdef_count} file{'s' if sdef_count != 1 else ''})")

if __name__ == "__main__":
    main()
