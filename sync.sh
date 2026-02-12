#!/bin/bash
# File Sync Tool - Easy launcher script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/file_sync.py"
DEFAULT_CONFIG="$SCRIPT_DIR/config.json"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

# Check if dependencies are installed
if ! python3 -c "import watchdog" &> /dev/null; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip3 install -r "$SCRIPT_DIR/requirements.txt"
fi

# Function to show usage
usage() {
    echo "File Sync Tool - Usage:"
    echo ""
    echo "  $0                    Start sync with default config.json"
    echo "  $0 -c CONFIG         Start sync with custom config file"
    echo "  $0 --setup           Create example config file"
    echo "  $0 --help            Show this help message"
    echo ""
}

# Parse arguments
CONFIG_FILE="$DEFAULT_CONFIG"

case "$1" in
    --setup)
        python3 "$PYTHON_SCRIPT" --create-config
        echo -e "${GREEN}Configuration file created: config.json${NC}"
        echo "Please edit this file and run: $0"
        exit 0
        ;;
    --help)
        usage
        exit 0
        ;;
    -c)
        if [ -z "$2" ]; then
            echo -e "${RED}Error: -c requires a config file path${NC}"
            usage
            exit 1
        fi
        CONFIG_FILE="$2"
        ;;
    "")
        # Use default config
        ;;
    *)
        echo -e "${RED}Error: Unknown option $1${NC}"
        usage
        exit 1
        ;;
esac

# Check if config exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}Error: Configuration file not found: $CONFIG_FILE${NC}"
    echo "Run '$0 --setup' to create an example config file"
    exit 1
fi

# Run the sync tool
echo -e "${GREEN}Starting File Sync Tool...${NC}"
python3 "$PYTHON_SCRIPT" -c "$CONFIG_FILE"
