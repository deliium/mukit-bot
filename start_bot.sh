#!/bin/bash

# Startup script for Mukit Bot using crontab

set -e

# Configuration
PRODUCTION_MODE=false
BOT_DIR="/home/mukitby/bot.mukit.by"
BOT_SCRIPT="$BOT_DIR/bot_runner.py"
PID_FILE="/tmp/mukit_bot.pid"
LOG_FILE="/home/mukitby/bot.mukit.by/bot.log"

# Virtual environment for production
VENV_ACTIVATE="/home/mukitby/virtualenv/bot.mukit.by/3.12/bin/activate"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --production)
            PRODUCTION_MODE=true
            shift
            ;;
        --local)
            PRODUCTION_MODE=false
            shift
            ;;
        *)
            # Unknown option
            shift
            ;;
    esac
done

# Set bot directory based on mode
if [ "$PRODUCTION_MODE" = true ]; then
    BOT_DIR="/home/mukitby/bot.mukit.by"
    BOT_SCRIPT="$BOT_DIR/bot_runner.py"
    LOG_FILE="$BOT_DIR/bot.log"
else
    # Local mode - use current directory
    BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    BOT_SCRIPT="$BOT_DIR/bot_runner.py"
    LOG_FILE="$BOT_DIR/bot.log"
fi

# Function to check if bot is running
is_bot_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            return 0  # Bot is running
        else
            # PID file exists but process is dead
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1  # Bot is not running
}

# Function to start the bot
start_bot() {
    if is_bot_running; then
        echo "$(date): Bot is already running (PID: $(cat $PID_FILE))"
        return 0
    fi
    
    echo "$(date): Starting Mukit Bot..."
    echo "$(date): Mode: $([ "$PRODUCTION_MODE" = true ] && echo "production" || echo "local")"
    
    # Change to bot directory
    cd "$BOT_DIR"
    
    # Prepare the command based on mode
    if [ "$PRODUCTION_MODE" = true ]; then
        # Production mode: activate virtual environment
        if [ -f "$VENV_ACTIVATE" ]; then
            echo "$(date): Activating virtual environment: $VENV_ACTIVATE"
            BOT_CMD="source $VENV_ACTIVATE && python3 $BOT_SCRIPT"
        else
            echo "$(date): Warning: Virtual environment not found at $VENV_ACTIVATE"
            BOT_CMD="python3 $BOT_SCRIPT"
        fi
    else
        # Local mode: use system python
        BOT_CMD="python3 $BOT_SCRIPT"
    fi
    
    # Start the bot in background and save PID
    nohup bash -c "$BOT_CMD" > "$LOG_FILE" 2>&1 &
    local bot_pid=$!
    
    # Save PID to file
    echo "$bot_pid" > "$PID_FILE"
    
    # Wait a moment and check if it's still running
    sleep 2
    if kill -0 "$bot_pid" 2>/dev/null; then
        echo "$(date): Bot started successfully (PID: $bot_pid)"
        return 0
    else
        echo "$(date): Failed to start bot"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Function to stop the bot
stop_bot() {
    if ! is_bot_running; then
        echo "$(date): Bot is not running"
        return 0
    fi
    
    local pid=$(cat "$PID_FILE")
    echo "$(date): Stopping bot (PID: $pid)..."
    
    # Send SIGTERM to gracefully stop the bot
    kill -TERM "$pid" 2>/dev/null || true
    
    # Wait for graceful shutdown
    local count=0
    while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
        sleep 1
        count=$((count + 1))
    done
    
    # Force kill if still running
    if kill -0 "$pid" 2>/dev/null; then
        echo "$(date): Force killing bot..."
        kill -KILL "$pid" 2>/dev/null || true
    fi
    
    rm -f "$PID_FILE"
    echo "$(date): Bot stopped"
}

# Function to restart the bot
restart_bot() {
    echo "$(date): Restarting bot..."
    stop_bot
    sleep 2
    start_bot
}

# Function to check and restart if needed
check_and_restart() {
    if ! is_bot_running; then
        echo "$(date): Bot is not running, starting..."
        start_bot
    else
        echo "$(date): Bot is running (PID: $(cat $PID_FILE))"
    fi
}

# Main script logic
case "${1:-check}" in
    start)
        start_bot
        ;;
    stop)
        stop_bot
        ;;
    restart)
        restart_bot
        ;;
    status)
        if is_bot_running; then
            echo "Bot is running (PID: $(cat $PID_FILE))"
            exit 0
        else
            echo "Bot is not running"
            exit 1
        fi
        ;;
    check|*)
        check_and_restart
        ;;
esac
