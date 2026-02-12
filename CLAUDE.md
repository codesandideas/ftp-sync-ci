# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FTP Sync CI is a single-file Python tool that watches local directories for file changes and automatically syncs them to remote servers via FTP, FTPS, or SFTP. It is designed for editors (like Zed) that lack built-in remote sync.

## Running the Tool

```bash
# Install dependencies
pip install -r requirements.txt    # watchdog, paramiko

# Run with default config.json
python file_sync.py

# Run with custom config
python file_sync.py -c myconfig.json

# Generate example config file
python file_sync.py --create-config

# Test connection without syncing
python file_sync.py --test-connection

# Via wrapper scripts (auto-install deps)
./sync.sh          # Unix/Linux
sync.bat           # Windows
```

There are no tests, linting, or build steps configured.

## Architecture

Everything lives in `file_sync.py` (~470 lines). The classes form a pipeline:

1. **Config** — Loads/creates JSON config files. Static utility methods only.
2. **SFTPUploader / FTPUploader** — Protocol-specific connection handlers with a shared interface (`connect`, `upload`, `delete`, `close`). SFTPUploader uses paramiko; FTPUploader uses stdlib ftplib.
3. **FileSyncHandler** (extends watchdog `FileSystemEventHandler`) — Receives filesystem events, applies ignore patterns, and queues uploads with a 0.5s debounce to batch rapid changes.
4. **FileSyncTool** — Orchestrator: loads config, creates the correct uploader based on `protocol` field, wires up the watchdog Observer, and runs the main loop (`sleep 0.1s` → `process_pending_uploads`).

### Key flows

- **File change detected** → `on_created`/`on_modified` → `schedule_upload` (adds to `pending_uploads` dict with timestamp) → main loop calls `process_pending_uploads` after 0.5s delay → `uploader.upload()`
- **File deleted** → `on_deleted` → immediate `uploader.delete()` (no debounce)
- **Path conversion** — `get_remote_path()` computes relative path from `local_path`, joins with `remote_path`, normalizes to forward slashes
- **Ignore matching** — Wildcard patterns (`*.pyc`) match via suffix; plain names (`.git`, `node_modules`) match against individual path components

### Configuration

JSON config file (default `config.json`). See `config.example.json` for template. Key fields: `protocol` (sftp/ftp/ftps), `host`, `port`, `username`, `password`/`key_file`, `local_path`, `remote_path`, `ignore_patterns`, `sync_on_start`.
