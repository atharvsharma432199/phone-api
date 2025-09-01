import os

# Google Drive Configuration
GOOGLE_DRIVE_FILE_ID = "1C726IZypnLOY85daHXiGQv4c7kfoXHOT"  # YAHAN FILE ID DAALO

# Database Configuration
PHONE_DB_NAME = "phone_data.db"
API_DB_NAME = "api_keys.db"

# API Configuration
REFRESH_INTERVAL = 3600

# Telegram Bot Configuration
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
ADMIN_CHAT_ID = os.environ.get('ADMIN_CHAT_ID', '')

# Web Service URL
WEB_SERVICE_URL = os.environ.get('RENDER_EXTERNAL_URL', 'https://your-app.onrender.com')

# Admin Configuration
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"