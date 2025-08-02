# Discord Rank Bot - GitHub Deployment Guide

## Files to Update/Add in Your GitHub Repository

### 1. Core Files (Replace existing files)
- `main.py` - Fixed token handling and error checking
- `bot.py` - Fixed Discord intents, type checking, and slash commands
- `role_manager.py` - Enhanced database connection with fallbacks
- `config.py` - Improved configuration validation
- `requirements.txt` - Python dependencies

### 2. Configuration Files (Add these)
- `render.yaml` - Render deployment configuration
- `.env.example` - Environment variables template

## Render Deployment Steps

### Step 1: Push Code to GitHub
1. Replace all existing files with the fixed versions
2. Add the new `render.yaml` file to your repository root
3. Commit and push all changes

### Step 2: Configure Environment Variables in Render
In your Render dashboard, add these environment variables:

**Required Variables:**
```
DISCORD_TOKEN=your_discord_bot_token
DATABASE_URL=your_postgresql_database_url
```

**Role Configuration (use the IDs you provided):**
```
TEMPORARY_ROLE_ID=1382396090703413368
REQUIRED_ROLE_ID=1320192443001344072

ROLE1_OPTION1_ID=1293310980800905288
ROLE1_OPTION2_ID=1293311045158440962

ROLE2_OPTION1_ID=1293390275091103744
ROLE2_OPTION2_ID=1293390311061717083
ROLE2_OPTION3_ID=1293390359228846152

ROLE3_OPTION1_ID=1318653659080298639
ROLE3_OPTION2_ID=1318653737283092510
ROLE3_OPTION3_ID=1318653784892768329
```

### Step 3: Database Setup
- Render will need a PostgreSQL database
- Add the database URL to the `DATABASE_URL` environment variable
- The bot will automatically create the necessary tables

### Step 4: Deploy
1. Connect your GitHub repository to Render
2. Select the branch to deploy
3. Render will automatically use the `render.yaml` configuration
4. Deploy and monitor the logs

## Key Fixes Applied
- ✅ Fixed DATABASE_URL error handling
- ✅ Corrected Discord intents (removed privileged intents requirement)
- ✅ Fixed type checking issues throughout the codebase
- ✅ Enhanced error handling and logging
- ✅ Improved database connection with multiple fallback methods
- ✅ Added proper null checking for Discord objects

## Bot Features
- `/rank` - Assign temporary roles with automatic expiration
- `/status` - Check current temporary roles
- `/cleanup` - Manual cleanup (admin only)
- Automatic role cleanup every 5 minutes
- PostgreSQL persistent storage

## Support
If you encounter any issues:
1. Check the Render deployment logs
2. Verify all environment variables are set correctly
3. Ensure your Discord bot has the necessary permissions in your server
4. Confirm the role IDs are correct and the bot can access those roles