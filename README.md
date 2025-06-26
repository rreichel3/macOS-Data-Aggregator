# sdef
SDEF Aggregator

[![Collect SDEF Files](https://github.com/rreichel3/sdef/actions/workflows/collect-sdef.yml/badge.svg)](https://github.com/rreichel3/sdef/actions/workflows/collect-sdef.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![macOS](https://img.shields.io/badge/macOS-10.15+-blue.svg)](https://www.apple.com/macos/)
[![Python](https://img.shields.io/badge/Python-3.6+-green.svg)](https://www.python.org/)

A collection tool for gathering and organizing all `.sdef` (Scripting Definition) files on macOS systems.

## What are SDEF files?

SDEF files are XML-based Scripting Definition files used by macOS applications to define their AppleScript interfaces. They describe the objects, commands, and properties that can be controlled via AppleScript or JavaScript for Automation.

## Features

- 🔍 Automatically finds all `.sdef` files on your Mac
- 📱 Organizes files by application name in a clean directory structure
- 🎯 Searches common locations including application bundles
- 🛡️ Handles permission errors gracefully
- 📊 Provides detailed progress and summary information
- 🔄 Handles filename conflicts automatically

## Usage

**⚠️ Important: Both scripts require sudo privileges to access system .sdef files.**

You can run either the Python script or the shell script - both do the same thing:

### Option 1: Python Script (Recommended)

```bash
sudo python3 collect_sdef_files.py
```

### Option 2: Shell Script

```bash
sudo ./collect_sdef_files.sh
```

## Output Structure

The script creates a `data/` directory with the following structure:

```
data/
├── ApplicationName1/
│   ├── original_sdef_file1.sdef
│   └── original_sdef_file2.sdef
├── ApplicationName2/
│   └── original_sdef_file.sdef
└── ...
```

## Search Locations

The script searches for `.sdef` files in:

- `/System/Library/ScriptingDefinitions`
- `/Library/ScriptingDefinitions`
- `/Applications` (and inside .app bundles)
- `/System/Applications`
- `/Developer/Applications`
- `~/Applications`

## Requirements

- macOS (tested on modern versions)
- Python 3.6+ (for Python script) or Bash (for shell script)
- No external dependencies required

## Example Output

```
🔍 Starting SDEF file collection...
📂 Output directory: /path/to/sdef/data
🔍 Searching for .sdef files...
📄 Found 45 .sdef files

✅ Collection complete!
📊 Successfully copied 45 out of 45 .sdef files
📂 Files organized in: /path/to/sdef/data

📁 Directory structure created:
  📱 Finder/ (1 file)
  📱 Safari/ (1 file)
  📱 TextEdit/ (1 file)
  📱 Terminal/ (1 file)
  ...
```

## GitHub Actions

This repository includes automated workflows to collect SDEF files on macOS runners:

### Daily Collection Workflow

- **File**: `.github/workflows/collect-sdef.yml`
- **Schedule**: Runs daily at 6:00 AM UTC
- **Function**: Automatically collects SDEF files and commits changes to main
- **Tagging**: Creates/updates tags based on macOS version (e.g., `macos-14.5`)
- **Manual Trigger**: Can be manually triggered via GitHub Actions UI

### Release Workflow

- **File**: `.github/workflows/release-sdef.yml`
- **Trigger**: Manual only (workflow_dispatch)
- **Function**: Creates comprehensive releases with:
  - Complete SDEF file archive
  - JSON manifest with collection metadata
  - Detailed release documentation
  - Versioned releases (v1.0.0, v1.1.0, etc.)

### Workflow Features

- ✅ **Automated Collection**: Runs on GitHub's macOS runners with sudo privileges
- 🏷️ **Smart Tagging**: Creates tags based on macOS version
- 📦 **Release Artifacts**: Generates downloadable archives
- 📊 **Detailed Reporting**: Provides collection statistics and summaries
- 🔄 **Change Detection**: Only commits when files actually change
- 📝 **Rich Documentation**: Auto-generates release notes and manifests

### Permissions

The workflows require:
- `contents: write` - To commit files and create releases
- `actions: write` - To upload artifacts
