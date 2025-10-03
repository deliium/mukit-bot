#!/bin/bash

# Setup script for Mukit Bot using crontab

set -e

echo "Setting up Mukit Bot with crontab..."

# Check if running as the correct user
if [ "$USER" != "mukitby" ]; then
    echo "Please run this script as user 'mukitby'"
    exit 1
fi

# Set variables
BOT_DIR="/home/mukitby/bot.mukit.by"
START_SCRIPT="$BOT_DIR/start_bot.sh"
CRON_ENTRY="*/5 * * * * $START_SCRIPT --production check >/dev/null 2>&1"

echo "Bot directory: $BOT_DIR"
echo "Start script: $START_SCRIPT"

# Check if start script exists
if [ ! -f "$START_SCRIPT" ]; then
    echo "Error: Start script not found at $START_SCRIPT"
    exit 1
fi

# Make sure start script is executable
chmod +x "$START_SCRIPT"

# Check if BOT_TOKEN is set
if [ -z "$BOT_TOKEN" ]; then
    echo "Warning: BOT_TOKEN environment variable is not set"
    echo "Make sure to set it in your .env file or environment"
fi

# Add crontab entry if it doesn't exist
echo "Setting up crontab entry..."

# Get current crontab
current_crontab=$(crontab -l 2>/dev/null || echo "")

# Check if our entry already exists
if echo "$current_crontab" | grep -q "start_bot.sh"; then
    echo "Crontab entry already exists"
else
    # Add our entry to crontab
    (echo "$current_crontab"; echo "$CRON_ENTRY") | crontab -
    echo "Crontab entry added successfully"
fi

# Show current crontab
echo ""
echo "Current crontab entries:"
crontab -l

echo ""
echo "Setup complete!"
echo ""
echo "The bot will be checked every 5 minutes and restarted if needed."
echo ""
echo "Manual commands:"
echo "  Start bot (production):     $START_SCRIPT --production start"
echo "  Stop bot:                   $START_SCRIPT --production stop"
echo "  Restart bot:                $START_SCRIPT --production restart"
echo "  Check status:               $START_SCRIPT --production status"
echo "  Check logs:                 tail -f $BOT_DIR/bot.log"
echo ""
echo "Local testing commands:"
echo "  Start bot (local):          $START_SCRIPT --local start"
echo "  Stop bot (local):           $START_SCRIPT --local stop"
echo "  Check status (local):       $START_SCRIPT --local status"
echo ""
echo "To remove the crontab entry later:"
echo "  crontab -e  # and remove the line with start_bot.sh"
