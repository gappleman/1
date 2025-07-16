import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class AchievementType(Enum):
    """Types of achievements available"""
    VETERAN = "veteran"
    ACTIVE_MODERATOR = "active_moderator"
    FAIR_JUDGE = "fair_judge"
    ROOKIE = "rookie"
    PUNISHMENT_MASTER = "punishment_master"
    TEAM_PLAYER = "team_player"
    MILESTONE = "milestone"

class Achievement:
    """Represents a single achievement/badge"""
    
    def __init__(self, achievement_type: AchievementType, name: str, description: str, 
                 emoji: str, requirements: Dict, rarity: str = "common"):
        self.type = achievement_type
        self.name = name
        self.description = description
        self.emoji = emoji
        self.requirements = requirements
        self.rarity = rarity
        self.earned_date = None

class AchievementSystem:
    """Manages the achievement/badge system for staff"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.achievements = self._initialize_achievements()
    
    def _initialize_achievements(self) -> Dict[str, Achievement]:
        """Initialize all available achievements"""
        achievements = {
            # Time-based achievements
            "rookie": Achievement(
                AchievementType.ROOKIE,
                "🆕 Fresh Face",
                "Welcome to the team! Earned for joining the staff.",
                "🆕",
                {"days_as_staff": 0},
                "common"
            ),
            "veteran": Achievement(
                AchievementType.VETERAN,
                "🏆 Veteran",
                "A seasoned member who's been staff for 30+ days.",
                "🏆",
                {"days_as_staff": 30},
                "rare"
            ),
            "legend": Achievement(
                AchievementType.MILESTONE,
                "👑 Legend",
                "An absolute legend who's been staff for 100+ days!",
                "👑",
                {"days_as_staff": 100},
                "legendary"
            ),
            
            # Activity-based achievements
            "active_mod": Achievement(
                AchievementType.ACTIVE_MODERATOR,
                "⚡ Active Moderator",
                "Issued 10+ punishments - keeping the peace!",
                "⚡",
                {"punishments_issued": 10},
                "uncommon"
            ),
            "punishment_master": Achievement(
                AchievementType.PUNISHMENT_MASTER,
                "🎯 Punishment Master",
                "Issued 50+ punishments - true dedication!",
                "🎯",
                {"punishments_issued": 50},
                "epic"
            ),
            "fair_judge": Achievement(
                AchievementType.FAIR_JUDGE,
                "⚖️ Fair Judge",
                "Issued punishments across multiple categories.",
                "⚖️",
                {"punishment_types": 3},
                "rare"
            ),
            
            # Role-based achievements
            "admin_power": Achievement(
                AchievementType.MILESTONE,
                "🌟 Admin Power",
                "Reached the rank of Admin - great responsibility!",
                "🌟",
                {"role": "Admin"},
                "epic"
            ),
            "senior_mod": Achievement(
                AchievementType.MILESTONE,
                "🥈 Senior Moderator",
                "Promoted to Senior Moderator - experience shows!",
                "🥈",
                {"role": "Senior Moderator"},
                "rare"
            ),
            
            # Special achievements
            "team_player": Achievement(
                AchievementType.TEAM_PLAYER,
                "🤝 Team Player",
                "Part of a team with 5+ active staff members.",
                "🤝",
                {"team_size": 5},
                "uncommon"
            ),
            "first_punishment": Achievement(
                AchievementType.MILESTONE,
                "🎯 First Strike",
                "Issued your first punishment - everyone starts somewhere!",
                "🎯",
                {"punishments_issued": 1},
                "common"
            )
        }
        return achievements
    
    async def check_and_award_achievements(self, user_id: int) -> List[Achievement]:
        """Check if a user has earned any new achievements"""
        try:
            # Get staff info
            staff_info = await self.db_manager.get_staff_by_id(user_id)
            if not staff_info:
                return []
            
            # Get current achievements
            current_achievements = await self.db_manager.get_user_achievements(user_id)
            current_achievement_ids = {ach['achievement_id'] for ach in current_achievements}
            
            new_achievements = []
            
            # Check each achievement
            for achievement_id, achievement in self.achievements.items():
                if achievement_id in current_achievement_ids:
                    continue  # Already earned
                
                if await self._check_achievement_requirements(user_id, staff_info, achievement):
                    # Award the achievement
                    success = await self.db_manager.award_achievement(user_id, achievement_id)
                    if success:
                        achievement.earned_date = datetime.now()
                        new_achievements.append(achievement)
                        logger.info(f"Awarded achievement '{achievement.name}' to user {user_id}")
            
            return new_achievements
            
        except Exception as e:
            logger.error(f"Error checking achievements for user {user_id}: {e}")
            return []
    
    async def _check_achievement_requirements(self, user_id: int, staff_info: Dict, 
                                           achievement: Achievement) -> bool:
        """Check if a user meets the requirements for an achievement"""
        try:
            requirements = achievement.requirements
            
            # Check days as staff
            if "days_as_staff" in requirements:
                added_date = datetime.fromisoformat(staff_info['added_date'])
                days_as_staff = (datetime.now() - added_date).days
                if days_as_staff < requirements["days_as_staff"]:
                    return False
            
            # Check punishments issued
            if "punishments_issued" in requirements:
                punishments = await self.db_manager.get_punishments_by_moderator(user_id)
                if len(punishments) < requirements["punishments_issued"]:
                    return False
            
            # Check punishment types diversity
            if "punishment_types" in requirements:
                punishments = await self.db_manager.get_punishments_by_moderator(user_id)
                unique_types = set(p['punishment_type'] for p in punishments)
                if len(unique_types) < requirements["punishment_types"]:
                    return False
            
            # Check role
            if "role" in requirements:
                if staff_info['role'] != requirements["role"]:
                    return False
            
            # Check team size
            if "team_size" in requirements:
                all_staff = await self.db_manager.get_all_staff()
                if len(all_staff) < requirements["team_size"]:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking achievement requirements: {e}")
            return False
    
    async def get_user_achievements(self, user_id: int) -> List[Dict]:
        """Get all achievements for a user with details"""
        try:
            user_achievements = await self.db_manager.get_user_achievements(user_id)
            detailed_achievements = []
            
            for ach in user_achievements:
                achievement_info = self.achievements.get(ach['achievement_id'])
                if achievement_info:
                    detailed_achievements.append({
                        'id': ach['id'],
                        'achievement_id': ach['achievement_id'],
                        'name': achievement_info.name,
                        'description': achievement_info.description,
                        'emoji': achievement_info.emoji,
                        'rarity': achievement_info.rarity,
                        'earned_date': ach['earned_date']
                    })
            
            return detailed_achievements
            
        except Exception as e:
            logger.error(f"Error getting user achievements: {e}")
            return []
    
    def get_achievement_info(self, achievement_id: str) -> Optional[Achievement]:
        """Get information about a specific achievement"""
        return self.achievements.get(achievement_id)
    
    def get_all_achievements(self) -> Dict[str, Achievement]:
        """Get all available achievements"""
        return self.achievements
    
    def get_rarity_color(self, rarity: str) -> int:
        """Get Discord color for achievement rarity"""
        colors = {
            "common": 0x95a5a6,      # Gray
            "uncommon": 0x27ae60,    # Green
            "rare": 0x3498db,        # Blue
            "epic": 0x9b59b6,        # Purple
            "legendary": 0xf39c12     # Gold
        }
        return colors.get(rarity, 0x95a5a6)