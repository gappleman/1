import discord
from discord.ext import commands
from typing import Dict, Optional, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AdminPanel:
    """Admin panel for managing economy system and user stats"""
    
    def __init__(self, bot, db_manager, economy_system):
        self.bot = bot
        self.db_manager = db_manager
        self.economy_system = economy_system
        self.authorized_admin = "s_atire"  # Only this user can access admin panel
    
    def is_authorized_admin(self, user: discord.User) -> bool:
        """Check if user is authorized to use admin panel"""
        return user.name.lower() == self.authorized_admin.lower()
    
    async def create_admin_embed(self, title: str, description: str, color: discord.Color) -> discord.Embed:
        """Create standardized admin embed"""
        embed = discord.Embed(
            title=f"🔧 Admin Panel - {title}",
            description=description,
            color=color,
            timestamp=datetime.now()
        )
        embed.set_footer(text="Admin Panel - Authorized Personnel Only")
        return embed
    
    async def show_admin_menu(self, interaction: discord.Interaction) -> None:
        """Display main admin menu"""
        if not self.is_authorized_admin(interaction.user):
            await interaction.response.send_message(
                "❌ Access denied. This command is restricted to authorized administrators.",
                ephemeral=True
            )
            return
        
        embed = await self.create_admin_embed(
            "Main Menu",
            "Admin controls for economy system and user management",
            discord.Color.red()
        )
        
        embed.add_field(
            name="💰 Economy Commands",
            value="`/admin_give_money <user> <amount>`\n"
                  "`/admin_remove_money <user> <amount>`\n"
                  "`/admin_set_level <user> <level>`\n"
                  "`/admin_reset_user <user>`",
            inline=False
        )
        
        embed.add_field(
            name="🎒 Item Commands",
            value="`/admin_give_item <user> <item_id> [quantity]`\n"
                  "`/admin_remove_item <user> <item_id>`\n"
                  "`/admin_clear_inventory <user>`\n"
                  "`/admin_list_items [category]`",
            inline=False
        )
        
        embed.add_field(
            name="📊 Stats Commands",
            value="`/admin_user_stats <user>`\n"
                  "`/admin_server_stats`\n"
                  "`/admin_economy_backup`",
            inline=False
        )
        
        embed.add_field(
            name="⚠️ Warning",
            value="These commands directly modify the database. Use with caution!",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def give_money(self, interaction: discord.Interaction, user: discord.Member, amount: int) -> None:
        """Give money to a user"""
        if not self.is_authorized_admin(interaction.user):
            await interaction.response.send_message(
                "❌ Access denied. This command is restricted to authorized administrators.",
                ephemeral=True
            )
            return
        
        try:
            success = await self.economy_system.add_money(user.id, amount, f"Admin grant by {interaction.user.name}")
            
            if success:
                new_balance = await self.economy_system.get_user_balance(user.id)
                embed = await self.create_admin_embed(
                    "Money Added",
                    f"Successfully gave **{amount}** credits to {user.mention}",
                    discord.Color.green()
                )
                embed.add_field(name="New Balance", value=f"{new_balance} Credits", inline=True)
                embed.add_field(name="Admin", value=interaction.user.mention, inline=True)
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(
                    "❌ Failed to add money. Check logs for details.",
                    ephemeral=True
                )
        except Exception as e:
            logger.error(f"Error in admin give_money: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while adding money.",
                ephemeral=True
            )
    
    async def remove_money(self, interaction: discord.Interaction, user: discord.Member, amount: int) -> None:
        """Remove money from a user"""
        if not self.is_authorized_admin(interaction.user):
            await interaction.response.send_message(
                "❌ Access denied. This command is restricted to authorized administrators.",
                ephemeral=True
            )
            return
        
        try:
            success = await self.economy_system.remove_money(user.id, amount, f"Admin removal by {interaction.user.name}")
            
            if success:
                new_balance = await self.economy_system.get_user_balance(user.id)
                embed = await self.create_admin_embed(
                    "Money Removed",
                    f"Successfully removed **{amount}** credits from {user.mention}",
                    discord.Color.orange()
                )
                embed.add_field(name="New Balance", value=f"{new_balance} Credits", inline=True)
                embed.add_field(name="Admin", value=interaction.user.mention, inline=True)
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(
                    "❌ Failed to remove money. User may not have enough credits.",
                    ephemeral=True
                )
        except Exception as e:
            logger.error(f"Error in admin remove_money: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while removing money.",
                ephemeral=True
            )
    
    async def give_item(self, interaction: discord.Interaction, user: discord.Member, item_id: str, quantity: int = 1) -> None:
        """Give an item to a user"""
        if not self.is_authorized_admin(interaction.user):
            await interaction.response.send_message(
                "❌ Access denied. This command is restricted to authorized administrators.",
                ephemeral=True
            )
            return
        
        try:
            if item_id not in self.economy_system.shop_items:
                await interaction.response.send_message(
                    f"❌ Item '{item_id}' not found. Use `/admin_list_items` to see available items.",
                    ephemeral=True
                )
                return
            
            success = await self.db_manager.add_item_to_inventory(user.id, item_id, quantity)
            
            if success:
                item_info = self.economy_system.shop_items[item_id]
                embed = await self.create_admin_embed(
                    "Item Added",
                    f"Successfully gave **{quantity}x {item_info['name']}** to {user.mention}",
                    discord.Color.green()
                )
                embed.add_field(name="Item", value=item_info['name'], inline=True)
                embed.add_field(name="Quantity", value=str(quantity), inline=True)
                embed.add_field(name="Admin", value=interaction.user.mention, inline=True)
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(
                    "❌ Failed to add item. Check logs for details.",
                    ephemeral=True
                )
        except Exception as e:
            logger.error(f"Error in admin give_item: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while adding item.",
                ephemeral=True
            )
    
    async def set_user_level(self, interaction: discord.Interaction, user: discord.Member, level: int) -> None:
        """Set a user's level by adjusting their total earnings"""
        if not self.is_authorized_admin(interaction.user):
            await interaction.response.send_message(
                "❌ Access denied. This command is restricted to authorized administrators.",
                ephemeral=True
            )
            return
        
        if level < 1 or level > 600:
            await interaction.response.send_message(
                "❌ Level must be between 1 and 600.",
                ephemeral=True
            )
            return
        
        try:
            # Calculate required total earnings for the level
            required_earnings = (level - 1) * 1000
            current_earnings = await self.db_manager.get_user_total_earned(user.id)
            
            if required_earnings > current_earnings:
                # Add the difference
                difference = required_earnings - current_earnings
                await self.economy_system.add_money(user.id, difference, f"Level adjustment by {interaction.user.name}")
            elif required_earnings < current_earnings:
                # Remove the difference
                difference = current_earnings - required_earnings
                await self.economy_system.remove_money(user.id, difference, f"Level adjustment by {interaction.user.name}")
            
            new_level = await self.economy_system.get_user_level(user.id)
            embed = await self.create_admin_embed(
                "Level Set",
                f"Successfully set {user.mention}'s level to **{new_level}**",
                discord.Color.blue()
            )
            embed.add_field(name="New Level", value=str(new_level), inline=True)
            embed.add_field(name="Total Earnings", value=f"{required_earnings} Credits", inline=True)
            embed.add_field(name="Admin", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in admin set_user_level: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while setting user level.",
                ephemeral=True
            )
    
    async def get_user_stats(self, interaction: discord.Interaction, user: discord.Member) -> None:
        """Get comprehensive stats for a user"""
        if not self.is_authorized_admin(interaction.user):
            await interaction.response.send_message(
                "❌ Access denied. This command is restricted to authorized administrators.",
                ephemeral=True
            )
            return
        
        try:
            balance = await self.economy_system.get_user_balance(user.id)
            total_earned = await self.db_manager.get_user_total_earned(user.id)
            level = await self.economy_system.get_user_level(user.id)
            inventory = await self.db_manager.get_user_inventory(user.id)
            
            embed = await self.create_admin_embed(
                f"User Stats: {user.display_name}",
                f"Comprehensive statistics for {user.mention}",
                discord.Color.blue()
            )
            
            embed.add_field(name="💰 Balance", value=f"{balance} Credits", inline=True)
            embed.add_field(name="📊 Level", value=f"Level {level}", inline=True)
            embed.add_field(name="💎 Total Earned", value=f"{total_earned} Credits", inline=True)
            embed.add_field(name="🎒 Inventory Items", value=f"{len(inventory)} unique items", inline=True)
            embed.add_field(name="👤 User ID", value=str(user.id), inline=True)
            embed.add_field(name="📅 Account Created", value=user.created_at.strftime("%Y-%m-%d"), inline=True)
            
            # Show top 5 items in inventory
            if inventory:
                inventory_text = ""
                for item_id, quantity in list(inventory.items())[:5]:
                    if item_id in self.economy_system.shop_items:
                        item_name = self.economy_system.shop_items[item_id]['name']
                        inventory_text += f"{item_name}: {quantity}\n"
                
                if len(inventory) > 5:
                    inventory_text += f"... and {len(inventory) - 5} more items"
                
                embed.add_field(name="🎒 Top Items", value=inventory_text, inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in admin get_user_stats: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while fetching user stats.",
                ephemeral=True
            )
    
    async def list_items(self, interaction: discord.Interaction, category: str = None) -> None:
        """List available items, optionally filtered by category"""
        if not self.is_authorized_admin(interaction.user):
            await interaction.response.send_message(
                "❌ Access denied. This command is restricted to authorized administrators.",
                ephemeral=True
            )
            return
        
        try:
            items = self.economy_system.shop_items
            
            if category:
                # Filter by category
                category_items = {k: v for k, v in items.items() if v['type'].value == category.lower()}
                items = category_items
            
            embed = await self.create_admin_embed(
                f"Available Items{f' ({category})' if category else ''}",
                f"Showing {len(items)} items",
                discord.Color.purple()
            )
            
            # Show first 25 items (Discord embed limit)
            items_text = ""
            for i, (item_id, item_info) in enumerate(list(items.items())[:25]):
                items_text += f"`{item_id}` - {item_info['name']} ({item_info['price']} credits)\n"
            
            if len(items) > 25:
                items_text += f"\n... and {len(items) - 25} more items"
            
            embed.add_field(name="Items", value=items_text, inline=False)
            embed.add_field(
                name="Usage",
                value="Use `/admin_give_item <user> <item_id>` to give items",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in admin list_items: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while listing items.",
                ephemeral=True
            )
    
    async def clear_inventory(self, interaction: discord.Interaction, user: discord.Member) -> None:
        """Clear a user's inventory"""
        if not self.is_authorized_admin(interaction.user):
            await interaction.response.send_message(
                "❌ Access denied. This command is restricted to authorized administrators.",
                ephemeral=True
            )
            return
        
        try:
            import aiosqlite
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                await db.execute("DELETE FROM economy_inventory WHERE user_id = ?", (user.id,))
                await db.commit()
            
            embed = await self.create_admin_embed(
                "Inventory Cleared",
                f"Successfully cleared inventory for {user.mention}",
                discord.Color.orange()
            )
            embed.add_field(name="Admin", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in admin clear_inventory: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while clearing inventory.",
                ephemeral=True
            )
    
    async def remove_item(self, interaction: discord.Interaction, user: discord.Member, item_id: str) -> None:
        """Remove an item from a user's inventory"""
        if not self.is_authorized_admin(interaction.user):
            await interaction.response.send_message(
                "❌ Access denied. This command is restricted to authorized administrators.",
                ephemeral=True
            )
            return
        
        try:
            import aiosqlite
            async with aiosqlite.connect(self.db_manager.db_path) as db:
                # Check if user has the item
                cursor = await db.execute(
                    "SELECT quantity FROM economy_inventory WHERE user_id = ? AND item_id = ?",
                    (user.id, item_id)
                )
                result = await cursor.fetchone()
                
                if not result:
                    await interaction.response.send_message(
                        f"❌ {user.mention} does not have the item '{item_id}'.",
                        ephemeral=True
                    )
                    return
                
                # Remove the item
                await db.execute(
                    "DELETE FROM economy_inventory WHERE user_id = ? AND item_id = ?",
                    (user.id, item_id)
                )
                await db.commit()
            
            item_name = self.economy_system.shop_items.get(item_id, {}).get('name', item_id)
            embed = await self.create_admin_embed(
                "Item Removed",
                f"Successfully removed **{item_name}** from {user.mention}'s inventory",
                discord.Color.orange()
            )
            embed.add_field(name="Item", value=item_name, inline=True)
            embed.add_field(name="Admin", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in admin remove_item: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while removing item.",
                ephemeral=True
            )
    
    async def server_stats(self, interaction: discord.Interaction) -> None:
        """Get comprehensive server statistics"""
        if not self.is_authorized_admin(interaction.user):
            await interaction.response.send_message(
                "❌ Access denied. This command is restricted to authorized administrators.",
                ephemeral=True
            )
            return
        
        try:
            stats = await self.db_manager.get_economy_stats()
            
            embed = await self.create_admin_embed(
                "Server Statistics",
                "Comprehensive server economy overview",
                discord.Color.gold()
            )
            
            embed.add_field(name="👥 Total Users", value=stats['total_users'], inline=True)
            embed.add_field(name="💰 Total Money", value=f"{stats['total_money']} Credits", inline=True)
            embed.add_field(name="📊 Avg Balance", value=f"{stats['average_balance']} Credits", inline=True)
            embed.add_field(name="🔄 Transactions", value=stats['total_transactions'], inline=True)
            embed.add_field(name="🛍️ Shop Items", value=len(self.economy_system.shop_items), inline=True)
            embed.add_field(name="🎯 Max Level", value="600", inline=True)
            
            # Guild info
            guild = interaction.guild
            if guild:
                embed.add_field(name="🏰 Server Name", value=guild.name, inline=True)
                embed.add_field(name="👑 Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
                embed.add_field(name="📅 Created", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in admin server_stats: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while fetching server stats.",
                ephemeral=True
            )