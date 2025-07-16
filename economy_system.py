import discord
import logging
import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import json

logger = logging.getLogger(__name__)

class ItemType(Enum):
    """Types of items in the economy"""
    CONSUMABLE = "consumable"
    COLLECTIBLE = "collectible"
    TOOL = "tool"
    UPGRADE = "upgrade"
    BADGE = "badge"

class JobType(Enum):
    """Available job types"""
    MODERATOR = "moderator"
    HELPER = "helper"
    STREAMER = "streamer"
    ARTIST = "artist"
    DEVELOPER = "developer"
    TRADER = "trader"
    SECURITY = "security"
    TEACHER = "teacher"
    DESIGNER = "designer"
    WRITER = "writer"
    MUSICIAN = "musician"
    CHEF = "chef"
    PHOTOGRAPHER = "photographer"
    GAMER = "gamer"
    SCIENTIST = "scientist"
    LAWYER = "lawyer"
    DOCTOR = "doctor"
    ENGINEER = "engineer"
    MINER = "miner"
    FISHER = "fisher"

class EconomySystem:
    """Comprehensive economy system for Discord server"""
    
    def __init__(self, bot, db_manager):
        self.bot = bot
        self.db_manager = db_manager
        self.currency_name = "Credits"
        self.currency_symbol = "💰"
        self.daily_cooldowns = {}
        self.work_cooldowns = {}
        self.crime_cooldowns = {}
        
        # Initialize shop items
        self.shop_items = {
            # CONSUMABLES
            "coffee": {
                "name": "☕ Coffee",
                "description": "A refreshing coffee that boosts your energy",
                "price": 50,
                "type": ItemType.CONSUMABLE,
                "effect": "energy_boost"
            },
            "energy_drink": {
                "name": "⚡ Energy Drink",
                "description": "High-caffeine energy drink for instant boost",
                "price": 75,
                "type": ItemType.CONSUMABLE,
                "effect": "energy_boost"
            },
            "pizza": {
                "name": "🍕 Pizza",
                "description": "Delicious pizza to satisfy your hunger",
                "price": 120,
                "type": ItemType.CONSUMABLE,
                "effect": "hunger_restore"
            },
            "health_potion": {
                "name": "🧪 Health Potion",
                "description": "Restores your health to full",
                "price": 200,
                "type": ItemType.CONSUMABLE,
                "effect": "health_restore"
            },
            "lottery_ticket": {
                "name": "🎟️ Lottery Ticket",
                "description": "Try your luck with a lottery ticket",
                "price": 100,
                "type": ItemType.CONSUMABLE,
                "effect": "lottery_chance"
            },
            "mystery_box": {
                "name": "📦 Mystery Box",
                "description": "Contains a random item worth 50-500 credits",
                "price": 250,
                "type": ItemType.CONSUMABLE,
                "effect": "mystery_reward"
            },
            "xp_boost": {
                "name": "🚀 XP Boost",
                "description": "Double XP gain for 2 hours",
                "price": 300,
                "type": ItemType.CONSUMABLE,
                "effect": "xp_boost"
            },
            
            # TOOLS
            "fishing_rod": {
                "name": "🎣 Fishing Rod",
                "description": "Essential tool for fishing jobs",
                "price": 500,
                "type": ItemType.TOOL,
                "effect": "fishing_bonus"
            },
            "pickaxe": {
                "name": "⛏️ Pickaxe",
                "description": "Mining tool for better ore extraction",
                "price": 800,
                "type": ItemType.TOOL,
                "effect": "mining_bonus"
            },
            "laptop": {
                "name": "💻 Laptop",
                "description": "High-performance laptop for developers",
                "price": 1500,
                "type": ItemType.TOOL,
                "effect": "dev_bonus"
            },
            "camera": {
                "name": "📸 Camera",
                "description": "Professional camera for photography",
                "price": 2000,
                "type": ItemType.TOOL,
                "effect": "photo_bonus"
            },
            "guitar": {
                "name": "🎸 Guitar",
                "description": "Acoustic guitar for musicians",
                "price": 1200,
                "type": ItemType.TOOL,
                "effect": "music_bonus"
            },
            "stethoscope": {
                "name": "🩺 Stethoscope",
                "description": "Medical tool for doctors",
                "price": 900,
                "type": ItemType.TOOL,
                "effect": "medical_bonus"
            },
            "microscope": {
                "name": "🔬 Microscope",
                "description": "Scientific instrument for research",
                "price": 3000,
                "type": ItemType.TOOL,
                "effect": "science_bonus"
            },
            
            # UPGRADES
            "boost_multiplier": {
                "name": "📈 Earning Boost",
                "description": "Double your earnings for 24 hours",
                "price": 2000,
                "type": ItemType.UPGRADE,
                "effect": "earning_boost"
            },
            "lucky_charm": {
                "name": "🍀 Lucky Charm",
                "description": "Increases success rate for all activities",
                "price": 1800,
                "type": ItemType.UPGRADE,
                "effect": "luck_boost"
            },
            "speed_boost": {
                "name": "💨 Speed Boost",
                "description": "Reduces all cooldowns by 25%",
                "price": 2500,
                "type": ItemType.UPGRADE,
                "effect": "speed_boost"
            },
            "protection_shield": {
                "name": "🛡️ Protection Shield",
                "description": "Reduces crime failure penalties by 50%",
                "price": 1600,
                "type": ItemType.UPGRADE,
                "effect": "protection"
            },
            "golden_touch": {
                "name": "✨ Golden Touch",
                "description": "Chance to find bonus credits while working",
                "price": 5000,
                "type": ItemType.UPGRADE,
                "effect": "golden_bonus"
            },
            
            # BADGES
            "vip_badge": {
                "name": "⭐ VIP Badge",
                "description": "Exclusive VIP status badge",
                "price": 5000,
                "type": ItemType.BADGE,
                "effect": "vip_status"
            },
            "premium_badge": {
                "name": "👑 Premium Badge",
                "description": "Premium member status",
                "price": 8000,
                "type": ItemType.BADGE,
                "effect": "premium_status"
            },
            "legend_badge": {
                "name": "🏆 Legend Badge",
                "description": "Legendary player status",
                "price": 15000,
                "type": ItemType.BADGE,
                "effect": "legend_status"
            },
            "supporter_badge": {
                "name": "💝 Supporter Badge",
                "description": "Server supporter recognition",
                "price": 3000,
                "type": ItemType.BADGE,
                "effect": "supporter_status"
            },
            "beta_tester": {
                "name": "🧪 Beta Tester",
                "description": "Early access beta tester badge",
                "price": 2500,
                "type": ItemType.BADGE,
                "effect": "beta_status"
            },
            
            # COLLECTIBLES
            "rare_diamond": {
                "name": "💎 Rare Diamond",
                "description": "A rare diamond collectible",
                "price": 10000,
                "type": ItemType.COLLECTIBLE,
                "effect": "none"
            },
            "gold_coin": {
                "name": "🪙 Gold Coin",
                "description": "Ancient gold coin from lost civilization",
                "price": 7500,
                "type": ItemType.COLLECTIBLE,
                "effect": "none"
            },
            "ruby_gem": {
                "name": "💍 Ruby Gem",
                "description": "Precious ruby gemstone",
                "price": 8500,
                "type": ItemType.COLLECTIBLE,
                "effect": "none"
            },
            "emerald_stone": {
                "name": "🟢 Emerald Stone",
                "description": "Brilliant emerald stone",
                "price": 9000,
                "type": ItemType.COLLECTIBLE,
                "effect": "none"
            },
            "sapphire_crystal": {
                "name": "🔵 Sapphire Crystal",
                "description": "Beautiful sapphire crystal",
                "price": 8800,
                "type": ItemType.COLLECTIBLE,
                "effect": "none"
            },
            "art_painting": {
                "name": "🖼️ Art Painting",
                "description": "Masterpiece painting by famous artist",
                "price": 12000,
                "type": ItemType.COLLECTIBLE,
                "effect": "none"
            },
            "vintage_watch": {
                "name": "⌚ Vintage Watch",
                "description": "Antique pocket watch",
                "price": 6500,
                "type": ItemType.COLLECTIBLE,
                "effect": "none"
            },
            "rare_book": {
                "name": "📚 Rare Book",
                "description": "First edition rare book",
                "price": 4500,
                "type": ItemType.COLLECTIBLE,
                "effect": "none"
            },
            "crystal_orb": {
                "name": "🔮 Crystal Orb",
                "description": "Mystical crystal orb",
                "price": 11000,
                "type": ItemType.COLLECTIBLE,
                "effect": "none"
            },
            "dragon_egg": {
                "name": "🥚 Dragon Egg",
                "description": "Legendary dragon egg (replica)",
                "price": 25000,
                "type": ItemType.COLLECTIBLE,
                "effect": "none"
            },
            "phoenix_feather": {
                "name": "🪶 Phoenix Feather",
                "description": "Rare phoenix feather",
                "price": 18000,
                "type": ItemType.COLLECTIBLE,
                "effect": "none"
            },
            "unicorn_horn": {
                "name": "🦄 Unicorn Horn",
                "description": "Mythical unicorn horn",
                "price": 22000,
                "type": ItemType.COLLECTIBLE,
                "effect": "none"
            },
            
            # LEVEL REWARD ITEMS
            "mythical_crown": {
                "name": "👑 Mythical Crown",
                "description": "Crown of ultimate power - Level 200 reward",
                "price": 50000,
                "type": ItemType.COLLECTIBLE,
                "effect": "mythical_power"
            },
            "infinity_stone": {
                "name": "♾️ Infinity Stone",
                "description": "Stone of infinite possibilities - Level 300 reward",
                "price": 100000,
                "type": ItemType.COLLECTIBLE,
                "effect": "infinite_power"
            },
            "cosmic_orb": {
                "name": "🌌 Cosmic Orb",
                "description": "Orb containing cosmic energy - Level 400 reward",
                "price": 200000,
                "type": ItemType.COLLECTIBLE,
                "effect": "cosmic_power"
            },
            "universe_crystal": {
                "name": "🔮 Universe Crystal",
                "description": "Crystal containing the essence of the universe - Level 500 reward",
                "price": 500000,
                "type": ItemType.COLLECTIBLE,
                "effect": "universe_power"
            },
            "omnipotence_relic": {
                "name": "⚡ Omnipotence Relic",
                "description": "Ultimate relic of omnipotence - Level 600 reward",
                "price": 1000000,
                "type": ItemType.COLLECTIBLE,
                "effect": "omnipotent_power"
            }
        }
        
        # Generate 500 additional items programmatically
        self._generate_additional_items()
    
    def _generate_additional_items(self):
        """Generate 500 additional items programmatically"""
        import random
        
        # Item categories and their prefixes
        categories = {
            ItemType.CONSUMABLE: {
                "prefixes": ["🍎", "🍊", "🍌", "🍇", "🍓", "🥤", "🍕", "🍔", "🍟", "🌮", "🍝", "🍜", "🥪", "🍰", "🍪", "🍩", "🍫", "🍬", "🍭", "🧁"],
                "names": ["Apple", "Orange", "Banana", "Grape", "Berry", "Soda", "Pizza", "Burger", "Fries", "Taco", "Pasta", "Ramen", "Sandwich", "Cake", "Cookie", "Donut", "Chocolate", "Candy", "Lollipop", "Cupcake"],
                "base_price": 25
            },
            ItemType.TOOL: {
                "prefixes": ["🔧", "🔨", "⚙️", "🛠️", "🔩", "📐", "📏", "🔬", "🧪", "💻", "⌨️", "🖱️", "📱", "📟", "🎮", "🕹️", "🎯", "🏹", "⚔️", "🛡️"],
                "names": ["Wrench", "Hammer", "Gear", "Toolkit", "Bolt", "Ruler", "Measure", "Scope", "Beaker", "Computer", "Keyboard", "Mouse", "Phone", "Device", "Controller", "Joystick", "Target", "Bow", "Sword", "Shield"],
                "base_price": 500
            },
            ItemType.UPGRADE: {
                "prefixes": ["⚡", "🔋", "💎", "✨", "🌟", "⭐", "🎇", "🎆", "🔥", "💥", "⚙️", "🔧", "🛠️", "🔮", "🎯", "🏆", "🥇", "🎖️", "🏅", "👑"],
                "names": ["Power", "Battery", "Diamond", "Sparkle", "Star", "Boost", "Firework", "Explosion", "Fire", "Blast", "Gear", "Tool", "Kit", "Crystal", "Target", "Trophy", "Gold", "Medal", "Badge", "Crown"],
                "base_price": 1500
            },
            ItemType.BADGE: {
                "prefixes": ["🏅", "🎖️", "🏆", "🥇", "🥈", "🥉", "👑", "💎", "⭐", "🌟", "✨", "🔰", "🛡️", "⚔️", "🎯", "🎪", "🎭", "🎨", "🎵", "🎶"],
                "names": ["Medal", "Award", "Trophy", "Gold", "Silver", "Bronze", "Crown", "Gem", "Star", "Shine", "Sparkle", "Badge", "Shield", "Sword", "Target", "Circus", "Theater", "Art", "Music", "Song"],
                "base_price": 3000
            },
            ItemType.COLLECTIBLE: {
                "prefixes": ["💎", "💍", "🔮", "🏺", "🗿", "🎭", "🖼️", "📜", "🗡️", "🏹", "🛡️", "👑", "💰", "🏴‍☠️", "🗝️", "🔱", "⚱️", "🎪", "🎨", "🎵"],
                "names": ["Gem", "Ring", "Orb", "Vase", "Statue", "Mask", "Painting", "Scroll", "Blade", "Arrow", "Shield", "Crown", "Treasure", "Flag", "Key", "Trident", "Urn", "Tent", "Canvas", "Note"],
                "base_price": 5000
            }
        }
        
        item_counter = 0
        
        for category, data in categories.items():
            items_per_category = 100  # 100 items per category = 500 total
            
            for i in range(items_per_category):
                prefix = random.choice(data["prefixes"])
                name = random.choice(data["names"])
                
                # Generate unique item ID
                item_id = f"gen_{category.value}_{item_counter}"
                item_counter += 1
                
                # Generate price variation
                price_multiplier = random.uniform(0.5, 3.0)
                price = int(data["base_price"] * price_multiplier)
                
                # Generate quality levels
                quality_levels = ["Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythical", "Cosmic"]
                quality = random.choice(quality_levels)
                
                # Generate descriptions
                descriptions = [
                    f"A {quality.lower()} {name.lower()} with special properties",
                    f"High-quality {name.lower()} crafted by skilled artisans",
                    f"Mystical {name.lower()} imbued with magical energy",
                    f"Ancient {name.lower()} from a lost civilization",
                    f"Futuristic {name.lower()} with advanced technology",
                    f"Legendary {name.lower()} of great power",
                    f"Cursed {name.lower()} with mysterious abilities",
                    f"Blessed {name.lower()} that brings good fortune",
                    f"Enchanted {name.lower()} with otherworldly power",
                    f"Divine {name.lower()} touched by the gods"
                ]
                
                self.shop_items[item_id] = {
                    "name": f"{prefix} {quality} {name}",
                    "description": random.choice(descriptions),
                    "price": price,
                    "type": category,
                    "effect": f"{category.value}_effect",
                    "quality": quality,
                    "tier": i // 20 + 1  # Tier 1-5 based on generation order
                }
        
        # Job configurations
        self.jobs = {
            JobType.MODERATOR: {
                "name": "Moderator",
                "description": "Help maintain server order",
                "base_pay": (100, 200),
                "cooldown": 3600,  # 1 hour
                "requirements": {"level": 5}
            },
            JobType.HELPER: {
                "name": "Helper",
                "description": "Assist other users",
                "base_pay": (50, 100),
                "cooldown": 3600,
                "requirements": {"level": 2}
            },
            JobType.STREAMER: {
                "name": "Streamer",
                "description": "Entertain the community",
                "base_pay": (80, 150),
                "cooldown": 7200,  # 2 hours
                "requirements": {"level": 3}
            },
            JobType.ARTIST: {
                "name": "Artist",
                "description": "Create beautiful artwork",
                "base_pay": (120, 250),
                "cooldown": 5400,  # 1.5 hours
                "requirements": {"level": 4}
            },
            JobType.DEVELOPER: {
                "name": "Developer",
                "description": "Build amazing applications",
                "base_pay": (200, 400),
                "cooldown": 7200,
                "requirements": {"level": 8}
            },
            JobType.TRADER: {
                "name": "Trader",
                "description": "Trade in the markets",
                "base_pay": (150, 300),
                "cooldown": 6000,  # 1 hour 40 minutes
                "requirements": {"level": 6}
            },
            JobType.SECURITY: {
                "name": "Security Guard",
                "description": "Keep the server safe and secure",
                "base_pay": (90, 180),
                "cooldown": 4800,  # 1 hour 20 minutes
                "requirements": {"level": 4}
            },
            JobType.TEACHER: {
                "name": "Teacher",
                "description": "Educate and guide community members",
                "base_pay": (110, 220),
                "cooldown": 5400,
                "requirements": {"level": 7}
            },
            JobType.DESIGNER: {
                "name": "Designer",
                "description": "Create stunning visual designs",
                "base_pay": (130, 260),
                "cooldown": 6000,
                "requirements": {"level": 5}
            },
            JobType.WRITER: {
                "name": "Writer",
                "description": "Craft engaging stories and content",
                "base_pay": (100, 200),
                "cooldown": 5400,
                "requirements": {"level": 4}
            },
            JobType.MUSICIAN: {
                "name": "Musician",
                "description": "Create and perform music",
                "base_pay": (120, 240),
                "cooldown": 6600,
                "requirements": {"level": 6}
            },
            JobType.CHEF: {
                "name": "Chef",
                "description": "Prepare delicious meals",
                "base_pay": (80, 160),
                "cooldown": 4200,
                "requirements": {"level": 3}
            },
            JobType.PHOTOGRAPHER: {
                "name": "Photographer",
                "description": "Capture stunning photographs",
                "base_pay": (140, 280),
                "cooldown": 7200,
                "requirements": {"level": 8}
            },
            JobType.GAMER: {
                "name": "Professional Gamer",
                "description": "Compete in gaming tournaments",
                "base_pay": (90, 180),
                "cooldown": 4800,
                "requirements": {"level": 5}
            },
            JobType.SCIENTIST: {
                "name": "Scientist",
                "description": "Conduct research and experiments",
                "base_pay": (250, 500),
                "cooldown": 9000,  # 2.5 hours
                "requirements": {"level": 12}
            },
            JobType.LAWYER: {
                "name": "Lawyer",
                "description": "Provide legal advice and representation",
                "base_pay": (300, 600),
                "cooldown": 10800,  # 3 hours
                "requirements": {"level": 15}
            },
            JobType.DOCTOR: {
                "name": "Doctor",
                "description": "Provide medical care and treatment",
                "base_pay": (280, 560),
                "cooldown": 10800,
                "requirements": {"level": 14}
            },
            JobType.ENGINEER: {
                "name": "Engineer",
                "description": "Design and build complex systems",
                "base_pay": (220, 440),
                "cooldown": 8400,
                "requirements": {"level": 10}
            },
            JobType.MINER: {
                "name": "Miner",
                "description": "Extract valuable resources from the earth",
                "base_pay": (60, 120),
                "cooldown": 3600,
                "requirements": {"level": 2}
            },
            JobType.FISHER: {
                "name": "Fisher",
                "description": "Catch fish from the ocean",
                "base_pay": (70, 140),
                "cooldown": 4200,
                "requirements": {"level": 3}
            }
        }
    
    async def create_economy_embed(self, title: str, description: str, color: discord.Color) -> discord.Embed:
        """Create standardized economy embed"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.now()
        )
        embed.set_footer(text="Economy System", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        return embed
    
    async def get_user_balance(self, user_id: int) -> int:
        """Get user's current balance"""
        try:
            balance = await self.db_manager.get_user_balance(user_id)
            return balance if balance is not None else 0
        except Exception as e:
            logger.error(f"Error getting user balance: {e}")
            return 0
    
    async def add_money(self, user_id: int, amount: int, reason: str = "Unknown") -> bool:
        """Add money to user's balance"""
        try:
            return await self.db_manager.add_money(user_id, amount, reason)
        except Exception as e:
            logger.error(f"Error adding money: {e}")
            return False
    
    async def remove_money(self, user_id: int, amount: int, reason: str = "Unknown") -> bool:
        """Remove money from user's balance"""
        try:
            return await self.db_manager.remove_money(user_id, amount, reason)
        except Exception as e:
            logger.error(f"Error removing money: {e}")
            return False
    
    async def get_user_level(self, user_id: int) -> int:
        """Get user's level (based on total earnings)"""
        try:
            total_earned = await self.db_manager.get_user_total_earned(user_id)
            # Level calculation: level = total_earned // 1000 + 1
            return min(total_earned // 1000 + 1, 600)  # Max level 600
        except Exception as e:
            logger.error(f"Error getting user level: {e}")
            return 1
    
    async def get_level_rewards(self, level: int) -> Dict:
        """Get rewards for reaching a specific level"""
        rewards = {
            "credits": 0,
            "items": [],
            "title": None,
            "special": None
        }
        
        # Base credit rewards
        if level <= 10:
            rewards["credits"] = level * 100
        elif level <= 50:
            rewards["credits"] = level * 200
        elif level <= 100:
            rewards["credits"] = level * 500
        elif level <= 200:
            rewards["credits"] = level * 1000
        elif level <= 400:
            rewards["credits"] = level * 2000
        else:
            rewards["credits"] = level * 5000
        
        # Special milestone rewards
        if level == 5:
            rewards["items"].append("lucky_charm")
            rewards["title"] = "Newcomer"
        elif level == 10:
            rewards["items"].append("boost_multiplier")
            rewards["title"] = "Apprentice"
        elif level == 25:
            rewards["items"].append("vip_badge")
            rewards["title"] = "Skilled Worker"
        elif level == 50:
            rewards["items"].extend(["golden_touch", "premium_badge"])
            rewards["title"] = "Expert"
        elif level == 100:
            rewards["items"].extend(["legend_badge", "dragon_egg"])
            rewards["title"] = "Master"
            rewards["special"] = "Unlock all jobs"
        elif level == 200:
            rewards["items"].append("mythical_crown")
            rewards["title"] = "Grandmaster"
            rewards["special"] = "Double daily rewards"
        elif level == 300:
            rewards["items"].append("infinity_stone")
            rewards["title"] = "Legendary"
            rewards["special"] = "Triple work earnings"
        elif level == 400:
            rewards["items"].append("cosmic_orb")
            rewards["title"] = "Mythical"
            rewards["special"] = "Quadruple crime success rate"
        elif level == 500:
            rewards["items"].append("universe_crystal")
            rewards["title"] = "Cosmic"
            rewards["special"] = "Quintuple gambling wins"
        elif level == 600:
            rewards["items"].append("omnipotence_relic")
            rewards["title"] = "Omnipotent"
            rewards["special"] = "Maximum economy power"
        
        # Every 50 levels get a special item
        if level % 50 == 0 and level > 0:
            milestone_items = ["rare_diamond", "gold_coin", "ruby_gem", "emerald_stone", "sapphire_crystal"]
            rewards["items"].append(milestone_items[min(level//50 - 1, len(milestone_items)-1)])
        
        return rewards
    
    async def check_level_up(self, user_id: int) -> Optional[Dict]:
        """Check if user leveled up and return rewards"""
        try:
            current_level = await self.get_user_level(user_id)
            
            # Check if user has already claimed this level reward
            claimed_levels = await self.db_manager.get_claimed_level_rewards(user_id)
            
            if current_level not in claimed_levels:
                # Mark level as claimed
                await self.db_manager.claim_level_reward(user_id, current_level)
                
                # Get and give rewards
                rewards = await self.get_level_rewards(current_level)
                
                # Give credit rewards
                if rewards["credits"] > 0:
                    await self.add_money(user_id, rewards["credits"], f"Level {current_level} reward")
                
                # Give item rewards
                for item_id in rewards["items"]:
                    if item_id in self.shop_items:
                        await self.db_manager.add_item_to_inventory(user_id, item_id, 1)
                
                return {
                    "level": current_level,
                    "rewards": rewards
                }
            
            return None
        except Exception as e:
            logger.error(f"Error checking level up: {e}")
            return None
    
    async def daily_reward(self, interaction: discord.Interaction) -> None:
        """Give daily reward to user"""
        user_id = interaction.user.id
        
        # Check cooldown
        if user_id in self.daily_cooldowns:
            last_daily = self.daily_cooldowns[user_id]
            if datetime.now() - last_daily < timedelta(hours=24):
                time_left = timedelta(hours=24) - (datetime.now() - last_daily)
                hours, remainder = divmod(time_left.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                
                embed = await self.create_economy_embed(
                    "⏰ Daily Reward on Cooldown",
                    f"You can claim your daily reward in {hours}h {minutes}m",
                    discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        # Calculate daily reward
        user_level = await self.get_user_level(user_id)
        base_reward = 100
        level_bonus = user_level * 25
        streak_bonus = random.randint(0, 50)
        total_reward = base_reward + level_bonus + streak_bonus
        
        # Add money
        success = await self.add_money(user_id, total_reward, "Daily reward")
        
        if success:
            self.daily_cooldowns[user_id] = datetime.now()
            
            embed = await self.create_economy_embed(
                f"{self.currency_symbol} Daily Reward Claimed!",
                f"You received **{total_reward}** {self.currency_name}",
                discord.Color.green()
            )
            embed.add_field(name="Base Reward", value=f"{base_reward} {self.currency_name}", inline=True)
            embed.add_field(name="Level Bonus", value=f"{level_bonus} {self.currency_name}", inline=True)
            embed.add_field(name="Streak Bonus", value=f"{streak_bonus} {self.currency_name}", inline=True)
            embed.add_field(name="Your Level", value=f"Level {user_level}", inline=True)
            
            new_balance = await self.get_user_balance(user_id)
            embed.add_field(name="New Balance", value=f"{new_balance} {self.currency_name}", inline=True)
            
            # Check for level up
            level_up_info = await self.check_level_up(user_id)
            if level_up_info:
                embed.add_field(
                    name="🎉 LEVEL UP!",
                    value=f"Level {level_up_info['level']} reached!\nRewards: {level_up_info['rewards']['credits']} credits + items",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)
        else:
            embed = await self.create_economy_embed(
                "❌ Error",
                "Failed to claim daily reward",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def work_job(self, interaction: discord.Interaction, job_type: JobType) -> None:
        """Work a job to earn money"""
        user_id = interaction.user.id
        
        # Check if user has required level
        user_level = await self.get_user_level(user_id)
        job_info = self.jobs[job_type]
        
        if user_level < job_info["requirements"]["level"]:
            embed = await self.create_economy_embed(
                "❌ Level Required",
                f"You need to be level {job_info['requirements']['level']} to work as a {job_info['name']}",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Check cooldown
        cooldown_key = f"{user_id}_{job_type.value}"
        if cooldown_key in self.work_cooldowns:
            last_work = self.work_cooldowns[cooldown_key]
            if datetime.now() - last_work < timedelta(seconds=job_info["cooldown"]):
                time_left = timedelta(seconds=job_info["cooldown"]) - (datetime.now() - last_work)
                hours, remainder = divmod(time_left.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                
                embed = await self.create_economy_embed(
                    "⏰ Job on Cooldown",
                    f"You can work as a {job_info['name']} again in {hours}h {minutes}m",
                    discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        # Calculate earnings
        min_pay, max_pay = job_info["base_pay"]
        base_earnings = random.randint(min_pay, max_pay)
        level_bonus = user_level * 5
        performance_bonus = random.randint(0, 50)
        total_earnings = base_earnings + level_bonus + performance_bonus
        
        # Add money
        success = await self.add_money(user_id, total_earnings, f"Work as {job_info['name']}")
        
        if success:
            self.work_cooldowns[cooldown_key] = datetime.now()
            
            # Create work scenario
            scenarios = [
                "You completed your shift successfully!",
                "You went above and beyond today!",
                "You helped solve a difficult problem!",
                "You received positive feedback from colleagues!",
                "You finished all your tasks efficiently!"
            ]
            
            embed = await self.create_economy_embed(
                f"💼 Work Complete - {job_info['name']}",
                random.choice(scenarios),
                discord.Color.green()
            )
            embed.add_field(name="Base Pay", value=f"{base_earnings} {self.currency_name}", inline=True)
            embed.add_field(name="Level Bonus", value=f"{level_bonus} {self.currency_name}", inline=True)
            embed.add_field(name="Performance Bonus", value=f"{performance_bonus} {self.currency_name}", inline=True)
            embed.add_field(name="Total Earned", value=f"**{total_earnings}** {self.currency_name}", inline=False)
            
            new_balance = await self.get_user_balance(user_id)
            embed.add_field(name="New Balance", value=f"{new_balance} {self.currency_name}", inline=True)
            
            # Check for level up
            level_up_info = await self.check_level_up(user_id)
            if level_up_info:
                embed.add_field(
                    name="🎉 LEVEL UP!",
                    value=f"Level {level_up_info['level']} reached!\nRewards: {level_up_info['rewards']['credits']} credits + items",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)
        else:
            embed = await self.create_economy_embed(
                "❌ Error",
                "Failed to complete work",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def commit_crime(self, interaction: discord.Interaction) -> None:
        """Commit a crime for potential money (risky)"""
        user_id = interaction.user.id
        
        # Check cooldown
        if user_id in self.crime_cooldowns:
            last_crime = self.crime_cooldowns[user_id]
            if datetime.now() - last_crime < timedelta(hours=2):
                time_left = timedelta(hours=2) - (datetime.now() - last_crime)
                hours, remainder = divmod(time_left.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                
                embed = await self.create_economy_embed(
                    "⏰ Crime on Cooldown",
                    f"You can commit another crime in {hours}h {minutes}m",
                    discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        # Crime scenarios
        crimes = [
            {"name": "Pickpocket", "success_rate": 0.6, "reward": (50, 200), "fine": (100, 300)},
            {"name": "Hack ATM", "success_rate": 0.4, "reward": (200, 500), "fine": (300, 600)},
            {"name": "Rob Bank", "success_rate": 0.2, "reward": (500, 1000), "fine": (600, 1200)},
            {"name": "Steal Car", "success_rate": 0.5, "reward": (300, 600), "fine": (400, 800)},
        ]
        
        crime = random.choice(crimes)
        success = random.random() < crime["success_rate"]
        
        if success:
            # Crime succeeded
            reward = random.randint(*crime["reward"])
            await self.add_money(user_id, reward, f"Crime: {crime['name']}")
            
            embed = await self.create_economy_embed(
                f"🔓 Crime Successful - {crime['name']}",
                f"You successfully committed {crime['name'].lower()} and earned **{reward}** {self.currency_name}!",
                discord.Color.green()
            )
            
            new_balance = await self.get_user_balance(user_id)
            embed.add_field(name="Reward", value=f"{reward} {self.currency_name}", inline=True)
            embed.add_field(name="New Balance", value=f"{new_balance} {self.currency_name}", inline=True)
            
        else:
            # Crime failed
            fine = random.randint(*crime["fine"])
            current_balance = await self.get_user_balance(user_id)
            fine = min(fine, current_balance)  # Can't pay more than they have
            
            await self.remove_money(user_id, fine, f"Crime fine: {crime['name']}")
            
            embed = await self.create_economy_embed(
                f"🚨 Crime Failed - {crime['name']}",
                f"You were caught trying to {crime['name'].lower()} and fined **{fine}** {self.currency_name}!",
                discord.Color.red()
            )
            
            new_balance = await self.get_user_balance(user_id)
            embed.add_field(name="Fine", value=f"{fine} {self.currency_name}", inline=True)
            embed.add_field(name="New Balance", value=f"{new_balance} {self.currency_name}", inline=True)
        
        self.crime_cooldowns[user_id] = datetime.now()
        await interaction.response.send_message(embed=embed)
    
    async def gamble_coins(self, interaction: discord.Interaction, amount: int) -> None:
        """Gamble coins with 50/50 chance"""
        user_id = interaction.user.id
        current_balance = await self.get_user_balance(user_id)
        
        if amount <= 0:
            embed = await self.create_economy_embed(
                "❌ Invalid Amount",
                "You must gamble a positive amount",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if amount > current_balance:
            embed = await self.create_economy_embed(
                "❌ Insufficient Funds",
                f"You only have {current_balance} {self.currency_name}",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # 50/50 chance
        won = random.choice([True, False])
        
        if won:
            await self.add_money(user_id, amount, "Gambling win")
            new_balance = await self.get_user_balance(user_id)
            
            embed = await self.create_economy_embed(
                "🎰 Gambling Win!",
                f"You won **{amount}** {self.currency_name}!",
                discord.Color.green()
            )
            embed.add_field(name="Winnings", value=f"{amount} {self.currency_name}", inline=True)
            embed.add_field(name="New Balance", value=f"{new_balance} {self.currency_name}", inline=True)
        else:
            await self.remove_money(user_id, amount, "Gambling loss")
            new_balance = await self.get_user_balance(user_id)
            
            embed = await self.create_economy_embed(
                "💸 Gambling Loss",
                f"You lost **{amount}** {self.currency_name}!",
                discord.Color.red()
            )
            embed.add_field(name="Lost", value=f"{amount} {self.currency_name}", inline=True)
            embed.add_field(name="New Balance", value=f"{new_balance} {self.currency_name}", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    async def transfer_money(self, interaction: discord.Interaction, recipient: discord.Member, amount: int) -> None:
        """Transfer money between users"""
        sender_id = interaction.user.id
        recipient_id = recipient.id
        
        if sender_id == recipient_id:
            embed = await self.create_economy_embed(
                "❌ Invalid Transfer",
                "You cannot transfer money to yourself",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if amount <= 0:
            embed = await self.create_economy_embed(
                "❌ Invalid Amount",
                "You must transfer a positive amount",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        sender_balance = await self.get_user_balance(sender_id)
        
        if amount > sender_balance:
            embed = await self.create_economy_embed(
                "❌ Insufficient Funds",
                f"You only have {sender_balance} {self.currency_name}",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Transfer money
        success1 = await self.remove_money(sender_id, amount, f"Transfer to {recipient.name}")
        success2 = await self.add_money(recipient_id, amount, f"Transfer from {interaction.user.name}")
        
        if success1 and success2:
            embed = await self.create_economy_embed(
                "💸 Transfer Complete",
                f"Successfully transferred **{amount}** {self.currency_name} to {recipient.mention}",
                discord.Color.green()
            )
            
            sender_new_balance = await self.get_user_balance(sender_id)
            recipient_new_balance = await self.get_user_balance(recipient_id)
            
            embed.add_field(name="Amount", value=f"{amount} {self.currency_name}", inline=True)
            embed.add_field(name="Your Balance", value=f"{sender_new_balance} {self.currency_name}", inline=True)
            embed.add_field(name="Recipient Balance", value=f"{recipient_new_balance} {self.currency_name}", inline=True)
            
            await interaction.response.send_message(embed=embed)
        else:
            embed = await self.create_economy_embed(
                "❌ Transfer Failed",
                "Failed to complete the transfer",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def show_shop(self, interaction: discord.Interaction) -> None:
        """Display the shop with available items"""
        embed = await self.create_economy_embed(
            "🛒 Economy Shop",
            "Available items for purchase - organized by category",
            discord.Color.blue()
        )
        
        # Group items by category
        categories = {
            ItemType.CONSUMABLE: [],
            ItemType.TOOL: [],
            ItemType.UPGRADE: [],
            ItemType.BADGE: [],
            ItemType.COLLECTIBLE: []
        }
        
        for item_id, item in self.shop_items.items():
            categories[item['type']].append((item_id, item))
        
        # Display each category
        category_names = {
            ItemType.CONSUMABLE: "🍎 Consumables",
            ItemType.TOOL: "🔧 Tools",
            ItemType.UPGRADE: "⬆️ Upgrades",
            ItemType.BADGE: "🏅 Badges",
            ItemType.COLLECTIBLE: "💎 Collectibles"
        }
        
        for category_type, items in categories.items():
            if items:
                category_text = ""
                for item_id, item in items[:3]:  # Show first 3 items per category
                    category_text += f"**{item['name']}** - {item['price']} {self.currency_name}\n{item['description']}\n\n"
                
                if len(items) > 3:
                    category_text += f"... and {len(items) - 3} more items"
                
                embed.add_field(
                    name=category_names[category_type],
                    value=category_text,
                    inline=True
                )
        
        embed.add_field(
            name="How to Buy",
            value="Use `/buy <item_name>` to purchase items\nExample: `/buy coffee` or `/buy vip_badge`",
            inline=False
        )
        
        embed.add_field(
            name="Total Items",
            value=f"**{len(self.shop_items)}** items available in shop",
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)
    
    async def show_shop_category(self, interaction: discord.Interaction, category: str = None) -> None:
        """Display shop items filtered by category with detailed info"""
        items = self.shop_items
        
        if category:
            # Filter by category
            category_items = {k: v for k, v in items.items() if v['type'].value == category.lower()}
            items = category_items
            
            if not items:
                embed = await self.create_economy_embed(
                    "❌ Invalid Category",
                    f"Category '{category}' not found. Available categories: consumable, tool, upgrade, badge, collectible",
                    discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        # Sort items by price
        sorted_items = sorted(items.items(), key=lambda x: x[1]['price'])
        
        embed = await self.create_economy_embed(
            f"🛒 Shop - {category.title() if category else 'All Items'}",
            f"Showing {len(sorted_items)} items {f'in {category}' if category else 'across all categories'}",
            discord.Color.blue()
        )
        
        # Show items in pages of 5 to avoid Discord's 1024 character limit
        page_size = 5
        items_text = ""
        
        for i, (item_id, item) in enumerate(sorted_items[:page_size]):
            rarity = item.get('quality', 'Common')
            tier = item.get('tier', 1)
            
            items_text += f"**{item['name']}** `{item_id}`\n"
            items_text += f"💰 {item['price']} Credits | {item['type'].value.title()}"
            if rarity != 'Common':
                items_text += f" | {rarity}"
            if tier > 1:
                items_text += f" | Tier {tier}"
            items_text += f"\n\n"
        
        if len(sorted_items) > page_size:
            items_text += f"... and {len(sorted_items) - page_size} more items\nUse category filters for more items"
        
        embed.add_field(name="Items", value=items_text, inline=False)
        
        embed.add_field(
            name="How to Buy",
            value="Use `/buy <item_id>` to purchase\nExample: `/buy coffee` or `/buy gen_consumable_1`",
            inline=False
        )
        
        embed.add_field(
            name="Categories",
            value="`/shop_category consumable` | `/shop_category tool` | `/shop_category upgrade` | `/shop_category badge` | `/shop_category collectible`",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    async def search_items(self, interaction: discord.Interaction, search_term: str) -> None:
        """Search for items by name or description"""
        search_term = search_term.lower()
        matching_items = {}
        
        for item_id, item in self.shop_items.items():
            if (search_term in item['name'].lower() or 
                search_term in item['description'].lower() or
                search_term in item_id.lower()):
                matching_items[item_id] = item
        
        if not matching_items:
            embed = await self.create_economy_embed(
                "🔍 No Results",
                f"No items found matching '{search_term}'",
                discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Sort by price
        sorted_items = sorted(matching_items.items(), key=lambda x: x[1]['price'])
        
        embed = await self.create_economy_embed(
            f"🔍 Search Results: '{search_term}'",
            f"Found {len(sorted_items)} matching items",
            discord.Color.green()
        )
        
        # Show first 15 results
        items_text = ""
        for i, (item_id, item) in enumerate(sorted_items[:15]):
            items_text += f"**{item['name']}** `{item_id}`\n"
            items_text += f"💰 {item['price']} Credits | {item['type'].value.title()}\n"
            items_text += f"{item['description']}\n\n"
        
        if len(sorted_items) > 15:
            items_text += f"... and {len(sorted_items) - 15} more results"
        
        embed.add_field(name="Results", value=items_text, inline=False)
        embed.add_field(
            name="Purchase",
            value="Use `/buy <item_id>` to purchase any item",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    async def show_item_details(self, interaction: discord.Interaction, item_id: str) -> None:
        """Show detailed information about a specific item"""
        if item_id not in self.shop_items:
            embed = await self.create_economy_embed(
                "❌ Item Not Found",
                f"Item '{item_id}' does not exist in the shop",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        item = self.shop_items[item_id]
        user_balance = await self.get_user_balance(interaction.user.id)
        can_afford = user_balance >= item['price']
        
        embed = await self.create_economy_embed(
            f"📋 Item Details",
            f"Detailed information for {item['name']}",
            discord.Color.blue()
        )
        
        embed.add_field(name="Name", value=item['name'], inline=True)
        embed.add_field(name="Price", value=f"{item['price']} Credits", inline=True)
        embed.add_field(name="Type", value=item['type'].value.title(), inline=True)
        
        if item.get('quality'):
            embed.add_field(name="Quality", value=item['quality'], inline=True)
        
        if item.get('tier'):
            embed.add_field(name="Tier", value=f"Tier {item['tier']}", inline=True)
        
        embed.add_field(name="Effect", value=item.get('effect', 'None'), inline=True)
        embed.add_field(name="Description", value=item['description'], inline=False)
        
        # Purchase info
        purchase_info = f"Your Balance: {user_balance} Credits\n"
        purchase_info += f"Can Afford: {'✅ Yes' if can_afford else '❌ No'}\n"
        purchase_info += f"Item ID: `{item_id}`"
        
        embed.add_field(name="Purchase Info", value=purchase_info, inline=False)
        
        if can_afford:
            embed.add_field(
                name="Buy Now",
                value=f"Use `/buy {item_id}` to purchase this item",
                inline=False
            )
        else:
            needed = item['price'] - user_balance
            embed.add_field(
                name="Insufficient Funds",
                value=f"You need {needed} more Credits to buy this item",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    async def buy_item(self, interaction: discord.Interaction, item_name: str) -> None:
        """Buy an item from the shop"""
        user_id = interaction.user.id
        
        # Find item
        item_id = None
        for iid, item in self.shop_items.items():
            if item_name.lower() in item['name'].lower() or item_name.lower() == iid:
                item_id = iid
                break
        
        if not item_id:
            embed = await self.create_economy_embed(
                "❌ Item Not Found",
                f"No item found with name '{item_name}'",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        item = self.shop_items[item_id]
        current_balance = await self.get_user_balance(user_id)
        
        if current_balance < item['price']:
            embed = await self.create_economy_embed(
                "❌ Insufficient Funds",
                f"You need {item['price']} {self.currency_name} but only have {current_balance}",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Purchase item
        success = await self.remove_money(user_id, item['price'], f"Bought {item['name']}")
        
        if success:
            # Add item to inventory
            await self.db_manager.add_item_to_inventory(user_id, item_id, 1)
            
            embed = await self.create_economy_embed(
                "✅ Purchase Successful",
                f"You bought {item['name']} for {item['price']} {self.currency_name}",
                discord.Color.green()
            )
            
            new_balance = await self.get_user_balance(user_id)
            embed.add_field(name="Item", value=item['name'], inline=True)
            embed.add_field(name="Price", value=f"{item['price']} {self.currency_name}", inline=True)
            embed.add_field(name="New Balance", value=f"{new_balance} {self.currency_name}", inline=True)
            
            await interaction.response.send_message(embed=embed)
        else:
            embed = await self.create_economy_embed(
                "❌ Purchase Failed",
                "Failed to complete the purchase",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def show_inventory(self, interaction: discord.Interaction, user: discord.Member = None) -> None:
        """Show user's inventory"""
        if user is None:
            user = interaction.user
        
        user_id = user.id
        inventory = await self.db_manager.get_user_inventory(user_id)
        
        if not inventory:
            embed = await self.create_economy_embed(
                "📦 Empty Inventory",
                f"{user.display_name}'s inventory is empty",
                discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        embed = await self.create_economy_embed(
            f"📦 {user.display_name}'s Inventory",
            "Items owned by this user",
            discord.Color.blue()
        )
        
        for item_id, quantity in inventory.items():
            if item_id in self.shop_items:
                item = self.shop_items[item_id]
                embed.add_field(
                    name=f"{item['name']} x{quantity}",
                    value=item['description'],
                    inline=True
                )
        
        await interaction.response.send_message(embed=embed)
    
    async def show_balance(self, interaction: discord.Interaction, user: discord.Member = None) -> None:
        """Show user's balance and stats"""
        if user is None:
            user = interaction.user
        
        user_id = user.id
        balance = await self.get_user_balance(user_id)
        level = await self.get_user_level(user_id)
        total_earned = await self.db_manager.get_user_total_earned(user_id)
        
        embed = await self.create_economy_embed(
            f"{self.currency_symbol} {user.display_name}'s Economy Stats",
            f"Financial information for {user.mention}",
            discord.Color.gold()
        )
        
        embed.add_field(name="Current Balance", value=f"{balance} {self.currency_name}", inline=True)
        embed.add_field(name="Level", value=f"Level {level}", inline=True)
        embed.add_field(name="Total Earned", value=f"{total_earned} {self.currency_name}", inline=True)
        
        # Calculate next level requirements
        next_level_requirement = level * 1000
        progress = total_earned % 1000
        embed.add_field(name="Next Level Progress", value=f"{progress}/1000 {self.currency_name}", inline=True)
        
        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)
        
        await interaction.response.send_message(embed=embed)
    
    async def show_leaderboard(self, interaction: discord.Interaction) -> None:
        """Show economy leaderboard"""
        leaderboard = await self.db_manager.get_economy_leaderboard()
        
        if not leaderboard:
            embed = await self.create_economy_embed(
                "📊 Economy Leaderboard",
                "No data available yet",
                discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        embed = await self.create_economy_embed(
            "📊 Economy Leaderboard",
            "Top users by balance",
            discord.Color.gold()
        )
        
        for i, (user_id, balance) in enumerate(leaderboard[:10], 1):
            user = self.bot.get_user(user_id)
            username = user.mention if user else f"Unknown User ({user_id})"
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
            embed.add_field(
                name=f"{medal} {username}",
                value=f"{balance} {self.currency_name}",
                inline=True
            )
        
        await interaction.response.send_message(embed=embed)
    
    async def use_item(self, interaction: discord.Interaction, item_id: str) -> None:
        """Use an item from inventory"""
        user_id = interaction.user.id
        
        # Check if user has the item
        inventory = await self.db_manager.get_user_inventory(user_id)
        if item_id not in inventory or inventory[item_id] <= 0:
            embed = await self.create_economy_embed(
                "❌ Item Not Found",
                f"You don't have '{item_id}' in your inventory",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if item_id not in self.shop_items:
            embed = await self.create_economy_embed(
                "❌ Invalid Item",
                f"Item '{item_id}' is not recognized",
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        item = self.shop_items[item_id]
        
        # Execute item effect
        result = await self._execute_item_effect(user_id, item_id, item)
        
        if result["success"]:
            # Remove item from inventory for consumables
            if item['type'] == ItemType.CONSUMABLE:
                import aiosqlite
                async with aiosqlite.connect(self.db_manager.db_path) as db:
                    await db.execute(
                        "UPDATE economy_inventory SET quantity = quantity - 1 WHERE user_id = ? AND item_id = ?",
                        (user_id, item_id)
                    )
                    await db.execute(
                        "DELETE FROM economy_inventory WHERE user_id = ? AND item_id = ? AND quantity <= 0",
                        (user_id, item_id)
                    )
                    await db.commit()
            
            embed = await self.create_economy_embed(
                f"✅ {item['name']} Used!",
                result["message"],
                discord.Color.green()
            )
            
            if result.get("reward"):
                embed.add_field(name="Reward", value=result["reward"], inline=True)
            
            if result.get("effect_duration"):
                embed.add_field(name="Duration", value=result["effect_duration"], inline=True)
            
            await interaction.response.send_message(embed=embed)
        else:
            embed = await self.create_economy_embed(
                f"❌ {item['name']} Failed",
                result["message"],
                discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def _execute_item_effect(self, user_id: int, item_id: str, item: dict) -> dict:
        """Execute the effect of using an item"""
        import random
        
        effect = item.get('effect', 'none')
        item_type = item['type']
        
        # Consumable items
        if item_type == ItemType.CONSUMABLE:
            if 'coffee' in item_id.lower() or 'energy' in item_id.lower():
                reward = random.randint(50, 150)
                await self.add_money(user_id, reward, f"Used {item['name']}")
                return {
                    "success": True,
                    "message": f"You feel energized and more productive!",
                    "reward": f"+{reward} Credits from increased productivity"
                }
            
            elif 'pizza' in item_id.lower() or 'burger' in item_id.lower() or 'food' in item_id.lower():
                reward = random.randint(25, 100)
                await self.add_money(user_id, reward, f"Used {item['name']}")
                return {
                    "success": True,
                    "message": f"Delicious! You feel satisfied and ready to work.",
                    "reward": f"+{reward} Credits from being well-fed"
                }
            
            elif 'potion' in item_id.lower() or 'health' in item_id.lower():
                # Reset all cooldowns
                if user_id in self.daily_cooldowns:
                    del self.daily_cooldowns[user_id]
                if user_id in self.work_cooldowns:
                    del self.work_cooldowns[user_id]
                if user_id in self.crime_cooldowns:
                    del self.crime_cooldowns[user_id]
                
                return {
                    "success": True,
                    "message": "You feel refreshed and ready for new activities!",
                    "reward": "All cooldowns reset"
                }
            
            elif 'lottery' in item_id.lower() or 'ticket' in item_id.lower():
                if random.random() < 0.1:  # 10% chance to win big
                    reward = random.randint(1000, 5000)
                    await self.add_money(user_id, reward, f"Lottery win from {item['name']}")
                    return {
                        "success": True,
                        "message": "🎉 JACKPOT! You won the lottery!",
                        "reward": f"+{reward} Credits"
                    }
                else:
                    return {
                        "success": True,
                        "message": "Better luck next time! No winning numbers today.",
                        "reward": "No prize this time"
                    }
            
            elif 'mystery' in item_id.lower() or 'box' in item_id.lower():
                rewards = [
                    (0.4, lambda: ("credits", random.randint(100, 500))),
                    (0.3, lambda: ("item", random.choice(list(self.shop_items.keys())))),
                    (0.2, lambda: ("multiplier", "2x earnings for next work")),
                    (0.1, lambda: ("jackpot", random.randint(1000, 2000)))
                ]
                
                rand = random.random()
                cumulative = 0
                for chance, reward_func in rewards:
                    cumulative += chance
                    if rand <= cumulative:
                        reward_type, reward_value = reward_func()
                        
                        if reward_type == "credits":
                            await self.add_money(user_id, reward_value, f"Mystery box reward")
                            return {
                                "success": True,
                                "message": f"You found {reward_value} credits in the mystery box!",
                                "reward": f"+{reward_value} Credits"
                            }
                        elif reward_type == "item":
                            await self.db_manager.add_item_to_inventory(user_id, reward_value, 1)
                            item_name = self.shop_items[reward_value]['name']
                            return {
                                "success": True,
                                "message": f"You found a {item_name} in the mystery box!",
                                "reward": f"+1 {item_name}"
                            }
                        elif reward_type == "multiplier":
                            # Store multiplier effect (simplified for this example)
                            return {
                                "success": True,
                                "message": "You found a lucky charm! Your next work will pay double!",
                                "reward": "2x work earnings (next work only)"
                            }
                        elif reward_type == "jackpot":
                            await self.add_money(user_id, reward_value, f"Mystery box jackpot")
                            return {
                                "success": True,
                                "message": "🎉 MYSTERY BOX JACKPOT! You struck gold!",
                                "reward": f"+{reward_value} Credits"
                            }
            
            elif 'boost' in item_id.lower() or 'xp' in item_id.lower():
                bonus = random.randint(200, 500)
                await self.add_money(user_id, bonus, f"XP Boost reward")
                return {
                    "success": True,
                    "message": "You feel a surge of experience and knowledge!",
                    "reward": f"+{bonus} Credits from XP boost"
                }
        
        # Tool items
        elif item_type == ItemType.TOOL:
            if 'fishing' in item_id.lower():
                if random.random() < 0.7:  # 70% success rate
                    reward = random.randint(150, 300)
                    await self.add_money(user_id, reward, f"Fishing with {item['name']}")
                    return {
                        "success": True,
                        "message": "You caught some fish and sold them at the market!",
                        "reward": f"+{reward} Credits from fishing"
                    }
                else:
                    return {
                        "success": True,
                        "message": "The fish weren't biting today. Better luck next time!",
                        "reward": "No catch today"
                    }
            
            elif 'pickaxe' in item_id.lower() or 'mining' in item_id.lower():
                if random.random() < 0.6:  # 60% success rate
                    reward = random.randint(200, 400)
                    await self.add_money(user_id, reward, f"Mining with {item['name']}")
                    return {
                        "success": True,
                        "message": "You struck ore and sold it for profit!",
                        "reward": f"+{reward} Credits from mining"
                    }
                else:
                    return {
                        "success": True,
                        "message": "The mine was empty today. Keep digging!",
                        "reward": "No ore found"
                    }
            
            elif 'laptop' in item_id.lower() or 'computer' in item_id.lower():
                reward = random.randint(300, 600)
                await self.add_money(user_id, reward, f"Programming with {item['name']}")
                return {
                    "success": True,
                    "message": "You completed a programming project and earned money!",
                    "reward": f"+{reward} Credits from coding"
                }
            
            elif 'camera' in item_id.lower():
                reward = random.randint(250, 450)
                await self.add_money(user_id, reward, f"Photography with {item['name']}")
                return {
                    "success": True,
                    "message": "You took stunning photos and sold them!",
                    "reward": f"+{reward} Credits from photography"
                }
        
        # Upgrade items
        elif item_type == ItemType.UPGRADE:
            if 'boost' in item_id.lower() or 'multiplier' in item_id.lower():
                return {
                    "success": True,
                    "message": "This upgrade provides passive benefits to your economy activities!",
                    "reward": "Passive bonus active",
                    "effect_duration": "Permanent"
                }
            
            elif 'lucky' in item_id.lower() or 'charm' in item_id.lower():
                return {
                    "success": True,
                    "message": "You feel luckier! Your next few activities will have better outcomes.",
                    "reward": "Increased success rates",
                    "effect_duration": "Next 3 activities"
                }
        
        # Badge items
        elif item_type == ItemType.BADGE:
            return {
                "success": True,
                "message": f"You proudly display your {item['name']}! This shows your status to others.",
                "reward": "Status symbol equipped"
            }
        
        # Collectible items
        elif item_type == ItemType.COLLECTIBLE:
            if 'dragon' in item_id.lower() or 'mythical' in item_id.lower():
                if random.random() < 0.05:  # 5% chance for legendary reward
                    reward = random.randint(2000, 5000)
                    await self.add_money(user_id, reward, f"Mythical power from {item['name']}")
                    return {
                        "success": True,
                        "message": "The mythical item releases incredible power!",
                        "reward": f"+{reward} Credits from legendary power"
                    }
                else:
                    return {
                        "success": True,
                        "message": "The item glows with mysterious energy but remains dormant.",
                        "reward": "Mystical energy (no effect this time)"
                    }
            
            elif 'gem' in item_id.lower() or 'crystal' in item_id.lower():
                reward = random.randint(500, 1000)
                await self.add_money(user_id, reward, f"Sold {item['name']}")
                return {
                    "success": True,
                    "message": "You sold the precious gem to a collector!",
                    "reward": f"+{reward} Credits from gem sale"
                }
        
        # Default effect
        return {
            "success": True,
            "message": f"You admire the {item['name']}. It's a nice item to have!",
            "reward": "No special effect"
        }