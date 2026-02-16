#!/usr/bin/env python
"""
Post-build script for PyInstaller
Copies necessary resource files to the dist directory after PyInstaller build
"""

import os
import shutil
from pathlib import Path

def post_build():
    """Copy resource files after PyInstaller build"""
    
    # Define paths
    dist_dir = Path("dist/sisPROJETOS")
    src_resources = Path("src/resources")
    
    # Ensure dist directory exists
    if not dist_dir.exists():
        print(f"❌ Distribution directory not found: {dist_dir}")
        return False
    
    print(f"📦 Post-build: Copying resources...")
    
    try:
        # Create resources directory in dist
        resources_dir = dist_dir / "resources"
        resources_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy templates
        templates_src = src_resources / "templates"
        templates_dst = resources_dir / "templates"
        
        if templates_src.exists():
            if templates_dst.exists():
                shutil.rmtree(templates_dst)
            shutil.copytree(templates_src, templates_dst)
            print(f"✅ Copied templates to {templates_dst}")
        else:
            print(f"⚠️  Templates directory not found: {templates_src}")
            return False
        
        # Copy database if needed
        db_src = src_resources / "sisprojetos.db"
        db_dst = resources_dir / "sisprojetos.db"
        
        if db_src.exists():
            shutil.copy2(db_src, db_dst)
            print(f"✅ Copied database to {db_dst}")
        
        print("✅ Post-build: All resources copied successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Post-build error: {e}")
        return False

if __name__ == "__main__":
    success = post_build()
    exit(0 if success else 1)
