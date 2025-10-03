# Mukit Bot

A Telegram bot that processes messages and creates pinned summaries with category formatting.

## Features

- Process messages starting with `.` or `.HH.MM`
- Automatic category detection and formatting
- Pinned message management
- Duplicate category handling (replaces previous entry)
- Auto-clear when pinned message is manually removed
- Web interface for status monitoring

## Setup

### 1. Deploy the code to your hosting

### 2. Set up the bot service using crontab

```bash
# Make sure BOT_TOKEN is set in your environment
export BOT_TOKEN=your_actual_bot_token

# Run the setup script
./setup_crontab.sh
```

This will:
- Add a crontab entry to check the bot every 5 minutes
- Automatically restart the bot if it stops
- Set up proper logging

### 3. Manual bot management

**Production commands:**
```bash
# Start the bot manually (production mode with venv)
./start_bot.sh --production start

# Stop the bot
./start_bot.sh --production stop

# Restart the bot
./start_bot.sh --production restart

# Check bot status
./start_bot.sh --production status

# View bot logs
tail -f bot.log
```

**Local testing commands:**
```bash
# Start the bot locally (for testing)
./start_bot.sh --local start

# Stop the bot locally
./start_bot.sh --local stop

# Check status locally
./start_bot.sh --local status
```

## Web Interface

The FastAPI app provides these endpoints:

- `/` - Basic status
- `/healthz` - Health check with bot status
- `/bot/status` - Detailed bot status

## How it works

1. **Bot Process**: Runs independently via crontab, writes status to `/tmp/mukit_bot_status.json`
2. **Web App**: Reads bot status from the status file, no longer manages the bot process
3. **Auto-restart**: Crontab checks every 5 minutes and restarts if needed
4. **Logging**: All bot output goes to `bot.log`

## Message Format

- `.message` - Process with current time
- `.HH.MM message` - Process with specified time
- `. Something` - Also works (normalizes to lowercase first letter)

Categories are automatically detected and wrapped with `=` signs.

## Troubleshooting

- Check bot status: `./start_bot.sh --production status`
- View logs: `tail -f bot.log`
- Check crontab: `crontab -l`
- Manual restart: `./start_bot.sh --production restart`
- Test locally: `./start_bot.sh --local start`