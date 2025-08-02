# Discord Role Assignment Bot

## Overview

This is a Discord bot built with Python that provides a modern slash command interface for role assignment with advanced temporary role management. The bot allows users with specific permissions to assign multiple roles to members while automatically managing temporary roles that expire after 48 hours. It features role-based access control, custom embed responses, rate limiting protection, comprehensive error handling, and background cleanup tasks to maintain server hygiene.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

**Core Framework**: Built on discord.py library using the modern Bot class with slash command integration. The application follows a modular architecture with clear separation of concerns across multiple components.

**Command System**: Utilizes Discord's native slash command API rather than traditional prefix commands, providing better user experience and integration with Discord's interface. Commands are synced automatically on startup.

**Role Management Architecture**: Implements a custom RoleManager class that handles temporary role assignments with JSON-based persistence. The system tracks role assignments with expiration timestamps and provides automatic cleanup through background tasks.

**Configuration Management**: Centralized configuration system using environment variables for sensitive data like bot tokens and role IDs. Role mappings are dynamically loaded from environment variables, allowing flexible configuration without code changes.

**Background Task System**: Employs discord.py's task loop system to run periodic cleanup operations every 30 minutes, automatically removing expired temporary roles to prevent manual intervention.

**Permission System**: Implements role-based access control requiring users to have a specific Discord role to use the command, ensuring only authorized users can assign roles.

**Rate Limiting Protection**: Includes built-in wait times between role assignments (0.5 seconds) to prevent Discord API rate limiting and interaction timeout errors.

**Custom Response System**: Features custom Discord embeds with styled success messages including decorative separators and user mentions for enhanced user experience.

**Logging Strategy**: Comprehensive logging system with both file and console output, tracking role assignments, removals, errors, and bot lifecycle events for debugging and monitoring.

**Data Persistence**: Uses PostgreSQL database for temporary role data persistence, ensuring role expiration information survives bot restarts and deployments. The database automatically handles expired role cleanup even if the bot was offline for extended periods.

## External Dependencies

**Discord API**: Primary integration through discord.py library for bot functionality, slash commands, role management, and real-time event handling.

**Environment Configuration**: Relies on python-dotenv for environment variable management, separating configuration from code.

**PostgreSQL Database**: Uses asyncpg for database connectivity and temporary role persistence. Ensures data survives bot restarts and automatically cleans up expired roles even after extended downtime.

**File System**: Log file output (bot.log) for debugging and monitoring.

**Required Python Packages**: 
- discord.py (Discord API wrapper)
- python-dotenv (Environment variable loading)
- asyncpg (PostgreSQL async database driver)
- psycopg2-binary (PostgreSQL adapter)

**Discord Permissions Required**:
- Manage Roles
- Use Slash Commands  
- View Channels
- Send Messages

**Runtime Dependencies**: Requires Python 3.7+ and access to Discord's API endpoints for bot operation.