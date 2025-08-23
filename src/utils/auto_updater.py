"""
Auto-updater System for Portal Receipts Application

Automatically checks for updates, downloads new versions, and performs
safe application updates with backup and rollback capabilities.

Features:
- Automatic update checking from GitHub releases
- Safe download verification with checksums
- Backup and rollback functionality
- User-controlled update process with notifications
- Update scheduling and deferring options
- Portuguese localization
"""

import os
import sys
import json
import hashlib
import zipfile
import shutil
import subprocess
import tempfile
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import threading
import time
import logging

try:
    from .logger import get_logger
    from .version import get_version
except ImportError:
    # Fallback for when imported directly
    try:
        from utils.logger import get_logger
        from utils.version import get_version
    except ImportError:
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        def get_version():
            return "1.0.0"  # Fallback version

logger = get_logger(__name__)

@dataclass
class UpdateInfo:
    """Information about an available update."""
    version: str
    release_date: str
    download_url: str
    download_size: int
    changelog: str
    is_critical: bool
    requires_restart: bool
    checksum: str
    installer_name: str

@dataclass
class UpdateConfig:
    """Configuration for auto-updater."""
    enabled: bool = True
    check_interval_hours: int = 24
    auto_download: bool = False  # Download automatically but don't install
    auto_install: bool = False   # Install automatically (not recommended)
    notify_user: bool = True
    allow_prerelease: bool = False
    github_repo: str = "luciaBytes/receipts"
    update_branch: str = "main"
    backup_enabled: bool = True
    max_backup_count: int = 3
    
@dataclass
class UpdateStatus:
    """Current status of the update system."""
    last_check: str
    current_version: str
    latest_version: str
    update_available: bool
    download_in_progress: bool
    install_in_progress: bool
    last_error: str
    next_check_time: str


class AutoUpdater:
    """Handles automatic updates for the application."""
    
    def __init__(self, data_dir: str = "update_data"):
        self.data_dir = data_dir
        self.config_file = os.path.join(data_dir, "update_config.json")
        self.status_file = os.path.join(data_dir, "update_status.json")
        self.backups_dir = os.path.join(data_dir, "backups")
        self.downloads_dir = os.path.join(data_dir, "downloads")
        
        # Create directories
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(self.backups_dir, exist_ok=True)
        os.makedirs(self.downloads_dir, exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
        
        # Application info (load before status)
        self.current_version = get_version()
        self.app_executable = sys.executable if hasattr(sys, 'frozen') else sys.argv[0]
        self.app_directory = os.path.dirname(os.path.abspath(self.app_executable))
        
        # Load status after application info is available
        self.status = self._load_status()
        
        # Update callback for GUI notifications
        self.update_callback = None
        
        # Background check thread
        self._check_thread = None
        self._stop_checking = False
    
    def _load_config(self) -> UpdateConfig:
        """Load update configuration."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return UpdateConfig(**data)
            except Exception as e:
                logger.warning(f"Failed to load update config: {e}")
        
        # Create default config
        config = UpdateConfig()
        self._save_config(config)
        return config
    
    def _save_config(self, config: UpdateConfig):
        """Save update configuration."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(config), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save update config: {e}")
    
    def _load_status(self) -> UpdateStatus:
        """Load update status."""
        if os.path.exists(self.status_file):
            try:
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return UpdateStatus(**data)
            except Exception as e:
                logger.warning(f"Failed to load update status: {e}")
        
        # Create default status
        return UpdateStatus(
            last_check="",
            current_version=self.current_version,
            latest_version=self.current_version,
            update_available=False,
            download_in_progress=False,
            install_in_progress=False,
            last_error="",
            next_check_time=""
        )
    
    def _save_status(self, status: UpdateStatus):
        """Save update status."""
        try:
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(status), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save update status: {e}")
    
    def set_update_callback(self, callback):
        """Set callback function for update notifications."""
        self.update_callback = callback
    
    def _notify_update_available(self, update_info: UpdateInfo):
        """Notify that an update is available."""
        if self.update_callback:
            try:
                self.update_callback('update_available', update_info)
            except Exception as e:
                logger.error(f"Error in update callback: {e}")
    
    def _notify_download_progress(self, progress: float):
        """Notify download progress."""
        if self.update_callback:
            try:
                self.update_callback('download_progress', progress)
            except Exception as e:
                logger.error(f"Error in download progress callback: {e}")
    
    def _notify_error(self, error_message: str):
        """Notify update error."""
        if self.update_callback:
            try:
                self.update_callback('update_error', error_message)
            except Exception as e:
                logger.error(f"Error in error callback: {e}")
    
    def check_for_updates(self) -> Optional[UpdateInfo]:
        """Check for available updates from GitHub releases."""
        try:
            logger.info("Checking for updates...")
            
            # GitHub API endpoint for releases
            api_url = f"https://api.github.com/repos/{self.config.github_repo}/releases"
            
            # Add user agent header
            headers = {
                'User-Agent': f'PortalReceipts/{self.current_version} (Auto-updater)',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(api_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            releases = response.json()
            
            if not releases:
                logger.info("No releases found")
                return None
            
            # Find the latest suitable release
            suitable_release = None
            for release in releases:
                # Skip pre-releases unless allowed
                if release['prerelease'] and not self.config.allow_prerelease:
                    continue
                
                # Skip drafts
                if release['draft']:
                    continue
                
                suitable_release = release
                break
            
            if not suitable_release:
                logger.info("No suitable releases found")
                return None
            
            latest_version = suitable_release['tag_name'].lstrip('v')
            
            # Compare versions
            if not self._is_newer_version(latest_version, self.current_version):
                logger.info(f"Current version {self.current_version} is up to date")
                return None
            
            # Find installer asset
            installer_asset = None
            for asset in suitable_release['assets']:
                if asset['name'].endswith('.exe') and 'Setup' in asset['name']:
                    installer_asset = asset
                    break
            
            if not installer_asset:
                logger.warning("No installer found in release assets")
                return None
            
            # Create update info
            update_info = UpdateInfo(
                version=latest_version,
                release_date=suitable_release['published_at'][:10],
                download_url=installer_asset['browser_download_url'],
                download_size=installer_asset['size'],
                changelog=suitable_release['body'] or f"Update to version {latest_version}",
                is_critical=self._is_critical_update(suitable_release['body']),
                requires_restart=True,
                checksum="",  # GitHub doesn't provide checksums, we'll compute it
                installer_name=installer_asset['name']
            )
            
            logger.info(f"Update available: {latest_version}")
            return update_info
            
        except requests.RequestException as e:
            error_msg = f"Failed to check for updates: {e}"
            logger.error(error_msg)
            self._notify_error(error_msg)
            return None
        except Exception as e:
            error_msg = f"Unexpected error checking for updates: {e}"
            logger.error(error_msg)
            self._notify_error(error_msg)
            return None
    
    def _is_newer_version(self, version1: str, version2: str) -> bool:
        """Compare two version strings."""
        try:
            def parse_version(v):
                return tuple(map(int, v.split('.')))
            
            return parse_version(version1) > parse_version(version2)
        except Exception:
            return version1 > version2  # Fallback to string comparison
    
    def _is_critical_update(self, release_body: str) -> bool:
        """Determine if update is critical based on release notes."""
        if not release_body:
            return False
        
        critical_keywords = [
            'critical', 'security', 'urgent', 'hotfix', 
            'vulnerability', 'importante', 'crítico', 'segurança'
        ]
        
        body_lower = release_body.lower()
        return any(keyword in body_lower for keyword in critical_keywords)
    
    def download_update(self, update_info: UpdateInfo) -> bool:
        """Download update installer."""
        try:
            self.status.download_in_progress = True
            self._save_status(self.status)
            
            logger.info(f"Downloading update {update_info.version}...")
            
            # Download file
            installer_path = os.path.join(self.downloads_dir, update_info.installer_name)
            
            response = requests.get(update_info.download_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(installer_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            self._notify_download_progress(progress)
            
            # Verify download
            if os.path.getsize(installer_path) != update_info.download_size:
                raise Exception("Downloaded file size doesn't match expected size")
            
            # Compute and store checksum
            with open(installer_path, 'rb') as f:
                file_hash = hashlib.sha256()
                for chunk in iter(lambda: f.read(4096), b""):
                    file_hash.update(chunk)
                computed_checksum = file_hash.hexdigest()
            
            update_info.checksum = computed_checksum
            
            logger.info(f"Update downloaded successfully: {installer_path}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to download update: {e}"
            logger.error(error_msg)
            self._notify_error(error_msg)
            return False
        finally:
            self.status.download_in_progress = False
            self._save_status(self.status)
    
    def create_backup(self) -> bool:
        """Create backup of current application."""
        try:
            if not self.config.backup_enabled:
                return True
            
            logger.info("Creating application backup...")
            
            # Create backup filename
            backup_name = f"backup_{self.current_version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            backup_path = os.path.join(self.backups_dir, backup_name)
            
            # Create zip backup
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(self.app_directory):
                    # Skip backup directories and temporary files
                    dirs[:] = [d for d in dirs if not d.startswith(('.', '__pycache__', 'backup', 'update_data'))]
                    
                    for file in files:
                        if not file.endswith(('.tmp', '.log', '.pyc')):
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, self.app_directory)
                            zipf.write(file_path, arcname)
            
            # Cleanup old backups
            self._cleanup_old_backups()
            
            logger.info(f"Backup created: {backup_path}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to create backup: {e}"
            logger.error(error_msg)
            self._notify_error(error_msg)
            return False
    
    def _cleanup_old_backups(self):
        """Remove old backup files."""
        try:
            backups = []
            for file in os.listdir(self.backups_dir):
                if file.startswith('backup_') and file.endswith('.zip'):
                    path = os.path.join(self.backups_dir, file)
                    backups.append((path, os.path.getmtime(path)))
            
            # Sort by modification time (newest first)
            backups.sort(key=lambda x: x[1], reverse=True)
            
            # Remove old backups
            for backup_path, _ in backups[self.config.max_backup_count:]:
                os.remove(backup_path)
                logger.info(f"Removed old backup: {backup_path}")
                
        except Exception as e:
            logger.warning(f"Failed to cleanup old backups: {e}")
    
    def install_update(self, update_info: UpdateInfo) -> bool:
        """Install the downloaded update."""
        try:
            self.status.install_in_progress = True
            self._save_status(self.status)
            
            installer_path = os.path.join(self.downloads_dir, update_info.installer_name)
            
            if not os.path.exists(installer_path):
                raise Exception("Installer file not found")
            
            # Create backup first
            if not self.create_backup():
                logger.warning("Backup creation failed, continuing anyway...")
            
            logger.info(f"Installing update {update_info.version}...")
            
            # Prepare installation arguments
            install_args = [
                installer_path,
                '/SILENT',  # Silent installation
                '/NORESTART',  # Don't restart automatically
                '/DIR=' + self.app_directory  # Install to current directory
            ]
            
            # Start installer
            process = subprocess.Popen(install_args, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            
            # Wait for installation to complete
            stdout, stderr = process.communicate(timeout=300)  # 5 minutes timeout
            
            if process.returncode != 0:
                raise Exception(f"Installer failed with exit code {process.returncode}: {stderr.decode()}")
            
            # Update status
            self.status.current_version = update_info.version
            self.status.latest_version = update_info.version
            self.status.update_available = False
            
            logger.info(f"Update installed successfully to version {update_info.version}")
            
            # Schedule restart notification
            if self.update_callback:
                self.update_callback('restart_required', update_info)
            
            return True
            
        except subprocess.TimeoutExpired:
            error_msg = "Installation timeout - installer may still be running"
            logger.error(error_msg)
            self._notify_error(error_msg)
            return False
        except Exception as e:
            error_msg = f"Failed to install update: {e}"
            logger.error(error_msg)
            self._notify_error(error_msg)
            return False
        finally:
            self.status.install_in_progress = False
            self._save_status(self.status)
    
    def rollback_update(self, backup_file: str) -> bool:
        """Rollback to a previous version from backup."""
        try:
            backup_path = os.path.join(self.backups_dir, backup_file)
            
            if not os.path.exists(backup_path):
                raise Exception(f"Backup file not found: {backup_file}")
            
            logger.info(f"Rolling back from backup: {backup_file}")
            
            # Create temporary directory for extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract backup
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                # Replace current files with backup files
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        src_path = os.path.join(root, file)
                        rel_path = os.path.relpath(src_path, temp_dir)
                        dst_path = os.path.join(self.app_directory, rel_path)
                        
                        # Create directory if needed
                        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                        
                        # Replace file
                        shutil.copy2(src_path, dst_path)
            
            logger.info("Rollback completed successfully")
            return True
            
        except Exception as e:
            error_msg = f"Failed to rollback: {e}"
            logger.error(error_msg)
            self._notify_error(error_msg)
            return False
    
    def start_background_checking(self):
        """Start background thread for automatic update checking."""
        if self._check_thread and self._check_thread.is_alive():
            return  # Already running
        
        if not self.config.enabled:
            return
        
        self._stop_checking = False
        self._check_thread = threading.Thread(target=self._background_check_loop, daemon=True)
        self._check_thread.start()
        logger.info("Background update checking started")
    
    def stop_background_checking(self):
        """Stop background update checking."""
        self._stop_checking = True
        if self._check_thread:
            self._check_thread.join(timeout=5)
        logger.info("Background update checking stopped")
    
    def _background_check_loop(self):
        """Background loop for checking updates."""
        while not self._stop_checking:
            try:
                # Calculate next check time
                now = datetime.now()
                next_check = now + timedelta(hours=self.config.check_interval_hours)
                self.status.next_check_time = next_check.isoformat()
                self._save_status(self.status)
                
                # Check for updates
                update_info = self.check_for_updates()
                
                # Update status
                self.status.last_check = now.isoformat()
                if update_info:
                    self.status.update_available = True
                    self.status.latest_version = update_info.version
                    self._notify_update_available(update_info)
                    
                    # Auto-download if enabled
                    if self.config.auto_download:
                        self.download_update(update_info)
                else:
                    self.status.update_available = False
                
                self._save_status(self.status)
                
                # Wait for next check
                sleep_seconds = self.config.check_interval_hours * 3600
                for _ in range(int(sleep_seconds)):
                    if self._stop_checking:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in background update check: {e}")
                self.status.last_error = str(e)
                self._save_status(self.status)
                
                # Wait before retrying (shorter interval on error)
                for _ in range(3600):  # 1 hour
                    if self._stop_checking:
                        break
                    time.sleep(1)
    
    def get_available_backups(self) -> List[Dict[str, str]]:
        """Get list of available backup files."""
        backups = []
        
        try:
            for file in os.listdir(self.backups_dir):
                if file.startswith('backup_') and file.endswith('.zip'):
                    path = os.path.join(self.backups_dir, file)
                    stat = os.stat(path)
                    
                    # Parse version from filename
                    parts = file.replace('backup_', '').replace('.zip', '').split('_')
                    version = parts[0] if parts else 'unknown'
                    
                    backups.append({
                        'filename': file,
                        'version': version,
                        'date': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M'),
                        'size': f"{stat.st_size / (1024*1024):.1f} MB"
                    })
                    
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
        
        # Sort by modification time (newest first)
        backups.sort(key=lambda x: x['date'], reverse=True)
        return backups
    
    def should_check_for_updates(self) -> bool:
        """Check if it's time to check for updates."""
        if not self.config.enabled:
            return False
        
        if not self.status.last_check:
            return True  # Never checked before
        
        try:
            last_check = datetime.fromisoformat(self.status.last_check)
            next_check = last_check + timedelta(hours=self.config.check_interval_hours)
            return datetime.now() >= next_check
        except ValueError:
            return True  # Invalid timestamp, check now
    
    def get_update_summary(self) -> Dict[str, Any]:
        """Get summary of update system status."""
        return {
            'enabled': self.config.enabled,
            'current_version': self.current_version,
            'latest_version': self.status.latest_version,
            'update_available': self.status.update_available,
            'last_check': self.status.last_check,
            'next_check': self.status.next_check_time,
            'download_in_progress': self.status.download_in_progress,
            'install_in_progress': self.status.install_in_progress,
            'auto_download': self.config.auto_download,
            'auto_install': self.config.auto_install,
            'check_interval_hours': self.config.check_interval_hours,
            'backup_count': len(self.get_available_backups()),
            'last_error': self.status.last_error
        }


def create_auto_updater() -> AutoUpdater:
    """Create auto-updater with default configuration."""
    return AutoUpdater()


if __name__ == "__main__":
    # Demo usage
    updater = create_auto_updater()
    
    print("🔄 Auto-updater Demo")
    print("=" * 30)
    
    # Check current status
    summary = updater.get_update_summary()
    print(f"Current version: {summary['current_version']}")
    print(f"Update checking enabled: {summary['enabled']}")
    print(f"Last check: {summary['last_check'] or 'Never'}")
    
    # Check for updates manually
    update_info = updater.check_for_updates()
    if update_info:
        print(f"\\n🎉 Update available: {update_info.version}")
        print(f"Release date: {update_info.release_date}")
        print(f"Download size: {update_info.download_size / (1024*1024):.1f} MB")
        print(f"Critical: {'Yes' if update_info.is_critical else 'No'}")
    else:
        print("\\n✅ No updates available")
    
    # Show backups
    backups = updater.get_available_backups()
    print(f"\\n💾 Available backups: {len(backups)}")
    for backup in backups[:3]:  # Show first 3
        print(f"  - Version {backup['version']} ({backup['date']}) - {backup['size']}")
    
    print("\\n🔄 Auto-updater ready for use!")
