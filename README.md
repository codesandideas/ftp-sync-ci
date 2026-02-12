# File Sync Tool - Standalone FTP/SFTP Client

A standalone file synchronization tool that watches for file changes and automatically syncs them to a remote server via FTP, FTPS, or SFTP. Perfect for use with Zed editor or any IDE lacking built-in FTP sync.

## Features

- 🔄 Real-time file watching and automatic sync
- 📡 Support for SFTP, FTP, and FTPS protocols
- 🔑 SSH key authentication for SFTP
- 📁 Automatic remote directory creation
- 🚫 Ignore patterns (like .git, node_modules, etc.)
- 🔒 Secure connection handling
- 📝 Detailed logging
- ⚡ Debounced uploads (prevents multiple uploads on rapid saves)
- 🗑️ File deletion sync

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install watchdog paramiko
```

## Quick Start

### 1. Create Configuration File

Run the tool once to generate an example config:

```bash
python file_sync.py --create-config
```

This creates `config.json` in the current directory.

### 2. Edit Configuration

Open `config.json` and update with your settings:

```json
{
  "protocol": "sftp",
  "host": "example.com",
  "port": 22,
  "username": "your_username",
  "password": "your_password",
  "local_path": "/path/to/local/project",
  "remote_path": "/path/to/remote/project",
  "ignore_patterns": [
    ".git",
    "node_modules",
    "__pycache__",
    "*.pyc",
    ".DS_Store"
  ],
  "auto_create_dirs": true,
  "sync_on_start": false
}
```

### 3. Run the Sync Tool

```bash
python file_sync.py
```

The tool will start watching your local directory and sync changes automatically!

## Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `protocol` | Connection type: `sftp`, `ftp`, or `ftps` | `sftp` |
| `host` | Remote server hostname or IP | Required |
| `port` | Server port | 22 (SFTP), 21 (FTP) |
| `username` | Login username | Required |
| `password` | Login password | Required (unless using key_file) |
| `key_file` | Path to SSH private key (SFTP only) | Optional |
| `local_path` | Local project directory to watch | Required |
| `remote_path` | Remote directory path | Required |
| `ignore_patterns` | List of patterns to ignore | See example |
| `auto_create_dirs` | Auto-create remote directories | `true` |
| `passive_mode` | Use passive mode (FTP only) | `true` |
| `sync_on_start` | Sync all files on startup | `false` |

## Usage Examples

### Basic Usage

```bash
# Use default config.json
python file_sync.py

# Use custom config file
python file_sync.py -c ~/myproject/sync-config.json
```

### SFTP with SSH Key

```json
{
  "protocol": "sftp",
  "host": "example.com",
  "port": 22,
  "username": "deploy",
  "key_file": "~/.ssh/id_rsa",
  "local_path": "/Users/me/myproject",
  "remote_path": "/var/www/myproject"
}
```

### FTP Configuration

```json
{
  "protocol": "ftp",
  "host": "ftp.example.com",
  "port": 21,
  "username": "ftpuser",
  "password": "ftppass",
  "local_path": "/Users/me/website",
  "remote_path": "/public_html",
  "passive_mode": true
}
```

### FTPS (FTP over TLS)

```json
{
  "protocol": "ftps",
  "host": "secure-ftp.example.com",
  "port": 21,
  "username": "secureuser",
  "password": "securepass",
  "local_path": "/Users/me/secure-project",
  "remote_path": "/home/user/project"
}
```

## Integration with Zed Editor

1. Open your project in Zed
2. In a separate terminal, navigate to your project root
3. Run the sync tool:
   ```bash
   python /path/to/file_sync.py -c /path/to/config.json
   ```
4. Edit files in Zed - they'll sync automatically!

### Tips for Zed Integration

- Keep the sync tool running in a dedicated terminal window
- Use `sync_on_start: true` to ensure remote is up-to-date when you start
- Add `.zed` to your ignore patterns if needed

## Ignore Patterns

Patterns can be:
- **Directory names**: `node_modules`, `.git`, `__pycache__`
- **File extensions**: `*.pyc`, `*.log`, `*.tmp`
- **Hidden files**: `.DS_Store`, `.env`

Example comprehensive ignore list:

```json
{
  "ignore_patterns": [
    ".git",
    ".gitignore",
    "node_modules",
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.log",
    ".DS_Store",
    ".vscode",
    ".idea",
    "*.swp",
    "*.swo",
    ".env",
    ".env.local",
    "venv",
    ".venv",
    "dist",
    "build"
  ]
}
```

## Running as a Background Service

### On macOS/Linux (using screen)

```bash
# Start in background
screen -dmS filesync python file_sync.py

# Attach to see logs
screen -r filesync

# Detach: Press Ctrl+A then D
```

### On macOS (using launchd)

Create `~/Library/LaunchAgents/com.filesync.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.filesync</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/file_sync.py</string>
        <string>-c</string>
        <string>/path/to/config.json</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Load the service:
```bash
launchctl load ~/Library/LaunchAgents/com.filesync.plist
```

### On Linux (using systemd)

Create `/etc/systemd/system/filesync.service`:

```ini
[Unit]
Description=File Sync Service
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/path/to/project
ExecStart=/usr/bin/python3 /path/to/file_sync.py -c /path/to/config.json
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable filesync
sudo systemctl start filesync
sudo systemctl status filesync
```

## Troubleshooting

### Connection Issues

**SFTP "No existing session" error:**
- Check hostname, port, and credentials
- Verify SSH key permissions: `chmod 600 ~/.ssh/id_rsa`
- Test connection: `sftp username@hostname`

**FTP "Connection refused":**
- Verify server is running: `telnet hostname 21`
- Check firewall settings
- Try passive mode: `"passive_mode": true`

### File Not Syncing

1. Check if file is being ignored (check logs)
2. Verify local_path and remote_path are correct
3. Check file permissions on remote server
4. Look for error messages in the console

### Permission Denied

- Check remote directory permissions
- Verify user has write access to remote_path
- For SFTP, ensure proper SSH permissions

## Advanced Features

### Multiple Projects

Create different config files for each project:

```bash
# Project 1
python file_sync.py -c ~/projects/website/sync-config.json

# Project 2
python file_sync.py -c ~/projects/app/sync-config.json
```

### Sync All Files on Start

Set `"sync_on_start": true` to upload all files when starting:

```json
{
  "sync_on_start": true
}
```

This is useful for ensuring the remote server has all current files.

## Security Notes

⚠️ **Important Security Considerations:**

1. **Never commit config files with credentials to version control**
   - Add `config.json` to `.gitignore`
   - Use environment variables for sensitive data

2. **Use SSH keys instead of passwords when possible**
   ```json
   {
     "password": "",
     "key_file": "~/.ssh/id_rsa"
   }
   ```

3. **Protect your config file**
   ```bash
   chmod 600 config.json
   ```

4. **Use SFTP or FTPS instead of plain FTP** when possible for encrypted connections

## Logging

The tool provides detailed logging:

```
12:34:56 - INFO - Connected to SFTP server: example.com
12:34:56 - INFO - Watching: /Users/me/myproject
12:34:56 - INFO - Remote: sftp://example.com/var/www/myproject
12:35:10 - INFO - Uploading: /Users/me/myproject/index.html -> /var/www/myproject/index.html
12:35:10 - INFO - ✓ Uploaded: index.html
```

## Performance

- **Debounced uploads**: Waits 0.5 seconds after file changes before uploading (prevents multiple uploads on rapid saves)
- **Batch operations**: Processes multiple pending uploads efficiently
- **Persistent connections**: Maintains connection between uploads

## Comparison with VSCode SFTP Extension

| Feature | This Tool | VSCode SFTP |
|---------|-----------|-------------|
| Editor Independent | ✅ | ❌ (VSCode only) |
| Auto-sync on save | ✅ | ✅ |
| SFTP support | ✅ | ✅ |
| FTP/FTPS support | ✅ | ✅ |
| Works with Zed | ✅ | ❌ |
| Background service | ✅ | ❌ |
| Manual sync | ⚠️ | ✅ |

## License

MIT License - feel free to use and modify!

## Contributing

Issues and pull requests welcome! This tool is designed to be simple and focused.

## Support

If you encounter issues:
1. Check the troubleshooting section
2. Review logs for error messages
3. Verify your configuration
4. Test connection manually (ssh/ftp client)
