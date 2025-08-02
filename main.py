#!/usr/bin/env python3
"""
Discord Role Assignment Bot
Main entry point for the bot application
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from bot import DiscordBot

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main function to run the Discord bot"""
    # Get bot token from environment
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        logger.error("DISCORD_BOT_TOKEN not found in environment variables!")
        logger.error("Please set your bot token in the .env file")
        return

    # Initialize and run the bot
    bot = DiscordBot()
    
    try:
        logger.info("Starting Discord bot...")
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
