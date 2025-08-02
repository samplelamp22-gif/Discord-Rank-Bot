"""
Role Manager
Handles temporary role assignments and cleanup with PostgreSQL database
"""

import os
import logging
import asyncpg
from datetime import datetime
from typing import Dict, List, Optional
import discord

logger = logging.getLogger(__name__)

class RoleManager:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        if not self.db_url:
            logger.error("DATABASE_URL environment variable not found!")
            raise ValueError("DATABASE_URL is required for RoleManager")

    async def _get_connection(self):
        """Get database connection"""
        try:
            return await asyncpg.connect(self.db_url)
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            raise

    async def _ensure_table_exists(self):
        """Ensure the temporary_roles table exists"""
        conn = await self._get_connection()
        try:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS temporary_roles (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    guild_id BIGINT NOT NULL,
                    role_id BIGINT NOT NULL,
                    expiry_time TIMESTAMP NOT NULL,
                    assigned_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    UNIQUE(user_id, guild_id, role_id)
                );
            ''')
        finally:
            await conn.close()

    async def schedule_role_removal(
        self, 
        user_id: int, 
        guild_id: int, 
        role_id: int, 
        expiry_time: datetime
    ):
        """Schedule a role for removal at a specific time"""
        await self._ensure_table_exists()
        conn = await self._get_connection()
        try:
            # Use ON CONFLICT to handle duplicate entries
            await conn.execute(
                '''
                INSERT INTO temporary_roles (user_id, guild_id, role_id, expiry_time)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id, guild_id, role_id) 
                DO UPDATE SET expiry_time = $4, assigned_at = NOW()
                ''',
                user_id, guild_id, role_id, expiry_time
            )
            logger.info(f"Scheduled role removal for user {user_id} in guild {guild_id}, role {role_id} at {expiry_time}")
        except Exception as e:
            logger.error(f"Error scheduling role removal: {e}")            
        finally:
            await conn.close()

    async def cleanup_expired_roles(self, bot: discord.Client):
        """Remove expired temporary roles"""
        await self._ensure_table_exists()
        conn = await self._get_connection()
        
        try:
            # Get all expired roles
            expired_roles = await conn.fetch(
                'SELECT * FROM temporary_roles WHERE expiry_time <= NOW()'
            )
            
            if not expired_roles:
                return
            
            roles_to_delete = []
            
            for role_data in expired_roles:
                try:
                    guild = bot.get_guild(role_data['guild_id'])
                    if not guild:
                        logger.warning(f"Guild {role_data['guild_id']} not found, removing from schedule")
                        roles_to_delete.append(role_data['id'])
                        continue
                    
                    member = guild.get_member(role_data['user_id'])
                    if not member:
                        logger.warning(f"Member {role_data['user_id']} not found in guild {guild.id}, removing from schedule")
                        roles_to_delete.append(role_data['id'])
                        continue
                    
                    role = guild.get_role(role_data['role_id'])
                    if not role:
                        logger.warning(f"Role {role_data['role_id']} not found in guild {guild.id}, removing from schedule")
                        roles_to_delete.append(role_data['id'])
                        continue
                    
                    if role in member.roles:
                        try:
                            await member.remove_roles(role, reason="Temporary role expired")
                            logger.info(f"Removed expired role {role.name} from {member} in {guild.name}")
                        except discord.Forbidden:
                            logger.error(f"No permission to remove role {role.name} from {member}")
                        except Exception as e:
                            logger.error(f"Error removing role {role.name} from {member}: {e}")
                    
                    roles_to_delete.append(role_data['id'])
                    
                except Exception as e:
                    logger.error(f"Error processing role cleanup for role {role_data['id']}: {e}")
                    roles_to_delete.append(role_data['id'])
            
            # Remove expired entries from database
            if roles_to_delete:
                await conn.execute(
                    'DELETE FROM temporary_roles WHERE id = ANY($1::integer[])',
                    roles_to_delete
                )
                logger.info(f"Cleaned up {len(roles_to_delete)} expired role assignments")
                
        except Exception as e:
            logger.error(f"Error during role cleanup: {e}")
        finally:
            await conn.close()

    async def get_user_temp_roles(self, user_id: int, guild_id: int) -> List[Dict]:
        """Get all temporary roles for a user in a guild"""
        await self._ensure_table_exists()
        conn = await self._get_connection()
        try:
            rows = await conn.fetch(
                'SELECT * FROM temporary_roles WHERE user_id = $1 AND guild_id = $2',
                user_id, guild_id
            )
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting user temp roles: {e}")
            return []
        finally:
            await conn.close()

    async def remove_scheduled_role(self, user_id: int, guild_id: int, role_id: int) -> bool:
        """Remove a role from the scheduled removal list"""
        await self._ensure_table_exists()
        conn = await self._get_connection()
        try:
            result = await conn.execute(
                'DELETE FROM temporary_roles WHERE user_id = $1 AND guild_id = $2 AND role_id = $3',
                user_id, guild_id, role_id
            )
            if result == 'DELETE 1':
                logger.info(f"Removed scheduled role removal for user {user_id}, role {role_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing scheduled role: {e}")
            return False
        finally:
            await conn.close()

    async def get_scheduled_count(self) -> int:
        """Get the number of roles scheduled for removal"""
        await self._ensure_table_exists()
        conn = await self._get_connection()
        try:
            count = await conn.fetchval('SELECT COUNT(*) FROM temporary_roles')
            return count or 0
        except Exception as e:
            logger.error(f"Error getting scheduled count: {e}")
            return 0
        finally:
            await conn.close()

    async def get_all_scheduled_roles(self) -> List[Dict]:
        """Get all scheduled role removals"""
        await self._ensure_table_exists()
        conn = await self._get_connection()
        try:
            rows = await conn.fetch('SELECT * FROM temporary_roles ORDER BY expiry_time')
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting all scheduled roles: {e}")
            return []
        finally:
            await conn.close()
