"""
Discord Rank Bot Implementation
Handles Discord bot events, slash commands, and role management
"""

import discord
from discord.ext import commands
import logging
from datetime import datetime, timedelta
from typing import List
from config import config
from role_manager import role_manager

logger = logging.getLogger(__name__)

class RankBot(commands.Bot):
    """Discord bot for managing ranks and temporary roles"""
    
    def __init__(self):
        """Initialize the Discord bot"""
        # Set up intents (no privileged intents needed)
        intents = discord.Intents.default()
        intents.message_content = False  # We don't need message content
        
        super().__init__(
            command_prefix='!',  # Not used, but required
            intents=intents,
            help_command=None
        )
        
        logger.info("Discord bot initialized")
    
    async def setup_hook(self):
        """Setup hook called when bot is starting"""
        logger.info("Setting up bot...")
        
        # Initialize role manager
        await role_manager.initialize()
        
        # Log configuration status
        config.log_config_status()
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")
    
    async def on_ready(self):
        """Called when bot is ready and connected"""
        logger.info(f"{self.user} has connected to Discord!")
        logger.info(f"Bot is in {len(self.guilds)} guilds")
        
        # Log bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="for /rank commands"
        )
        await self.change_presence(activity=activity)
    
    async def on_error(self, event, *args, **kwargs):
        """Handle bot errors"""
        logger.error(f"Bot error in event {event}: {args}")
    
    async def close(self):
        """Clean shutdown of the bot"""
        logger.info("Shutting down bot...")
        await role_manager.close()
        await super().close()

# Create bot instance
bot = RankBot()

# Utility functions for autocomplete
async def stage_autocomplete(interaction: discord.Interaction, current: str) -> List[discord.app_commands.Choice[str]]:
    """Autocomplete for stage parameter"""
    stages = list(config.stage_roles.keys())
    return [
        discord.app_commands.Choice(name=stage, value=stage)
        for stage in stages if current.lower() in stage.lower()
    ]

async def priority_autocomplete(interaction: discord.Interaction, current: str) -> List[discord.app_commands.Choice[str]]:
    """Autocomplete for priority parameter"""
    priorities = list(config.priority_roles.keys())
    return [
        discord.app_commands.Choice(name=priority, value=priority)
        for priority in priorities if current.lower() in priority.lower()
    ]

async def strength_autocomplete(interaction: discord.Interaction, current: str) -> List[discord.app_commands.Choice[str]]:
    """Autocomplete for strength parameter"""
    strengths = list(config.strength_roles.keys())
    return [
        discord.app_commands.Choice(name=strength, value=strength)
        for strength in strengths if current.lower() in strength.lower()
    ]

# Slash Commands
@bot.tree.command(name="rank", description="Assign permanent roles and temporary access (48h)")
@discord.app_commands.describe(
    stage="Select your stage",
    priority="Select your priority level",
    strength="Select your strength level"
)
@discord.app_commands.autocomplete(stage=stage_autocomplete)
@discord.app_commands.autocomplete(priority=priority_autocomplete)
@discord.app_commands.autocomplete(strength=strength_autocomplete)
async def rank_command(interaction: discord.Interaction, stage: str, priority: str, strength: str):
    """Assign roles to a user with temporary access"""
    try:
        # Check if user has required role
        member = interaction.user
        if not isinstance(member, discord.Member):
            embed = discord.Embed(
                title="❌ Error",
                description="This command can only be used in a server.",
                color=0xff0000,
                timestamp=datetime.utcnow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        if not any(role.id == config.required_role_id for role in member.roles):
            embed = discord.Embed(
                title="❌ Access Denied",
                description="You don't have permission to use this command.",
                color=0xff0000,
                timestamp=datetime.utcnow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Validate role choices
        stage_role_id = config.get_role_id('stage', stage)
        priority_role_id = config.get_role_id('priority', priority)
        strength_role_id = config.get_role_id('strength', strength)
        
        if not all([stage_role_id, priority_role_id, strength_role_id]):
            embed = discord.Embed(
                title="❌ Invalid Selection",
                description="One or more of your selections are invalid. Please try again.",
                color=0xff0000,
                timestamp=datetime.utcnow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Get guild and roles
        guild = interaction.guild
        if not guild:
            embed = discord.Embed(
                title="❌ Error",
                description="This command can only be used in a server.",
                color=0xff0000,
                timestamp=datetime.utcnow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        stage_role = guild.get_role(stage_role_id)
        priority_role = guild.get_role(priority_role_id)
        strength_role = guild.get_role(strength_role_id)
        temp_role = guild.get_role(config.temporary_role_id)
        
        if not all([stage_role, priority_role, strength_role, temp_role]):
            embed = discord.Embed(
                title="❌ Role Error",
                description="Some roles could not be found. Please contact an administrator.",
                color=0xff0000,
                timestamp=datetime.utcnow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Assign permanent roles
        permanent_roles = [stage_role, priority_role, strength_role]
        added_roles = []
        
        for role in permanent_roles:
            if role not in member.roles:
                await member.add_roles(role, reason=f"Rank assignment: {stage}, {priority}, {strength}")
                added_roles.append(role.name)
        
        # Assign temporary role
        temp_added = False
        if temp_role not in member.roles:
            await member.add_roles(temp_role, reason="Temporary access (48h)")
            temp_added = True
        
        # Schedule temporary role removal
        expires_at = datetime.utcnow() + timedelta(seconds=config.temporary_role_duration)
        await role_manager.schedule_role_removal(
            member.id,
            guild.id,
            config.temporary_role_id,
            expires_at
        )
        
        # Create response embed
        embed = discord.Embed(
            title="✅ Roles Assigned Successfully",
            color=0x00ff00,
            timestamp=datetime.utcnow()
        )
        
        if added_roles:
            embed.add_field(
                name="🔒 Permanent Roles Added",
                value="\n".join(f"• {role}" for role in added_roles),
                inline=False
            )
        else:
            embed.add_field(
                name="🔒 Permanent Roles",
                value="Already assigned",
                inline=False
            )
        
        if temp_added:
            embed.add_field(
                name="⏰ Temporary Access",
                value=f"• {temp_role.name} (expires in 48 hours)",
                inline=False
            )
        else:
            embed.add_field(
                name="⏰ Temporary Access",
                value="Already active",
                inline=False
            )
        
        embed.add_field(
            name="📋 Selection",
            value=f"Stage: {stage}\nPriority: {priority}\nStrength: {strength}",
            inline=True
        )
        
        embed.set_footer(text=f"Assigned to {member.display_name}")
        
        await interaction.response.send_message(embed=embed)
        logger.info(f"Roles assigned to {member.display_name}: {stage}, {priority}, {strength}")
        
    except Exception as e:
        logger.error(f"Error in rank command: {e}")
        embed = discord.Embed(
            title="❌ Command Error",
            description="An error occurred while processing your request. Please try again later.",
            color=0xff0000,
            timestamp=datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="status", description="Check your temporary access time remaining")
async def status_command(interaction: discord.Interaction):
    """Check temporary role status for the user"""
    try:
        # Check if command is used in a server
        if not interaction.guild:
            embed = discord.Embed(
                title="❌ Error",
                description="This command can only be used in a server.",
                color=0xff0000,
                timestamp=datetime.utcnow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        member = interaction.user
        if not isinstance(member, discord.Member):
            embed = discord.Embed(
                title="❌ Error", 
                description="This command can only be used by server members.",
                color=0xff0000,
                timestamp=datetime.utcnow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        # Get user's temporary roles
        temp_roles = await role_manager.get_user_temporary_roles(
            member.id,
            interaction.guild.id
        )
        
        embed = discord.Embed(
            title="📊 Your Role Status",
            color=0x0099ff,
            timestamp=datetime.utcnow()
        )
        
        if not temp_roles:
            embed.add_field(
                name="⏰ Temporary Access",
                value="No active temporary roles",
                inline=False
            )
        else:
            temp_info = []
            for role_data in temp_roles:
                role = interaction.guild.get_role(role_data['role_id'])
                if role:
                    expires_at = role_data['expires_at']
                    time_left = expires_at - datetime.utcnow()
                    
                    if time_left.total_seconds() > 0:
                        hours = int(time_left.total_seconds() // 3600)
                        minutes = int((time_left.total_seconds() % 3600) // 60)
                        temp_info.append(f"• {role.name}: {hours}h {minutes}m remaining")
                    else:
                        temp_info.append(f"• {role.name}: Expired (awaiting cleanup)")
            
            embed.add_field(
                name="⏰ Temporary Access",
                value="\n".join(temp_info) if temp_info else "No active temporary roles",
                inline=False
            )
        
        # Show permanent roles
        permanent_role_names = []
        all_role_ids = set()
        all_role_ids.update(config.stage_roles.values())
        all_role_ids.update(config.priority_roles.values())
        all_role_ids.update(config.strength_roles.values())
        
        for role in member.roles:
            if role.id in all_role_ids:
                permanent_role_names.append(role.name)
        
        if permanent_role_names:
            embed.add_field(
                name="🔒 Permanent Roles",
                value="\n".join(f"• {name}" for name in permanent_role_names),
                inline=False
            )
        
        embed.set_footer(text=f"Status for {member.display_name}")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        logger.error(f"Error in status command: {e}")
        embed = discord.Embed(
            title="❌ Command Error",
            description="An error occurred while checking your status. Please try again later.",
            color=0xff0000,
            timestamp=datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="cleanup", description="Manually trigger role cleanup (Admin only)")
async def cleanup_command(interaction: discord.Interaction):
    """Manually trigger role cleanup"""
    try:
        # Check if command is used in a server and user is admin
        if not interaction.guild:
            embed = discord.Embed(
                title="❌ Error",
                description="This command can only be used in a server.",
                color=0xff0000,
                timestamp=datetime.utcnow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        member = interaction.user
        if not isinstance(member, discord.Member):
            embed = discord.Embed(
                title="❌ Error",
                description="This command can only be used by server members.",
                color=0xff0000,
                timestamp=datetime.utcnow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        if not member.guild_permissions.administrator:
            embed = discord.Embed(
                title="❌ Access Denied",
                description="Only administrators can use this command.",
                color=0xff0000,
                timestamp=datetime.utcnow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Defer response for potentially long operation
        await interaction.response.defer()
        
        # Perform cleanup
        removed_count = await role_manager.cleanup_expired_roles(bot)
        
        embed = discord.Embed(
            title="🧹 Cleanup Completed",
            description=f"Removed {removed_count} expired roles.",
            color=0x00ff00,
            timestamp=datetime.utcnow()
        )
        
        embed.set_footer(text=f"Cleanup initiated by {member.display_name}")
        
        await interaction.followup.send(embed=embed)
        logger.info(f"Manual cleanup performed by {member.display_name}: {removed_count} roles removed")
        
    except Exception as e:
        logger.error(f"Error in cleanup command: {e}")
        embed = discord.Embed(
            title="❌ Command Error",
            description="An error occurred during cleanup. Please try again later.",
            color=0xff0000,
            timestamp=datetime.utcnow()
        )
        await interaction.followup.send(embed=embed)

# Export the bot instance for main.py
__all__ = ['bot', 'RankBot']