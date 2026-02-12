# Quick Setup Guide

## Installation (5 minutes)

### Step 1: Install Python Dependencies

```bash
pip install watchdog paramiko
```

Or use the requirements file:

```bash
pip install -r requirements.txt
```

### Step 2: Create Your Configuration

**Option A: Use the script to generate config**
```bash
python file_sync.py --create-config
```

**Option B: Copy the example**
```bash
cp config.example.json config.json
```

### Step 3: Edit Configuration

Open `config.json` and update these required fields:

```json
{
  "protocol": "sftp",           // or "ftp", "ftps"
  "host": "your-server.com",    // Your server address
  "username": "your_username",  // Your login
  "password": "your_password",  // Your password
  "local_path": "/Users/you/myproject",   // Your local project folder
  "remote_path": "/var/www/myproject"     // Remote project folder
}
```

### Step 4: Run It!

**Linux/macOS:**
```bash
# Using Python directly
python file_sync.py

# Or using the wrapper script
./sync.sh
```

**Windows:**
```batch
REM Using Python directly
python file_sync.py

REM Or using the batch file
sync.bat
```

### Step 5: Test It

1. Keep the sync tool running
2. Edit a file in your project
3. Save the file
4. Check the console - you should see:
   ```
   12:34:56 - INFO - Uploading: /path/to/file.txt -> /remote/path/file.txt
   12:34:56 - INFO - ✓ Uploaded: file.txt
   ```

## Quick Troubleshooting

**"Module not found" errors:**
```bash
pip install watchdog paramiko
```

**"Permission denied" on remote:**
- Check your username/password
- Verify remote_path permissions
- Test with: `ssh username@host` (for SFTP)

**Files not syncing:**
- Check if file matches ignore_patterns
- Look for error messages in console
- Verify local_path is correct

**Connection timeout:**
- Check host and port
- Verify firewall settings
- Test connection manually

## Common Configurations

### SFTP with Password
```json
{
  "protocol": "sftp",
  "host": "example.com",
  "port": 22,
  "username": "deploy",
  "password": "secret123",
  "local_path": "/Users/me/project",
  "remote_path": "/var/www/project"
}
```

### SFTP with SSH Key (Recommended)
```json
{
  "protocol": "sftp",
  "host": "example.com",
  "port": 22,
  "username": "deploy",
  "key_file": "~/.ssh/id_rsa",
  "password": "",
  "local_path": "/Users/me/project",
  "remote_path": "/var/www/project"
}
```

### Regular FTP
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

### Secure FTP (FTPS)
```json
{
  "protocol": "ftps",
  "host": "secure.example.com",
  "port": 21,
  "username": "secureuser",
  "password": "securepass",
  "local_path": "/Users/me/project",
  "remote_path": "/home/project"
}
```

## Using with Zed Editor

1. Open your project in Zed
2. Open a terminal in your project directory
3. Run the sync tool:
   ```bash
   python /path/to/file_sync.py
   ```
4. Edit files in Zed - they sync automatically!

**Pro Tip:** Keep the sync tool running in a dedicated terminal tab or use a terminal multiplexer like tmux/screen.

## Next Steps

- Read the full README.md for advanced features
- Set up as a background service (see README)
- Configure ignore patterns for your project type
- Consider using SSH keys instead of passwords

## Need Help?

Check the main README.md for:
- Detailed configuration options
- Running as a background service
- Security best practices
- Advanced features
- Troubleshooting guide
