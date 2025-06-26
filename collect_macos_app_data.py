#!/usr/bin/env python3
"""
macOS Application Data Collector

This script searches for all applications on a Mac system and collects:
- .sdef files (Scripting Definitions)
- Code signing information
- Entitlements
- Info.plist data
- Sandbox information

Organizes data in structure: data/<ApplicationName>/[sdef/, codesign.txt, entitlements.plist, info.plist, sandbox.txt]
"""

import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
import re
from typing import Optional, Set, Dict, Tuple
import logging
import sys
import json
import plistlib
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_all_applications() -> Set[Path]:
    """
    Find all .app bundles on the system.
    
    Returns:
        Set of Path objects pointing to .app bundles
    """
    app_bundles = set()
    
    # Common locations where applications are found
    search_paths = [
        "/Applications",
        "/System/Applications", 
        "/System/Library/CoreServices",
        "/Developer/Applications",
        "~/Applications",
        "/Library/Application Support",
        "/System/Library/Frameworks",
    ]
    
    logger.info("Searching for application bundles...")
    
    for search_path in search_paths:
        expanded_path = Path(search_path).expanduser()
        if expanded_path.exists():
            logger.info(f"Searching in: {expanded_path}")
            try:
                # Find .app bundles recursively
                result = subprocess.run([
                    'find', str(expanded_path), '-name', '*.app', '-type', 'd', '-maxdepth', '3'
                ], capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line and Path(line).exists():
                            app_bundles.add(Path(line))
                            
            except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
                logger.warning(f"Error searching {expanded_path}: {e}")
                # Fallback to Python's glob
                try:
                    for app_bundle in expanded_path.rglob("*.app"):
                        if app_bundle.is_dir():
                            app_bundles.add(app_bundle)
                except PermissionError:
                    logger.warning(f"Permission denied accessing {expanded_path}")
    
    logger.info(f"Found {len(app_bundles)} application bundles")
    return app_bundles

def get_application_name(app_path: Path) -> str:
    """
    Get a clean application name from the app bundle path.
    
    Args:
        app_path: Path to the .app bundle
        
    Returns:
        Clean application name for directory use
    """
    app_name = app_path.name
    if app_name.endswith('.app'):
        app_name = app_name[:-4]
    
    # Clean up the name for directory use
    app_name = re.sub(r'[<>:"/\\|?*]', '_', app_name)
    return app_name

def extract_code_signing_info(app_path: Path) -> Dict[str, str]:
    """
    Extract code signing information from an application.
    
    Args:
        app_path: Path to the .app bundle
        
    Returns:
        Dictionary with code signing information
    """
    info = {
        'signature_status': 'Unknown',
        'authority': 'Unknown',
        'identifier': 'Unknown',
        'team_identifier': 'Unknown',
        'sealed_resources': 'Unknown',
        'error': None
    }
    
    try:
        # Get basic code signature info
        result = subprocess.run([
            'codesign', '-dv', str(app_path)
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            info['signature_status'] = 'Valid'
            output = result.stderr  # codesign outputs to stderr
            
            # Parse codesign output
            for line in output.split('\n'):
                if 'Authority=' in line:
                    info['authority'] = line.split('Authority=')[1].strip()
                elif 'Identifier=' in line:
                    info['identifier'] = line.split('Identifier=')[1].strip()
                elif 'TeamIdentifier=' in line:
                    info['team_identifier'] = line.split('TeamIdentifier=')[1].strip()
                elif 'Sealed Resources' in line:
                    info['sealed_resources'] = 'Yes' if 'version' in line else 'No'
        else:
            info['signature_status'] = 'Invalid or Unsigned'
            info['error'] = result.stderr.strip()
            
        # Additional verification
        verify_result = subprocess.run([
            'codesign', '--verify', '--verbose', str(app_path)
        ], capture_output=True, text=True, timeout=30)
        
        if verify_result.returncode != 0:
            info['signature_status'] += ' (Verification Failed)'
            
    except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
        info['error'] = str(e)
        logger.debug(f"Code signing check failed for {app_path}: {e}")
    
    return info

def extract_entitlements(app_path: Path) -> Optional[str]:
    """
    Extract and format entitlements from an application.
    
    Args:
        app_path: Path to the .app bundle
        
    Returns:
        Entitlements as nicely formatted XML string, or None if not found
    """
    try:
        result = subprocess.run([
            'codesign', '-d', '--entitlements', ':-', str(app_path)
        ], capture_output=True, text=True, timeout=30)
        
        raw_xml = None
        if result.returncode == 0 and result.stdout.strip():
            raw_xml = result.stdout
        else:
            # Try alternative method for some apps
            result = subprocess.run([
                'codesign', '--display', '--entitlements', ':-', str(app_path)
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and result.stdout.strip():
                raw_xml = result.stdout
        
        if raw_xml:
            # Format the XML nicely
            try:
                # Parse the XML
                root = ET.fromstring(raw_xml)
                
                # Create a formatted XML string with proper indentation
                ET.indent(root, space="  ", level=0)
                formatted_xml = ET.tostring(root, encoding='unicode', xml_declaration=True)
                
                # Add a header comment for clarity
                header = f"""<!-- Entitlements for {app_path.name} -->
<!-- Extracted on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -->

"""
                return header + formatted_xml
                
            except ET.ParseError as e:
                logger.debug(f"XML parsing failed for {app_path}, returning raw data: {e}")
                # If parsing fails, at least clean up the raw XML a bit
                lines = raw_xml.strip().split('\n')
                cleaned_lines = []
                for line in lines:
                    stripped = line.strip()
                    if stripped:  # Skip empty lines
                        cleaned_lines.append(stripped)
                
                # Add basic indentation
                formatted_lines = []
                indent_level = 0
                for line in cleaned_lines:
                    if line.startswith('</') and not line.startswith('<?'):
                        indent_level = max(0, indent_level - 1)
                    
                    formatted_lines.append('  ' * indent_level + line)
                    
                    if line.startswith('<') and not line.startswith('<?') and not line.startswith('</') and not line.endswith('/>'):
                        indent_level += 1
                
                header = f"""<!-- Entitlements for {app_path.name} -->
<!-- Extracted on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -->
<!-- Note: XML formatting may be basic due to parsing issues -->

"""
                return header + '\n'.join(formatted_lines)
                
    except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
        logger.debug(f"Entitlements extraction failed for {app_path}: {e}")
    
    return None

def extract_info_plist(app_path: Path) -> Optional[str]:
    """
    Extract and format Info.plist from an application as nicely formatted XML.
    
    Args:
        app_path: Path to the .app bundle
        
    Returns:
        Formatted Info.plist as XML string, or None if not found
    """
    info_plist_path = app_path / "Contents" / "Info.plist"
    
    if not info_plist_path.exists():
        return None
    
    try:
        # Use plutil to convert to nicely formatted XML
        result = subprocess.run([
            'plutil', '-convert', 'xml1', '-o', '-', str(info_plist_path)
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and result.stdout.strip():
            raw_xml = result.stdout
            
            try:
                # Parse and reformat the XML for consistent indentation
                root = ET.fromstring(raw_xml)
                ET.indent(root, space="  ", level=0)
                formatted_xml = ET.tostring(root, encoding='unicode', xml_declaration=True)
                
                # Add a header comment for clarity
                header = f"""<!-- Info.plist for {app_path.name} -->
<!-- Extracted on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -->
<!-- Source: {info_plist_path} -->

"""
                return header + formatted_xml
                
            except ET.ParseError as e:
                logger.debug(f"XML formatting failed for {app_path}, returning raw plutil output: {e}")
                # Add basic header even if formatting fails
                header = f"""<!-- Info.plist for {app_path.name} -->
<!-- Extracted on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -->
<!-- Source: {info_plist_path} -->

"""
                return header + raw_xml
        
    except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
        logger.debug(f"plutil conversion failed for {app_path}: {e}")
    
    # Fallback: try reading the plist directly and convert manually
    try:
        with open(info_plist_path, 'rb') as f:
            plist_data = plistlib.load(f)
        
        # Convert back to plist XML format using plistlib
        xml_bytes = plistlib.dumps(plist_data, fmt=plistlib.FMT_XML)
        raw_xml = xml_bytes.decode('utf-8')
        
        try:
            # Parse and reformat for consistent indentation
            root = ET.fromstring(raw_xml)
            ET.indent(root, space="  ", level=0)
            formatted_xml = ET.tostring(root, encoding='unicode', xml_declaration=True)
            
            header = f"""<!-- Info.plist for {app_path.name} -->
<!-- Extracted on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -->
<!-- Source: {info_plist_path} -->

"""
            return header + formatted_xml
            
        except ET.ParseError:
            # Last resort: return raw XML with header
            header = f"""<!-- Info.plist for {app_path.name} -->
<!-- Extracted on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -->
<!-- Source: {info_plist_path} -->

"""
            return header + raw_xml
        
    except (OSError, plistlib.InvalidFileException) as e:
        logger.debug(f"Direct plist reading failed for {app_path}: {e}")
    
    return None

def analyze_sandbox_info(app_path: Path, info_plist_data: Optional[str], entitlements: Optional[str]) -> Dict[str, str]:
    """
    Analyze sandbox information for an application.
    
    Args:
        app_path: Path to the .app bundle
        info_plist_data: Info.plist data as XML string
        entitlements: Entitlements as XML string
        
    Returns:
        Dictionary with sandbox analysis
    """
    sandbox_info = {
        'sandboxed': 'Unknown',
        'sandbox_type': 'Unknown',
        'entitlements_count': '0',
        'hardened_runtime': 'Unknown',
        'library_validation': 'Unknown',
        'analysis_notes': []
    }
    
    # Check entitlements for sandbox indicators
    if entitlements:
        try:
            # Count entitlements
            entitlement_lines = [line for line in entitlements.split('\n') if '<key>' in line and '</key>' in line]
            sandbox_info['entitlements_count'] = str(len(entitlement_lines))
            
            # Check for sandbox entitlement
            if 'com.apple.security.app-sandbox' in entitlements:
                if '<true/>' in entitlements.split('com.apple.security.app-sandbox')[1].split('</dict>')[0]:
                    sandbox_info['sandboxed'] = 'Yes'
                    sandbox_info['sandbox_type'] = 'App Sandbox'
                else:
                    sandbox_info['sandboxed'] = 'No'
            
            # Check for hardened runtime
            if 'com.apple.security.cs.allow-jit' in entitlements or 'com.apple.security.cs.allow-unsigned-executable-memory' in entitlements:
                sandbox_info['hardened_runtime'] = 'Yes (with exceptions)'
            elif any(key in entitlements for key in ['com.apple.security.cs.', 'hardened-runtime']):
                sandbox_info['hardened_runtime'] = 'Yes'
            
            # Check for library validation
            if 'com.apple.security.cs.disable-library-validation' in entitlements:
                sandbox_info['library_validation'] = 'Disabled'
            else:
                sandbox_info['library_validation'] = 'Enabled'
            
        except Exception as e:
            sandbox_info['analysis_notes'].append(f"Entitlements parsing error: {e}")
    
    # Check Info.plist for additional sandbox indicators
    if info_plist_data:
        try:
            # Parse XML plist data
            # First, try to extract just the plist content (remove comments)
            plist_content = info_plist_data
            if '<?xml' in plist_content:
                # Find the start of the actual plist
                plist_start = plist_content.find('<?xml')
                plist_content = plist_content[plist_start:]
            
            # Parse the XML and convert to a dictionary
            root = ET.fromstring(plist_content)
            
            # Find the main dict element
            dict_element = root.find('dict')
            if dict_element is not None:
                # Parse plist dict structure
                plist_dict = {}
                children = list(dict_element)
                for i in range(0, len(children), 2):
                    if i + 1 < len(children) and children[i].tag == 'key':
                        key = children[i].text
                        value_elem = children[i + 1]
                        
                        # Extract value based on type
                        if value_elem.tag == 'true':
                            plist_dict[key] = True
                        elif value_elem.tag == 'false':
                            plist_dict[key] = False
                        elif value_elem.tag == 'string':
                            plist_dict[key] = value_elem.text or ''
                        elif value_elem.tag == 'integer':
                            plist_dict[key] = int(value_elem.text or 0)
                        else:
                            plist_dict[key] = value_elem.text or ''
                
                # Check for LSUIElement (background app)
                if plist_dict.get('LSUIElement'):
                    sandbox_info['analysis_notes'].append('Background app (LSUIElement)')
                
                # Check for LSBackgroundOnly
                if plist_dict.get('LSBackgroundOnly'):
                    sandbox_info['analysis_notes'].append('Background only app')
                
                # Check for specific frameworks that indicate sandboxing
                if plist_dict.get('LSRequiresIPhoneOS'):
                    sandbox_info['analysis_notes'].append('iOS app on macOS')
                
                # Check for app transport security
                if 'NSAppTransportSecurity' in plist_dict:
                    sandbox_info['analysis_notes'].append('Uses App Transport Security')
                    
        except (ET.ParseError, ValueError) as e:
            sandbox_info['analysis_notes'].append(f"Info.plist XML parsing error: {e}")
        except Exception as e:
            sandbox_info['analysis_notes'].append(f"Info.plist analysis error: {e}")
    
    # Additional system-level checks
    try:
        # Check if app is in /System/Applications (usually sandboxed system apps)
        if '/System/Applications' in str(app_path):
            sandbox_info['analysis_notes'].append('System application')
            
        # Check if app is in /Applications (user apps, may or may not be sandboxed)
        elif '/Applications' == str(app_path.parent):
            sandbox_info['analysis_notes'].append('User application')
            
    except Exception as e:
        sandbox_info['analysis_notes'].append(f"Path analysis error: {e}")
    
    return sandbox_info

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
                ], capture_output=True, text=True, timeout=300)
                
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
        
        # Create application directory with sdef subdirectory
        app_dir = data_dir / app_name
        sdef_dir = app_dir / "sdef"
        sdef_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine destination filename
        dest_path = sdef_dir / sdef_path.name
        
        # Handle filename conflicts
        counter = 1
        original_dest = dest_path
        while dest_path.exists():
            name_parts = original_dest.stem, counter, original_dest.suffix
            dest_path = sdef_dir / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
            counter += 1
        
        # Copy the file
        shutil.copy2(sdef_path, dest_path)
        logger.info(f"Copied SDEF: {sdef_path} -> {dest_path}")
        return True
        
    except (OSError, PermissionError) as e:
        logger.error(f"Failed to copy {sdef_path}: {e}")
        return False

def process_application(app_path: Path, data_dir: Path) -> bool:
    """
    Process a single application and collect all its data.
    
    Args:
        app_path: Path to the .app bundle
        data_dir: Base data directory
        
    Returns:
        True if any data was collected, False otherwise
    """
    app_name = get_application_name(app_path)
    app_dir = data_dir / app_name
    
    try:
        # Create application directory
        app_dir.mkdir(parents=True, exist_ok=True)
        
        collected_data = False
        
        # 1. Collect SDEF files
        sdef_count = 0
        for sdef_file in app_path.rglob("*.sdef"):
            if sdef_file.is_file():
                # Use the existing copy_sdef_file but modify for new structure
                sdef_dir = app_dir / "sdef"
                sdef_dir.mkdir(exist_ok=True)
                
                dest_path = sdef_dir / sdef_file.name
                counter = 1
                original_dest = dest_path
                while dest_path.exists():
                    name_parts = original_dest.stem, counter, original_dest.suffix
                    dest_path = sdef_dir / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
                    counter += 1
                
                try:
                    shutil.copy2(sdef_file, dest_path)
                    sdef_count += 1
                    collected_data = True
                except (OSError, PermissionError) as e:
                    logger.debug(f"Failed to copy SDEF {sdef_file}: {e}")
        
        # 2. Collect code signing information
        logger.debug(f"Collecting code signing info for {app_name}")
        codesign_info = extract_code_signing_info(app_path)
        
        codesign_text = f"""Code Signing Information for {app_name}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Application Path: {app_path}

Signature Status: {codesign_info['signature_status']}
Authority: {codesign_info['authority']}
Identifier: {codesign_info['identifier']}
Team Identifier: {codesign_info['team_identifier']}
Sealed Resources: {codesign_info['sealed_resources']}
"""
        
        if codesign_info['error']:
            codesign_text += f"\nError: {codesign_info['error']}"
        
        codesign_file = app_dir / "codesign.txt"
        with open(codesign_file, 'w') as f:
            f.write(codesign_text)
        collected_data = True
        
        # 3. Collect entitlements
        logger.debug(f"Collecting entitlements for {app_name}")
        entitlements = extract_entitlements(app_path)
        
        entitlements_file = app_dir / "entitlements.plist"
        if entitlements:
            with open(entitlements_file, 'w') as f:
                f.write(entitlements)
        else:
            with open(entitlements_file, 'w') as f:
                f.write(f"No entitlements found for {app_name}\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        collected_data = True
        
        # 4. Collect Info.plist
        logger.debug(f"Collecting Info.plist for {app_name}")
        info_plist_data = extract_info_plist(app_path)
        
        info_plist_file = app_dir / "info.plist"
        if info_plist_data:
            with open(info_plist_file, 'w') as f:
                f.write(info_plist_data)
        else:
            with open(info_plist_file, 'w') as f:
                f.write(f"{{\n  \"error\": \"No Info.plist found or could not be read for {app_name}\",\n  \"generated\": \"{datetime.now().isoformat()}\"\n}}")
        collected_data = True
        
        # 5. Analyze sandbox information
        logger.debug(f"Analyzing sandbox info for {app_name}")
        sandbox_info = analyze_sandbox_info(app_path, info_plist_data, entitlements)
        
        sandbox_text = f"""Sandbox Analysis for {app_name}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Application Path: {app_path}

Sandboxed: {sandbox_info['sandboxed']}
Sandbox Type: {sandbox_info['sandbox_type']}
Entitlements Count: {sandbox_info['entitlements_count']}
Hardened Runtime: {sandbox_info['hardened_runtime']}
Library Validation: {sandbox_info['library_validation']}

Analysis Notes:
"""
        
        for note in sandbox_info['analysis_notes']:
            sandbox_text += f"- {note}\n"
        
        if not sandbox_info['analysis_notes']:
            sandbox_text += "- No additional notes\n"
        
        sandbox_file = app_dir / "sandbox.txt"
        with open(sandbox_file, 'w') as f:
            f.write(sandbox_text)
        collected_data = True
        
        if collected_data:
            logger.info(f"Processed {app_name}: {sdef_count} SDEF files + metadata")
        
        return collected_data
        
    except (OSError, PermissionError) as e:
        logger.error(f"Failed to process application {app_path}: {e}")
        return False

def main():
    """Main function to orchestrate the application data collection."""
    # Check if running with sudo privileges
    if os.geteuid() != 0:
        logger.error("This script requires sudo privileges to access system applications and signing data.")
        logger.error("Please run with: sudo python3 collect_sdef_files.py")
        sys.exit(1)
    
    script_dir = Path(__file__).parent
    data_dir = script_dir / "data"
    
    logger.info("Starting macOS application data collection...")
    logger.info(f"Output directory: {data_dir}")
    
    # Create data directory
    data_dir.mkdir(exist_ok=True)
    
    # Find all applications
    app_bundles = find_all_applications()
    
    if not app_bundles:
        logger.warning("No application bundles found!")
        return
    
    # Process each application
    success_count = 0
    sdef_total = 0
    
    for app_bundle in app_bundles:
        logger.info(f"Processing: {app_bundle.name}")
        if process_application(app_bundle, data_dir):
            success_count += 1
            
            # Count SDEF files in this app
            app_name = get_application_name(app_bundle)
            sdef_dir = data_dir / app_name / "sdef"
            if sdef_dir.exists():
                sdef_count = len(list(sdef_dir.glob("*.sdef")))
                sdef_total += sdef_count
    
    logger.info(f"Successfully processed {success_count} out of {len(app_bundles)} applications")
    logger.info(f"Total SDEF files collected: {sdef_total}")
    logger.info(f"Data organized in: {data_dir}")
    
    # Print summary
    if success_count > 0:
        print(f"\n✅ Collection complete!")
        print(f"� Processed {success_count} applications")
        print(f"📄 Collected {sdef_total} SDEF files")
        print(f"📂 Output directory: {data_dir}")
        print(f"\nDirectory structure created:")
        
        # Show the directory structure
        for app_dir in sorted(data_dir.iterdir()):
            if app_dir.is_dir():
                app_name = app_dir.name
                sdef_dir = app_dir / "sdef"
                sdef_count = len(list(sdef_dir.glob("*.sdef"))) if sdef_dir.exists() else 0
                
                # Check what files were created
                files_created = []
                for file_name in ["codesign.txt", "entitlements.plist", "info.plist", "sandbox.txt"]:
                    if (app_dir / file_name).exists():
                        files_created.append(file_name)
                
                sdef_text = f"{sdef_count} SDEF" if sdef_count > 0 else "no SDEF"
                files_text = f"{len(files_created)} metadata files" if files_created else "no metadata"
                print(f"  📱 {app_name}/ ({sdef_text}, {files_text})")
        
        print(f"\n📊 Summary:")
        print(f"  • Each app directory contains:")
        print(f"    - sdef/ (SDEF files)")
        print(f"    - codesign.txt (code signing info)")
        print(f"    - entitlements.plist (app entitlements)")
        print(f"    - info.plist (app metadata)")
        print(f"    - sandbox.txt (sandbox analysis)")

if __name__ == "__main__":
    main()
