import telebot
import re
import json
import os
from telebot import types

# ============== DEFAULT SETTINGS ==============
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7634920543:AAE4RaPPd3TO26hURlyBauOsJ_zJEnLk9rY")
YOUR_USER_ID = int(os.environ.get("YOUR_USER_ID", "7406197326"))
TARGET_CHANNEL_ID = int(os.environ.get("TARGET_CHANNEL_ID", "-1003120043320"))
TARGET_CHANNEL_USERNAME = os.environ.get("TARGET_CHANNEL_USERNAME", "@animethic2")
YOUR_WEBSITE = os.environ.get("YOUR_WEBSITE", "www.animethic.xyz")
SETTINGS_FILE = "settings.json"
# =============================================

# Load settings from file (jodi thake)
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except:
        pass

# Current settings load
settings = load_settings()
if settings:
    TARGET_CHANNEL_USERNAME = settings.get('channel_username', TARGET_CHANNEL_USERNAME)
    YOUR_WEBSITE = settings.get('website', YOUR_WEBSITE)
    REPLACE_URLS = settings.get('replace_urls', True)
    REPLACE_MENTIONS = settings.get('replace_mentions', True)
    ADD_CREDIT = settings.get('add_credit', True)
else:
    REPLACE_URLS = True
    REPLACE_MENTIONS = True
    ADD_CREDIT = True

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

def is_authorized(user_id):
    return user_id == YOUR_USER_ID

def edit_caption(original_caption):
    if original_caption is None:
        original_caption = ""
    
    edited = str(original_caption)
    
    if REPLACE_MENTIONS:
        # @username replace
        edited = re.sub(r'@[a-zA-Z][a-zA-Z0-9_]{3,}', TARGET_CHANNEL_USERNAME, edited)
    
    if REPLACE_URLS:
        # t.me/ link replace
        edited = re.sub(r'(https?://)?t\.me/[a-zA-Z][a-zA-Z0-9_]+', f'https://t.me/{TARGET_CHANNEL_USERNAME[1:]}', edited)
        # Other URLs replace
        edited = re.sub(r'https?://(?!t\.me)[^\s]+', f'https://{YOUR_WEBSITE}', edited)
    
    if ADD_CREDIT:
        if edited.strip():
            edited += f"\n\nProvided by {YOUR_WEBSITE}"
        else:
            edited = f"Provided by {YOUR_WEBSITE}"
    
    return edited

# ============== SETTINGS PANEL ==============
@bot.message_handler(commands=['settings'])
def settings_panel(message):
    if not is_authorized(message.from_user.id):
        bot.reply_to(message, "❌ Unauthorized")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Current status show
    url_status = "✅" if REPLACE_URLS else "❌"
    mention_status = "✅" if REPLACE_MENTIONS else "❌"
    credit_status = "✅" if ADD_CREDIT else "❌"
    
    markup.add(
        types.InlineKeyboardButton(f"{url_status} URL Replace", callback_data="toggle_url"),
        types.InlineKeyboardButton(f"{mention_status} @Mention Replace", callback_data="toggle_mention"),
        types.InlineKeyboardButton(f"{credit_status} Add Credit", callback_data="toggle_credit"),
        types.InlineKeyboardButton("📊 Current Settings", callback_data="show_settings"),
        types.InlineKeyboardButton("✏️ Edit Channel", callback_data="edit_channel"),
        types.InlineKeyboardButton("🌐 Edit Website", callback_data="edit_website")
    )
    
    text = f"""
⚙️ <b>Settings Panel</b>

📌 <b>Current Settings:</b>
• Channel: <code>{TARGET_CHANNEL_USERNAME}</code>
• Website: <code>{YOUR_WEBSITE}</code>
• Replace URLs: {url_status}
• Replace @Mentions: {mention_status}
• Add Credit: {credit_status}

Tap buttons to toggle or edit.
    """
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    global REPLACE_URLS, REPLACE_MENTIONS, ADD_CREDIT, TARGET_CHANNEL_USERNAME, YOUR_WEBSITE
    
    if not is_authorized(call.from_user.id):
        bot.answer_callback_query(call.id, "Unauthorized")
        return
    
    if call.data == "toggle_url":
        REPLACE_URLS = not REPLACE_URLS
        save_settings_to_file()
        bot.answer_callback_query(call.id, f"URL Replace: {'ON' if REPLACE_URLS else 'OFF'}")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        settings_panel(call.message)
        
    elif call.data == "toggle_mention":
        REPLACE_MENTIONS = not REPLACE_MENTIONS
        save_settings_to_file()
        bot.answer_callback_query(call.id, f"@Mention Replace: {'ON' if REPLACE_MENTIONS else 'OFF'}")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        settings_panel(call.message)
        
    elif call.data == "toggle_credit":
        ADD_CREDIT = not ADD_CREDIT
        save_settings_to_file()
        bot.answer_callback_query(call.id, f"Add Credit: {'ON' if ADD_CREDIT else 'OFF'}")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        settings_panel(call.message)
        
    elif call.data == "show_settings":
        text = f"""
📊 <b>Current Configuration</b>

🔹 Channel: <code>{TARGET_CHANNEL_USERNAME}</code>
🔹 Channel ID: <code>{TARGET_CHANNEL_ID}</code>
🔹 Website: <code>{YOUR_WEBSITE}</code>
🔹 Replace URLs: {REPLACE_URLS}
🔹 Replace @Mentions: {REPLACE_MENTIONS}
🔹 Add Credit: {ADD_CREDIT}
        """
        bot.send_message(call.message.chat.id, text, parse_mode="HTML")
        bot.answer_callback_query(call.id)
        
    elif call.data == "edit_channel":
        msg = bot.send_message(call.message.chat.id, "Send new channel username (e.g., @newchannel):")
        bot.register_next_step_handler(msg, update_channel)
        bot.answer_callback_query(call.id)
        
    elif call.data == "edit_website":
        msg = bot.send_message(call.message.chat.id, "Send new website (e.g., example.com):")
        bot.register_next_step_handler(msg, update_website)
        bot.answer_callback_query(call.id)

def update_channel(message):
    global TARGET_CHANNEL_USERNAME
    if not is_authorized(message.from_user.id):
        return
    if not message.text.startswith('@'):
        bot.reply_to(message, "❌ Must start with @")
        return
    TARGET_CHANNEL_USERNAME = message.text.strip()
    save_settings_to_file()
    bot.reply_to(message, f"✅ Channel updated to {TARGET_CHANNEL_USERNAME}")

def update_website(message):
    global YOUR_WEBSITE
    if not is_authorized(message.from_user.id):
        return
    YOUR_WEBSITE = message.text.strip().replace('https://', '').replace('http://', '').split('/')[0]
    save_settings_to_file()
    bot.reply_to(message, f"✅ Website updated to {YOUR_WEBSITE}")

def save_settings_to_file():
    data = {
        'channel_username': TARGET_CHANNEL_USERNAME,
        'website': YOUR_WEBSITE,
        'replace_urls': REPLACE_URLS,
        'replace_mentions': REPLACE_MENTIONS,
        'add_credit': ADD_CREDIT
    }
    save_settings(data)

# ============== MEDIA HANDLERS ==============
@bot.message_handler(content_types=['video'])
def handle_video(message):
    if not is_authorized(message.from_user.id):
        bot.reply_to(message, "❌ Unauthorized")
        return
    
    new_caption = edit_caption(message.caption)
    try:
        bot.send_video(TARGET_CHANNEL_ID, message.video.file_id, caption=new_caption, parse_mode="HTML")
        bot.reply_to(message, "✅ Video posted to channel!")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    if not is_authorized(message.from_user.id):
        bot.reply_to(message, "❌ Unauthorized")
        return
    
    new_caption = edit_caption(message.caption)
    try:
        bot.send_document(TARGET_CHANNEL_ID, message.document.file_id, caption=new_caption, parse_mode="HTML")
        bot.reply_to(message, "✅ Document posted to channel!")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['start', 'help'])
def start(message):
    if is_authorized(message.from_user.id):
        bot.reply_to(message, "👋 Bot is ready!\n/settings - Open control panel\nForward video/document to post.")
    else:
        bot.reply_to(message, "❌ Unauthorized")

# ============== KEEP ALIVE ==============
print("🤖 Bot is running...")
print(f"Channel: {TARGET_CHANNEL_USERNAME}")
print(f"Website: {YOUR_WEBSITE}")

# Error handling for polling
while True:
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"Error: {e}")
        import time
        time.sleep(10)
