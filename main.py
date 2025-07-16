import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import logging
from datetime import datetime
from database import DatabaseManager
from achievements import AchievementSystem
from moderation_panel import ModerationPanel
from economy_system import EconomySystem, JobType
from admin_panel import AdminPanel

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Required intents for the bot
intents = discord.Intents.default()
intents.message_content = False  # Not needed for slash commands
intents.guilds = True

# Initialize bot with command prefix and intents
bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize database manager and systems
db_manager = DatabaseManager()
achievement_system = AchievementSystem(db_manager)
moderation_panel = ModerationPanel(bot, db_manager, achievement_system)
economy_system = EconomySystem(bot, db_manager)
admin_panel = AdminPanel(bot, db_manager, economy_system)

@bot.event
async def on_ready():
    """Event triggered when bot is ready and connected"""
    logger.info(f'{bot.user} has connected to Discord!')
    
    # Initialize database
    await db_manager.initialize_database()
    logger.info('Database initialized successfully')
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        logger.info(f'Synced {len(synced)} slash command(s)')
    except Exception as e:
        logger.error(f'Failed to sync commands: {e}')

def is_admin():
    """Check if user has administrator permissions"""
    def predicate(interaction: discord.Interaction):
        return interaction.user.guild_permissions.administrator
    return discord.app_commands.check(predicate)

# Staff Management Commands
@bot.tree.command(name='add_staff', description='Add a staff member to the database')
@discord.app_commands.describe(
    user='The user to add as staff',
    role='The staff role (e.g., Moderator, Admin)',
    notes='Optional notes about the staff member'
)
@is_admin()
async def add_staff(interaction: discord.Interaction, user: discord.Member, role: str, notes: str = None):
    """Add a staff member to the database"""
    try:
        success = await db_manager.add_staff(user.id, user.name, role, notes)
        
        if success:
            embed = discord.Embed(
                title="✅ Staff Added",
                description=f"Successfully added {user.mention} as {role}",
                color=discord.Color.green()
            )
            if notes:
                embed.add_field(name="Notes", value=notes, inline=False)
            
            # Check for new achievements
            new_achievements = await achievement_system.check_and_award_achievements(user.id)
            if new_achievements:
                achievement_text = "\n".join([f"{ach.emoji} {ach.name}" for ach in new_achievements])
                embed.add_field(name="🎉 New Achievements!", value=achievement_text, inline=False)
        else:
            embed = discord.Embed(
                title="❌ Error",
                description=f"{user.mention} is already in the staff database",
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f'Error adding staff: {e}')
        embed = discord.Embed(
            title="❌ Database Error",
            description="An error occurred while adding the staff member",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name='remove_staff', description='Remove a staff member from the database')
@discord.app_commands.describe(user='The user to remove from staff')
@is_admin()
async def remove_staff(interaction: discord.Interaction, user: discord.Member):
    """Remove a staff member from the database"""
    try:
        success = await db_manager.remove_staff(user.id)
        
        if success:
            embed = discord.Embed(
                title="✅ Staff Removed",
                description=f"Successfully removed {user.mention} from staff database",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Not Found",
                description=f"{user.mention} is not in the staff database",
                color=discord.Color.orange()
            )
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f'Error removing staff: {e}')
        embed = discord.Embed(
            title="❌ Database Error",
            description="An error occurred while removing the staff member",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name='list_staff', description='View all staff members in the database')
async def list_staff(interaction: discord.Interaction):
    """List all staff members"""
    try:
        staff_list = await db_manager.get_all_staff()
        
        if not staff_list:
            embed = discord.Embed(
                title="📋 Staff List",
                description="No staff members found in the database",
                color=discord.Color.blue()
            )
        else:
            embed = discord.Embed(
                title="📋 Staff List",
                description=f"Total staff members: {len(staff_list)}",
                color=discord.Color.blue()
            )
            
            for staff in staff_list:
                user = bot.get_user(staff['user_id'])
                username = user.mention if user else f"Unknown User ({staff['user_id']})"
                
                field_value = f"**Role:** {staff['role']}"
                if staff['notes']:
                    field_value += f"\n**Notes:** {staff['notes']}"
                field_value += f"\n**Added:** {staff['added_date']}"
                
                embed.add_field(
                    name=f"{staff['username']} ({username})",
                    value=field_value,
                    inline=True
                )
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f'Error listing staff: {e}')
        embed = discord.Embed(
            title="❌ Database Error",
            description="An error occurred while retrieving staff list",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# Punishment Management Commands
@bot.tree.command(name='add_punishment', description='Add a punishment record to the database')
@discord.app_commands.describe(
    user='The user who was punished',
    punishment_type='Type of punishment (e.g., Ban, Kick, Mute)',
    reason='Reason for the punishment',
    moderator='The moderator who issued the punishment'
)
@is_admin()
async def add_punishment(interaction: discord.Interaction, user: discord.Member, punishment_type: str, reason: str, moderator: discord.Member = None):
    """Add a punishment record to the database"""
    try:
        if moderator is None:
            moderator = interaction.user
            
        success = await db_manager.add_punishment(user.id, user.name, punishment_type, reason, moderator.id, moderator.name)
        
        if success:
            embed = discord.Embed(
                title="⚖️ Punishment Added",
                description=f"Punishment record added for {user.mention}",
                color=discord.Color.orange()
            )
            embed.add_field(name="Type", value=punishment_type, inline=True)
            embed.add_field(name="Moderator", value=moderator.mention, inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            
            # Check for new achievements for the moderator
            new_achievements = await achievement_system.check_and_award_achievements(moderator.id)
            if new_achievements:
                achievement_text = "\n".join([f"{ach.emoji} {ach.name}" for ach in new_achievements])
                embed.add_field(name="🎉 New Achievements!", value=achievement_text, inline=False)
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to add punishment record",
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f'Error adding punishment: {e}')
        embed = discord.Embed(
            title="❌ Database Error",
            description="An error occurred while adding the punishment record",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name='remove_punishment', description='Remove a punishment record by ID')
@discord.app_commands.describe(punishment_id='The ID of the punishment to remove')
@is_admin()
async def remove_punishment(interaction: discord.Interaction, punishment_id: int):
    """Remove a punishment record by ID"""
    try:
        success = await db_manager.remove_punishment(punishment_id)
        
        if success:
            embed = discord.Embed(
                title="✅ Punishment Removed",
                description=f"Successfully removed punishment record #{punishment_id}",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Not Found",
                description=f"Punishment record #{punishment_id} not found",
                color=discord.Color.orange()
            )
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f'Error removing punishment: {e}')
        embed = discord.Embed(
            title="❌ Database Error",
            description="An error occurred while removing the punishment record",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name='list_punishments', description='View punishment records for a user')
@discord.app_commands.describe(user='The user to check punishments for (optional)')
async def list_punishments(interaction: discord.Interaction, user: discord.Member = None):
    """List punishment records"""
    try:
        if user:
            punishments = await db_manager.get_user_punishments(user.id)
            title = f"⚖️ Punishments for {user.display_name}"
        else:
            punishments = await db_manager.get_all_punishments()
            title = "⚖️ All Punishment Records"
        
        if not punishments:
            description = "No punishment records found" if not user else f"No punishment records found for {user.mention}"
            embed = discord.Embed(
                title=title,
                description=description,
                color=discord.Color.blue()
            )
        else:
            embed = discord.Embed(
                title=title,
                description=f"Total records: {len(punishments)}",
                color=discord.Color.orange()
            )
            
            for punishment in punishments[:10]:  # Limit to 10 records to avoid embed limits
                target_user = bot.get_user(punishment['user_id'])
                target_name = target_user.mention if target_user else f"Unknown User ({punishment['user_id']})"
                
                moderator_user = bot.get_user(punishment['moderator_id'])
                moderator_name = moderator_user.mention if moderator_user else f"Unknown Moderator ({punishment['moderator_id']})"
                
                field_value = f"**User:** {target_name}\n"
                field_value += f"**Type:** {punishment['punishment_type']}\n"
                field_value += f"**Moderator:** {moderator_name}\n"
                field_value += f"**Date:** {punishment['punishment_date']}\n"
                field_value += f"**Reason:** {punishment['reason']}"
                
                embed.add_field(
                    name=f"ID: {punishment['id']}",
                    value=field_value,
                    inline=True
                )
            
            if len(punishments) > 10:
                embed.set_footer(text=f"Showing first 10 of {len(punishments)} records")
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f'Error listing punishments: {e}')
        embed = discord.Embed(
            title="❌ Database Error",
            description="An error occurred while retrieving punishment records",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# Utility Commands
@bot.tree.command(name='bot_info', description='Display bot information and statistics')
async def bot_info(interaction: discord.Interaction):
    """Display bot information"""
    try:
        staff_count = len(await db_manager.get_all_staff())
        punishment_count = len(await db_manager.get_all_punishments())
        
        embed = discord.Embed(
            title="🤖 Bot Information",
            description="Discord Staff & Punishment Management Bot",
            color=discord.Color.blue()
        )
        embed.add_field(name="Servers", value=len(bot.guilds), inline=True)
        embed.add_field(name="Staff Records", value=staff_count, inline=True)
        embed.add_field(name="Punishment Records", value=punishment_count, inline=True)
        embed.add_field(name="Bot Latency", value=f"{round(bot.latency * 1000)}ms", inline=True)
        embed.set_footer(text="Use /help for command information")
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f'Error getting bot info: {e}')
        embed = discord.Embed(
            title="❌ Error",
            description="An error occurred while retrieving bot information",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# Achievement Management Commands
@bot.tree.command(name='my_achievements', description='View your achievements and badges')
async def my_achievements(interaction: discord.Interaction):
    """Display user's achievements"""
    try:
        # Check if user is staff
        staff_info = await db_manager.get_staff_by_id(interaction.user.id)
        if not staff_info:
            embed = discord.Embed(
                title="❌ Not a Staff Member",
                description="You need to be a staff member to view achievements",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Get user achievements
        achievements = await achievement_system.get_user_achievements(interaction.user.id)
        
        if not achievements:
            embed = discord.Embed(
                title="🏆 Your Achievements",
                description="No achievements yet! Keep working to earn your first badge!",
                color=discord.Color.blue()
            )
        else:
            embed = discord.Embed(
                title="🏆 Your Achievements",
                description=f"You have earned {len(achievements)} achievements!",
                color=discord.Color.gold()
            )
            
            # Group achievements by rarity
            rarity_groups = {}
            for ach in achievements:
                rarity = ach['rarity']
                if rarity not in rarity_groups:
                    rarity_groups[rarity] = []
                rarity_groups[rarity].append(ach)
            
            # Display achievements grouped by rarity
            rarity_order = ['legendary', 'epic', 'rare', 'uncommon', 'common']
            for rarity in rarity_order:
                if rarity in rarity_groups:
                    rarity_achs = rarity_groups[rarity]
                    rarity_text = "\n".join([f"{ach['emoji']} **{ach['name']}**\n{ach['description']}" for ach in rarity_achs])
                    embed.add_field(
                        name=f"{rarity.title()} Achievements",
                        value=rarity_text,
                        inline=False
                    )
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f'Error displaying achievements: {e}')
        embed = discord.Embed(
            title="❌ Error",
            description="An error occurred while retrieving your achievements",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name='leaderboard', description='View the achievement leaderboard')
async def leaderboard(interaction: discord.Interaction):
    """Display achievement leaderboard"""
    try:
        all_staff = await db_manager.get_all_staff()
        
        if not all_staff:
            embed = discord.Embed(
                title="🏆 Achievement Leaderboard",
                description="No staff members found",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        # Get achievement counts for each staff member
        leaderboard_data = []
        for staff in all_staff:
            achievements = await achievement_system.get_user_achievements(staff['user_id'])
            
            # Count achievements by rarity
            rarity_counts = {'legendary': 0, 'epic': 0, 'rare': 0, 'uncommon': 0, 'common': 0}
            for ach in achievements:
                rarity_counts[ach['rarity']] += 1
            
            # Calculate weighted score
            weights = {'legendary': 50, 'epic': 25, 'rare': 10, 'uncommon': 5, 'common': 1}
            total_score = sum(rarity_counts[rarity] * weights[rarity] for rarity in rarity_counts)
            
            leaderboard_data.append({
                'user_id': staff['user_id'],
                'username': staff['username'],
                'role': staff['role'],
                'total_achievements': len(achievements),
                'score': total_score,
                'rarity_counts': rarity_counts
            })
        
        # Sort by score (descending)
        leaderboard_data.sort(key=lambda x: x['score'], reverse=True)
        
        embed = discord.Embed(
            title="🏆 Achievement Leaderboard",
            description="Top staff members by achievement score",
            color=discord.Color.gold()
        )
        
        for i, staff_data in enumerate(leaderboard_data[:10], 1):
            user = bot.get_user(staff_data['user_id'])
            username = user.mention if user else staff_data['username']
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
            
            field_value = f"**Role:** {staff_data['role']}\n"
            field_value += f"**Total Achievements:** {staff_data['total_achievements']}\n"
            field_value += f"**Score:** {staff_data['score']}\n"
            
            # Show rarity breakdown
            rarity_text = []
            for rarity in ['legendary', 'epic', 'rare', 'uncommon', 'common']:
                count = staff_data['rarity_counts'][rarity]
                if count > 0:
                    rarity_text.append(f"{rarity.title()}: {count}")
            
            if rarity_text:
                field_value += f"**Breakdown:** {', '.join(rarity_text)}"
            
            embed.add_field(
                name=f"{medal} {username}",
                value=field_value,
                inline=True
            )
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f'Error displaying leaderboard: {e}')
        embed = discord.Embed(
            title="❌ Error",
            description="An error occurred while retrieving the leaderboard",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name='all_achievements', description='View all available achievements')
async def all_achievements(interaction: discord.Interaction):
    """Display all available achievements"""
    try:
        all_achievements = achievement_system.get_all_achievements()
        
        embed = discord.Embed(
            title="🎯 All Available Achievements",
            description="Complete list of achievements you can earn",
            color=discord.Color.blue()
        )
        
        # Group by rarity
        rarity_groups = {}
        for ach_id, ach in all_achievements.items():
            rarity = ach.rarity
            if rarity not in rarity_groups:
                rarity_groups[rarity] = []
            rarity_groups[rarity].append(ach)
        
        # Display achievements grouped by rarity
        rarity_order = ['legendary', 'epic', 'rare', 'uncommon', 'common']
        for rarity in rarity_order:
            if rarity in rarity_groups:
                rarity_achs = rarity_groups[rarity]
                rarity_text = "\n".join([f"{ach.emoji} **{ach.name}**\n{ach.description}" for ach in rarity_achs])
                
                embed.add_field(
                    name=f"{rarity.title()} Achievements",
                    value=rarity_text,
                    inline=False
                )
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f'Error displaying all achievements: {e}')
        embed = discord.Embed(
            title="❌ Error",
            description="An error occurred while retrieving achievements",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# Moderation Panel Commands
@bot.tree.command(name='kick', description='Kick a user from the server')
@discord.app_commands.describe(
    user='The user to kick',
    reason='Reason for kicking (optional)'
)
@is_admin()
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    """Kick a user from the server"""
    await moderation_panel.kick_user(interaction, user, reason)

@bot.tree.command(name='ban', description='Ban a user from the server')
@discord.app_commands.describe(
    user='The user to ban',
    reason='Reason for banning (optional)',
    delete_messages='Delete recent messages from the user'
)
@is_admin()
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided", delete_messages: bool = False):
    """Ban a user from the server"""
    await moderation_panel.ban_user(interaction, user, reason, delete_messages)

@bot.tree.command(name='timeout', description='Timeout a user for specified minutes')
@discord.app_commands.describe(
    user='The user to timeout',
    duration='Duration in minutes (1-40320)',
    reason='Reason for timeout (optional)'
)
@is_admin()
async def timeout(interaction: discord.Interaction, user: discord.Member, duration: int, reason: str = "No reason provided"):
    """Timeout a user"""
    if duration < 1 or duration > 40320:  # Discord's max timeout is 28 days
        embed = discord.Embed(
            title="❌ Invalid Duration",
            description="Duration must be between 1 and 40320 minutes (28 days)",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    await moderation_panel.timeout_user(interaction, user, duration, reason)

@bot.tree.command(name='warn', description='Warn a user')
@discord.app_commands.describe(
    user='The user to warn',
    reason='Reason for warning (optional)'
)
@is_admin()
async def warn(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    """Warn a user"""
    await moderation_panel.warn_user(interaction, user, reason)

@bot.tree.command(name='unban', description='Unban a user by their ID')
@discord.app_commands.describe(
    user_id='The ID of the user to unban',
    reason='Reason for unbanning (optional)'
)
@is_admin()
async def unban(interaction: discord.Interaction, user_id: str, reason: str = "No reason provided"):
    """Unban a user by ID"""
    try:
        user_id_int = int(user_id)
        await moderation_panel.unban_user(interaction, user_id_int, reason)
    except ValueError:
        embed = discord.Embed(
            title="❌ Invalid User ID",
            description="Please provide a valid user ID (numbers only)",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name='userinfo', description='Get detailed information about a user')
@discord.app_commands.describe(user='The user to get information about')
async def userinfo(interaction: discord.Interaction, user: discord.Member):
    """Get user information"""
    await moderation_panel.get_user_info(interaction, user)

@bot.tree.command(name='purge', description='Delete multiple messages from a channel')
@discord.app_commands.describe(
    amount='Number of messages to delete (1-100)',
    channel='Channel to delete messages from (optional)'
)
@is_admin()
async def purge(interaction: discord.Interaction, amount: int, channel: discord.TextChannel = None):
    """Bulk delete messages"""
    if channel is None:
        channel = interaction.channel
    
    await moderation_panel.bulk_delete_messages(interaction, channel, amount)

@bot.tree.command(name='modstats', description='View moderation statistics')
@is_admin()
async def modstats(interaction: discord.Interaction):
    """Display moderation statistics"""
    try:
        # Get staff count
        staff_count = len(await db_manager.get_all_staff())
        
        # Get punishment statistics
        all_punishments = await db_manager.get_all_punishments()
        
        # Count punishment types
        punishment_types = {}
        recent_punishments = []
        
        for punishment in all_punishments:
            p_type = punishment['punishment_type']
            punishment_types[p_type] = punishment_types.get(p_type, 0) + 1
            
            # Get recent punishments (last 7 days)
            punishment_date = datetime.fromisoformat(punishment['punishment_date'])
            if (datetime.now() - punishment_date).days <= 7:
                recent_punishments.append(punishment)
        
        # Get top moderators
        moderator_counts = {}
        for punishment in all_punishments:
            mod_id = punishment['moderator_id']
            moderator_counts[mod_id] = moderator_counts.get(mod_id, 0) + 1
        
        # Sort moderators by activity
        top_moderators = sorted(moderator_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        embed = discord.Embed(
            title="📊 Moderation Statistics",
            description="Server moderation overview",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        # General stats
        embed.add_field(name="Staff Members", value=staff_count, inline=True)
        embed.add_field(name="Total Punishments", value=len(all_punishments), inline=True)
        embed.add_field(name="Recent (7 days)", value=len(recent_punishments), inline=True)
        
        # Punishment breakdown
        if punishment_types:
            type_text = "\n".join([f"{p_type}: {count}" for p_type, count in punishment_types.items()])
            embed.add_field(name="Punishment Types", value=type_text, inline=True)
        
        # Top moderators
        if top_moderators:
            mod_text = ""
            for mod_id, count in top_moderators:
                user = bot.get_user(mod_id)
                name = user.mention if user else f"Unknown ({mod_id})"
                mod_text += f"{name}: {count}\n"
            embed.add_field(name="Top Moderators", value=mod_text, inline=True)
        
        # Server info
        embed.add_field(name="Server Members", value=interaction.guild.member_count, inline=True)
        embed.add_field(name="Text Channels", value=len(interaction.guild.text_channels), inline=True)
        embed.add_field(name="Voice Channels", value=len(interaction.guild.voice_channels), inline=True)
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f'Error getting moderation stats: {e}')
        embed = discord.Embed(
            title="❌ Error",
            description="An error occurred while retrieving moderation statistics",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# Economy System Commands
@bot.tree.command(name="balance", description="Check your balance or another user's balance")
async def balance(interaction: discord.Interaction, user: discord.Member = None):
    """Show user's balance and stats"""
    await economy_system.show_balance(interaction, user)

@bot.tree.command(name="daily", description="Claim your daily reward")
async def daily(interaction: discord.Interaction):
    """Give daily reward to user"""
    await economy_system.daily_reward(interaction)

@bot.tree.command(name="work", description="Work a job to earn money")
async def work(interaction: discord.Interaction, job: str):
    """Work a job to earn money"""
    # Convert job string to JobType enum
    job_map = {
        "moderator": JobType.MODERATOR,
        "helper": JobType.HELPER,
        "streamer": JobType.STREAMER,
        "artist": JobType.ARTIST,
        "developer": JobType.DEVELOPER,
        "trader": JobType.TRADER,
        "security": JobType.SECURITY,
        "teacher": JobType.TEACHER,
        "designer": JobType.DESIGNER,
        "writer": JobType.WRITER,
        "musician": JobType.MUSICIAN,
        "chef": JobType.CHEF,
        "photographer": JobType.PHOTOGRAPHER,
        "gamer": JobType.GAMER,
        "scientist": JobType.SCIENTIST,
        "lawyer": JobType.LAWYER,
        "doctor": JobType.DOCTOR,
        "engineer": JobType.ENGINEER,
        "miner": JobType.MINER,
        "fisher": JobType.FISHER
    }
    
    if job.lower() not in job_map:
        embed = discord.Embed(
            title="❌ Invalid Job",
            description=f"Available jobs: {', '.join(job_map.keys())}",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    await economy_system.work_job(interaction, job_map[job.lower()])

@bot.tree.command(name="crime", description="Commit a crime for potential money (risky)")
async def crime(interaction: discord.Interaction):
    """Commit a crime for potential money (risky)"""
    await economy_system.commit_crime(interaction)

@bot.tree.command(name="gamble", description="Gamble your money with 50/50 chance")
async def gamble(interaction: discord.Interaction, amount: int):
    """Gamble coins with 50/50 chance"""
    await economy_system.gamble_coins(interaction, amount)

@bot.tree.command(name="transfer", description="Transfer money to another user")
async def transfer(interaction: discord.Interaction, user: discord.Member, amount: int):
    """Transfer money between users"""
    await economy_system.transfer_money(interaction, user, amount)

@bot.tree.command(name="shop", description="View the economy shop")
async def shop(interaction: discord.Interaction):
    """Display the shop with available items"""
    await economy_system.show_shop(interaction)

@bot.tree.command(name="buy", description="Buy an item from the shop")
async def buy(interaction: discord.Interaction, item: str):
    """Buy an item from the shop"""
    await economy_system.buy_item(interaction, item)

@bot.tree.command(name="inventory", description="View your inventory or another user's inventory")
async def inventory(interaction: discord.Interaction, user: discord.Member = None):
    """Show user's inventory"""
    await economy_system.show_inventory(interaction, user)

@bot.tree.command(name="eco_leaderboard", description="View the economy leaderboard")
async def eco_leaderboard(interaction: discord.Interaction):
    """Show economy leaderboard"""
    await economy_system.show_leaderboard(interaction)

@bot.tree.command(name="jobs", description="View all available jobs and their requirements")
async def jobs(interaction: discord.Interaction):
    """Display all available jobs"""
    try:
        user_level = await economy_system.get_user_level(interaction.user.id)
        
        embed = discord.Embed(
            title="💼 Available Jobs",
            description=f"Your current level: **{user_level}**\nJobs you can work:",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        available_jobs = []
        locked_jobs = []
        
        for job_type, job_info in economy_system.jobs.items():
            level_req = job_info["requirements"]["level"]
            pay_range = f"{job_info['base_pay'][0]}-{job_info['base_pay'][1]}"
            cooldown_hours = job_info["cooldown"] / 3600
            
            job_text = f"**{job_info['name']}**\n{job_info['description']}\n💰 Pay: {pay_range} Credits\n⏰ Cooldown: {cooldown_hours:.1f}h\n📊 Level: {level_req}"
            
            if user_level >= level_req:
                available_jobs.append(job_text)
            else:
                locked_jobs.append(job_text)
        
        # Show available jobs
        for i, job in enumerate(available_jobs[:10]):  # Show first 10 available
            embed.add_field(name="✅ Available", value=job, inline=True)
        
        # Show locked jobs
        for i, job in enumerate(locked_jobs[:5]):  # Show first 5 locked
            embed.add_field(name="🔒 Locked", value=job, inline=True)
        
        embed.add_field(
            name="How to Work",
            value="Use `/work <job_name>` to work a job\nExample: `/work moderator`",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in jobs command: {e}")
        await interaction.response.send_message(
            "❌ An error occurred while fetching job information.", 
            ephemeral=True
        )

@bot.tree.command(name="claim_level_rewards", description="Claim all pending level rewards")
async def claim_level_rewards(interaction: discord.Interaction):
    """Claim all pending level rewards"""
    try:
        user_id = interaction.user.id
        current_level = await economy_system.get_user_level(user_id)
        claimed_levels = await db_manager.get_claimed_level_rewards(user_id)
        
        # Find unclaimed levels
        unclaimed_levels = [level for level in range(1, current_level + 1) if level not in claimed_levels]
        
        if not unclaimed_levels:
            embed = discord.Embed(
                title="✅ All Rewards Claimed",
                description="You have already claimed all available level rewards!",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        total_credits = 0
        total_items = []
        
        # Process each unclaimed level
        for level in unclaimed_levels:
            level_rewards = await economy_system.get_level_rewards(level)
            await db_manager.claim_level_reward(user_id, level)
            
            # Give rewards
            if level_rewards["credits"] > 0:
                await economy_system.add_money(user_id, level_rewards["credits"], f"Level {level} reward")
                total_credits += level_rewards["credits"]
            
            for item_id in level_rewards["items"]:
                if item_id in economy_system.shop_items:
                    await db_manager.add_item_to_inventory(user_id, item_id, 1)
                    total_items.append(economy_system.shop_items[item_id]["name"])
        
        embed = discord.Embed(
            title="🎉 Level Rewards Claimed!",
            description=f"Claimed rewards for levels {min(unclaimed_levels)} to {max(unclaimed_levels)}",
            color=discord.Color.gold()
        )
        
        embed.add_field(name="Credits Earned", value=f"{total_credits} Credits", inline=True)
        embed.add_field(name="Items Received", value=f"{len(total_items)} items", inline=True)
        embed.add_field(name="Current Level", value=f"Level {current_level}", inline=True)
        
        if total_items:
            items_text = "\n".join(total_items[:10])  # Show first 10 items
            if len(total_items) > 10:
                items_text += f"\n... and {len(total_items) - 10} more items"
            embed.add_field(name="Items Received", value=items_text, inline=False)
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in claim_level_rewards command: {e}")
        await interaction.response.send_message(
            "❌ An error occurred while claiming level rewards.", 
            ephemeral=True
        )

@bot.tree.command(name="level_progress", description="View your level progress and next rewards")
async def level_progress(interaction: discord.Interaction):
    """Display user's level progress"""
    try:
        user_id = interaction.user.id
        current_level = await economy_system.get_user_level(user_id)
        total_earned = await db_manager.get_user_total_earned(user_id)
        
        # Calculate progress to next level
        current_level_requirement = (current_level - 1) * 1000
        next_level_requirement = current_level * 1000
        progress = total_earned - current_level_requirement
        progress_needed = next_level_requirement - total_earned
        
        embed = discord.Embed(
            title="📊 Level Progress",
            description=f"Level progression for {interaction.user.display_name}",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Current Level", value=f"Level {current_level}", inline=True)
        embed.add_field(name="Total Earned", value=f"{total_earned} Credits", inline=True)
        embed.add_field(name="Next Level", value=f"Level {current_level + 1}", inline=True)
        
        if current_level < 600:
            embed.add_field(name="Progress", value=f"{progress}/1000 Credits", inline=True)
            embed.add_field(name="Needed", value=f"{progress_needed} Credits", inline=True)
            
            # Progress bar
            progress_percentage = (progress / 1000) * 100
            progress_bar = "█" * int(progress_percentage // 10) + "░" * (10 - int(progress_percentage // 10))
            embed.add_field(name="Progress Bar", value=f"`{progress_bar}` {progress_percentage:.1f}%", inline=True)
            
            # Show next level rewards
            next_rewards = await economy_system.get_level_rewards(current_level + 1)
            if next_rewards["credits"] > 0 or next_rewards["items"]:
                reward_text = f"Credits: {next_rewards['credits']}"
                if next_rewards["items"]:
                    reward_text += f"\nItems: {len(next_rewards['items'])}"
                if next_rewards["title"]:
                    reward_text += f"\nTitle: {next_rewards['title']}"
                if next_rewards["special"]:
                    reward_text += f"\nSpecial: {next_rewards['special']}"
                
                embed.add_field(name="Next Level Rewards", value=reward_text, inline=False)
        else:
            embed.add_field(name="Status", value="Maximum level reached!", inline=False)
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in level_progress command: {e}")
        await interaction.response.send_message(
            "❌ An error occurred while fetching level progress.", 
            ephemeral=True
        )

@bot.tree.command(name="eco_stats", description="View economy statistics")
@is_admin()
async def eco_stats(interaction: discord.Interaction):
    """Display economy statistics"""
    try:
        stats = await db_manager.get_economy_stats()
        
        embed = discord.Embed(
            title="💰 Economy Statistics",
            description="Server economy overview",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="👥 Users",
            value=f"**Total Users:** {stats['total_users']}\n"
                  f"**Average Balance:** {stats['average_balance']} Credits",
            inline=True
        )
        
        embed.add_field(
            name="💸 Economy",
            value=f"**Total Money:** {stats['total_money']} Credits\n"
                  f"**Total Transactions:** {stats['total_transactions']}",
            inline=True
        )
        
        embed.add_field(
            name="🛍️ Shop",
            value=f"**Total Items:** {len(economy_system.shop_items)}\n"
                  f"**Max Level:** 600",
            inline=True
        )
        
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in eco_stats command: {e}")
        await interaction.response.send_message(
            "❌ An error occurred while fetching economy statistics.", 
            ephemeral=True
        )

# =============================================================================
# ADMIN PANEL COMMANDS
# =============================================================================

@bot.tree.command(name="admin_panel", description="Access admin panel (Authorized users only)")
async def admin_panel_menu(interaction: discord.Interaction):
    """Display admin panel menu"""
    await admin_panel.show_admin_menu(interaction)

@bot.tree.command(name="admin_give_money", description="Give money to a user (Admin only)")
async def admin_give_money(interaction: discord.Interaction, user: discord.Member, amount: int):
    """Give money to a user"""
    await admin_panel.give_money(interaction, user, amount)

@bot.tree.command(name="admin_remove_money", description="Remove money from a user (Admin only)")
async def admin_remove_money(interaction: discord.Interaction, user: discord.Member, amount: int):
    """Remove money from a user"""
    await admin_panel.remove_money(interaction, user, amount)

@bot.tree.command(name="admin_give_item", description="Give an item to a user (Admin only)")
async def admin_give_item(interaction: discord.Interaction, user: discord.Member, item_id: str, quantity: int = 1):
    """Give an item to a user"""
    await admin_panel.give_item(interaction, user, item_id, quantity)

@bot.tree.command(name="admin_set_level", description="Set a user's level (Admin only)")
async def admin_set_level(interaction: discord.Interaction, user: discord.Member, level: int):
    """Set a user's level"""
    await admin_panel.set_user_level(interaction, user, level)

@bot.tree.command(name="admin_user_stats", description="Get comprehensive user statistics (Admin only)")
async def admin_user_stats(interaction: discord.Interaction, user: discord.Member):
    """Get user statistics"""
    await admin_panel.get_user_stats(interaction, user)

@bot.tree.command(name="admin_list_items", description="List available items (Admin only)")
async def admin_list_items(interaction: discord.Interaction, category: str = None):
    """List available items"""
    await admin_panel.list_items(interaction, category)

@bot.tree.command(name="admin_reset_user", description="Reset a user's economy data (Admin only)")
async def admin_reset_user(interaction: discord.Interaction, user: discord.Member):
    """Reset a user's economy data"""
    if not admin_panel.is_authorized_admin(interaction.user):
        await interaction.response.send_message(
            "❌ Access denied. This command is restricted to authorized administrators.",
            ephemeral=True
        )
        return
    
    try:
        # Reset user's economy data
        import aiosqlite
        async with aiosqlite.connect(db_manager.db_path) as db:
            await db.execute("DELETE FROM economy_users WHERE user_id = ?", (user.id,))
            await db.execute("DELETE FROM economy_transactions WHERE user_id = ?", (user.id,))
            await db.execute("DELETE FROM economy_inventory WHERE user_id = ?", (user.id,))
            await db.execute("DELETE FROM level_rewards WHERE user_id = ?", (user.id,))
            await db.commit()
        
        embed = discord.Embed(
            title="🔧 Admin Panel - User Reset",
            description=f"Successfully reset all economy data for {user.mention}",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Reset Data", value="Balance, Inventory, Level Rewards, Transactions", inline=False)
        embed.add_field(name="Admin", value=interaction.user.mention, inline=True)
        embed.set_footer(text="Admin Panel - Authorized Personnel Only")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        logger.error(f"Error in admin_reset_user: {e}")
        await interaction.response.send_message(
            "❌ An error occurred while resetting user data.",
            ephemeral=True
        )

@bot.tree.command(name="admin_clear_inventory", description="Clear a user's inventory (Admin only)")
async def admin_clear_inventory(interaction: discord.Interaction, user: discord.Member):
    """Clear a user's inventory"""
    await admin_panel.clear_inventory(interaction, user)

@bot.tree.command(name="admin_remove_item", description="Remove an item from a user's inventory (Admin only)")
async def admin_remove_item(interaction: discord.Interaction, user: discord.Member, item_id: str):
    """Remove an item from a user's inventory"""
    await admin_panel.remove_item(interaction, user, item_id)

@bot.tree.command(name="admin_server_stats", description="Get comprehensive server statistics (Admin only)")
async def admin_server_stats(interaction: discord.Interaction):
    """Get server statistics"""
    await admin_panel.server_stats(interaction)

# =============================================================================
# ENHANCED SHOP COMMANDS
# =============================================================================

@bot.tree.command(name="shop_category", description="Browse shop items by category")
async def shop_category(interaction: discord.Interaction, category: str = None):
    """Browse shop items by category"""
    await economy_system.show_shop_category(interaction, category)

@bot.tree.command(name="search_items", description="Search for items by name or description")
async def search_items(interaction: discord.Interaction, search_term: str):
    """Search for items"""
    await economy_system.search_items(interaction, search_term)

@bot.tree.command(name="item_details", description="View detailed information about a specific item")
async def item_details(interaction: discord.Interaction, item_id: str):
    """View item details"""
    await economy_system.show_item_details(interaction, item_id)

@bot.tree.command(name="all_items", description="View all items sorted by price")
async def all_items(interaction: discord.Interaction):
    """View all items"""
    await economy_system.show_shop_category(interaction, None)

@bot.tree.command(name="use_item", description="Use an item from your inventory")
async def use_item(interaction: discord.Interaction, item_id: str):
    """Use an item from inventory"""
    await economy_system.use_item(interaction, item_id)

# Error handling
@bot.event
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    """Handle application command errors"""
    if isinstance(error, discord.app_commands.CheckFailure):
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need administrator permissions to use this command",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        logger.error(f'Command error: {error}')
        embed = discord.Embed(
            title="❌ Command Error",
            description="An unexpected error occurred while processing the command",
            color=discord.Color.red()
        )
        try:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            pass  # Interaction might already be responded to

@bot.event
async def on_error(event, *args, **kwargs):
    """Handle general bot errors"""
    logger.error(f'An error occurred in {event}')

# Run the bot
if __name__ == '__main__':
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        logger.error('DISCORD_TOKEN not found in environment variables')
        print('Please set DISCORD_TOKEN in your .env file')
        exit(1)
    
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        logger.error('Invalid Discord token')
        print('Invalid Discord token. Please check your DISCORD_TOKEN in .env file')
    except Exception as e:
        logger.error(f'Failed to start bot: {e}')
