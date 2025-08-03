# Discord Rank Bot

A Discord bot designed for server rank management with automatic role assignment and temporary access control. The bot provides slash commands for assigning permanent rank roles (Stage, Priority, Strength) along with temporary access roles that expire after 48 hours. Built using discord.py with PostgreSQL for persistent storage and automated cleanup functionality.

## Features

- **Slash Commands**: Modern Discord slash command interface with autocomplete
- **Permanent Role Assignment**: Assigns Stage, Priority, and Strength roles that never expire
- **Temporary Access Control**: Assigns temporary access role that automatically expires after 48 hours
- **PostgreSQL Integration**: Persistent storage for role scheduling and tracking
- **Automatic Cleanup**: Background task removes expired roles every 5 minutes
- **Permission System**: Configurable required role to use rank commands
- **Status Checking**: Users can check their current temporary role status
- **Admin Controls**: Manual cleanup commands for administrators

## Commands

- `/rank <stage> <priority> <strength>` - Assign permanent roles + temporary access (48h auto-expiry)
- `/status` - Check your temporary access time remaining (available to all members)
- `/cleanup` - Manually trigger role cleanup (Admin only)

## Role System

### Permanent Roles (Never Expire)
- **Stage Roles**: Stage2, Stage3
- **Priority Roles**: High, Mid, Low  
- **Strength Roles**: Strong, Stable, Weak

### Temporary Role (48-Hour Expiry)
- **Temporary Access**: Automatically removed after exactly 48 hours

## Quick Setup

### 1. Prerequisites
- Python 3.11+
- PostgreSQL database
- Discord bot token with appropriate permissions

### 2. Installation
```bash
git clone https://github.com/samplelamp22-gif/Discord-Rank-Bot.git
cd Discord-Rank-Bot
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env` and configure:

```env
# Discord Bot Configuration
DISCORD_TOKEN=your_discord_bot_token_here

# Database Configuration
DATABASE_URL=postgresql://username:password@host:port/database

# Role IDs (get these from your Discord server)
TEMPORARY_ROLE_ID=123456789012345678
REQUIRED_ROLE_ID=123456789012345678

# Stage Roles
ROLE1_OPTION1_ID=123456789012345678  # Stage2
ROLE1_OPTION2_ID=123456789012345678  # Stage3

# Priority Roles
ROLE2_OPTION1_ID=123456789012345678  # High
ROLE2_OPTION2_ID=123456789012345678  # Mid
ROLE2_OPTION3_ID=123456789012345678  # Low

# Strength Roles
ROLE3_OPTION1_ID=123456789012345678  # Strong
ROLE3_OPTION2_ID=123456789012345678  # Stable
ROLE3_OPTION3_ID=123456789012345678  # Weak
```

### 4. Discord Bot Setup
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application and bot
3. Copy the bot token to your `.env` file
4. Enable these bot permissions:
   - Send Messages
   - Use Slash Commands
   - Manage Roles
   - Read Message History
5. Invite bot to your server with these permissions

### 5. Get Role IDs
1. Enable Developer Mode in Discord (User Settings > Advanced > Developer Mode)
2. Right-click on each role in your server settings
3. Select "Copy ID" and paste into your `.env` file

### 6. Run the Bot
```bash
python main.py
```

## System Architecture

### Bot Framework
- **Discord.py Library**: Modern discord.py with slash commands
- **Asynchronous Design**: Efficient event handling and database operations
- **Error Handling**: Comprehensive error handling with graceful degradation

### Role Management
- **Dual Role System**: Permanent roles vs temporary access roles
- **Time-Based Expiration**: Only temporary roles expire after 48 hours
- **Permission Gating**: Requires specific role to access rank commands

### Database Architecture
- **PostgreSQL Backend**: Asyncpg for efficient database operations
- **Automatic Cleanup**: Background task removes expired roles every 5 minutes
- **Fallback Design**: Bot continues operating without database if connection fails

## Database Schema

```sql
CREATE TABLE temporary_roles (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Usage Examples

### Assigning Ranks
```
/rank Stage2 High Strong
```
This assigns:
- **Permanent**: Stage2 + High + Strong roles (never expire)
- **Temporary**: Access role (expires in 48 hours)

### Checking Status
```
/status
```
Shows your current temporary role status and time remaining.

### Manual Cleanup (Admin Only)
```
/cleanup
```
Manually triggers removal of expired roles.

## Deployment Options

### Replit (Recommended)
1. Import this repository to Replit
2. Set environment variables in Replit Secrets
3. Run the project

### Self-Hosted
1. Set up Python 3.11+ environment
2. Install PostgreSQL database
3. Configure environment variables
4. Run with `python main.py`

### Cloud Platforms
- Compatible with Heroku, Railway, Render, and other cloud platforms
- Requires PostgreSQL add-on for database functionality

## Troubleshooting

### Common Issues

**Bot not responding to commands:**
- Check that slash commands are synced
- Verify bot has necessary permissions
- Check if bot token is valid

**Database connection errors:**
- Verify DATABASE_URL format
- Check database server accessibility
- Ensure database exists and credentials are correct

**Role assignment failures:**
- Verify all role IDs are correct
- Check bot's role hierarchy position
- Ensure bot has "Manage Roles" permission

### Logs
The bot provides detailed logging for monitoring:
- Connection status
- Command usage
- Database operations
- Error messages

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the logs for error details