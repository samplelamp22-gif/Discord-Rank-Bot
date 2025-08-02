"""
Discord Rank Bot
Main bot implementation with slash commands for role management
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List

import discord
from discord.ext import commands, tasks
from discord import app_commands

from config import Config
from role_manager import RoleManager

logger = logging.getLogger(__name__)

class RankBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = False  # Not needed for slash commands
        intents.guilds = True
        intents.members = False  # Disable privileged intent initially
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        self.config = Config()
        self.role_manager = RoleManager()
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        logger.info("Bot is starting up...")
        
        # Start the role cleanup task
        self.role_cleanup_task.start()
        
        # Sync commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

    async def on_ready(self):
        """Called when the bot is ready"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guild(s)')
        
        # Log configuration summary
        config_summary = self.config.get_configuration_summary()
        logger.info(f"\n{config_summary}")

    async def on_command_error(self, ctx, error):
        """Handle command errors"""
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: {error.param}")
        else:
            logger.error(f"Command error: {error}")
            await ctx.send("❌ An error occurred while processing the command.")

    @tasks.loop(minutes=5)
    async def role_cleanup_task(self):
        """Background task to clean up expired roles"""
        try:
            await self.role_manager.cleanup_expired_roles(self)
        except Exception as e:
            logger.error(f"Error in role cleanup task: {e}")

    @role_cleanup_task.before_loop
    async def before_role_cleanup(self):
        """Wait until bot is ready before starting cleanup task"""
        await self.wait_until_ready()

    def has_required_role(self, member: discord.Member) -> bool:
        """Check if member has the required role to use commands"""
        required_role_id = self.config.get_required_role_id()
        if not required_role_id:
            return True  # No required role set, allow everyone
        
        return any(role.id == required_role_id for role in member.roles)

    @app_commands.command(name="rank", description="Assign temporary roles based on parameters")
    @app_commands.describe(
        role1="First parameter (Stage 2/Stage 3)",
        role2="Second parameter (High/Mid/Low)", 
        role3="Third parameter (Strong/Stable/Weak)",
        duration="Duration in hours (default: 24)"
    )
    async def rank_command(
        self,
        interaction: discord.Interaction,
        role1: str,
        role2: str,
        role3: str,
        duration: Optional[int] = 24
    ):
        """Main rank command to assign temporary roles"""
        await interaction.response.defer()
        
        try:
            # Check if user has required role (only check if user is a member)
            if isinstance(interaction.user, discord.Member):
                if not self.has_required_role(interaction.user):
                    await interaction.followup.send(
                        "❌ You don't have permission to use this command.",
                        ephemeral=True
                    )
                    return
            else:
                await interaction.followup.send(
                    "❌ This command can only be used in a server.",
                    ephemeral=True
                )
                return

            # Validate role options
            all_options = self.config.get_all_role_options()
            
            if role1 not in all_options["role1"]:
                await interaction.followup.send(
                    f"❌ Invalid role1. Choose from: {', '.join(all_options['role1'])}",
                    ephemeral=True
                )
                return
                
            if role2 not in all_options["role2"]:
                await interaction.followup.send(
                    f"❌ Invalid role2. Choose from: {', '.join(all_options['role2'])}",
                    ephemeral=True
                )
                return
                
            if role3 not in all_options["role3"]:
                await interaction.followup.send(
                    f"❌ Invalid role3. Choose from: {', '.join(all_options['role3'])}",
                    ephemeral=True
                )
                return

            # Validate duration
            if duration is None or duration < 1 or duration > 168:  # Max 1 week
                await interaction.followup.send(
                    "❌ Duration must be between 1 and 168 hours (1 week).",
                    ephemeral=True
                )
                return

            # Get role IDs
            role1_id = self.config.get_role_id(role1)
            role2_id = self.config.get_role_id(role2)
            role3_id = self.config.get_role_id(role3)
            temp_role_id = self.config.get_temporary_role_id()

            if not all([role1_id, role2_id, role3_id, temp_role_id]):
                await interaction.followup.send(
                    "❌ Some roles are not properly configured. Please contact an administrator.",
                    ephemeral=True
                )
                return

            # Get Discord role objects
            guild = interaction.guild
            if not guild:
                await interaction.followup.send(
                    "❌ This command can only be used in a server.",
                    ephemeral=True
                )
                return
                
            discord_role1 = guild.get_role(role1_id) if role1_id else None
            discord_role2 = guild.get_role(role2_id) if role2_id else None
            discord_role3 = guild.get_role(role3_id) if role3_id else None
            temp_role = guild.get_role(temp_role_id) if temp_role_id else None

            if not all([discord_role1, discord_role2, discord_role3, temp_role]):
                missing_roles = []
                if not discord_role1: missing_roles.append(f"{role1} (ID: {role1_id})")
                if not discord_role2: missing_roles.append(f"{role2} (ID: {role2_id})")
                if not discord_role3: missing_roles.append(f"{role3} (ID: {role3_id})")
                if not temp_role: missing_roles.append(f"Temporary role (ID: {temp_role_id})")
                
                await interaction.followup.send(
                    f"❌ The following roles were not found in this server: {', '.join(missing_roles)}",
                    ephemeral=True
                )
                return

            # Assign roles to user
            if not isinstance(interaction.user, discord.Member):
                await interaction.followup.send(
                    "❌ This command can only be used in a server.",
                    ephemeral=True
                )
                return
                
            member = interaction.user
            roles_to_add = [role for role in [discord_role1, discord_role2, discord_role3, temp_role] if role is not None]
            
            try:
                await member.add_roles(*roles_to_add, reason=f"Rank command: {role1}, {role2}, {role3}")
                
                # Schedule role removal
                expiry_time = datetime.utcnow() + timedelta(hours=duration)
                
                for role in roles_to_add:
                    if role:  # Check if role exists
                        await self.role_manager.schedule_role_removal(
                            member.id,
                            guild.id,
                            role.id,
                            expiry_time
                        )

                # Create response embed
                embed = discord.Embed(
                    title="✅ Roles Assigned Successfully",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                
                role_mentions = []
                if discord_role1: role_mentions.append(f"• {discord_role1.mention}")
                if discord_role2: role_mentions.append(f"• {discord_role2.mention}")
                if discord_role3: role_mentions.append(f"• {discord_role3.mention}")
                if temp_role: role_mentions.append(f"• {temp_role.mention}")
                
                embed.add_field(
                    name="Assigned Roles",
                    value="\n".join(role_mentions) if role_mentions else "None",
                    inline=False
                )
                
                embed.add_field(
                    name="Duration",
                    value=f"{duration} hours",
                    inline=True
                )
                
                embed.add_field(
                    name="Expires At",
                    value=f"<t:{int(expiry_time.timestamp())}:F>",
                    inline=True
                )
                
                embed.set_footer(text=f"Assigned to {member.display_name}")
                
                await interaction.followup.send(embed=embed)
                
                logger.info(f"Assigned roles to {member} in {guild.name}: {role1}, {role2}, {role3} (expires in {duration}h)")

            except discord.Forbidden:
                await interaction.followup.send(
                    "❌ I don't have permission to assign these roles. Please check my role hierarchy.",
                    ephemeral=True
                )
            except Exception as e:
                logger.error(f"Error assigning roles: {e}")
                await interaction.followup.send(
                    "❌ An error occurred while assigning roles.",
                    ephemeral=True
                )

        except Exception as e:
            logger.error(f"Error in rank command: {e}")
            await interaction.followup.send(
                "❌ An unexpected error occurred.",
                ephemeral=True
            )

    @app_commands.command(name="status", description="Check your current temporary roles")
    async def status_command(self, interaction: discord.Interaction):
        """Check user's current temporary roles"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Get user's temporary roles
            if not interaction.guild:
                await interaction.followup.send(
                    "❌ This command can only be used in a server.",
                    ephemeral=True
                )
                return
                
            temp_roles = await self.role_manager.get_user_temp_roles(
                interaction.user.id,
                interaction.guild.id
            )
            
            if not temp_roles:
                await interaction.followup.send(
                    "You don't have any temporary roles scheduled for removal.",
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title="Your Temporary Roles",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            for role_data in temp_roles:
                role = interaction.guild.get_role(role_data['role_id'])
                role_name = role.name if role else f"Unknown Role (ID: {role_data['role_id']})"
                
                expiry_timestamp = int(role_data['expiry_time'].timestamp())
                
                embed.add_field(
                    name=role_name,
                    value=f"Expires: <t:{expiry_timestamp}:R>",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in status command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while fetching your status.",
                ephemeral=True
            )

    @app_commands.command(name="cleanup", description="Manually trigger role cleanup (Admin only)")
    async def cleanup_command(self, interaction: discord.Interaction):
        """Manually trigger role cleanup"""
        # Check if user has administrator permissions
        if not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ You need administrator permissions to use this command.",
                ephemeral=True
            )
            return
            
        await interaction.response.defer()
        
        try:
            await self.role_manager.cleanup_expired_roles(self)
            
            scheduled_count = await self.role_manager.get_scheduled_count()
            
            embed = discord.Embed(
                title="✅ Role Cleanup Complete",
                description=f"Expired roles have been cleaned up.\n\nRemaining scheduled roles: {scheduled_count}",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            await interaction.followup.send(embed=embed)
            
            guild_name = interaction.guild.name if interaction.guild else "Unknown Guild"
            logger.info(f"Manual cleanup triggered by {interaction.user} in {guild_name}")
            
        except Exception as e:
            logger.error(f"Error in cleanup command: {e}")
            await interaction.followup.send(
                "❌ An error occurred during cleanup.",
                ephemeral=True
            )

    @rank_command.autocomplete('role1')
    async def role1_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplete for role1 parameter"""
        options = self.config.get_all_role_options()["role1"]
        return [
            app_commands.Choice(name=option, value=option)
            for option in options
            if current.lower() in option.lower()
        ][:25]

    @rank_command.autocomplete('role2')
    async def role2_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplete for role2 parameter"""
        options = self.config.get_all_role_options()["role2"]
        return [
            app_commands.Choice(name=option, value=option)
            for option in options
            if current.lower() in option.lower()
        ][:25]

    @rank_command.autocomplete('role3')
    async def role3_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplete for role3 parameter"""
        options = self.config.get_all_role_options()["role3"]
        return [
            app_commands.Choice(name=option, value=option)
            for option in options
            if current.lower() in option.lower()
        ][:25]
