# M
macOS Application Data Aggregator

[![Collect macOS Application Data](https://github.com/rreichel3/sdef/actions/workflows/collect-sdef.yml/badge.svg)](https://github.com/rreichel3/sdef/actions/workflows/collect-sdef.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![macOS](https://img.shields.io/badge/macOS-10.15+-blue.svg)](https://www.apple.com/macos/)
[![Python](https://img.shields.io/badge/Python-3.6+-green.svg)](https://www.python.org/)

A comprehensive tool for collecting and organizing macOS application data including SDEF files, code signing information, entitlements, Info.plist data, sandbox analysis, and app icons. Features a modern React webapp for browsing the collected data.

## 🌐 Live Browser

**[View the interactive macOS App Data Browser →](http://rreichel3.github.io/macOS-Data-Aggregator/)**

The webapp provides an intuitive interface to:
- Search and filter through macOS applications
- View app icons, metadata, and security information
- Browse SDEF files, entitlements, and sandbox details
- Get insights into code signing and sandboxing status

## What This Tool Collects

This tool performs comprehensive analysis of all macOS applications and collects:

### 📄 SDEF Files (Scripting Definitions)
XML-based files that define AppleScript interfaces for applications, specifying objects, commands, and properties for automation.

### 🔐 Code Signing Information
- Digital signature status and validity
- Signing authority and certificates
- Team identifiers and sealed resources
- Verification status

### 🛡️ Entitlements
- Security entitlements granted to applications
- Sandbox permissions and capabilities
- Hardened runtime settings
- Special privileges and access rights

### 📋 Info.plist Data
- Application metadata and configuration
- Bundle identifiers and version information
- Supported file types and URL schemes
- Application capabilities and requirements

### 🏗️ Sandbox Analysis
- App sandboxing status and type
- Security restrictions and permissions
- Hardened runtime analysis
- Library validation settings

## Features

- 🔍 **Comprehensive Discovery**: Finds all application bundles across the system
- 📱 **Complete Data Collection**: Gathers SDEF files, code signing, entitlements, Info.plist, sandbox data, and app icons
- 🎯 **Intelligent Organization**: Organizes data by application in a clean directory structure
- 🛡️ **Security Analysis**: Analyzes code signing, sandboxing, and security entitlements
- 🖼️ **Icon Extraction**: Extracts and converts app icons to PNG format
- 🌐 **Interactive Browser**: Modern React webapp for browsing collected data
- 📊 **Detailed Reporting**: Provides comprehensive analysis and statistics
- 🔄 **Conflict Handling**: Manages filename conflicts automatically
- ⚡ **Efficient Processing**: Uses system tools for optimal performance

## Usage

**⚠️ Important: The script requires sudo privileges to access system applications and code signing data.**

```bash
sudo python3 collect_sdef_files.py
```


## Output Structure

The script creates a `data/` directory with comprehensive application data:

```
data/
├── ApplicationName1/
│   ├── sdef/
│   │   ├── app_script_definition.sdef
│   │   └── additional_definitions.sdef
│   ├── codesign.txt          # Code signing information
│   ├── entitlements.plist    # Security entitlements
│   ├── info.plist           # Application metadata
│   ├── sandbox.txt          # Sandbox analysis
│   ├── icon.png             # App icon (if available)
│   └── manifest.json        # App summary for webapp
├── ApplicationName2/
│   ├── sdef/
│   ├── codesign.txt
│   ├── entitlements.plist
│   ├── info.plist
│   ├── sandbox.txt
│   ├── icon.png
│   └── manifest.json
└── ...
```

### File Descriptions

- **`sdef/`**: Directory containing all SDEF files for the application
- **`codesign.txt`**: Code signing status, authority, team identifier, and verification results
- **`entitlements.plist`**: Security entitlements and permissions in XML format
- **`info.plist`**: Application metadata, bundle information, and capabilities in JSON format
- **`sandbox.txt`**: Sandbox analysis including security restrictions and runtime settings
- **`icon.png`**: Application icon extracted and converted to PNG format (when available)
- **`manifest.json`**: JSON summary of application data for webapp consumption

## Search Locations

The script searches for applications in:

- `/Applications` (user applications)
- `/System/Applications` (system applications)
- `/System/Library/CoreServices` (core system services)
- `/Developer/Applications` (development tools)
- `~/Applications` (user-specific applications)
- `/Library/Application Support` (support applications)
- `/System/Library/Frameworks` (system frameworks with apps)

## Requirements

- macOS (tested on modern versions)
- Python 3.6+ (for Python script) or Bash (for shell script)
- Sudo privileges for accessing system applications and code signing data
- System tools: `codesign`, `plutil` (included with macOS)
- No external Python dependencies required

## Example Output

```
🔍 Starting macOS application data collection...
📂 Output directory: /path/to/sdef/data
🔍 Searching for application bundles...
📄 Found 245 application bundles

✅ Collection complete!
� Processed 245 applications
📄 Collected 67 SDEF files
📂 Output directory: /path/to/sdef/data

Directory structure created:
  📱 Safari/ (2 SDEF, 4 metadata files)
  📱 TextEdit/ (1 SDEF, 4 metadata files)
  📱 Terminal/ (1 SDEF, 4 metadata files)
  📱 Xcode/ (3 SDEF, 4 metadata files)
  ...

📊 Summary:
  • Each app directory contains:
    - sdef/ (SDEF files)
    - codesign.txt (code signing info)
    - entitlements.plist (app entitlements)
    - info.plist (app metadata)
    - sandbox.txt (sandbox analysis)
```

## GitHub Actions

This repository includes automated workflows to collect SDEF files on macOS runners:

### Daily Collection Workflow

- **File**: `.github/workflows/collect-sdef.yml`
- **Schedule**: Runs daily at 6:00 AM UTC
- **Function**: Automatically collects comprehensive application data and commits changes to main
- **Data Collected**: SDEF files, code signing info, entitlements, Info.plist, sandbox analysis
- **Tagging**: Creates/updates tags based on macOS version (e.g., `macos-14.5`)
- **Manual Trigger**: Can be manually triggered via GitHub Actions UI

### Release Workflow

- **File**: `.github/workflows/release-sdef.yml`
- **Trigger**: Manual only (workflow_dispatch)
- **Function**: Creates comprehensive releases with:
  - Complete application data archive
  - JSON manifest with collection metadata
  - Detailed release documentation
  - Versioned releases (v1.0.0, v1.1.0, etc.)
- **Data Included**: All SDEF files, code signing reports, entitlements, Info.plist files, sandbox analyses

### Workflow Features

- ✅ **Comprehensive Collection**: Collects SDEF files, code signing data, entitlements, Info.plist, and sandbox analysis
- 🏷️ **Smart Tagging**: Creates tags based on macOS version
- 📦 **Release Artifacts**: Generates downloadable archives with all application data
- 📊 **Detailed Reporting**: Provides collection statistics and change summaries
- 🔄 **Change Detection**: Only commits when application data actually changes
- 📝 **Rich Documentation**: Auto-generates release notes and manifests
- 🛡️ **Security Analysis**: Includes comprehensive security and sandbox analysis

### Permissions

The workflows require:
- `contents: write` - To commit files and create releases
- `actions: write` - To upload artifacts
