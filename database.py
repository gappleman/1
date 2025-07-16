import sqlite3
import aiosqlite
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages SQLite database operations for staff and punishment records"""
    
    def __init__(self, db_path: str = 'bot_database.db'):
        self.db_path = db_path
    
    async def initialize_database(self):
        """Initialize the database and create tables if they don't exist"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Create staff table
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS staff (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER UNIQUE NOT NULL,
                        username TEXT NOT NULL,
                        role TEXT NOT NULL,
                        notes TEXT,
                        added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create punishments table
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS punishments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        username TEXT NOT NULL,
                        punishment_type TEXT NOT NULL,
                        reason TEXT NOT NULL,
                        moderator_id INTEGER NOT NULL,
                        moderator_username TEXT NOT NULL,
                        punishment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create achievements table
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS achievements (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        achievement_id TEXT NOT NULL,
                        earned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES staff (user_id),
                        UNIQUE (user_id, achievement_id)
                    )
                ''')
                
                # Create economy tables
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS economy_users (
                        user_id INTEGER PRIMARY KEY,
                        balance INTEGER DEFAULT 0,
                        total_earned INTEGER DEFAULT 0,
                        last_daily TIMESTAMP,
                        last_work TIMESTAMP,
                        last_crime TIMESTAMP
                    )
                ''')
                
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS economy_transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        amount INTEGER NOT NULL,
                        transaction_type TEXT NOT NULL,
                        reason TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES economy_users (user_id)
                    )
                ''')
                
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS economy_inventory (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        item_id TEXT NOT NULL,
                        quantity INTEGER DEFAULT 1,
                        acquired_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES economy_users (user_id),
                        UNIQUE (user_id, item_id)
                    )
                ''')
                
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS level_rewards (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        level INTEGER NOT NULL,
                        claimed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES economy_users (user_id),
                        UNIQUE (user_id, level)
                    )
                ''')
                
                await db.commit()
                logger.info('Database tables initialized successfully')
                
        except Exception as e:
            logger.error(f'Error initializing database: {e}')
            raise
    
    # Staff Management Methods
    async def add_staff(self, user_id: int, username: str, role: str, notes: Optional[str] = None) -> bool:
        """Add a staff member to the database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO staff (user_id, username, role, notes)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, username, role, notes))
                await db.commit()
                logger.info(f'Added staff member: {username} (ID: {user_id})')
                return True
                
        except sqlite3.IntegrityError:
            logger.warning(f'Staff member already exists: {username} (ID: {user_id})')
            return False
        except Exception as e:
            logger.error(f'Error adding staff member: {e}')
            raise
    
    async def remove_staff(self, user_id: int) -> bool:
        """Remove a staff member from the database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('DELETE FROM staff WHERE user_id = ?', (user_id,))
                await db.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f'Removed staff member with ID: {user_id}')
                    return True
                else:
                    logger.warning(f'No staff member found with ID: {user_id}')
                    return False
                    
        except Exception as e:
            logger.error(f'Error removing staff member: {e}')
            raise
    
    async def get_all_staff(self) -> List[Dict]:
        """Get all staff members from the database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute('''
                    SELECT id, user_id, username, role, notes, added_date
                    FROM staff
                    ORDER BY added_date DESC
                ''')
                rows = await cursor.fetchall()
                
                staff_list = []
                for row in rows:
                    staff_list.append({
                        'id': row['id'],
                        'user_id': row['user_id'],
                        'username': row['username'],
                        'role': row['role'],
                        'notes': row['notes'],
                        'added_date': row['added_date']
                    })
                
                logger.info(f'Retrieved {len(staff_list)} staff members')
                return staff_list
                
        except Exception as e:
            logger.error(f'Error retrieving staff list: {e}')
            raise
    
    async def get_staff_by_id(self, user_id: int) -> Optional[Dict]:
        """Get a specific staff member by user ID"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute('''
                    SELECT id, user_id, username, role, notes, added_date
                    FROM staff
                    WHERE user_id = ?
                ''', (user_id,))
                row = await cursor.fetchone()
                
                if row:
                    return {
                        'id': row['id'],
                        'user_id': row['user_id'],
                        'username': row['username'],
                        'role': row['role'],
                        'notes': row['notes'],
                        'added_date': row['added_date']
                    }
                return None
                
        except Exception as e:
            logger.error(f'Error retrieving staff member: {e}')
            raise
    
    # Punishment Management Methods
    async def add_punishment(self, user_id: int, username: str, punishment_type: str, 
                           reason: str, moderator_id: int, moderator_username: str) -> bool:
        """Add a punishment record to the database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO punishments (user_id, username, punishment_type, reason, moderator_id, moderator_username)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, username, punishment_type, reason, moderator_id, moderator_username))
                await db.commit()
                logger.info(f'Added punishment for {username} (ID: {user_id}): {punishment_type}')
                return True
                
        except Exception as e:
            logger.error(f'Error adding punishment: {e}')
            raise
    
    async def remove_punishment(self, punishment_id: int) -> bool:
        """Remove a punishment record by ID"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('DELETE FROM punishments WHERE id = ?', (punishment_id,))
                await db.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f'Removed punishment record with ID: {punishment_id}')
                    return True
                else:
                    logger.warning(f'No punishment record found with ID: {punishment_id}')
                    return False
                    
        except Exception as e:
            logger.error(f'Error removing punishment: {e}')
            raise
    
    async def get_all_punishments(self) -> List[Dict]:
        """Get all punishment records from the database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute('''
                    SELECT id, user_id, username, punishment_type, reason, 
                           moderator_id, moderator_username, punishment_date
                    FROM punishments
                    ORDER BY punishment_date DESC
                ''')
                rows = await cursor.fetchall()
                
                punishment_list = []
                for row in rows:
                    punishment_list.append({
                        'id': row['id'],
                        'user_id': row['user_id'],
                        'username': row['username'],
                        'punishment_type': row['punishment_type'],
                        'reason': row['reason'],
                        'moderator_id': row['moderator_id'],
                        'moderator_username': row['moderator_username'],
                        'punishment_date': row['punishment_date']
                    })
                
                logger.info(f'Retrieved {len(punishment_list)} punishment records')
                return punishment_list
                
        except Exception as e:
            logger.error(f'Error retrieving punishment list: {e}')
            raise
    
    async def get_user_punishments(self, user_id: int) -> List[Dict]:
        """Get all punishment records for a specific user"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute('''
                    SELECT id, user_id, username, punishment_type, reason, 
                           moderator_id, moderator_username, punishment_date
                    FROM punishments
                    WHERE user_id = ?
                    ORDER BY punishment_date DESC
                ''', (user_id,))
                rows = await cursor.fetchall()
                
                punishment_list = []
                for row in rows:
                    punishment_list.append({
                        'id': row['id'],
                        'user_id': row['user_id'],
                        'username': row['username'],
                        'punishment_type': row['punishment_type'],
                        'reason': row['reason'],
                        'moderator_id': row['moderator_id'],
                        'moderator_username': row['moderator_username'],
                        'punishment_date': row['punishment_date']
                    })
                
                logger.info(f'Retrieved {len(punishment_list)} punishment records for user {user_id}')
                return punishment_list
                
        except Exception as e:
            logger.error(f'Error retrieving user punishments: {e}')
            raise
    
    async def get_punishment_by_id(self, punishment_id: int) -> Optional[Dict]:
        """Get a specific punishment record by ID"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute('''
                    SELECT id, user_id, username, punishment_type, reason, 
                           moderator_id, moderator_username, punishment_date
                    FROM punishments
                    WHERE id = ?
                ''', (punishment_id,))
                row = await cursor.fetchone()
                
                if row:
                    return {
                        'id': row['id'],
                        'user_id': row['user_id'],
                        'username': row['username'],
                        'punishment_type': row['punishment_type'],
                        'reason': row['reason'],
                        'moderator_id': row['moderator_id'],
                        'moderator_username': row['moderator_username'],
                        'punishment_date': row['punishment_date']
                    }
                return None
                
        except Exception as e:
            logger.error(f'Error retrieving punishment record: {e}')
            raise
    
    # Database Maintenance Methods
    async def get_database_stats(self) -> Dict:
        """Get database statistics"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Get staff count
                cursor = await db.execute('SELECT COUNT(*) FROM staff')
                staff_count = (await cursor.fetchone())[0]
                
                # Get punishment count
                cursor = await db.execute('SELECT COUNT(*) FROM punishments')
                punishment_count = (await cursor.fetchone())[0]
                
                return {
                    'staff_count': staff_count,
                    'punishment_count': punishment_count,
                    'database_path': self.db_path
                }
                
        except Exception as e:
            logger.error(f'Error getting database stats: {e}')
            raise
    
    async def cleanup_old_data(self, days: int = 365) -> int:
        """Clean up punishment records older than specified days"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('''
                    DELETE FROM punishments 
                    WHERE punishment_date < datetime('now', '-{} days')
                '''.format(days))
                await db.commit()
                
                deleted_count = cursor.rowcount
                logger.info(f'Cleaned up {deleted_count} old punishment records')
                return deleted_count
                
        except Exception as e:
            logger.error(f'Error cleaning up old data: {e}')
            raise
    
    # Achievement Management Methods
    async def award_achievement(self, user_id: int, achievement_id: str) -> bool:
        """Award an achievement to a user"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO achievements (user_id, achievement_id)
                    VALUES (?, ?)
                ''', (user_id, achievement_id))
                await db.commit()
                logger.info(f'Awarded achievement {achievement_id} to user {user_id}')
                return True
                
        except sqlite3.IntegrityError:
            logger.warning(f'Achievement {achievement_id} already exists for user {user_id}')
            return False
        except Exception as e:
            logger.error(f'Error awarding achievement: {e}')
            raise
    
    async def get_user_achievements(self, user_id: int) -> List[Dict]:
        """Get all achievements for a user"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute('''
                    SELECT id, user_id, achievement_id, earned_date
                    FROM achievements
                    WHERE user_id = ?
                    ORDER BY earned_date DESC
                ''', (user_id,))
                rows = await cursor.fetchall()
                
                achievements = []
                for row in rows:
                    achievements.append({
                        'id': row['id'],
                        'user_id': row['user_id'],
                        'achievement_id': row['achievement_id'],
                        'earned_date': row['earned_date']
                    })
                
                logger.info(f'Retrieved {len(achievements)} achievements for user {user_id}')
                return achievements
                
        except Exception as e:
            logger.error(f'Error retrieving user achievements: {e}')
            raise
    
    async def get_all_achievements(self) -> List[Dict]:
        """Get all achievements across all users"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute('''
                    SELECT a.id, a.user_id, a.achievement_id, a.earned_date, s.username
                    FROM achievements a
                    JOIN staff s ON a.user_id = s.user_id
                    ORDER BY a.earned_date DESC
                ''')
                rows = await cursor.fetchall()
                
                achievements = []
                for row in rows:
                    achievements.append({
                        'id': row['id'],
                        'user_id': row['user_id'],
                        'username': row['username'],
                        'achievement_id': row['achievement_id'],
                        'earned_date': row['earned_date']
                    })
                
                logger.info(f'Retrieved {len(achievements)} total achievements')
                return achievements
                
        except Exception as e:
            logger.error(f'Error retrieving all achievements: {e}')
            raise
    
    async def get_punishments_by_moderator(self, moderator_id: int) -> List[Dict]:
        """Get all punishments issued by a specific moderator"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute('''
                    SELECT id, user_id, username, punishment_type, reason, 
                           moderator_id, moderator_username, punishment_date
                    FROM punishments
                    WHERE moderator_id = ?
                    ORDER BY punishment_date DESC
                ''', (moderator_id,))
                rows = await cursor.fetchall()
                
                punishments = []
                for row in rows:
                    punishments.append({
                        'id': row['id'],
                        'user_id': row['user_id'],
                        'username': row['username'],
                        'punishment_type': row['punishment_type'],
                        'reason': row['reason'],
                        'moderator_id': row['moderator_id'],
                        'moderator_username': row['moderator_username'],
                        'punishment_date': row['punishment_date']
                    })
                
                logger.info(f'Retrieved {len(punishments)} punishments for moderator {moderator_id}')
                return punishments
                
        except Exception as e:
            logger.error(f'Error retrieving moderator punishments: {e}')
            raise
    
    # Economy Management Methods
    async def ensure_economy_user(self, user_id: int):
        """Ensure user exists in economy_users table"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT OR IGNORE INTO economy_users (user_id, balance, total_earned)
                    VALUES (?, 0, 0)
                ''', (user_id,))
                await db.commit()
        except Exception as e:
            logger.error(f'Error ensuring economy user: {e}')
            raise
    
    async def get_user_balance(self, user_id: int) -> int:
        """Get user's current balance"""
        try:
            await self.ensure_economy_user(user_id)
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('''
                    SELECT balance FROM economy_users WHERE user_id = ?
                ''', (user_id,))
                result = await cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f'Error getting user balance: {e}')
            raise
    
    async def get_user_total_earned(self, user_id: int) -> int:
        """Get user's total earned amount"""
        try:
            await self.ensure_economy_user(user_id)
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('''
                    SELECT total_earned FROM economy_users WHERE user_id = ?
                ''', (user_id,))
                result = await cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f'Error getting user total earned: {e}')
            raise
    
    async def add_money(self, user_id: int, amount: int, reason: str = "Unknown") -> bool:
        """Add money to user's balance"""
        try:
            await self.ensure_economy_user(user_id)
            async with aiosqlite.connect(self.db_path) as db:
                # Update balance and total earned
                await db.execute('''
                    UPDATE economy_users 
                    SET balance = balance + ?, total_earned = total_earned + ?
                    WHERE user_id = ?
                ''', (amount, amount, user_id))
                
                # Log transaction
                await db.execute('''
                    INSERT INTO economy_transactions (user_id, amount, transaction_type, reason)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, amount, "ADD", reason))
                
                await db.commit()
                logger.info(f'Added {amount} to user {user_id}: {reason}')
                return True
        except Exception as e:
            logger.error(f'Error adding money: {e}')
            raise
    
    async def remove_money(self, user_id: int, amount: int, reason: str = "Unknown") -> bool:
        """Remove money from user's balance"""
        try:
            await self.ensure_economy_user(user_id)
            async with aiosqlite.connect(self.db_path) as db:
                # Check if user has enough balance
                cursor = await db.execute('''
                    SELECT balance FROM economy_users WHERE user_id = ?
                ''', (user_id,))
                result = await cursor.fetchone()
                current_balance = result[0] if result else 0
                
                if current_balance < amount:
                    logger.warning(f'Insufficient funds for user {user_id}: {current_balance} < {amount}')
                    return False
                
                # Update balance
                await db.execute('''
                    UPDATE economy_users 
                    SET balance = balance - ?
                    WHERE user_id = ?
                ''', (amount, user_id))
                
                # Log transaction
                await db.execute('''
                    INSERT INTO economy_transactions (user_id, amount, transaction_type, reason)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, -amount, "REMOVE", reason))
                
                await db.commit()
                logger.info(f'Removed {amount} from user {user_id}: {reason}')
                return True
        except Exception as e:
            logger.error(f'Error removing money: {e}')
            raise
    
    async def get_economy_leaderboard(self, limit: int = 10) -> List[Tuple[int, int]]:
        """Get economy leaderboard by balance"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('''
                    SELECT user_id, balance 
                    FROM economy_users 
                    ORDER BY balance DESC 
                    LIMIT ?
                ''', (limit,))
                results = await cursor.fetchall()
                return results
        except Exception as e:
            logger.error(f'Error getting economy leaderboard: {e}')
            raise
    
    async def add_item_to_inventory(self, user_id: int, item_id: str, quantity: int = 1) -> bool:
        """Add item to user's inventory"""
        try:
            await self.ensure_economy_user(user_id)
            async with aiosqlite.connect(self.db_path) as db:
                # Check if item already exists
                cursor = await db.execute('''
                    SELECT quantity FROM economy_inventory 
                    WHERE user_id = ? AND item_id = ?
                ''', (user_id, item_id))
                result = await cursor.fetchone()
                
                if result:
                    # Update existing item
                    await db.execute('''
                        UPDATE economy_inventory 
                        SET quantity = quantity + ?
                        WHERE user_id = ? AND item_id = ?
                    ''', (quantity, user_id, item_id))
                else:
                    # Add new item
                    await db.execute('''
                        INSERT INTO economy_inventory (user_id, item_id, quantity)
                        VALUES (?, ?, ?)
                    ''', (user_id, item_id, quantity))
                
                await db.commit()
                logger.info(f'Added {quantity}x {item_id} to user {user_id} inventory')
                return True
        except Exception as e:
            logger.error(f'Error adding item to inventory: {e}')
            raise
    
    async def get_user_inventory(self, user_id: int) -> Dict[str, int]:
        """Get user's inventory"""
        try:
            await self.ensure_economy_user(user_id)
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('''
                    SELECT item_id, quantity 
                    FROM economy_inventory 
                    WHERE user_id = ?
                ''', (user_id,))
                results = await cursor.fetchall()
                return {item_id: quantity for item_id, quantity in results}
        except Exception as e:
            logger.error(f'Error getting user inventory: {e}')
            raise
    
    async def get_economy_stats(self) -> Dict:
        """Get economy statistics"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Get total users
                cursor = await db.execute('SELECT COUNT(*) FROM economy_users')
                total_users = (await cursor.fetchone())[0]
                
                # Get total money in circulation
                cursor = await db.execute('SELECT SUM(balance) FROM economy_users')
                total_money = (await cursor.fetchone())[0] or 0
                
                # Get total transactions
                cursor = await db.execute('SELECT COUNT(*) FROM economy_transactions')
                total_transactions = (await cursor.fetchone())[0]
                
                # Get average balance
                cursor = await db.execute('SELECT AVG(balance) FROM economy_users WHERE balance > 0')
                avg_balance = (await cursor.fetchone())[0] or 0
                
                return {
                    'total_users': total_users,
                    'total_money': total_money,
                    'total_transactions': total_transactions,
                    'average_balance': round(avg_balance, 2)
                }
        except Exception as e:
            logger.error(f'Error getting economy stats: {e}')
            raise
    
    async def get_claimed_level_rewards(self, user_id: int) -> List[int]:
        """Get list of levels for which user has claimed rewards"""
        try:
            await self.ensure_economy_user(user_id)
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('''
                    SELECT level FROM level_rewards WHERE user_id = ?
                ''', (user_id,))
                results = await cursor.fetchall()
                return [row[0] for row in results]
        except Exception as e:
            logger.error(f'Error getting claimed level rewards: {e}')
            raise
    
    async def claim_level_reward(self, user_id: int, level: int) -> bool:
        """Mark a level reward as claimed"""
        try:
            await self.ensure_economy_user(user_id)
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT OR IGNORE INTO level_rewards (user_id, level)
                    VALUES (?, ?)
                ''', (user_id, level))
                await db.commit()
                logger.info(f'Claimed level {level} reward for user {user_id}')
                return True
        except Exception as e:
            logger.error(f'Error claiming level reward: {e}')
            raise
