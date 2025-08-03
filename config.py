"""
Configuration management for Discord Rank Bot
Handles environment variables and role ID validation
"""

import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class Config:
    """Configuration manager for the Discord bot"""
    
    def __init__(self):
        """Initialize configuration with environment variables"""
        # Discord Configuration
        self.discord_token = self._get_required_env('DISCORD_TOKEN')
        
        # Database Configuration with multiple fallback options
        self.database_url = self._get_database_url()
        
        # Role IDs
        self.temporary_role_id = self._get_required_env_int('TEMPORARY_ROLE_ID')
        self.required_role_id = self._get_required_env_int('REQUIRED_ROLE_ID')
        
        # Stage Roles (Role1)
        self.stage_roles = {
            'Stage2': self._get_required_env_int('ROLE1_OPTION1_ID'),
            'Stage3': self._get_required_env_int('ROLE1_OPTION2_ID')
        }
        
        # Priority Roles (Role2)
        self.priority_roles = {
            'High': self._get_required_env_int('ROLE2_OPTION1_ID'),
            'Mid': self._get_required_env_int('ROLE2_OPTION2_ID'),
            'Low': self._get_required_env_int('ROLE2_OPTION3_ID')
        }
        
        # Strength Roles (Role3)
        self.strength_roles = {
            'Strong': self._get_required_env_int('ROLE3_OPTION1_ID'),
            'Stable': self._get_required_env_int('ROLE3_OPTION2_ID'),
            'Weak': self._get_required_env_int('ROLE3_OPTION3_ID')
        }
        
        # Bot Configuration
        self.cleanup_interval = 300  # 5 minutes
        self.temporary_role_duration = 48 * 60 * 60  # 48 hours in seconds
        
        logger.info("Configuration loaded successfully")
        logger.info(f"Database URL configured: {'Yes' if self.database_url else 'No'}")
    
    def _get_database_url(self) -> Optional[str]:
        """Get database URL with multiple fallback options"""
        # First try the original DATABASE_URL
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            logger.info("Using DATABASE_URL environment variable")
            return database_url
        
        # Try constructing from individual PostgreSQL variables
        pghost = os.getenv('PGHOST')
        pgport = os.getenv('PGPORT', '5432')
        pgdatabase = os.getenv('PGDATABASE')
        pguser = os.getenv('PGUSER')
        pgpassword = os.getenv('PGPASSWORD')
        
        if all([pghost, pgdatabase, pguser, pgpassword]):
            constructed_url = f"postgresql://{pguser}:{pgpassword}@{pghost}:{pgport}/{pgdatabase}?sslmode=require"
            logger.info("Constructed database URL from individual PG variables")
            return constructed_url
        
        # Log what variables we found for debugging
        available_vars = []
        for var_name in ['DATABASE_URL', 'PGHOST', 'PGPORT', 'PGDATABASE', 'PGUSER', 'PGPASSWORD']:
            if os.getenv(var_name):
                available_vars.append(var_name)
        
        logger.warning(f"Could not construct database URL. Available variables: {available_vars}")
        return None
    
    def _get_required_env(self, key: str) -> str:
        """Get a required environment variable"""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value
    
    def _get_required_env_int(self, key: str) -> int:
        """Get a required environment variable as integer"""
        value = self._get_required_env(key)
        try:
            return int(value)
        except ValueError:
            raise ValueError(f"Environment variable {key} must be a valid integer, got: {value}")
    
    def get_role_id(self, category: str, value: str) -> Optional[int]:
        """Get role ID for a given category and value"""
        role_maps = {
            'stage': self.stage_roles,
            'priority': self.priority_roles,
            'strength': self.strength_roles
        }
        
        role_map = role_maps.get(category.lower())
        if not role_map:
            return None
        
        return role_map.get(value)
    
    def get_all_role_choices(self) -> Dict[str, Dict[str, int]]:
        """Get all role choices for autocomplete"""
        return {
            'stage': self.stage_roles,
            'priority': self.priority_roles,
            'strength': self.strength_roles
        }
    
    def has_database_config(self) -> bool:
        """Check if database configuration is available"""
        return self.database_url is not None
    
    def log_config_status(self):
        """Log the current configuration status"""
        logger.info("=== Configuration Status ===")
        logger.info(f"Discord Token: {'✓ Set' if self.discord_token else '✗ Missing'}")
        logger.info(f"Database URL: {'✓ Set' if self.database_url else '✗ Missing'}")
        logger.info(f"Temporary Role ID: {self.temporary_role_id}")
        logger.info(f"Required Role ID: {self.required_role_id}")
        logger.info(f"Stage Roles: {len(self.stage_roles)} configured")
        logger.info(f"Priority Roles: {len(self.priority_roles)} configured")
        logger.info(f"Strength Roles: {len(self.strength_roles)} configured")
        logger.info("=== End Configuration ===")

# Global configuration instance
config = Config()