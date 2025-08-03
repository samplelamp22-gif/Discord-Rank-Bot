"""
Role Management and Database Operations
Handles PostgreSQL connections, role scheduling, and cleanup tasks
"""

import asyncio
import asyncpg
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from config import config

logger = logging.getLogger(__name__)

class RoleManager:
    """Manages role assignments and database operations"""
    
    def __init__(self):
        """Initialize the role manager"""
        self.pool: Optional[asyncpg.Pool] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        self.database_available = False
        
    async def initialize(self):
        """Initialize database connection and setup tables"""
        if not config.has_database_config():
            logger.warning("No database configuration found. Bot will operate without persistent storage.")
            return
        
        try:
            # Create connection pool with retry logic
            await self._create_connection_pool()
            
            if self.pool:
                # Setup database tables
                await self._setup_tables()
                self.database_available = True
                logger.info("Database connection established successfully")
                
                # Start cleanup task
                self._start_cleanup_task()
            else:
                logger.warning("Database connection failed. Operating without persistent storage.")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            logger.warning("Bot will continue without database functionality")
    
    async def _create_connection_pool(self):
        """Create database connection pool with retry logic"""
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting database connection (attempt {attempt + 1}/{max_retries})")
                
                # Create connection pool
                self.pool = await asyncpg.create_pool(
                    config.database_url,
                    min_size=1,
                    max_size=5,
                    command_timeout=30,
                    server_settings={
                        'application_name': 'discord_rank_bot',
                    }
                )
                
                # Test the connection
                async with self.pool.acquire() as conn:
                    await conn.execute('SELECT 1')
                
                logger.info("Database connection pool created successfully")
                return
                
            except Exception as e:
                logger.error(f"Database connection attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error("All database connection attempts failed")
                    self.pool = None
    
    async def _setup_tables(self):
        """Setup required database tables"""
        if not self.pool:
            return
        
        try:
            async with self.pool.acquire() as conn:
                # Create temporary_roles table
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS temporary_roles (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        guild_id BIGINT NOT NULL,
                        role_id BIGINT NOT NULL,
                        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                ''')
                
                # Create index for efficient cleanup queries
                await conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_temporary_roles_expires_at 
                    ON temporary_roles(expires_at)
                ''')
                
                logger.info("Database tables setup completed")
                
        except Exception as e:
            logger.error(f"Failed to setup database tables: {e}")
            raise
    
    async def schedule_role_removal(self, user_id: int, guild_id: int, role_id: int, expires_at: datetime):
        """Schedule a role for automatic removal"""
        if not self.database_available or not self.pool:
            logger.warning(f"Cannot schedule role removal for user {user_id} - database unavailable")
            return False
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO temporary_roles (user_id, guild_id, role_id, expires_at)
                    VALUES ($1, $2, $3, $4)
                ''', user_id, guild_id, role_id, expires_at)
            
            logger.info(f"Scheduled role removal for user {user_id}, role {role_id} at {expires_at}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to schedule role removal: {e}")
            return False
    
    async def get_user_temporary_roles(self, user_id: int, guild_id: int) -> List[Dict[str, Any]]:
        """Get all temporary roles for a user"""
        if not self.database_available or not self.pool:
            return []
        
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT role_id, expires_at, created_at
                    FROM temporary_roles
                    WHERE user_id = $1 AND guild_id = $2 AND expires_at > NOW()
                    ORDER BY expires_at
                ''', user_id, guild_id)
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get user temporary roles: {e}")
            return []
    
    async def cleanup_expired_roles(self, bot) -> int:
        """Remove expired roles and clean up database"""
        if not self.database_available or not self.pool:
            return 0
        
        removed_count = 0
        
        try:
            async with self.pool.acquire() as conn:
                # Get expired roles
                expired_roles = await conn.fetch('''
                    SELECT user_id, guild_id, role_id, expires_at
                    FROM temporary_roles
                    WHERE expires_at <= NOW()
                ''')
                
                for record in expired_roles:
                    try:
                        # Get guild and member
                        guild = bot.get_guild(record['guild_id'])
                        if not guild:
                            logger.warning(f"Guild {record['guild_id']} not found for cleanup")
                            continue
                        
                        member = guild.get_member(record['user_id'])
                        if not member:
                            logger.warning(f"Member {record['user_id']} not found in guild {record['guild_id']}")
                            continue
                        
                        # Get role
                        role = guild.get_role(record['role_id'])
                        if not role:
                            logger.warning(f"Role {record['role_id']} not found in guild {record['guild_id']}")
                            continue
                        
                        # Remove role from member
                        if role in member.roles:
                            await member.remove_roles(role, reason="Temporary role expired")
                            logger.info(f"Removed expired role {role.name} from {member.display_name}")
                            removed_count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to remove role for user {record['user_id']}: {e}")
                
                # Clean up expired records from database
                deleted_count = await conn.execute('''
                    DELETE FROM temporary_roles
                    WHERE expires_at <= NOW()
                ''')
                
                if removed_count > 0:
                    logger.info(f"Cleanup completed: {removed_count} roles removed, {deleted_count} records cleaned")
                
        except Exception as e:
            logger.error(f"Failed during role cleanup: {e}")
        
        return removed_count
    
    def _start_cleanup_task(self):
        """Start the automatic cleanup task"""
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()
        
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Automatic cleanup task started")
    
    async def _cleanup_loop(self):
        """Main cleanup loop that runs every 5 minutes"""
        while True:
            try:
                await asyncio.sleep(config.cleanup_interval)
                
                # Import bot here to avoid circular imports
                from bot import RankBot
                bot_instance = None
                
                # Find the bot instance
                for task in asyncio.all_tasks():
                    try:
                        if hasattr(task, 'get_coro'):
                            coro = task.get_coro()
                            if hasattr(coro, 'cr_frame') and coro.cr_frame:
                                frame = coro.cr_frame
                                if frame and 'self' in frame.f_locals:
                                    obj = frame.f_locals['self']
                                    if isinstance(obj, RankBot):
                                        bot_instance = obj
                                        break
                    except Exception:
                        continue
                
                if bot_instance and bot_instance.is_ready():
                    removed_count = await self.cleanup_expired_roles(bot_instance)
                    if removed_count > 0:
                        logger.info(f"Automated cleanup removed {removed_count} expired roles")
                
            except asyncio.CancelledError:
                logger.info("Cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                # Continue running despite errors
    
    async def close(self):
        """Close database connections and cleanup tasks"""
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")

# Global role manager instance
role_manager = RoleManager()