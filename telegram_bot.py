import os
import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ContextTypes, MessageHandler, filters
)
import database as db
from config import BOT_TOKEN, ADMIN_CHAT_ID

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message"""
    welcome_text = """
    🤖 *Phone API Management Bot*

    *Available Commands:*
    /createkey - Create new API key
    /listkeys - List all API keys
    /deletekey - Delete an API key
    /keyinfo - Get key information
    /usage - Check API usage

    *Admin Only Commands*
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def create_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create new API key"""
    user_id = update.effective_user.id
    
    # Check if user is admin
    if str(user_id) != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Only admin can create API keys")
        return
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Usage: /createkey <key> <owner> [max_usage] [days_valid]")
        return
    
    try:
        key = context.args[0]
        owner = context.args[1]
        max_usage = int(context.args[2]) if len(context.args) > 2 else 1000
        days_valid = int(context.args[3]) if len(context.args) > 3 else 30
        
        if db.add_api_key(key, owner, max_usage, days_valid):
            await update.message.reply_text(
                f"✅ *API Key Created Successfully!*\n\n"
                f"🔑 *Key:* `{key}`\n"
                f"👤 *Owner:* {owner}\n"
                f"📊 *Max Usage:* {max_usage}\n"
                f"📅 *Valid for:* {days_valid} days\n\n"
                f"*Usage URL:*\n`https://your-app.onrender.com/?apikey={key}&query=PHONE_NUMBER`",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ API key already exists")
            
    except ValueError:
        await update.message.reply_text("❌ Invalid format. Usage: /createkey <key> <owner> [max_usage] [days_valid]")

async def list_keys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all API keys"""
    user_id = update.effective_user.id
    if str(user_id) != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Only admin can list API keys")
        return
    
    keys = db.get_all_api_keys()
    
    if not keys:
        await update.message.reply_text("📭 No API keys found")
        return
    
    response = "🔑 *All API Keys:*\n\n"
    for key in keys:
        status = "✅ Active" if key['is_active'] else "❌ Inactive"
        usage_percent = (key['current_usage'] / key['max_usage'] * 100) if key['max_usage'] > 0 else 0
        
        response += (
            f"🔑 *Key:* `{key['key']}`\n"
            f"👤 *Owner:* {key['owner']}\n"
            f"📊 *Usage:* {key['current_usage']}/{key['max_usage']} ({usage_percent:.1f}%)\n"
            f"📅 *Expires:* {key['expires_at']}\n"
            f"🔄 *Status:* {status}\n\n"
        )
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def delete_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete an API key"""
    user_id = update.effective_user.id
    if str(user_id) != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Only admin can delete API keys")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /deletekey <api_key>")
        return
    
    key_to_delete = context.args[0]
    if db.delete_api_key(key_to_delete):
        await update.message.reply_text(f"✅ API key `{key_to_delete}` deleted successfully", parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ API key not found")

async def key_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get information about a specific key"""
    user_id = update.effective_user.id
    if str(user_id) != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Only admin can view key information")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /keyinfo <api_key>")
        return
    
    key = context.args[0]
    details = db.get_api_key_details(key)
    
    if details:
        status = "✅ Active" if details['is_active'] else "❌ Inactive"
        usage_percent = (details['current_usage'] / details['max_usage'] * 100) if details['max_usage'] > 0 else 0
        
        await update.message.reply_text(
            f"🔑 *Key Information:*\n\n"
            f"🔑 *Key:* `{details['key']}`\n"
            f"👤 *Owner:* {details['owner']}\n"
            f"📊 *Usage:* {details['current_usage']}/{details['max_usage']} ({usage_percent:.1f}%)\n"
            f"📅 *Created:* {details['created_at']}\n"
            f"📅 *Expires:* {details['expires_at']}\n"
            f"🔄 *Status:* {status}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ API key not found")

async def usage_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get usage statistics"""
    user_id = update.effective_user.id
    if str(user_id) != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ Only admin can view usage statistics")
        return
    
    stats = db.get_usage_stats()
    keys = db.get_all_api_keys()
    active_keys = len([k for k in keys if k['is_active']])
    total_usage = sum(key['current_usage'] for key in keys)
    
    await update.message.reply_text(
        f"📊 *Usage Statistics:*\n\n"
        f"🔑 *Total Keys:* {len(keys)}\n"
        f"✅ *Active Keys:* {active_keys}\n"
        f"📈 *Total API Calls:* {stats['total_calls']}\n"
        f"📅 *Today's Calls:* {stats['today_calls']}\n"
        f"🎯 *Success Rate:* {stats['success_rate']:.1f}%\n"
        f"💯 *Total Usage:* {total_usage} requests",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    help_text = """
    🤖 *Phone API Bot Help*

    *Commands:*
    /start - Start the bot
    /createkey <key> <owner> [max_usage] [days] - Create API key
    /listkeys - List all API keys
    /deletekey <key> - Delete an API key
    /keyinfo <key> - Get key information
    /usage - Show usage statistics
    /help - Show this help message

    *Example:*
    `/createkey MYKEY123 JohnDoe 1000 30`
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

def main():
    """Start the bot"""
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not set")
        return
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("createkey", create_key))
    application.add_handler(CommandHandler("listkeys", list_keys))
    application.add_handler(CommandHandler("deletekey", delete_key))
    application.add_handler(CommandHandler("keyinfo", key_info))
    application.add_handler(CommandHandler("usage", usage_stats))
    application.add_handler(CommandHandler("help", help_command))
    
    # Start polling
    print("🤖 Telegram Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()