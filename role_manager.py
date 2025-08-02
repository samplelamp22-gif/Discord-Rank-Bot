"""
Role Manager
Handles temporary role assignments and cleanup
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional
import discord

logger = logging.getLogger(__name__)

class RoleManager:
    def __init__(self, data_file: str = "temp_roles.json"):
        self.data_file = data_file
        self.temp_roles: Dict = self._load_data()

    def _load_data(self) -> Dict:
        """Load temporary role data from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading role data: {e}")
        return {}

    def _save_data(self):
        """Save temporary role data to file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.temp_roles, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving role data: {e}")

    async def schedule_role_removal(
        self, 
        user_id: int, 
        guild_id: int, 
        role_id: int, 
        expiry_time: datetime
    ):
        """Schedule a role for removal at a specific time"""
        key = f"{guild_id}_{user_id}_{role_id}"
        
        self.temp_roles[key] = {
            "user_id": user_id,
            "guild_id": guild_id,
            "role_id": role_id,
            "expiry_time": expiry_time.isoformat(),
            "assigned_at": datetime.utcnow().isoformat()
        }
        
        self._save_data()
        logger.info(f"Scheduled role removal for user {user_id} in guild {guild_id}, role {role_id} at {expiry_time}")

    async def cleanup_expired_roles(self, bot: discord.Client):
        """Remove expired temporary roles"""
        if not self.temp_roles:
            return

        current_time = datetime.utcnow()
        expired_keys = []
        
        for key, role_data in self.temp_roles.items():
            try:
                expiry_time = datetime.fromisoformat(role_data["expiry_time"])
                
                if current_time >= expiry_time:
                    # Role has expired, remove it
                    guild = bot.get_guild(role_data["guild_id"])
                    if not guild:
                        logger.warning(f"Guild {role_data['guild_id']} not found, removing from schedule")
                        expired_keys.append(key)
                        continue
                    
                    member = guild.get_member(role_data["user_id"])
                    if not member:
                        logger.warning(f"Member {role_data['user_id']} not found in guild {guild.id}, removing from schedule")
                        expired_keys.append(key)
                        continue
                    
                    role = guild.get_role(role_data["role_id"])
                    if not role:
                        logger.warning(f"Role {role_data['role_id']} not found in guild {guild.id}, removing from schedule")
                        expired_keys.append(key)
                        continue
                    
                    if role in member.roles:
                        try:
                            await member.remove_roles(role, reason="Temporary role expired")
                            logger.info(f"Removed expired role {role.name} from {member} in {guild.name}")
                        except discord.Forbidden:
                            logger.error(f"No permission to remove role {role.name} from {member}")
                        except Exception as e:
                            logger.error(f"Error removing role {role.name} from {member}: {e}")
                    
                    expired_keys.append(key)
                    
            except Exception as e:
                logger.error(f"Error processing role cleanup for {key}: {e}")
                expired_keys.append(key)

        # Remove expired entries
        for key in expired_keys:
            del self.temp_roles[key]
        
        if expired_keys:
            self._save_data()
            logger.info(f"Cleaned up {len(expired_keys)} expired role assignments")

    def get_user_temp_roles(self, user_id: int, guild_id: int) -> List[Dict]:
        """Get all temporary roles for a user in a guild"""
        user_roles = []
        for key, role_data in self.temp_roles.items():
            if role_data["user_id"] == user_id and role_data["guild_id"] == guild_id:
                user_roles.append(role_data)
        return user_roles

    def remove_scheduled_role(self, user_id: int, guild_id: int, role_id: int) -> bool:
        """Remove a role from the scheduled removal list"""
        key = f"{guild_id}_{user_id}_{role_id}"
        if key in self.temp_roles:
            del self.temp_roles[key]
            self._save_data()
            logger.info(f"Removed scheduled role removal for user {user_id}, role {role_id}")
            return True
        return False

    def get_scheduled_count(self) -> int:
        """Get the number of roles scheduled for removal"""
        return len(self.temp_roles)

    def get_all_scheduled_roles(self) -> Dict:
        """Get all scheduled role removals"""
        return self.temp_roles.copy()
