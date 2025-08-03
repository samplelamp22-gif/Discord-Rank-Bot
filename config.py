"""
Configuration Management
Handles bot configuration and role mappings with proper environment variable handling
"""

import os
from typing import Optional, Dict, List

class Config:
    """Configuration class for the Discord bot with fallback values"""

    def __init__(self):
        # Role options for each parameter with environment variable support
        self.ROLE1_OPTIONS = [
            os.getenv('ROLE1_OPTION1', 'Stage 2'),
            os.getenv('ROLE1_OPTION2', 'Stage 3')
        ]

        self.ROLE2_OPTIONS = [
            os.getenv('ROLE2_OPTION1', 'High'),
            os.getenv('ROLE2_OPTION2', 'Mid'),
            os.getenv('ROLE2_OPTION3', 'Low')
        ]

        self.ROLE3_OPTIONS = [
            os.getenv('ROLE3_OPTION1', 'Strong'),
            os.getenv('ROLE3_OPTION2', 'Stable'),
            os.getenv('ROLE3_OPTION3', 'Weak')
        ]

        # Role ID mappings with proper error handling
        self.role_mappings = {}
        
        # Initialize role mappings with error handling
        try:
            self.role_mappings = {
                # Role1 mappings
                self.ROLE1_OPTIONS[0]: int(os.getenv('ROLE1_OPTION1_ID', '0')),
                self.ROLE1_OPTIONS[1]: int(os.getenv('ROLE1_OPTION2_ID', '0')),

                # Role2 mappings
                self.ROLE2_OPTIONS[0]: int(os.getenv('ROLE2_OPTION1_ID', '0')),
                self.ROLE2_OPTIONS[1]: int(os.getenv('ROLE2_OPTION2_ID', '0')),
                self.ROLE2_OPTIONS[2]: int(os.getenv('ROLE2_OPTION3_ID', '0')),

                # Role3 mappings
                self.ROLE3_OPTIONS[0]: int(os.getenv('ROLE3_OPTION1_ID', '0')),
                self.ROLE3_OPTIONS[1]: int(os.getenv('ROLE3_OPTION2_ID', '0')),
                self.ROLE3_OPTIONS[2]: int(os.getenv('ROLE3_OPTION3_ID', '0')),
            }
        except ValueError as e:
            print(f"Warning: Invalid role ID in environment variables: {e}")
            # Initialize with zeros if there's an error
            self.role_mappings = {option: 0 for option in self.ROLE1_OPTIONS + self.ROLE2_OPTIONS + self.ROLE3_OPTIONS}

        # Temporary role ID and required role ID with error handling
        try:
            self.temporary_role_id = int(os.getenv('TEMPORARY_ROLE_ID', '0'))
        except ValueError:
            print("Warning: Invalid TEMPORARY_ROLE_ID in environment variables")
            self.temporary_role_id = 0

        try:
            self.required_role_id = int(os.getenv('REQUIRED_ROLE_ID', '0'))
        except ValueError:
            print("Warning: Invalid REQUIRED_ROLE_ID in environment variables")
            self.required_role_id = 0

    def get_role_id(self, role_name: str) -> Optional[int]:
        """Get the Discord role ID for a given role name"""
        role_id = self.role_mappings.get(role_name, 0)
        return role_id if role_id > 0 else None

    def get_temporary_role_id(self) -> Optional[int]:
        """Get the temporary role ID"""
        return self.temporary_role_id if self.temporary_role_id > 0 else None

    def get_required_role_id(self) -> Optional[int]:
        """Get the required role ID to use the command"""
        return self.required_role_id if self.required_role_id > 0 else None

    def validate_configuration(self) -> List[str]:
        """Validate the configuration and return any errors"""
        errors = []

        # Check if all role IDs are configured
        for role_name, role_id in self.role_mappings.items():
            if role_id == 0:
                errors.append(f"Role ID not configured for: {role_name}")

        # Check temporary role
        if self.temporary_role_id == 0:
            errors.append("Temporary role ID not configured (TEMPORARY_ROLE_ID)")

        # Check database URL
        if not os.getenv('DATABASE_URL'):
            errors.append("DATABASE_URL environment variable not configured")

        # Check Discord token
        if not os.getenv('DISCORD_TOKEN'):
            errors.append("DISCORD_TOKEN environment variable not configured")

        return errors

    def get_all_role_options(self) -> Dict[str, List[str]]:
        """Get all role options organized by parameter"""
        return {
            "role1": self.ROLE1_OPTIONS,
            "role2": self.ROLE2_OPTIONS,
            "role3": self.ROLE3_OPTIONS
        }

    def get_configuration_summary(self) -> str:
        """Get a summary of the current configuration"""
        summary = []
        summary.append("=== Bot Configuration Summary ===")
        summary.append(f"Role 1 Options (2): {', '.join(self.ROLE1_OPTIONS)}")
        summary.append(f"Role 2 Options (3): {', '.join(self.ROLE2_OPTIONS)}")
        summary.append(f"Role 3 Options (3): {', '.join(self.ROLE3_OPTIONS)}")
        summary.append(f"Temporary Role ID: {self.temporary_role_id}")
        summary.append(f"Required Role ID: {self.required_role_id}")

        # Check database configuration
        db_url = os.getenv('DATABASE_URL')
        if db_url:
            # Hide sensitive parts of the URL
            if '@' in db_url:
                parts = db_url.split('@')
                masked_url = f"{parts[0].split('://')[0]}://***@{parts[1]}"
            else:
                masked_url = "***"
            summary.append(f"Database URL: {masked_url}")
        else:
            summary.append("Database URL: Not configured")

        errors = self.validate_configuration()
        if errors:
            summary.append("\n=== Configuration Errors ===")
            for error in errors:
                summary.append(f"❌ {error}")
        else:
            summary.append("\n✅ All configurations are valid")

        return "\n".join(summary)

    def get_environment_template(self) -> str:
        """Get a template for environment variables"""
        template = []
        template.append("# Discord Bot Configuration")
        template.append("DISCORD_TOKEN=your_discord_bot_token_here")
        template.append("")
        template.append("# Database Configuration")
        template.append("DATABASE_URL=postgresql://username:password@host:port/database")
        template.append("")
        template.append("# Role Configuration")
        template.append("TEMPORARY_ROLE_ID=123456789012345678")
        template.append("REQUIRED_ROLE_ID=123456789012345678")
        template.append("")
        template.append("# Role 1 Options (Stage)")
        template.append("ROLE1_OPTION1=Stage 2")
        template.append("ROLE1_OPTION2=Stage 3")
        template.append("ROLE1_OPTION1_ID=123456789012345678")
        template.append("ROLE1_OPTION2_ID=123456789012345678")
        template.append("")
        template.append("# Role 2 Options (Priority)")
        template.append("ROLE2_OPTION1=High")
        template.append("ROLE2_OPTION2=Mid")
        template.append("ROLE2_OPTION3=Low")
        template.append("ROLE2_OPTION1_ID=123456789012345678")
        template.append("ROLE2_OPTION2_ID=123456789012345678")
        template.append("ROLE2_OPTION3_ID=123456789012345678")
        template.append("")
        template.append("# Role 3 Options (Strength)")
        template.append("ROLE3_OPTION1=Strong")
        template.append("ROLE3_OPTION2=Stable")
        template.append("ROLE3_OPTION3=Weak")
        template.append("ROLE3_OPTION1_ID=123456789012345678")
        template.append("ROLE3_OPTION2_ID=123456789012345678")
        template.append("ROLE3_OPTION3_ID=123456789012345678")
        
        return "\n".join(template)
