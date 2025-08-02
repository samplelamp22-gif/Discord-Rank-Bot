# Discord Rank Bot

A Discord bot for managing temporary role assignments with PostgreSQL database integration. The bot allows users to assign temporary roles based on different parameters and automatically removes them after a specified duration.

## Features

- **Slash Commands**: Modern Discord slash command interface
- **Temporary Roles**: Automatically assigns and removes roles after a specified time
- **PostgreSQL Integration**: Persistent storage for role scheduling
- **Role Categories**: Three configurable role categories (Stage, Priority, Strength)
- **Permission System**: Configurable required role to use commands
- **Auto-cleanup**: Background task to remove expired roles
- **Status Checking**: Users can check their current temporary roles
- **Admin Controls**: Manual cleanup commands for administrators

## Commands

- `/rank <role1> <role2> <role3> [duration]` - Assign temporary roles (default: 24 hours)
- `/status` - Check your current temporary roles
- `/cleanup` - Manually trigger role cleanup (Admin only)

## Setup Instructions

### 1. Environment Variables

Copy `.env.example` to `.env` and configure the following variables:

#### Required Variables
```env
DISCORD_TOKEN=your_discord_bot_token
DATABASE_URL=postgresql://user:password@host:port/database
