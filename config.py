# Google Drive Configuration
GOOGLE_DRIVE_FILE_ID = "1C726IZypnLOY85daHXiGQv4c7kfoXHOT"

# Database Configuration
PHONE_DB_NAME = "phone_data.db"
API_DB_NAME = "api_keys.db"

# API Configuration
REFRESH_INTERVAL = 3600

# Telegram Bot Configuration - Render Environment Variables se ayenge
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
ADMIN_CHAT_ID = os.environ.get('ADMIN_CHAT_ID', '')

# Admin Configuration
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"