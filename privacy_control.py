"""
Receipt Database Privacy & Data Control Guide

This script provides utilities for managing your sensitive receipt data
including viewing storage location, data cleanup, and privacy controls.
"""

import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.receipt_database import ReceiptDatabase


def show_data_location():
    """Show where your sensitive data is stored."""
    print("🔒 RECEIPT DATABASE PRIVACY INFORMATION")
    print("=" * 60)
    
    # Create database instance to show location
    db = ReceiptDatabase()
    db_path = os.path.abspath(db.db_path)
    
    print(f"\n📍 Database Location:")
    print(f"   {db_path}")
    
    if os.path.exists(db_path):
        file_size = os.path.getsize(db_path)
        print(f"   📊 File size: {file_size:,} bytes")
        
        # Get record count
        stats = db.get_statistics()
        record_count = stats.get('total_receipts', 0)
        print(f"   📋 Records stored: {record_count:,}")
    else:
        print(f"   📝 Database not yet created (will be created on first use)")
    
    print(f"\n🛡️ Privacy Status:")
    print(f"   ✅ Local storage only (no cloud/remote access)")
    print(f"   ✅ Protected by .gitignore (never shared via Git)")
    print(f"   ✅ Standard file system permissions apply")
    print(f"   ✅ No automatic backups or sharing")


def show_data_content_summary():
    """Show summary of what data is stored (without revealing actual data)."""
    print("\n📊 DATA CONTENT SUMMARY")
    print("=" * 40)
    
    try:
        db = ReceiptDatabase()
        
        if not os.path.exists(db.db_path):
            print("   📝 No data stored yet")
            return
        
        stats = db.get_statistics()
        
        print(f"   Total receipts: {stats.get('total_receipts', 0):,}")
        print(f"   Unique contracts: {stats.get('unique_contracts', 0):,}")
        print(f"   Date range: {stats.get('earliest_receipt', 'N/A')[:10]} to {stats.get('latest_receipt', 'N/A')[:10]}")
        
        # Status breakdown without revealing specifics
        status_breakdown = stats.get('status_breakdown', {})
        if status_breakdown:
            print(f"   Processing results:")
            for status, count in status_breakdown.items():
                print(f"      • {status}: {count:,}")
        
    except Exception as e:
        print(f"   ❌ Error accessing database: {e}")


def clear_all_data():
    """Safely clear all stored receipt data."""
    print("\n🗑️ DATA CLEARING UTILITY")
    print("=" * 40)
    
    try:
        db = ReceiptDatabase()
        
        if not os.path.exists(db.db_path):
            print("   📝 No database file exists - nothing to clear")
            return
        
        stats = db.get_statistics()
        record_count = stats.get('total_receipts', 0)
        
        if record_count == 0:
            print("   📝 Database is empty - nothing to clear")
            return
        
        print(f"   ⚠️  Found {record_count:,} receipt records")
        print(f"   📍 Database location: {os.path.abspath(db.db_path)}")
        
        response = input("\n   Do you want to permanently delete all receipt data? (yes/no): ")
        
        if response.lower() in ['yes', 'y']:
            deleted_count = db.clear_all_receipts()
            print(f"   ✅ Deleted {deleted_count:,} receipt records")
            print(f"   🧹 Database cleared successfully")
        else:
            print(f"   ✋ Operation cancelled - data preserved")
            
    except Exception as e:
        print(f"   ❌ Error during data clearing: {e}")


def delete_database_file():
    """Completely remove the database file."""
    print("\n🗑️ DATABASE FILE DELETION")
    print("=" * 40)
    
    try:
        db = ReceiptDatabase()
        db_path = os.path.abspath(db.db_path)
        
        if not os.path.exists(db_path):
            print("   📝 No database file exists")
            return
        
        file_size = os.path.getsize(db_path)
        print(f"   📍 Database file: {db_path}")
        print(f"   📊 File size: {file_size:,} bytes")
        
        response = input("\n   Do you want to completely delete the database file? (yes/no): ")
        
        if response.lower() in ['yes', 'y']:
            os.remove(db_path)
            print(f"   ✅ Database file deleted successfully")
            print(f"   🔄 New database will be created on next use")
        else:
            print(f"   ✋ Operation cancelled - file preserved")
            
    except Exception as e:
        print(f"   ❌ Error during file deletion: {e}")


def show_privacy_recommendations():
    """Show privacy best practices."""
    print("\n🛡️ PRIVACY RECOMMENDATIONS")
    print("=" * 40)
    print("   1. ✅ Database is already excluded from Git (.gitignore)")
    print("   2. 🔄 Regularly clear old data if not needed")
    print("   3. 🗂️  Consider manual backups to encrypted storage if needed")
    print("   4. 🔒 Ensure your computer has proper access controls")
    print("   5. 💾 Database uses standard SQLite format (widely supported)")
    print("   6. 🚫 Never share the logs/ directory or .db files")
    print("   7. ⚠️  Be cautious when exporting CSV files")


def main():
    """Main privacy and data control interface."""
    print("🔐 RECEIPT DATABASE PRIVACY & DATA CONTROL")
    print("=" * 80)
    print("This utility helps you understand and control your sensitive receipt data.")
    print("All data is stored locally and never shared automatically.")
    print("=" * 80)
    
    while True:
        print("\nOptions:")
        print("1. 📍 Show data storage location")
        print("2. 📊 Show data summary (no sensitive details)")
        print("3. 🗑️  Clear all receipt data")
        print("4. 🗑️  Delete entire database file")
        print("5. 🛡️  Show privacy recommendations")
        print("6. ❌ Exit")
        
        try:
            choice = input("\nSelect option (1-6): ").strip()
            
            if choice == '1':
                show_data_location()
            elif choice == '2':
                show_data_content_summary()
            elif choice == '3':
                clear_all_data()
            elif choice == '4':
                delete_database_file()
            elif choice == '5':
                show_privacy_recommendations()
            elif choice == '6':
                print("\n👋 Goodbye!")
                break
            else:
                print("   ❌ Invalid option. Please select 1-6.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"   ❌ Error: {e}")


if __name__ == "__main__":
    main()
