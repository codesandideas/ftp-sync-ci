#!/usr/bin/env python3
"""
Standalone FTP/SFTP File Sync Tool
Watches local directories and syncs changes to remote server
"""

import os
import sys
import time
import json
import stat
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Set, Optional
import logging

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("Error: watchdog library not found. Install it with: pip install watchdog")
    sys.exit(1)

try:
    import paramiko
    from paramiko import SSHClient, AutoAddPolicy
except ImportError:
    print("Error: paramiko library not found. Install it with: pip install paramiko")
    sys.exit(1)

try:
    from ftplib import FTP, FTP_TLS
except ImportError:
    print("Error: ftplib not available")
    sys.exit(1)


class Config:
    """Configuration management"""
    
    @staticmethod
    def load(config_path: str) -> dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Configuration file not found: {config_path}")
            Config.create_example(config_path)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in configuration file: {e}")
            sys.exit(1)
    
    @staticmethod
    def create_example(config_path: str):
        """Create example configuration file"""
        example_config = {
            "protocol": "sftp",  # or "ftp", "ftps"
            "host": "example.com",
            "port": 22,  # 22 for SFTP, 21 for FTP
            "username": "your_username",
            "password": "your_password",  # or use key_file for SFTP
            "key_file": "",  # path to SSH private key (optional for SFTP)
            "local_path": "/path/to/local/project",
            "remote_path": "/path/to/remote/project",
            "ignore_patterns": [
                ".git",
                "node_modules",
                "__pycache__",
                "*.pyc",
                ".DS_Store",
                ".vscode",
                ".idea"
            ],
            "auto_create_dirs": True,
            "passive_mode": True,  # for FTP
            "auto_upload": True,  # auto-upload on file changes
            "auto_delete": True,  # auto-delete remote file when local is deleted
            "sync_on_start": False  # sync all files on startup
        }
        
        try:
            with open(config_path, 'w') as f:
                json.dump(example_config, f, indent=2)
            print(f"Created example configuration at: {config_path}")
            print("Please edit this file with your settings and run again.")
        except Exception as e:
            print(f"Could not create example config: {e}")


class SFTPUploader:
    """SFTP connection handler"""
    
    def __init__(self, config: dict):
        self.config = config
        self.ssh = None
        self.sftp = None
        self.connect()
    
    def connect(self):
        """Establish SFTP connection"""
        try:
            self.ssh = SSHClient()
            self.ssh.set_missing_host_key_policy(AutoAddPolicy())
            
            connect_kwargs = {
                'hostname': self.config['host'],
                'port': self.config.get('port', 22),
                'username': self.config['username']
            }
            
            if self.config.get('key_file'):
                connect_kwargs['key_filename'] = self.config['key_file']
            else:
                connect_kwargs['password'] = self.config['password']
            
            self.ssh.connect(**connect_kwargs)
            self.sftp = self.ssh.open_sftp()
            logging.info(f"Connected to SFTP server: {self.config['host']}")
            
        except Exception as e:
            logging.error(f"SFTP connection failed: {e}")
            raise
    
    def upload(self, local_path: str, remote_path: str) -> bool:
        """Upload file to remote server"""
        try:
            # Create remote directory if needed
            if self.config.get('auto_create_dirs', True):
                self._ensure_remote_dir(os.path.dirname(remote_path))
            
            self.sftp.put(local_path, remote_path)
            return True
        except Exception as e:
            logging.error(f"Upload failed for {local_path}: {e}")
            return False
    
    def delete(self, remote_path: str) -> bool:
        """Delete file from remote server"""
        try:
            self.sftp.remove(remote_path)
            return True
        except FileNotFoundError:
            return True  # Already deleted
        except Exception as e:
            logging.error(f"Delete failed for {remote_path}: {e}")
            return False
    
    def _ensure_remote_dir(self, remote_dir: str):
        """Create remote directory if it doesn't exist"""
        dirs = []
        while remote_dir and remote_dir != '/':
            dirs.append(remote_dir)
            remote_dir = os.path.dirname(remote_dir)
        
        dirs.reverse()
        for d in dirs:
            try:
                self.sftp.stat(d)
            except FileNotFoundError:
                try:
                    self.sftp.mkdir(d)
                except Exception as e:
                    logging.warning(f"Could not create directory {d}: {e}")
    
    def download(self, remote_path: str, local_path: str) -> bool:
        """Download file from remote server"""
        try:
            local_dir = os.path.dirname(local_path)
            if local_dir:
                os.makedirs(local_dir, exist_ok=True)
            self.sftp.get(remote_path, local_path)
            return True
        except Exception as e:
            logging.error(f"Download failed for {remote_path}: {e}")
            return False

    def walk_remote(self, remote_path: str):
        """Recursively yield all file paths under remote_path"""
        try:
            for entry in self.sftp.listdir_attr(remote_path):
                if entry.filename in ('.', '..'):
                    continue
                full_path = remote_path.rstrip('/') + '/' + entry.filename
                if stat.S_ISDIR(entry.st_mode):
                    yield from self.walk_remote(full_path)
                else:
                    yield full_path
        except Exception as e:
            logging.error(f"Failed to list remote directory {remote_path}: {e}")

    def close(self):
        """Close connection"""
        if self.sftp:
            self.sftp.close()
        if self.ssh:
            self.ssh.close()
        logging.info("SFTP connection closed")


class FTPUploader:
    """FTP/FTPS connection handler"""
    
    def __init__(self, config: dict):
        self.config = config
        self.ftp = None
        self.connect()
    
    def connect(self):
        """Establish FTP connection"""
        try:
            protocol = self.config.get('protocol', 'ftp')
            
            if protocol == 'ftps':
                self.ftp = FTP_TLS()
            else:
                self.ftp = FTP()
            
            self.ftp.connect(
                self.config['host'],
                self.config.get('port', 21)
            )
            
            self.ftp.login(
                self.config['username'],
                self.config['password']
            )
            
            if protocol == 'ftps':
                self.ftp.prot_p()
            
            if self.config.get('passive_mode', True):
                self.ftp.set_pasv(True)
            
            logging.info(f"Connected to FTP server: {self.config['host']}")
            
        except Exception as e:
            logging.error(f"FTP connection failed: {e}")
            raise
    
    def upload(self, local_path: str, remote_path: str) -> bool:
        """Upload file to remote server"""
        try:
            # Create remote directory if needed
            if self.config.get('auto_create_dirs', True):
                self._ensure_remote_dir(os.path.dirname(remote_path))
            
            with open(local_path, 'rb') as f:
                self.ftp.storbinary(f'STOR {remote_path}', f)
            return True
        except Exception as e:
            logging.error(f"Upload failed for {local_path}: {e}")
            return False
    
    def delete(self, remote_path: str) -> bool:
        """Delete file from remote server"""
        try:
            self.ftp.delete(remote_path)
            return True
        except Exception as e:
            logging.error(f"Delete failed for {remote_path}: {e}")
            return False
    
    def _ensure_remote_dir(self, remote_dir: str):
        """Create remote directory if it doesn't exist"""
        dirs = []
        while remote_dir and remote_dir != '/':
            dirs.append(remote_dir)
            remote_dir = os.path.dirname(remote_dir)
        
        dirs.reverse()
        for d in dirs:
            try:
                self.ftp.cwd(d)
            except:
                try:
                    self.ftp.mkd(d)
                except Exception as e:
                    logging.warning(f"Could not create directory {d}: {e}")
    
    def download(self, remote_path: str, local_path: str) -> bool:
        """Download file from remote server"""
        try:
            local_dir = os.path.dirname(local_path)
            if local_dir:
                os.makedirs(local_dir, exist_ok=True)
            with open(local_path, 'wb') as f:
                self.ftp.retrbinary(f'RETR {remote_path}', f.write)
            return True
        except Exception as e:
            logging.error(f"Download failed for {remote_path}: {e}")
            return False

    def walk_remote(self, remote_path: str):
        """Recursively yield all file paths under remote_path"""
        try:
            for name, facts in self.ftp.mlsd(remote_path):
                if name in ('.', '..'):
                    continue
                full_path = remote_path.rstrip('/') + '/' + name
                if facts.get('type') == 'dir':
                    yield from self.walk_remote(full_path)
                else:
                    yield full_path
        except Exception as e:
            logging.error(f"Failed to list remote directory {remote_path}: {e}")

    def close(self):
        """Close connection"""
        if self.ftp:
            try:
                self.ftp.quit()
            except:
                self.ftp.close()
        logging.info("FTP connection closed")


class FileSyncHandler(FileSystemEventHandler):
    """Handle file system events and sync to remote"""
    
    def __init__(self, uploader, config: dict):
        self.uploader = uploader
        self.config = config
        self.local_path = Path(config['local_path']).resolve()
        self.remote_path = config['remote_path']
        self.ignore_patterns = config.get('ignore_patterns', [])
        self.pending_uploads: Dict[str, float] = {}
        self.upload_delay = 0.5  # seconds to wait before uploading
        self._downloaded_paths: Dict[str, float] = {}  # loop prevention
    
    def should_ignore(self, path: str) -> bool:
        """Check if path should be ignored"""
        rel_path = Path(path).relative_to(self.local_path)
        
        for pattern in self.ignore_patterns:
            # Check if pattern matches any part of the path
            if pattern.startswith('*'):
                if str(rel_path).endswith(pattern[1:]):
                    return True
            elif pattern in str(rel_path).split(os.sep):
                return True
        
        return False

    def mark_as_downloaded(self, local_path: str):
        """Mark a file as recently downloaded to prevent re-upload"""
        resolved = str(Path(local_path).resolve())
        self._downloaded_paths[resolved] = time.time()

    def _is_recently_downloaded(self, local_path: str) -> bool:
        """Check if a file was recently downloaded (within 10s grace period)"""
        resolved = str(Path(local_path).resolve())
        download_time = self._downloaded_paths.get(resolved)
        if download_time is not None:
            if time.time() - download_time < 10.0:
                return True
            else:
                del self._downloaded_paths[resolved]
        return False

    def get_remote_path(self, local_path: str) -> str:
        """Convert local path to remote path"""
        rel_path = Path(local_path).relative_to(self.local_path)
        remote = os.path.join(self.remote_path, str(rel_path))
        # Normalize to forward slashes for remote
        return remote.replace(os.sep, '/')
    
    def on_created(self, event):
        if event.is_directory:
            return
        self.schedule_upload(event.src_path)
    
    def on_modified(self, event):
        if event.is_directory:
            return
        self.schedule_upload(event.src_path)
    
    def on_deleted(self, event):
        if event.is_directory:
            return
        if not self.config.get('auto_delete', True):
            return
        if self.should_ignore(event.src_path):
            return

        remote_path = self.get_remote_path(event.src_path)
        logging.info(f"Deleting: {event.src_path} -> {remote_path}")
        self.uploader.delete(remote_path)
    
    def schedule_upload(self, local_path: str):
        """Schedule file for upload after delay"""
        if not self.config.get('auto_upload', True):
            return
        if self.should_ignore(local_path):
            return
        if self._is_recently_downloaded(local_path):
            logging.debug(f"Skipping re-upload of downloaded file: {os.path.basename(local_path)}")
            return

        self.pending_uploads[local_path] = time.time()
    
    def process_pending_uploads(self):
        """Process files scheduled for upload"""
        current_time = time.time()
        to_upload = []
        
        for path, schedule_time in list(self.pending_uploads.items()):
            if current_time - schedule_time >= self.upload_delay:
                to_upload.append(path)
                del self.pending_uploads[path]
        
        for path in to_upload:
            if os.path.exists(path):
                remote_path = self.get_remote_path(path)
                logging.info(f"Uploading: {path} -> {remote_path}")
                success = self.uploader.upload(path, remote_path)
                if success:
                    logging.info(f"✓ Uploaded: {os.path.basename(path)}")
                else:
                    logging.error(f"✗ Failed: {os.path.basename(path)}")


class FileSyncTool:
    """Main sync tool"""
    
    def __init__(self, config_path: str):
        self.config = Config.load(config_path)
        self.setup_logging()
        self.uploader = self.create_uploader()
        self.handler = FileSyncHandler(self.uploader, self.config)
        self.observer = Observer()
    
    def setup_logging(self):
        """Configure logging"""
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            datefmt='%H:%M:%S'
        )
    
    def create_uploader(self):
        """Create appropriate uploader based on protocol"""
        protocol = self.config.get('protocol', 'sftp').lower()
        
        if protocol == 'sftp':
            return SFTPUploader(self.config)
        elif protocol in ['ftp', 'ftps']:
            return FTPUploader(self.config)
        else:
            raise ValueError(f"Unsupported protocol: {protocol}")
    
    def sync_all_files(self):
        """Sync all files on startup"""
        logging.info("Syncing all files...")
        local_path = Path(self.config['local_path'])
        
        for root, dirs, files in os.walk(local_path):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if not self.handler.should_ignore(os.path.join(root, d))]
            
            for file in files:
                file_path = os.path.join(root, file)
                if not self.handler.should_ignore(file_path):
                    remote_path = self.handler.get_remote_path(file_path)
                    logging.info(f"Syncing: {file_path} -> {remote_path}")
                    self.uploader.upload(file_path, remote_path)
        
        logging.info("Initial sync complete")

    def download_all_files(self):
        """Download all files from remote server to local directory"""
        logging.info("Downloading all files from remote...")
        remote_base = self.config['remote_path']
        local_base = Path(self.config['local_path'])

        count = 0
        for remote_file in self.uploader.walk_remote(remote_base):
            # Convert remote path to local path
            rel_path = remote_file[len(remote_base):].lstrip('/')
            local_file = str(local_base / rel_path)

            # Check ignore patterns
            if self.handler.should_ignore(local_file):
                continue

            logging.info(f"Downloading: {remote_file} -> {local_file}")
            success = self.uploader.download(remote_file, local_file)
            if success:
                # Mark after download to prevent re-upload by watcher
                self.handler.mark_as_downloaded(local_file)
                logging.info(f"  Downloaded: {rel_path}")
                count += 1
            else:
                logging.error(f"  Failed: {rel_path}")

        logging.info(f"Download complete ({count} files)")

    def start(self):
        """Start watching for file changes"""
        try:
            # Sync all files if configured
            if self.config.get('sync_on_start', False):
                self.sync_all_files()
            
            # Start watching
            watch_path = self.config['local_path']
            self.observer.schedule(self.handler, watch_path, recursive=True)
            self.observer.start()
            
            logging.info(f"Watching: {watch_path}")
            logging.info(f"Remote: {self.config['protocol']}://{self.config['host']}{self.config['remote_path']}")
            logging.info(f"Auto-upload: {'enabled' if self.config.get('auto_upload', True) else 'disabled'}")
            logging.info("Press Ctrl+C to stop")
            
            try:
                while True:
                    time.sleep(0.1)
                    self.handler.process_pending_uploads()
            except KeyboardInterrupt:
                logging.info("Stopping...")
                self.observer.stop()
            
            self.observer.join()
            
        except Exception as e:
            logging.error(f"Error: {e}")
            raise
        finally:
            self.uploader.close()


def main():
    parser = argparse.ArgumentParser(
        description='Standalone FTP/SFTP File Sync Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Use config.json in current directory
  %(prog)s -c myconfig.json         # Use custom config file
  %(prog)s --create-config          # Create example config file
  %(prog)s --test-connection        # Test connection and exit
  %(prog)s --download               # Download all remote files to local
        """
    )
    
    parser.add_argument(
        '-c', '--config',
        default='config.json',
        help='Path to configuration file (default: config.json)'
    )
    
    parser.add_argument(
        '--create-config',
        action='store_true',
        help='Create example configuration file and exit'
    )

    parser.add_argument(
        '--test-connection',
        action='store_true',
        help='Test connection to remote server and exit'
    )

    parser.add_argument(
        '--download',
        action='store_true',
        help='Download all files from remote server to local directory and exit'
    )

    args = parser.parse_args()
    
    if args.create_config:
        Config.create_example(args.config)
        return

    if args.test_connection:
        config = Config.load(args.config)
        protocol = config.get('protocol', 'sftp').lower()
        host = config.get('host', '?')
        port = config.get('port', 22 if protocol == 'sftp' else 21)
        print(f"Testing {protocol.upper()} connection to {host}:{port}...")
        try:
            if protocol == 'sftp':
                uploader = SFTPUploader(config)
            elif protocol in ['ftp', 'ftps']:
                uploader = FTPUploader(config)
            else:
                print(f"Unsupported protocol: {protocol}")
                sys.exit(1)
            uploader.close()
            print(f"Connection successful!")
        except Exception as e:
            print(f"Connection failed: {e}")
            sys.exit(1)
        return

    if args.download:
        try:
            sync_tool = FileSyncTool(args.config)
            sync_tool.download_all_files()
            sync_tool.uploader.close()
        except Exception as e:
            print(f"Download failed: {e}")
            sys.exit(1)
        return

    try:
        sync_tool = FileSyncTool(args.config)
        sync_tool.start()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
