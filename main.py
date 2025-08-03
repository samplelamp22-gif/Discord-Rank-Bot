"""
Discord Rank Bot - Main Entry Point
Handles bot initialization and database setup
"""

import os
import sys
import logging
import asyncio
from bot import RankBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def check_environment_variables():
    """Check if all required environment variables are set"""
    required_vars = [
        'DISCORD_TOKEN',
        'DATABASE_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these environment variables before running the bot.")
        return False
    
    return True

async def main():
    """Main function to run the bot"""
    logger.info("Starting Discord Rank Bot...")
    
    # Check environment variables
    if not check_environment_variables():
        sys.exit(1)
    
    # Get Discord token
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN is required")
        sys.exit(1)
    
    # Create and run the bot
    try:
        bot = RankBot()
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Handle the event loop properly
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
