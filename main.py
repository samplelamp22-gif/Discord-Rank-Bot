#!/usr/bin/env python3
"""
Discord Rank Bot - Main Entry Point
Handles bot startup and graceful error handling
"""

import asyncio
import logging
import os
import sys
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

async def main():
    """Main entry point for the Discord bot"""
    try:
        logger.info("Starting Discord Rank Bot...")
        
        # Verify Discord token is available
        discord_token = os.getenv('DISCORD_TOKEN')
        if not discord_token:
            logger.error("DISCORD_TOKEN environment variable is required")
            sys.exit(1)
        
        # Initialize and start the bot
        bot = RankBot()
        
        # Start the bot with proper error handling
        await bot.start(discord_token)
        
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
    except Exception as e:
        logger.error(f"Critical error during bot startup: {e}")
        logger.exception("Full traceback:")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1)