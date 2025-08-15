#!/bin/bash

# UniFi MCP Server (Modular Version) Startup Script

# Set default log file and PID file to use /tmp
LOG_FILE=${MCP_LOG_FILE:-${LOG_FILE:-"/tmp/unifi-mcp.log"}}
PID_FILE=${MCP_PID_FILE:-${PID_FILE:-"/tmp/unifi-mcp.pid"}}

# Handle command line arguments
if [[ "$1" == "logs" ]]; then
    echo "Streaming logs from $LOG_FILE (Ctrl+C to stop)..."
    
    # Check if log file exists
    if [[ ! -f "$LOG_FILE" ]]; then
        echo "Log file $LOG_FILE not found. Is the server running?"
        exit 1
    fi
    
    # Stream logs with prettification
    tail -f "$LOG_FILE" | while IFS= read -r line; do
        # Extract timestamp, level, logger name, and message
        if [[ $line =~ ^([0-9-]+\ [0-9:,]+)\ -\ ([^\ ]+)\ -\ ([^\ ]+)\ -\ (.+)$ ]]; then
            timestamp="${BASH_REMATCH[1]}"
            logger="${BASH_REMATCH[2]}"
            level="${BASH_REMATCH[3]}"
            message="${BASH_REMATCH[4]}"
            
            # Color codes  
            case "$level" in
                "DEBUG") color=$'\033[36m' ;;    # Cyan
                "INFO")  color=$'\033[32m' ;;    # Green
                "WARNING") color=$'\033[33m' ;;  # Yellow
                "ERROR") color=$'\033[31m' ;;    # Red
                "CRITICAL") color=$'\033[35m' ;; # Magenta
                *) color=$'\033[0m' ;;           # Default
            esac
            
            # Format timestamp
            formatted_time=$(date -d "$timestamp" "+%H:%M:%S" 2>/dev/null || echo "${timestamp##* }")
            
            # Pretty print with colors
            printf "%s%-8s\033[0m \033[90m%s [%s]\033[0m %s\n" \
                "$color" "$level" "$formatted_time" "${logger##*.}" "$message"
        else
            # Print non-matching lines as-is with dim color
            printf "\033[90m%s\033[0m\n" "$line"
        fi
    done
    exit 0
fi

echo "Starting UniFi MCP Server (modular version)..."

# Sync dependencies
echo "Syncing dependencies..."
uv sync

# Run the modular server in background with proper daemonization
echo "Starting server in background..."
# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"
# Create log file immediately
touch "$LOG_FILE"
setsid nohup uv run python -m unifi_mcp.main > "$LOG_FILE" 2>&1 &
SERVER_PID=$!
echo "$SERVER_PID" > "$PID_FILE"
echo "Server started with PID: $SERVER_PID (saved to $PID_FILE)"
echo "Server is running independently - it will continue even if you stop log streaming"

# Function to handle cleanup
cleanup() {
    echo ""
    echo "Log streaming stopped. Server continues running with PID: $SERVER_PID"
    echo "To stop the server: kill $SERVER_PID"
    echo "To restart log streaming: ./run.sh logs"
    exit 0
}

# Set up signal handler
trap cleanup SIGINT SIGTERM

# Stream logs with prettification
echo "Streaming server logs from $LOG_FILE (Ctrl+C to stop log streaming only)..."
tail -f "$LOG_FILE" | while IFS= read -r line; do
    # Extract timestamp, level, logger name, and message
    if [[ $line =~ ^([0-9-]+\ [0-9:,]+)\ -\ ([^\ ]+)\ -\ ([^\ ]+)\ -\ (.+)$ ]]; then
        timestamp="${BASH_REMATCH[1]}"
        logger="${BASH_REMATCH[2]}"
        level="${BASH_REMATCH[3]}"
        message="${BASH_REMATCH[4]}"
        
        # Color codes  
        case "$level" in
            "DEBUG") color=$'\033[36m' ;;    # Cyan
            "INFO")  color=$'\033[32m' ;;    # Green
            "WARNING") color=$'\033[33m' ;;  # Yellow
            "ERROR") color=$'\033[31m' ;;    # Red
            "CRITICAL") color=$'\033[35m' ;; # Magenta
            *) color=$'\033[0m' ;;           # Default
        esac
        
        # Format timestamp
        formatted_time=$(date -d "$timestamp" "+%H:%M:%S" 2>/dev/null || echo "${timestamp##* }")
        
        # Pretty print with colors
        printf "%s%-8s\033[0m \033[90m%s [%s]\033[0m %s\n" \
            "$color" "$level" "$formatted_time" "${logger##*.}" "$message"
    else
        # Print non-matching lines as-is with dim color
        printf "\033[90m%s\033[0m\n" "$line"
    fi
done