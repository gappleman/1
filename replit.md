# Discord Bot Project

## Overview

This is a comprehensive Discord moderation bot built with Python using the discord.py library. The bot provides complete server moderation capabilities including staff management, punishment tracking, achievement systems, full moderation panel functionality, and a massive economy system with 600 levels, 532+ items, and automatic level rewards. It uses SQLite for persistent data storage and implements modern Discord features including slash commands with proper permission controls.

## Recent Changes (July 16, 2025)

- **Massive Economy Expansion**: Added 500 procedurally generated items across all categories
- **600-Level System**: Expanded from 50 to 600 maximum levels with progressive rewards
- **Level Rewards System**: Automatic credit and item distribution when users level up
- **New Commands**: Added `/claim_level_rewards` and `/level_progress` for reward management
- **Special Milestone Rewards**: Unique items and titles at levels 5, 10, 25, 50, 100, 200, 300, 400, 500, and 600
- **Progressive Scaling**: Rewards scale from 100 credits at level 1 to 5000+ credits at higher levels
- **Enhanced Integration**: Level up notifications integrated into daily rewards and work activities
- **Admin Panel System**: Complete admin control system accessible only by 's_atire' user with 10 powerful commands for economy management
- **Enhanced Shop System**: Added 4 new shop browsing commands for better item discovery and purchasing
- **Interactive Item System**: Added comprehensive item interaction system with `/use_item` command and real effects

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a simple two-tier architecture:

1. **Application Layer**: Discord bot using discord.py with command handling and event management
2. **Data Layer**: SQLite database with async operations using aiosqlite

The bot uses a modular design separating database operations from Discord bot logic, making it easy to maintain and extend.

## Key Components

### Discord Bot (`main.py`)
- **Bot Configuration**: Uses command prefix `!` with comprehensive intents for message content and guild access
- **Slash Command Support**: Implements modern Discord slash commands with automatic syncing
- **Permission System**: Admin-only command access using Discord's built-in permission system
- **Event Handling**: Handles bot ready events and initializes required components
- **Moderation Integration**: Full integration with moderation panel and achievement system

### Database Manager (`database.py`)
- **Async SQLite Operations**: Uses aiosqlite for non-blocking database operations
- **Table Management**: Creates and manages seven core tables (staff, punishments, achievements, economy_users, economy_transactions, economy_inventory, level_rewards)
- **Error Handling**: Comprehensive logging and exception handling for database operations
- **Achievement Support**: Methods for tracking and awarding user achievements
- **Economy Support**: Full economy database operations including balance management, transactions, and inventory tracking
- **Level Rewards Tracking**: Database support for tracking claimed level rewards and preventing duplicate claims

### Achievement System (`achievements.py`)
- **10 Achievement Types**: Rookie, Veteran, Active Moderator, Fair Judge, Punishment Master, Team Player, Milestone achievements
- **5 Rarity Levels**: Common, Uncommon, Rare, Epic, Legendary with weighted scoring system
- **Automatic Checking**: Real-time achievement evaluation when actions are performed
- **Leaderboard System**: Ranked scoring based on achievement rarity and quantity

### Moderation Panel (`moderation_panel.py`)
- **User Management**: Kick, ban, timeout, warn, and unban functionality
- **Advanced Features**: Bulk message deletion, comprehensive user information display
- **Audit Logging**: Complete action logging with timestamps and reasons
- **Permission Checks**: Proper Discord permission validation for all actions
- **Integration**: Seamless integration with punishment tracking and achievement systems

### Economy System (`economy_system.py`)
- **Currency System**: Credits-based economy with user balances and transaction logging
- **Job System**: 20 different jobs from entry-level (Helper, Miner) to high-paying (Lawyer, Doctor, Scientist) with level requirements
- **Activities**: Daily rewards, work jobs, crime activities, gambling, and money transfers
- **Shopping System**: 532+ items across 5 categories (Consumables, Tools, Upgrades, Badges, Collectibles) with 500 procedurally generated items
- **Inventory Management**: User inventories with item tracking and quantity management
- **Leaderboards**: Balance-based rankings and comprehensive economy statistics
- **Level System**: User progression based on total earnings (up to level 600)
- **Level Rewards**: Automatic credit and item rewards for reaching new levels, with special milestone rewards and titles
- **Progressive Rewards**: Escalating rewards from 100 credits at level 1 to 5000+ credits at higher levels

### Admin Panel (`admin_panel.py`)
- **Restricted Access**: Only accessible by Discord user 's_atire' with comprehensive authorization checks
- **Economy Management**: Full control over user balances, levels, and total earnings
- **Item Administration**: Give, remove, and manage user inventories with all 532+ items
- **User Statistics**: Comprehensive user data analysis including balance, level, inventory, and account details
- **Server Overview**: Complete server statistics and economy health monitoring
- **Data Management**: User reset capabilities and inventory clearing functions
- **Audit Trail**: All admin actions are logged with timestamps and admin identification

### Data Models
Two main entities are tracked:

1. **Staff Records**:
   - User identification (Discord user ID and username)
   - Role assignment and notes
   - Automatic timestamp tracking

2. **Punishment Records**:
   - User and moderator information
   - Punishment type and reason tracking
   - Complete audit trail with timestamps

## Data Flow

1. Bot starts and connects to Discord
2. Database tables are automatically created/verified
3. Slash commands are synced with Discord
4. Admin users can execute moderation commands
5. All actions are logged to SQLite database
6. Data persists across bot restarts

## External Dependencies

### Core Dependencies
- **discord.py**: Discord API interaction and bot framework
- **aiosqlite**: Async SQLite database operations
- **python-dotenv**: Environment variable management for secure configuration

### Environment Configuration
- Bot token stored securely in environment variables
- Database path configurable (defaults to local SQLite file)

## Deployment Strategy

### Local Development
- SQLite database file (`bot_database.db`) stored locally
- Environment variables loaded from `.env` file
- Logging configured for development debugging

### Production Considerations
- Environment variables should be configured in deployment platform
- SQLite file persistence needs to be ensured in containerized deployments
- Logging level should be configured appropriately for production

### Database Strategy
- **Current**: SQLite for simplicity and local development
- **Scalability**: Architecture supports easy migration to PostgreSQL via database manager abstraction
- **Backup**: SQLite file-based storage allows simple backup strategies

The bot architecture is designed to be simple yet extensible, with clear separation of concerns between Discord interactions and data persistence.