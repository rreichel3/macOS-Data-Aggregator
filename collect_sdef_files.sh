#!/bin/bash

# SDEF File Collector for macOS
# This script searches for all .sdef files and organizes them by application name
# 
# Note: This script requires sudo privileges to access system .sdef files.
# Usage: sudo ./collect_sdef_files.sh

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script requires sudo privileges to access system .sdef files."
    echo "Please run with: sudo ./collect_sdef_files.sh"
    exit 1
fi

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/data"

echo "🔍 Starting SDEF file collection..."
echo "📂 Output directory: $DATA_DIR"

# Create data directory
mkdir -p "$DATA_DIR"

# Function to get application name from sdef file
get_app_name() {
    local sdef_file="$1"
    local app_name=""
    
    # Try to extract from XML first
    if command -v xmllint >/dev/null 2>&1; then
        app_name=$(xmllint --xpath 'string(/dictionary/@title)' "$sdef_file" 2>/dev/null || true)
        if [[ -z "$app_name" ]]; then
            app_name=$(xmllint --xpath 'string(/suite/@name)' "$sdef_file" 2>/dev/null || true)
        fi
    fi
    
    # Fallback: extract from file path
    if [[ -z "$app_name" ]]; then
        # Look for .app in the path
        if [[ "$sdef_file" == *".app"* ]]; then
            app_name=$(echo "$sdef_file" | sed -E 's|.*/(.*\.app)/.*|\1|' | sed 's/\.app$//')
        else
            # Use parent directory name, skipping common directories
            local dir=$(dirname "$sdef_file")
            local parent=$(basename "$dir")
            case "$parent" in
                "ScriptingDefinitions"|"Resources"|"Contents"|"Library"|"System"|"Applications")
                    parent=$(basename "$(dirname "$dir")")
                    ;;
            esac
            app_name="$parent"
        fi
    fi
    
    # Clean up the name for directory use
    app_name=$(echo "$app_name" | sed 's/[<>:"/\\|?*]/_/g' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    
    # Default name if still empty
    if [[ -z "$app_name" ]]; then
        app_name="Unknown"
    fi
    
    echo "$app_name"
}

# Find all .sdef files
echo "🔍 Searching for .sdef files..."

# Search in common locations
SEARCH_PATHS=(
    "/System/Library/ScriptingDefinitions"
    "/Library/ScriptingDefinitions"
    "/Applications"
    "/System/Applications"
    "/Developer/Applications"
    "$HOME/Applications"
)

# Temporary file to store found files
TEMP_FILE=$(mktemp)
trap "rm -f $TEMP_FILE" EXIT

for search_path in "${SEARCH_PATHS[@]}"; do
    if [[ -d "$search_path" ]]; then
        echo "  📁 Searching in: $search_path"
        find "$search_path" -name "*.sdef" -type f 2>/dev/null >> "$TEMP_FILE" || true
    fi
done

# Remove duplicates and count files
sort -u "$TEMP_FILE" > "${TEMP_FILE}.sorted"
mv "${TEMP_FILE}.sorted" "$TEMP_FILE"

TOTAL_FILES=$(wc -l < "$TEMP_FILE" | tr -d ' ')
echo "📄 Found $TOTAL_FILES .sdef files"

if [[ "$TOTAL_FILES" -eq 0 ]]; then
    echo "❌ No .sdef files found!"
    exit 1
fi

# Copy files to organized structure
SUCCESS_COUNT=0

while IFS= read -r sdef_file; do
    if [[ -f "$sdef_file" ]]; then
        app_name=$(get_app_name "$sdef_file")
        app_dir="$DATA_DIR/$app_name"
        
        # Create application directory
        mkdir -p "$app_dir"
        
        # Get the original filename
        filename=$(basename "$sdef_file")
        dest_file="$app_dir/$filename"
        
        # Handle filename conflicts
        counter=1
        original_dest="$dest_file"
        while [[ -f "$dest_file" ]]; do
            name="${filename%.*}"
            ext="${filename##*.}"
            dest_file="$app_dir/${name}_${counter}.${ext}"
            ((counter++))
        done
        
        # Copy the file
        if cp "$sdef_file" "$dest_file"; then
            echo "  ✅ $sdef_file -> $dest_file"
            ((SUCCESS_COUNT++))
        else
            echo "  ❌ Failed to copy: $sdef_file"
        fi
    fi
done < "$TEMP_FILE"

echo ""
echo "🎉 Collection complete!"
echo "📊 Successfully copied $SUCCESS_COUNT out of $TOTAL_FILES .sdef files"
echo "📂 Files organized in: $DATA_DIR"

# Show directory structure
if [[ "$SUCCESS_COUNT" -gt 0 ]]; then
    echo ""
    echo "📁 Directory structure created:"
    for app_dir in "$DATA_DIR"/*; do
        if [[ -d "$app_dir" ]]; then
            app_name=$(basename "$app_dir")
            file_count=$(find "$app_dir" -name "*.sdef" | wc -l | tr -d ' ')
            echo "  📱 $app_name/ ($file_count file$([ "$file_count" -ne 1 ] && echo "s"))"
        fi
    done
fi
