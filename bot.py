"""
Discord Bot Implementation
Handles slash commands and role management
"""

import os
import discord
from discord.ext import commands, tasks
import logging
from datetime import datetime, timedelta
from role_manager import RoleManager
from config import Config

logger = logging.getLogger(__name__)

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        # Remove privileged intents that require approval
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        self.role_manager = RoleManager()
        self.config = Config()
        
        # Add the stage command
        @self.tree.command(name="stage", description="Assign roles to a user with temporary access")
        @discord.app_commands.describe(
            user="The user to assign roles to",
            stage="Stage level (2 options available)",
            progress="Progress level (3 options available)", 
            progress2="Progress type (3 options available)",
            reason="Optional reason for role assignment"
        )
        async def stage(
            interaction: discord.Interaction,
            user: discord.Member,
            stage: str,
            progress: str,
            progress2: str,
            reason: str = ""
        ):
            await self._handle_stage_command(interaction, user, stage, progress, progress2, reason)
        
        # Add autocomplete - always return all options for better reliability
        @stage.autocomplete('stage') 
        async def stage_autocomplete(interaction: discord.Interaction, current: str):
            try:
                choices = []
                for option in self.config.ROLE1_OPTIONS:
                    # Always include all options if current is empty, otherwise filter
                    if not current or current.lower() in option.lower():
                        choices.append(discord.app_commands.Choice(name=option, value=option))
                return choices[:25]  # Discord limit
            except Exception as e:
                logger.error(f"Error in stage autocomplete: {e}")
                return [
                    discord.app_commands.Choice(name="Stage 2", value="Stage 2"),
                    discord.app_commands.Choice(name="Stage 3", value="Stage 3")
                ]
        
        @stage.autocomplete('progress')
        async def progress_autocomplete(interaction: discord.Interaction, current: str):
            try:
                choices = []
                for option in self.config.ROLE2_OPTIONS:
                    # Always include all options if current is empty, otherwise filter
                    if not current or current.lower() in option.lower():
                        choices.append(discord.app_commands.Choice(name=option, value=option))
                return choices[:25]  # Discord limit
            except Exception as e:
                logger.error(f"Error in progress autocomplete: {e}")
                return [
                    discord.app_commands.Choice(name="High", value="High"),
                    discord.app_commands.Choice(name="Mid", value="Mid"),
                    discord.app_commands.Choice(name="Low", value="Low")
                ]
        
        @stage.autocomplete('progress2')
        async def progress2_autocomplete(interaction: discord.Interaction, current: str):
            try:
                choices = []
                for option in self.config.ROLE3_OPTIONS:
                    # Always include all options if current is empty, otherwise filter
                    if not current or current.lower() in option.lower():
                        choices.append(discord.app_commands.Choice(name=option, value=option))
                return choices[:25]  # Discord limit
            except Exception as e:
                logger.error(f"Error in progress2 autocomplete: {e}")
                return [
                    discord.app_commands.Choice(name="Strong", value="Strong"),
                    discord.app_commands.Choice(name="Stable", value="Stable"),
                    discord.app_commands.Choice(name="Weak", value="Weak")
                ]

    async def _handle_stage_command(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        stage: str,
        progress: str,
        progress2: str,
        reason: str = ""
    ):
        """Handle the stage command logic"""
        
        # Check if user has the required role to use this command
        required_role_id = self.config.get_required_role_id()
        if required_role_id and interaction.guild:
            required_role = discord.utils.get(interaction.guild.roles, id=required_role_id)
            if required_role and hasattr(interaction.user, 'roles') and required_role not in interaction.user.roles:
                embed = discord.Embed(
                    title="❌ Access Denied",
                    description=f"You need the {required_role.mention} role to use this command.",
                    color=0xff0000
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        # Validate role choices
        if stage not in self.config.ROLE1_OPTIONS:
            embed = discord.Embed(
                title="❌ Invalid Role",
                description=f"Invalid stage. Available options: {', '.join(self.config.ROLE1_OPTIONS)}",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        if progress not in self.config.ROLE2_OPTIONS:
            embed = discord.Embed(
                title="❌ Invalid Role",
                description=f"Invalid progress. Available options: {', '.join(self.config.ROLE2_OPTIONS)}",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        if progress2 not in self.config.ROLE3_OPTIONS:
            embed = discord.Embed(
                title="❌ Invalid Role",
                description=f"Invalid progress type. Available options: {', '.join(self.config.ROLE3_OPTIONS)}",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Defer the response as role assignment might take time
        await interaction.response.defer()

        try:
            import asyncio
            
            # First, remove any existing roles from the same categories
            if interaction.guild:
                await self._remove_existing_roles(user, interaction.guild)
            
            # Assign the three roles with wait times
            success_roles = []
            failed_roles = []
            
            for i, role_name in enumerate([stage, progress, progress2]):
                role_id = self.config.get_role_id(role_name)
                if not role_id:
                    failed_roles.append(f"{role_name} (not configured)")
                    continue
                    
                role = discord.utils.get(interaction.guild.roles, id=role_id) if interaction.guild else None
                if not role:
                    failed_roles.append(f"{role_name} (role not found)")
                    continue
                    
                try:
                    await user.add_roles(role, reason=f"Role assigned by {interaction.user} via /stage command")
                    success_roles.append(role_name)
                    logger.info(f"Assigned role {role_name} to {user} by {interaction.user}")
                    
                    # Wait between role assignments to prevent rate limits
                    if i < 2:  # Don't wait after the last role
                        await asyncio.sleep(0.5)
                        
                except discord.Forbidden:
                    failed_roles.append(f"{role_name} (permission denied)")
                except Exception as e:
                    failed_roles.append(f"{role_name} (error: {str(e)})")

            # Assign temporary role if any roles were successfully assigned
            temp_role_assigned = False
            if success_roles:
                await asyncio.sleep(0.5)  # Wait before assigning temp role
                temp_role_id = self.config.get_temporary_role_id()
                if temp_role_id:
                    temp_role = discord.utils.get(interaction.guild.roles, id=temp_role_id) if interaction.guild else None
                    if temp_role:
                        try:
                            await user.add_roles(temp_role, reason="Temporary role via /stage command")
                            
                            # Schedule removal after 2 days
                            expiry_time = datetime.utcnow() + timedelta(days=2)
                            await self.role_manager.schedule_role_removal(
                                user.id, interaction.guild.id if interaction.guild else 0, temp_role_id, expiry_time
                            )
                            temp_role_assigned = True
                            logger.info(f"Assigned temporary role to {user}, expires at {expiry_time}")
                        except Exception as e:
                            logger.error(f"Failed to assign temporary role: {e}")

            # Create custom embed response
            if success_roles:
                embed = discord.Embed(color=0xffffff)  # White color
                reason_text = reason if reason and reason.strip() else "Left Empty."
                embed.add_field(
                    name="Successfully given " + " ".join(success_roles),
                    value=f"{reason_text}\n────────── ⋆⋅☆⋅⋆ ───────────\nYou now have a 2 day cooldown " + user.mention,
                    inline=False
                )
                await interaction.followup.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="❌ Role Assignment Failed",
                    description="No roles could be assigned successfully.",
                    color=0xff0000
                )
                if failed_roles:
                    embed.add_field(
                        name="Failed roles:",
                        value="\n".join([f"• {role}" for role in failed_roles]),
                        inline=False
                    )
                await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Error in stage command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred while processing the command: {str(e)}",
                color=0xff0000
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    async def _remove_existing_roles(self, user: discord.Member, guild: discord.Guild):
        """Remove any existing roles from the same categories before assigning new ones"""
        try:
            import asyncio
            
            # Get all role IDs that we manage - include ALL possible role IDs from environment
            all_managed_role_ids = set()
            
            # Get all role IDs from environment variables, not just the configured options
            env_role_ids = [
                'ROLE1_OPTION1_ID', 'ROLE1_OPTION2_ID',
                'ROLE2_OPTION1_ID', 'ROLE2_OPTION2_ID', 'ROLE2_OPTION3_ID', 
                'ROLE3_OPTION1_ID', 'ROLE3_OPTION2_ID', 'ROLE3_OPTION3_ID'
            ]
            
            for env_var in env_role_ids:
                role_id = os.getenv(env_var)
                if role_id and role_id.isdigit():
                    all_managed_role_ids.add(int(role_id))
            
            logger.info(f"Looking for roles to remove from user {user}. Managed role IDs: {all_managed_role_ids}")
            
            # Find roles to remove
            roles_to_remove = []
            for role in user.roles:
                if role.id in all_managed_role_ids:
                    roles_to_remove.append(role)
                    logger.info(f"Found role to remove: {role.name} (ID: {role.id})")
            
            if not roles_to_remove:
                logger.info(f"No roles to remove from {user}")
                return
            
            # Remove roles with small delays
            for i, role in enumerate(roles_to_remove):
                try:
                    await user.remove_roles(role, reason="Removing old roles before assigning new ones")
                    logger.info(f"Successfully removed role {role.name} from {user}")
                    
                    # Small delay between removals
                    if i < len(roles_to_remove) - 1:
                        await asyncio.sleep(0.3)
                        
                except discord.Forbidden:
                    logger.error(f"Permission denied removing role {role.name} from {user}")
                except Exception as e:
                    logger.error(f"Error removing role {role.name} from {user}: {e}")
                    
            # Wait a bit after all removals before assigning new roles
            if roles_to_remove:
                await asyncio.sleep(0.5)
                logger.info(f"Completed role removal for {user}")
                
        except Exception as e:
            logger.error(f"Error in _remove_existing_roles: {e}")

    async def setup_hook(self):
        """Called when the bot is starting up"""
        # Start the cleanup task
        self.cleanup_expired_roles.start()
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

    async def on_ready(self):
        """Called when the bot is ready"""
        logger.info(f'{self.user} has logged in!')
        logger.info(f'Bot is in {len(self.guilds)} guild(s)')

    @tasks.loop(minutes=30)
    async def cleanup_expired_roles(self):
        """Background task to remove expired temporary roles"""
        try:
            await self.role_manager.cleanup_expired_roles(self)
        except Exception as e:
            logger.error(f"Error during role cleanup: {e}")

    @cleanup_expired_roles.before_loop
    async def before_cleanup(self):
        await self.wait_until_ready()
