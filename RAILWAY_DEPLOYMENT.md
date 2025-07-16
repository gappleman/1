# Railway Deployment Guide for Discord Bot

## Step 1: Prepare Your Project

✅ **Files Created:**
- `Procfile` - Defines how Railway should run your bot
- `railway.toml` - Railway configuration file
- `railway_requirements.txt` - Python dependencies for Railway

## Step 2: Set Up Railway Account

1. Go to [railway.app](https://railway.app)
2. Sign up/login with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"

## Step 3: Connect Your Repository

1. **Option A - Upload Files:**
   - Create a new GitHub repository
   - Upload all your bot files including:
     - `main.py`
     - `database.py`
     - `economy_system.py`
     - `achievements.py`
     - `moderation_panel.py`
     - `admin_panel.py`
     - `Procfile`
     - `railway.toml`
     - `railway_requirements.txt`
     - `.env.example`

2. **Option B - Use Replit GitHub Integration:**
   - Use Replit's GitHub integration to push your code
   - Connect your Replit project to a GitHub repository

## Step 4: Configure Environment Variables

In Railway dashboard:
1. Go to your project
2. Click "Variables" tab
3. Add these environment variables:
   - `DISCORD_TOKEN` = Your Discord bot token
   - `PYTHONPATH` = `/app`

## Step 5: Database Configuration

Your bot uses SQLite, which works with Railway's persistent storage:
1. In Railway, go to "Settings" → "Environment"
2. Railway will automatically provide persistent storage
3. Your `bot_database.db` file will be saved in the container

## Step 6: Deploy

1. Push your code to GitHub
2. Railway will automatically detect and deploy
3. Check the "Deployments" tab for build logs
4. Your bot should start automatically

## Step 7: Monitor Your Bot

1. Check "Logs" tab for runtime information
2. Monitor for any errors or issues
3. Your bot will restart automatically if it crashes

## Important Notes:

- **Database Persistence**: Railway provides persistent storage, so your SQLite database will survive restarts
- **Environment Variables**: Make sure your Discord token is properly set
- **Automatic Restarts**: Railway will restart your bot if it crashes
- **Logs**: Monitor logs regularly for any issues

## Troubleshooting:

- **Build Fails**: Check that `railway_requirements.txt` has correct dependencies
- **Bot Won't Start**: Verify `DISCORD_TOKEN` environment variable is set
- **Database Issues**: Ensure write permissions are working in Railway environment

## Cost:

- Railway offers a free tier with generous limits
- Perfect for Discord bots with moderate usage
- Automatic scaling and reliable uptime

Your Discord bot is now ready for Railway deployment!