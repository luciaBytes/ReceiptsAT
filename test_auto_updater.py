"""Test script for auto-updater functionality."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from src.utils.auto_updater import create_auto_updater
    
    print("🔄 Testing Auto-updater System")
    print("=" * 35)
    
    # Create auto-updater
    updater = create_auto_updater()
    print("✅ Auto-updater created successfully")
    
    # Get system summary
    summary = updater.get_update_summary()
    print(f"✅ Current version: {summary['current_version']}")
    print(f"✅ System enabled: {summary['enabled']}")
    print(f"✅ Check interval: {summary['check_interval_hours']} hours")
    print(f"✅ Auto-download: {summary['auto_download']}")
    print(f"✅ Backup enabled: {summary.get('backup_count', 0)} backups available")
    
    # Test configuration
    print(f"✅ GitHub repo: {updater.config.github_repo}")
    print(f"✅ Data directory: {updater.data_dir}")
    
    print("\n🎉 Auto-updater system ready!")
    
except Exception as e:
    print(f"❌ Error testing auto-updater: {e}")
    import traceback
    traceback.print_exc()
