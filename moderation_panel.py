import discord
from discord.ext import commands
from discord import app_commands
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import asyncio

logger = logging.getLogger(__name__)

class ModerationPanel:
    """Comprehensive moderation panel for Discord server management"""
    
    def __init__(self, bot, db_manager, achievement_system):
        self.bot = bot
        self.db_manager = db_manager
        self.achievement_system = achievement_system
        self.active_cases = {}  # Track active moderation cases
    
    async def create_moderation_embed(self, title: str, description: str, color: discord.Color) -> discord.Embed:
        """Create a standardized moderation embed"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.now()
        )
        embed.set_footer(text="Moderation Panel", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        return embed
    
    async def log_moderation_action(self, interaction: discord.Interaction, action: str, target: str, reason: str = None):
        """Log moderation actions for audit trail"""
        log_message = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {interaction.user.name} ({interaction.user.id}) performed {action} on {target}"
        if reason:
            log_message += f" - Reason: {reason}"
        logger.info(log_message)
    
    # User Management Commands
    async def kick_user(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        """Kick a user from the server"""
        try:
            # Check permissions
            if not interaction.user.guild_permissions.kick_members:
                embed = await self.create_moderation_embed(
                    "❌ Permission Denied",
                    "You don't have permission to kick members",
                    discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Check if user can be kicked
            if user.top_role >= interaction.user.top_role:
                embed = await self.create_moderation_embed(
                    "❌ Cannot Kick",
                    "You cannot kick someone with equal or higher role",
                    discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Kick the user
            await user.kick(reason=reason)
            
            # Log the action
            await self.log_moderation_action(interaction, "KICK", f"{user.name} ({user.id})", reason)
            
            # Add punishment record
            await self.db_manager.add_punishment(
                user.id, user.name, "Kick", reason, 
                interaction.user.id, interaction.user.name
            )
            
            # Check for achievements
            new_achievements = await self.achievement_system.check_and_award_achievements(interaction.user.id)
            
            embed = await self.create_moderation_embed(
                "✅ User Kicked",
                f"{user.mention} has been kicked from the server",
                discord.Color.orange()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            if new_achievements:
                achievement_text = "\n".join([f"{ach.emoji} {ach.name}" for ach in new_achievements])
                embed.add_field(name="🎉 New Achievements!", value=achievement_text, inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            embed = await self.create_moderation_embed(
                "❌ Permission Error",
                "I don't have permission to kick this user",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error kicking user: {e}")
            embed = await self.create_moderation_embed(
                "❌ Error",
                "An error occurred while kicking the user",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def ban_user(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided", delete_messages: bool = False):
        """Ban a user from the server"""
        try:
            # Check permissions
            if not interaction.user.guild_permissions.ban_members:
                embed = await self.create_moderation_embed(
                    "❌ Permission Denied",
                    "You don't have permission to ban members",
                    discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Check if user can be banned
            if user.top_role >= interaction.user.top_role:
                embed = await self.create_moderation_embed(
                    "❌ Cannot Ban",
                    "You cannot ban someone with equal or higher role",
                    discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Ban the user
            delete_days = 1 if delete_messages else 0
            await user.ban(reason=reason, delete_message_days=delete_days)
            
            # Log the action
            await self.log_moderation_action(interaction, "BAN", f"{user.name} ({user.id})", reason)
            
            # Add punishment record
            await self.db_manager.add_punishment(
                user.id, user.name, "Ban", reason, 
                interaction.user.id, interaction.user.name
            )
            
            # Check for achievements
            new_achievements = await self.achievement_system.check_and_award_achievements(interaction.user.id)
            
            embed = await self.create_moderation_embed(
                "🔨 User Banned",
                f"{user.mention} has been banned from the server",
                discord.Color.red()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.add_field(name="Messages Deleted", value="Yes" if delete_messages else "No", inline=True)
            
            if new_achievements:
                achievement_text = "\n".join([f"{ach.emoji} {ach.name}" for ach in new_achievements])
                embed.add_field(name="🎉 New Achievements!", value=achievement_text, inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            embed = await self.create_moderation_embed(
                "❌ Permission Error",
                "I don't have permission to ban this user",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error banning user: {e}")
            embed = await self.create_moderation_embed(
                "❌ Error",
                "An error occurred while banning the user",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def timeout_user(self, interaction: discord.Interaction, user: discord.Member, duration: int, reason: str = "No reason provided"):
        """Timeout a user for specified minutes"""
        try:
            # Check permissions
            if not interaction.user.guild_permissions.moderate_members:
                embed = await self.create_moderation_embed(
                    "❌ Permission Denied",
                    "You don't have permission to timeout members",
                    discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Check if user can be timed out
            if user.top_role >= interaction.user.top_role:
                embed = await self.create_moderation_embed(
                    "❌ Cannot Timeout",
                    "You cannot timeout someone with equal or higher role",
                    discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Calculate timeout duration
            timeout_until = datetime.now() + timedelta(minutes=duration)
            
            # Timeout the user
            await user.timeout(timeout_until, reason=reason)
            
            # Log the action
            await self.log_moderation_action(interaction, "TIMEOUT", f"{user.name} ({user.id})", f"{reason} - Duration: {duration} minutes")
            
            # Add punishment record
            await self.db_manager.add_punishment(
                user.id, user.name, "Timeout", f"{reason} - Duration: {duration} minutes", 
                interaction.user.id, interaction.user.name
            )
            
            # Check for achievements
            new_achievements = await self.achievement_system.check_and_award_achievements(interaction.user.id)
            
            embed = await self.create_moderation_embed(
                "⏰ User Timed Out",
                f"{user.mention} has been timed out",
                discord.Color.yellow()
            )
            embed.add_field(name="Duration", value=f"{duration} minutes", inline=True)
            embed.add_field(name="Expires", value=f"<t:{int(timeout_until.timestamp())}:R>", inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            if new_achievements:
                achievement_text = "\n".join([f"{ach.emoji} {ach.name}" for ach in new_achievements])
                embed.add_field(name="🎉 New Achievements!", value=achievement_text, inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            embed = await self.create_moderation_embed(
                "❌ Permission Error",
                "I don't have permission to timeout this user",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error timing out user: {e}")
            embed = await self.create_moderation_embed(
                "❌ Error",
                "An error occurred while timing out the user",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def warn_user(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        """Warn a user"""
        try:
            # Add warning record
            await self.db_manager.add_punishment(
                user.id, user.name, "Warning", reason, 
                interaction.user.id, interaction.user.name
            )
            
            # Log the action
            await self.log_moderation_action(interaction, "WARN", f"{user.name} ({user.id})", reason)
            
            # Check for achievements
            new_achievements = await self.achievement_system.check_and_award_achievements(interaction.user.id)
            
            # Send warning to user via DM
            try:
                dm_embed = await self.create_moderation_embed(
                    "⚠️ Warning",
                    f"You have been warned in {interaction.guild.name}",
                    discord.Color.yellow()
                )
                dm_embed.add_field(name="Reason", value=reason, inline=False)
                dm_embed.add_field(name="Moderator", value=interaction.user.name, inline=True)
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
            embed = await self.create_moderation_embed(
                "⚠️ User Warned",
                f"{user.mention} has been warned",
                discord.Color.yellow()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            if new_achievements:
                achievement_text = "\n".join([f"{ach.emoji} {ach.name}" for ach in new_achievements])
                embed.add_field(name="🎉 New Achievements!", value=achievement_text, inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error warning user: {e}")
            embed = await self.create_moderation_embed(
                "❌ Error",
                "An error occurred while warning the user",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def unban_user(self, interaction: discord.Interaction, user_id: int, reason: str = "No reason provided"):
        """Unban a user by their ID"""
        try:
            # Check permissions
            if not interaction.user.guild_permissions.ban_members:
                embed = await self.create_moderation_embed(
                    "❌ Permission Denied",
                    "You don't have permission to unban members",
                    discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Get the user object
            user = await self.bot.fetch_user(user_id)
            
            # Unban the user
            await interaction.guild.unban(user, reason=reason)
            
            # Log the action
            await self.log_moderation_action(interaction, "UNBAN", f"{user.name} ({user.id})", reason)
            
            embed = await self.create_moderation_embed(
                "✅ User Unbanned",
                f"{user.mention} has been unbanned from the server",
                discord.Color.green()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        except discord.NotFound:
            embed = await self.create_moderation_embed(
                "❌ User Not Found",
                "User is not banned or doesn't exist",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.Forbidden:
            embed = await self.create_moderation_embed(
                "❌ Permission Error",
                "I don't have permission to unban users",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error unbanning user: {e}")
            embed = await self.create_moderation_embed(
                "❌ Error",
                "An error occurred while unbanning the user",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def get_user_info(self, interaction: discord.Interaction, user: discord.Member):
        """Get comprehensive information about a user"""
        try:
            # Get user's punishment history
            punishments = await self.db_manager.get_user_punishments(user.id)
            
            # Get user's achievements if they're staff
            staff_info = await self.db_manager.get_staff_by_id(user.id)
            achievements = []
            if staff_info:
                achievements = await self.achievement_system.get_user_achievements(user.id)
            
            embed = await self.create_moderation_embed(
                f"👤 User Info - {user.display_name}",
                f"Detailed information about {user.mention}",
                discord.Color.blue()
            )
            
            # Basic info
            embed.add_field(name="Username", value=f"{user.name}#{user.discriminator}", inline=True)
            embed.add_field(name="User ID", value=user.id, inline=True)
            embed.add_field(name="Nickname", value=user.nick or "None", inline=True)
            
            # Dates
            embed.add_field(name="Account Created", value=f"<t:{int(user.created_at.timestamp())}:R>", inline=True)
            embed.add_field(name="Joined Server", value=f"<t:{int(user.joined_at.timestamp())}:R>", inline=True)
            
            # Roles
            roles = [role.mention for role in user.roles[1:]]  # Skip @everyone
            embed.add_field(name="Roles", value=", ".join(roles) if roles else "None", inline=False)
            
            # Staff info
            if staff_info:
                embed.add_field(name="Staff Role", value=staff_info['role'], inline=True)
                embed.add_field(name="Staff Since", value=staff_info['added_date'], inline=True)
                embed.add_field(name="Achievements", value=f"{len(achievements)} earned", inline=True)
            
            # Punishment history
            if punishments:
                recent_punishments = punishments[:5]  # Show last 5
                punishment_text = "\n".join([
                    f"**{p['punishment_type']}** - {p['reason']} ({p['punishment_date']})"
                    for p in recent_punishments
                ])
                embed.add_field(name="Recent Punishments", value=punishment_text, inline=False)
                
                if len(punishments) > 5:
                    embed.add_field(name="Total Punishments", value=f"{len(punishments)} total", inline=True)
            else:
                embed.add_field(name="Punishment History", value="Clean record", inline=True)
            
            # Set user avatar
            if user.avatar:
                embed.set_thumbnail(url=user.avatar.url)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            embed = await self.create_moderation_embed(
                "❌ Error",
                "An error occurred while retrieving user information",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def bulk_delete_messages(self, interaction: discord.Interaction, channel: discord.TextChannel, amount: int):
        """Bulk delete messages from a channel"""
        try:
            # Check permissions
            if not interaction.user.guild_permissions.manage_messages:
                embed = await self.create_moderation_embed(
                    "❌ Permission Denied",
                    "You don't have permission to manage messages",
                    discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Validate amount
            if amount < 1 or amount > 100:
                embed = await self.create_moderation_embed(
                    "❌ Invalid Amount",
                    "Amount must be between 1 and 100",
                    discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Delete messages
            deleted = await channel.purge(limit=amount)
            
            # Log the action
            await self.log_moderation_action(interaction, "BULK_DELETE", f"{len(deleted)} messages in {channel.name}")
            
            embed = await self.create_moderation_embed(
                "✅ Messages Deleted",
                f"Successfully deleted {len(deleted)} messages from {channel.mention}",
                discord.Color.green()
            )
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            embed = await self.create_moderation_embed(
                "❌ Permission Error",
                "I don't have permission to delete messages in that channel",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error bulk deleting messages: {e}")
            embed = await self.create_moderation_embed(
                "❌ Error",
                "An error occurred while deleting messages",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)