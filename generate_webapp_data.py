#!/usr/bin/env python3
"""
Generate index.json for the webapp from the collected data.
"""

import json
import os
from pathlib import Path
from datetime import datetime

def generate_data_index():
    """Generate an index.json file for the webapp."""
    script_dir = Path(__file__).parent
    data_dir = script_dir / "data"
    webapp_data_dir = script_dir / "webapp" / "public" / "data"
    
    if not data_dir.exists():
        print("❌ Data directory not found. Run collect_macos_app_data.py first.")
        return False
    
    # Create webapp data directory
    webapp_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Get list of all app directories
    app_dirs = [d for d in data_dir.iterdir() if d.is_dir()]
    app_names = [d.name for d in app_dirs]
    
    # Copy all data to webapp public directory
    import shutil
    print(f"📁 Copying data for {len(app_dirs)} applications...")
    
    for app_dir in app_dirs:
        dest_dir = webapp_data_dir / app_dir.name
        if dest_dir.exists():
            shutil.rmtree(dest_dir)
        shutil.copytree(app_dir, dest_dir)
        
        # Generate SDEF file listing for each app
        sdef_dir = dest_dir / "sdef"
        if sdef_dir.exists():
            sdef_files = [f.name for f in sdef_dir.iterdir() if f.is_file() and f.suffix == '.sdef']
            sdef_index = {
                "files": sdef_files,
                "count": len(sdef_files)
            }
            
            # Write SDEF index
            with open(dest_dir / "sdef_index.json", 'w') as f:
                json.dump(sdef_index, f, indent=2)
    
    # Generate index
    index_data = {
        "generated": datetime.now().isoformat(),
        "total_apps": len(app_names),
        "apps": sorted(app_names)
    }
    
    # Write index to webapp public directory
    index_file = webapp_data_dir / "index.json"
    with open(index_file, 'w') as f:
        json.dump(index_data, f, indent=2)
    
    print(f"✅ Generated index.json with {len(app_names)} applications")
    print(f"📁 Data copied to: {webapp_data_dir}")
    
    return True

if __name__ == "__main__":
    generate_data_index()
