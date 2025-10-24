#!/usr/bin/python
# << CODE BY HUNX04
# << TELEGRAM BOT VERSION WITH TABS DESIGN & MULTI-LANGUAGE SUPPORT
# "Wahai orang-orang yang beriman! Janganlah kamu saling memakan harta sesamamu dengan jalan yang batil," (QS. An Nisaa': 29). Rasulullah SAW juga melarang umatnya untuk mengambil hak orang lain tanpa izin.

import telebot
import json
import requests
import phonenumbers
from phonenumbers import carrier, geocoder, timezone
import logging
import time
import sqlite3
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Telegram Bot
API_TOKEN = '8376484178:AAEuAHMcWQftbU9H9bjjgFJxpxvUnVi6yeI'
bot = telebot.TeleBot(API_TOKEN)

# Admin configuration
ADMIN_IDS = [5525126008]  # د ادمینانو ID ګانې

# Required channels
REQUIRED_CHANNELS = ['@Pro43zone', '@SQ_ZONE']  # اجباري چینلونه

# Database setup
def init_db():
    conn = sqlite3.connect('ghost_tracker.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            language TEXT DEFAULT 'pashto',
            points INTEGER DEFAULT 0,
            referral_code TEXT UNIQUE,
            referred_by INTEGER,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            free_track_used INTEGER DEFAULT 0,
            channels_joined INTEGER DEFAULT 0
        )
    ''')
    
    # Tracking history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracking_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            track_type TEXT,
            target TEXT,
            points_used INTEGER,
            track_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Referrals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER,
            referred_id INTEGER,
            reward_claimed INTEGER DEFAULT 0,
            referral_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Language texts
TEXTS = {
    'pashto': {
        'welcome': """
🕵️‍♂️ **GHOST TRACKER BOT** 🤖

🔎 **د OSINT معلوماتو لپاره ستاسو پوره مرستیال!** ⚡

🎯 **د لاسرسي وړ برخې:**
📱 **د تلیفون تعقیب** - د شمېرې څخه موقعیت او GPS
🌐 **IP تعقیب** - د انټرنېت پتې څیړنه  
👤 **د کارن نوم تعقیب** - د ټولنیزو رسنیو څیړنه
📍 **GPS موقعیت** - د نقشې موقعیت معلومات

🚀 **لاندې څخه یوه برخه وټاکئ:**
""",
        'phone_tab': "📱 د تلیفون تعقیب",
        'ip_tab': "🌐 IP تعقیب", 
        'username_tab': "👤 د کارن نوم تعقیب",
        'gps_tab': "📍 GPS موقعیت",
        'help_tab': "ℹ️ مرسته",
        'points_tab': "🏆 پوائنټونه",
        'referral_tab': "👥 ریفرال",
        'language_tab': "🌐 ژبه",
        'back_button': "🔙 بیرته",
        'phone_text': """
📱 **د تلیفون شمېرې تعقیب**

🔎 **مهرباني وکړئ خپل ټارګیټ تلیفون شمېره ولیکئ:**

💻 **بېلګې:**
`+93877177111`
`+93765432198`
`+93012345678`

🔐 **یادونه:** شمېره باید په نړیواله بڼه وي
""",
        'points_info': """
🏆 **د پوائنټونو معلومات**

💰 **ستاسو اوسني پوائنټونه:** `{points}`

✅ **د پوائنټونو کارونې:**
• 📱 د تلیفون تعقیب: **1 پوائنټ**
• 🌐 IP تعقیب: **1 پوائنټ**  
• 👤 د کارن نوم تعقیب: **1 پوائنټ**
• 📍 GPS موقعیت: **1 پوائنټ**

📈 **د پوائنټونو ترلاسه کولو لارې:**
• 👥 د ریفرال سیسټم څخه: **1 پوائنټ**
• ⭐ ورځنی لاسرسی: **1 پوائنټ**
""",
        'referral_info': """
👥 **د ریفرال سیسټم**

🔐 **ستاسو ریفرال کوډ:** `{referral_code}`

🔗 **د ریفرال لینک:**
`https://t.me/{bot_username}?start={referral_code}`

⚙️ **د ریفرال سیسټم قوانین:**
• 🤝 هر ریفرال: **1 پوائنټ**
• 📈 د ریفرال شمېر: **{referral_count}**
• 💰 ټولټال پوائنټونه: **{referral_points}**

🔎 **ستاسو ریفرالونه:**
{referral_list}
""",
        'language_select': "🌐 **خپله ژبه وټاکئ:**",
        'tracking_cost': "🪙 **د دې تعقیب لپاره 1 پوائنټ ضروري دی**",
        'insufficient_points': "❌ **ستاسو په ډیرو پوائنټونو ضرورت دی. اوسني پوائنټونه: {points}**",
        'free_track_used': "✅ **تاسو خپل وړیا تعقیب وکاروه. اوس پوائنټونه ضروري دي.**",
        'track_success': "✅ **تعقیب په بریالیتوب سره بشپړ شو**",
        'points_added': "💰 **تاسو {points} پوائنټونه ترلاسه کړل**",
        'new_referral': "🎉 **ستاسو یو نوی ریفرال! تاسو 1 پوائنټ ترلاسه کړل.**",
        'admin_only': "🛡️ **تاسو د دې حکم لپاره اجازه نلرئ. یوازې ادمینان کولای شي دا حکم وکاروي.**",
        'broadcast_usage': "📢 **د بروډکاسټ لپاره پیغام ولیکئ: `/broadcast د پیغام متن`**",
        'broadcast_started': "📡 **بروډکاسټ پیل شو...**",
        'broadcast_completed': "✅ **بروډکاسټ بشپړ شو:**\n\n✅ **بریالي:** {success_count}\n❌ **نابریالي:** {fail_count}",
        'admin_stats': """
💻 **د بوت احصائیې**

👥 **ټول کارنان:** {total_users}
📈 **نوي کارنان (نن):** {new_users_today}
👤 **فعال کارنان (ورځ):** {active_today}
🔎 **ټول تعقیبونه:** {total_tracks}
🔗 **ټول ریفرالونه:** {total_referrals}

📈 **د کارن ګراف:**
{user_graph}
""",
        'channels_required': """
🔔 **لاندې چینلونو ته باید شامل شئ**

📢 **اړینه ده چې لاندې چینلونو ته شامل شئ ترڅو د بوت خدمات وکاروئ:**

{channels_list}

⚙️ **لارښود:**
1. لاندې چینلونو ته شامل شئ
2. د "✅ چیک کړه" بټن کلیک کړئ
3. د بوت خدمات وکاروئ

🛡️ **یادونه:** که تاسو چینلونو ته شامل نه شئ، نشئ کولای د بوت خدمات وکاروئ
""",
        'check_channels': "✅ چیک کړه",
        'channels_verified': "✅ **ستاسو چینلونه تایید شول! اوس تاسو کولای شئ د بوت خدمات وکاروئ.**",
        'channels_not_joined': "❌ **تاسو لاندې چینلونو ته شامل نه یاست:**\n{not_joined}",
        'language_welcome': "🌐 **خپله ژبه وټاکئ / Choose your language / زبان خود را انتخاب کنید**",
        'transfer_success': "✅ **پوائنټونه په بریالیتوب سره ولېږدول شول**\n\n👤 **کارن ایدی:** `{user_id}`\n💰 **پوائنټونه:** `{points}`\n📈 **نوي پوائنټونه:** `{new_points}`",
        'transfer_help': """
💰 **د پوائنټ لیږد لارښود**

💻 **کارونې:**
`/transfer [پوائنټونه] [د کارن ایدی]`

🔐 **بېلګې:**
`/transfer 100 123456789` - 100 پوائنټونه د 123456789 ایدی کارن ته لیږدي
`/transfer 500 987654321` - 500 پوائنټونه د 987654321 ایدی کارن ته لیږدي

💰 **ستاسو اوسني پوائنټونه:** 999999999999999
"""
    },
    'dari': {
        'welcome': """
🕵️‍♂️ **ربات ردیاب GHOST** 🤖

🔎 **دستیار کامل شما برای اطلاعات OSINT!** ⚡

🎯 **بخش های قابل دسترسی:**
📱 **ردیابی تلفن** - موقعیت و GPS از شماره
🌐 **ردیابی IP** - تحقیق آدرس اینترنتی  
👤 **ردیابی نام کاربری** - تحقیق شبکه های اجتماعی
📍 **موقعیت GPS** - اطلاعات موقعیت نقشه

🚀 **یک بخش از زیر انتخاب کنید:**
""",
        'phone_tab': "📱 ردیابی تلفن",
        'ip_tab': "🌐 ردیابی IP",
        'username_tab': "👤 ردیابی نام کاربری", 
        'gps_tab': "📍 موقعیت GPS",
        'help_tab': "ℹ️ راهنما",
        'points_tab': "🏆 امتیازات",
        'referral_tab': "👥 معرفی",
        'language_tab': "🌐 زبان",
        'back_button': "🔙 بازگشت",
        'phone_text': """
📱 **ردیابی شماره تلفن**

🔎 **لطفاً شماره تلفن هدف خود را وارد کنید:**

💻 **مثال ها:**
`+93877177111`
`+93765432198` 
`+93012345678`

🔐 **توجه:** شماره باید در فرمت بین المللی باشد
""",
        'points_info': """
🏆 **اطلاعات امتیازات**

💰 **امتیازات فعلی شما:** `{points}`

✅ **کاربرد امتیازات:**
• 📱 ردیابی تلفن: **1 امتیاز**
• 🌐 ردیابی IP: **1 امتیاز**
• 👤 ردیابی نام کاربری: **1 امتیاز**
• 📍 موقعیت GPS: **1 امتیاز**

📈 **راه های کسب امتیازات:**
• 👥 از سیستم معرفی: **1 امتیاز**
• ⭐ دسترسی روزانه: **1 امتیاز**
""",
        'referral_info': """
👥 **سیستم معرفی**

🔐 **کد معرف شما:** `{referral_code}`

🔗 **لینک معرفی:**
`https://t.me/{bot_username}?start={referral_code}`

⚙️ **قوانین سیستم معرفی:**
• 🤝 هر معرفی: **1 امتیاز**
• 📈 تعداد معرفی ها: **{referral_count}**
• 💰 مجموع امتیازات: **{referral_points}**

🔎 **معرفی های شما:**
{referral_list}
""",
        'language_select': "🌐 **زبان خود را انتخاب کنید:**",
        'tracking_cost': "🪙 **برای این ردیابی 1 امتیاز لازم است**",
        'insufficient_points': "❌ **شما به امتیازات بیشتری نیاز دارید. امتیازات فعلی: {points}**",
        'free_track_used': "✅ **شما از ردیابی رایگان خود استفاده کردید. اکنون امتیازات لازم است.**",
        'track_success': "✅ **ردیابی با موفقیت کامل شد**",
        'points_added': "💰 **شما {points} امتیاز دریافت کردید**",
        'new_referral': "🎉 **یک معرفی جدید! شما 1 امتیاز دریافت کردید.**",
        'admin_only': "🛡️ **شما اجازه استفاده از این دستور را ندارید. فقط ادمین ها می توانند این دستور را استفاده کنند.**",
        'broadcast_usage': "📢 **برای برودکست پیام بنویسید: `/broadcast متن پیام`**",
        'broadcast_started': "📡 **برودکست شروع شد...**",
        'broadcast_completed': "✅ **برودکست کامل شد:**\n\n✅ **موفق:** {success_count}\n❌ **ناموفق:** {fail_count}",
        'admin_stats': """
💻 **آمار ربات**

👥 **کل کاربران:** {total_users}
📈 **کاربران جدید (امروز):** {new_users_today}
👤 **کاربران فعال (روز):** {active_today}
🔎 **کل ردیابی ها:** {total_tracks}
🔗 **کل معرفی ها:** {total_referrals}

📈 **گراف کاربران:**
{user_graph}
""",
        'channels_required': """
🔔 **شما باید به کانال های زیر عضو شوید**

📢 **الزامی است که به کانال های زیر عضو شوید تا از خدمات ربات استفاده کنید:**

{channels_list}

⚙️ **راهنما:**
1. به کانال های زیر عضو شوید
2. دکمه "✅ بررسی کن" را کلیک کنید
3. از خدمات ربات استفاده کنید

🛡️ **توجه:** اگر به کانال ها عضو نشوید، نمی توانید از خدمات ربات استفاده کنید
""",
        'check_channels': "✅ بررسی کن",
        'channels_verified': "✅ **کانال های شما تایید شد! اکنون می توانید از خدمات ربات استفاده کنید.**",
        'channels_not_joined': "❌ **شما به کانال های زیر عضو نیستید:**\n{not_joined}",
        'language_welcome': "🌐 **خپله ژبه وټاکئ / Choose your language / زبان خود را انتخاب کنید**",
        'transfer_success': "✅ **امتیازات با موفقیت انتقال یافت**\n\n👤 **آیدی کاربر:** `{user_id}`\n💰 **امتیازات:** `{points}`\n📈 **امتیازات جدید:** `{new_points}`",
        'transfer_help': """
💰 **راهنمای انتقال امتیازات**

💻 **کاربرد:**
`/transfer [امتیازات] [آیدی کاربر]`

🔐 **مثال ها:**
`/transfer 100 123456789` - 100 امتیاز به کاربر با آیدی 123456789 انتقال دهید
`/transfer 500 987654321` - 500 امتیاز به کاربر با آیدی 987654321 انتقال دهید

💰 **امتیازات فعلی شما:** 999999999999999
"""
    },
    'english': {
        'welcome': """
🕵️‍♂️ **GHOST TRACKER BOT** 🤖

🔎 **Your complete assistant for OSINT information!** ⚡

🎯 **Available Sections:**
📱 **Phone Tracking** - Location & GPS from number
🌐 **IP Tracking** - Internet address research  
👤 **Username Tracking** - Social media research
📍 **GPS Location** - Map location information

🚀 **Choose one section below:**
""",
        'phone_tab': "📱 Phone Tracking",
        'ip_tab': "🌐 IP Tracking",
        'username_tab': "👤 Username Tracking",
        'gps_tab': "📍 GPS Location", 
        'help_tab': "ℹ️ Help",
        'points_tab': "🏆 Points",
        'referral_tab': "👥 Referral",
        'language_tab': "🌐 Language",
        'back_button': "🔙 Back",
        'phone_text': """
📱 **Phone Number Tracking**

🔎 **Please enter your target phone number:**

💻 **Examples:**
`+93877177111`
`+93765432198`
`+93012345678`

🔐 **Note:** Number must be in international format
""",
        'points_info': """
🏆 **Points Information**

💰 **Your Current Points:** `{points}`

✅ **Points Usage:**
• 📱 Phone Tracking: **1 Point**
• 🌐 IP Tracking: **1 Point**
• 👤 Username Tracking: **1 Point** 
• 📍 GPS Location: **1 Point**

📈 **Ways to Earn Points:**
• 👥 From Referral System: **1 Point**
• ⭐ Daily Access: **1 Point**
""",
        'referral_info': """
👥 **Referral System**

🔐 **Your Referral Code:** `{referral_code}`

🔗 **Referral Link:**
`https://t.me/{bot_username}?start={referral_code}`

⚙️ **Referral System Rules:**
• 🤝 Each Referral: **1 Point**
• 📈 Referral Count: **{referral_count}**
• 💰 Total Points: **{referral_points}**

🔎 **Your Referrals:**
{referral_list}
""",
        'language_select': "🌐 **Choose your language:**",
        'tracking_cost': "🪙 **1 Point required for this tracking**",
        'insufficient_points': "❌ **You need more points. Current points: {points}**",
        'free_track_used': "✅ **You used your free track. Now points are required.**",
        'track_success': "✅ **Tracking completed successfully**",
        'points_added': "💰 **You received {points} points**",
        'new_referral': "🎉 **New referral! You received 1 point.**",
        'admin_only': "🛡️ **You don't have permission for this command. Only admins can use this command.**",
        'broadcast_usage': "📢 **Write message for broadcast: `/broadcast message text`**",
        'broadcast_started': "📡 **Broadcast started...**",
        'broadcast_completed': "✅ **Broadcast completed:**\n\n✅ **Successful:** {success_count}\n❌ **Failed:** {fail_count}",
        'admin_stats': """
💻 **Bot Statistics**

👥 **Total Users:** {total_users}
📈 **New Users (Today):** {new_users_today}
👤 **Active Users (Day):** {active_today}
🔎 **Total Tracks:** {total_tracks}
🔗 **Total Referrals:** {total_referrals}

📈 **User Graph:**
{user_graph}
""",
        'channels_required': """
🔔 **You must join the following channels**

📢 **It is mandatory to join the following channels to use bot services:**

{channels_list}

⚙️ **Guide:**
1. Join the channels below
2. Click the "✅ Check" button
3. Use bot services

🛡️ **Note:** If you don't join the channels, you cannot use bot services
""",
        'check_channels': "✅ Check",
        'channels_verified': "✅ **Your channels verified! Now you can use bot services.**",
        'channels_not_joined': "❌ **You are not joined to these channels:**\n{not_joined}",
        'language_welcome': "🌐 **خپله ژبه وټاکئ / Choose your language / زبان خود را انتخاب کنید**",
        'transfer_success': "✅ **Points transferred successfully**\n\n👤 **User ID:** `{user_id}`\n💰 **Points:** `{points}`\n📈 **New Points:** `{new_points}`",
        'transfer_help': """
💰 **Points Transfer Guide**

💻 **Usage:**
`/transfer [points] [user ID]`

🔐 **Examples:**
`/transfer 100 123456789` - Transfer 100 points to user with ID 123456789
`/transfer 500 987654321` - Transfer 500 points to user with ID 987654321

💰 **Your Current Points:** 999999999999999
"""
    }
}

# Database functions
def get_user(user_id):
    conn = sqlite3.connect('ghost_tracker.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            'user_id': user[0],
            'username': user[1],
            'language': user[2],
            'points': user[3],
            'referral_code': user[4],
            'referred_by': user[5],
            'join_date': user[6],
            'free_track_used': user[7],
            'channels_joined': user[8]
        }
    return None

def create_user(user_id, username, referral_code=None):
    conn = sqlite3.connect('ghost_tracker.db')
    cursor = conn.cursor()
    
    # Generate unique referral code
    import random
    import string
    user_referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    # Give admin unlimited points
    initial_points = 999999999999999 if user_id in ADMIN_IDS else 0
    
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, referral_code, referred_by, points)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, user_referral_code, referral_code, initial_points))
    
    conn.commit()
    conn.close()
    
    # If user was referred, give 1 point to referrer
    if referral_code:
        give_referral_points(referral_code, user_id)
    
    return user_referral_code

def update_channels_joined(user_id, status):
    conn = sqlite3.connect('ghost_tracker.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET channels_joined = ? WHERE user_id = ?', (status, user_id))
    conn.commit()
    conn.close()

def give_referral_points(referral_code, referred_user_id):
    """Give 1 point to referrer when someone uses their referral code"""
    conn = sqlite3.connect('ghost_tracker.db')
    cursor = conn.cursor()
    
    # Find referrer
    cursor.execute('SELECT user_id FROM users WHERE referral_code = ?', (referral_code,))
    referrer = cursor.fetchone()
    
    if referrer:
        referrer_id = referrer[0]
        
        # Check if this referral was already processed
        cursor.execute('SELECT * FROM referrals WHERE referrer_id = ? AND referred_id = ?', 
                      (referrer_id, referred_user_id))
        existing = cursor.fetchone()
        
        if not existing:
            # Give 1 point to referrer
            cursor.execute('UPDATE users SET points = points + 1 WHERE user_id = ?', (referrer_id,))
            
            # Record the referral
            cursor.execute('INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)', 
                         (referrer_id, referred_user_id))
            
            conn.commit()
            
            # Notify referrer
            try:
                user = get_user(referrer_id)
                if user:
                    language = user['language']
                    texts = TEXTS[language]
                    bot.send_message(referrer_id, texts['new_referral'])
            except:
                pass
    
    conn.close()

def update_points(user_id, points_change):
    conn = sqlite3.connect('ghost_tracker.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (points_change, user_id))
    conn.commit()
    conn.close()

def update_language(user_id, language):
    conn = sqlite3.connect('ghost_tracker.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET language = ? WHERE user_id = ?', (language, user_id))
    conn.commit()
    conn.close()

def add_tracking_history(user_id, track_type, target, points_used):
    conn = sqlite3.connect('ghost_tracker.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tracking_history (user_id, track_type, target, points_used)
        VALUES (?, ?, ?, ?)
    ''', (user_id, track_type, target, points_used))
    conn.commit()
    conn.close()

def get_user_referrals(user_id):
    conn = sqlite3.connect('ghost_tracker.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.username, r.referral_date 
        FROM referrals r 
        JOIN users u ON r.referred_id = u.user_id 
        WHERE r.referrer_id = ?
    ''', (user_id,))
    referrals = cursor.fetchall()
    conn.close()
    return referrals

def is_admin(user_id):
    """Check if user is admin"""
    return user_id in ADMIN_IDS

def check_user_joined_channels(user_id):
    """Check if user has joined all required channels"""
    try:
        not_joined = []
        for channel in REQUIRED_CHANNELS:
            try:
                chat_member = bot.get_chat_member(chat_id=channel, user_id=user_id)
                if chat_member.status not in ['member', 'administrator', 'creator']:
                    not_joined.append(channel)
            except Exception as e:
                logging.error(f"Error checking channel {channel}: {e}")
                not_joined.append(channel)
        
        return len(not_joined) == 0, not_joined
    except Exception as e:
        logging.error(f"Error in check_user_joined_channels: {e}")
        return False, REQUIRED_CHANNELS

def get_bot_stats():
    """Get bot statistics for admin"""
    conn = sqlite3.connect('ghost_tracker.db')
    cursor = conn.cursor()
    
    # Total users
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    # New users today
    cursor.execute('SELECT COUNT(*) FROM users WHERE DATE(join_date) = DATE("now")')
    new_users_today = cursor.fetchone()[0]
    
    # Active users today (users who did tracking today)
    cursor.execute('SELECT COUNT(DISTINCT user_id) FROM tracking_history WHERE DATE(track_date) = DATE("now")')
    active_today = cursor.fetchone()[0]
    
    # Total tracks
    cursor.execute('SELECT COUNT(*) FROM tracking_history')
    total_tracks = cursor.fetchone()[0]
    
    # Total referrals
    cursor.execute('SELECT COUNT(*) FROM referrals')
    total_referrals = cursor.fetchone()[0]
    
    # User growth graph (last 7 days)
    cursor.execute('''
        SELECT DATE(join_date) as date, COUNT(*) as count 
        FROM users 
        WHERE join_date >= DATE('now', '-7 days')
        GROUP BY DATE(join_date) 
        ORDER BY date
    ''')
    user_growth = cursor.fetchall()
    
    conn.close()
    
    # Create simple graph
    graph = ""
    for date, count in user_growth:
        bar = "█" * min(count, 10)  # Max 10 bars
        graph += f"{date}: {bar} ({count})\n"
    
    if not graph:
        graph = "❌ No data available"
    
    return {
        'total_users': total_users,
        'new_users_today': new_users_today,
        'active_today': active_today,
        'total_tracks': total_tracks,
        'total_referrals': total_referrals,
        'user_graph': graph
    }

# Command handlers
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Check if user was referred
    referral_code = None
    if len(message.text.split()) > 1:
        referral_code = message.text.split()[1]
    
    # Create or get user
    user = get_user(user_id)
    if not user:
        create_user(user_id, username, referral_code)
        user = get_user(user_id)
        # New user - show language selection first
        show_language_selection(message)
        return
    
    # Existing user - check channels first
    channels_joined, not_joined = check_user_joined_channels(user_id)
    
    if not channels_joined:
        show_channels_required(message, user_id, not_joined)
        return
    
    # User has joined channels and has language set - show main menu
    language = user['language'] if user else 'pashto'
    texts = TEXTS[language]
    
    # Create inline keyboard with tabs
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    buttons = [
        InlineKeyboardButton(texts['phone_tab'], callback_data="tab_phone"),
        InlineKeyboardButton(texts['ip_tab'], callback_data="tab_ip"),
        InlineKeyboardButton(texts['username_tab'], callback_data="tab_username"),
        InlineKeyboardButton(texts['gps_tab'], callback_data="tab_gps"),
        InlineKeyboardButton(texts['points_tab'], callback_data="tab_points"),
        InlineKeyboardButton(texts['referral_tab'], callback_data="tab_referral"),
        InlineKeyboardButton(texts['language_tab'], callback_data="tab_language"),
        InlineKeyboardButton(texts['help_tab'], callback_data="tab_help")
    ]
    
    keyboard.add(*buttons[0:2])
    keyboard.add(*buttons[2:4])
    keyboard.add(*buttons[4:6])
    keyboard.add(*buttons[6:8])
    
    welcome_text = texts['welcome']
    bot.send_message(message.chat.id, welcome_text, reply_markup=keyboard, parse_mode='Markdown')

def show_language_selection(message):
    """Show language selection for new users"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    buttons = [
        InlineKeyboardButton("پښتو", callback_data="lang_pashto"),
        InlineKeyboardButton("دری", callback_data="lang_dari"),
        InlineKeyboardButton("English", callback_data="lang_english")
    ]
    
    keyboard.add(*buttons[0:2])
    keyboard.add(buttons[2])
    
    language_text = "🌐 **خپله ژبه وټاکئ / Choose your language / زبان خود را انتخاب کنید**"
    bot.send_message(message.chat.id, language_text, reply_markup=keyboard, parse_mode='Markdown')

def show_channels_required(message, user_id, not_joined):
    """Show channels requirement message"""
    user = get_user(user_id)
    language = user['language'] if user else 'pashto'
    texts = TEXTS[language]
    
    keyboard = InlineKeyboardMarkup()
    
    # Add channel links
    for channel in REQUIRED_CHANNELS:
        keyboard.add(InlineKeyboardButton(f"📢 {channel}", url=f"https://t.me/{channel[1:]}"))
    
    # Add check button
    keyboard.add(InlineKeyboardButton(texts['check_channels'], callback_data="check_channels"))
    
    channels_list = "\n".join([f"• {channel}" for channel in REQUIRED_CHANNELS])
    
    channels_text = texts['channels_required'].format(channels_list=channels_list)
    bot.send_message(message.chat.id, channels_text, reply_markup=keyboard, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    user = get_user(user_id)
    language = user['language'] if user else 'pashto'
    texts = TEXTS[language]
    
    if call.data == "tab_phone":
        ask_phone_number(call.message, language)
    elif call.data == "tab_ip":
        ask_ip_address(call.message, language)
    elif call.data == "tab_username":
        ask_username(call.message, language)
    elif call.data == "tab_gps":
        ask_gps_coordinates(call.message, language)
    elif call.data == "tab_points":
        show_points_tab(call.message, user_id, language)
    elif call.data == "tab_referral":
        show_referral_tab(call.message, user_id, language)
    elif call.data == "tab_language":
        show_language_tab(call.message, language)
    elif call.data == "tab_help":
        show_help_tab(call.message, language)
    elif call.data == "back_to_main":
        send_welcome(call.message)
    elif call.data.startswith("lang_"):
        new_language = call.data.split("_")[1]
        update_language(user_id, new_language)
        bot.answer_callback_query(call.id, f"Language changed to {new_language}")
        
        # After language selection, check channels
        channels_joined, not_joined = check_user_joined_channels(user_id)
        if not channels_joined:
            show_channels_required(call.message, user_id, not_joined)
        else:
            send_welcome(call.message)
    elif call.data == "check_channels":
        # Check if user has joined channels
        channels_joined, not_joined = check_user_joined_channels(user_id)
        if channels_joined:
            update_channels_joined(user_id, 1)
            bot.answer_callback_query(call.id, texts['channels_verified'])
            send_welcome(call.message)
        else:
            bot.answer_callback_query(call.id, texts['channels_not_joined'].format(not_joined="\n".join(not_joined)))

def ask_phone_number(message, language):
    texts = TEXTS[language]
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(texts['back_button'], callback_data="back_to_main"))
    
    phone_text = texts['phone_text']
    bot.send_message(message.chat.id, phone_text, reply_markup=keyboard, parse_mode='Markdown')

def ask_ip_address(message, language):
    texts = TEXTS[language]
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(texts['back_button'], callback_data="back_to_main"))
    
    ip_text = """
🌐 **IP تعقیب**

🔎 **مهرباني وکړئ خپل ټارګیټ IP پته ولیکئ:**

💻 **بېلګې:**
`8.8.8.8`
`1.1.1.1`
`192.168.1.1`

🔐 **یادونه:** یوازې عامه IP پتې کارولای شی
"""
    bot.send_message(message.chat.id, ip_text, reply_markup=keyboard, parse_mode='Markdown')

def ask_username(message, language):
    texts = TEXTS[language]
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(texts['back_button'], callback_data="back_to_main"))
    
    username_text = """
👤 **د کارن نوم تعقیب**

🔎 **مهرباني وکړئ خپل ټارګیټ کارن نوم ولیکئ:**

💻 **بېلګې:**
`john_doe`
`example_user`
`test123`

🔐 **یادونه:** د ټولنیزو رسنیو کارن نومونه څیړل کېږي
"""
    bot.send_message(message.chat.id, username_text, reply_markup=keyboard, parse_mode='Markdown')

def ask_gps_coordinates(message, language):
    texts = TEXTS[language]
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(texts['back_button'], callback_data="back_to_main"))
    
    gps_text = """
📍 **GPS موقعیت تعقیب**

🔎 **مهرباني وکړئ خپل ټارګیټ GPS موقعیت ولیکئ:**

💻 **بېلګې:**
`34.5432,69.1234`
`34.123,69.456`
`34.5678,69.8765`

🔐 **یادونه:** موقعیت باید په (عرض البلد,طول البلد) بڼه وي
"""
    bot.send_message(message.chat.id, gps_text, reply_markup=keyboard, parse_mode='Markdown')

def show_points_tab(message, user_id, language):
    texts = TEXTS[language]
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(texts['back_button'], callback_data="back_to_main"))
    
    user = get_user(user_id)
    points = user['points'] if user else 0
    
    points_text = texts['points_info'].format(points=points)
    bot.send_message(message.chat.id, points_text, reply_markup=keyboard, parse_mode='Markdown')

def show_referral_tab(message, user_id, language):
    texts = TEXTS[language]
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(texts['back_button'], callback_data="back_to_main"))
    
    user = get_user(user_id)
    if not user:
        return
    
    referrals = get_user_referrals(user_id)
    referral_list = ""
    for i, (ref_username, ref_date) in enumerate(referrals, 1):
        referral_list += f"{i}. @{ref_username} - {ref_date[:10]}\n"
    
    if not referral_list:
        referral_list = "❌ هیڅ ریفرال نشته"
    
    bot_username = bot.get_me().username
    referral_text = texts['referral_info'].format(
        referral_code=user['referral_code'],
        bot_username=bot_username,
        referral_count=len(referrals),
        referral_points=len(referrals),  # 1 point per referral
        referral_list=referral_list
    )
    
    bot.send_message(message.chat.id, referral_text, reply_markup=keyboard, parse_mode='Markdown')

def show_language_tab(message, language):
    texts = TEXTS[language]
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    buttons = [
        InlineKeyboardButton("پښتو", callback_data="lang_pashto"),
        InlineKeyboardButton("دری", callback_data="lang_dari"),
        InlineKeyboardButton("English", callback_data="lang_english"),
        InlineKeyboardButton(texts['back_button'], callback_data="back_to_main")
    ]
    
    keyboard.add(*buttons[0:2])
    keyboard.add(*buttons[2:4])
    
    language_text = texts['language_select']
    bot.send_message(message.chat.id, language_text, reply_markup=keyboard, parse_mode='Markdown')

def show_help_tab(message, language):
    texts = TEXTS[language]
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(texts['back_button'], callback_data="back_to_main"))
    
    help_text = """
ℹ️ **د بوت کارونې لارښود**

💻 **لارښود:**
1. لاندې څخه یوه برخه وټاکئ
2. ټارګیټ معلومات ولیکئ
3. په اتوماتيک ډول تعقیب به پیل شي
4. پایلې به په 5 ثانیو کې وښودل شي

🔐 **د مستقیمو حکمونو کارول:**
`/phone +93877177111` - د تلیفون تعقیب
`/ip 8.8.8.8` - د IP تعقیب  
`/username example` - د کارن نوم تعقیب
`/gps 34.543,69.123` - د GPS تعقیب

💰 **د پوائنټونو سیسټم:**
• لومړی تعقیب وړیا دی
• هر تعقیب لپاره 1 پوائنټ ضروري دی
• هر ریفرال سره 1 پوائنټ ترلاسه کوئ

🛡️ **یادونه:** دا ټولګه یوازې د اخلاقي او قانوني موخو لپاره دی
"""
    bot.send_message(message.chat.id, help_text, reply_markup=keyboard, parse_mode='Markdown')

# د ادمین پوائنټ لیږد سیستم
@bot.message_handler(commands=['transfer'])
def admin_transfer(message):
    user_id = message.from_user.id
    
    # Check if user is admin
    if not is_admin(user_id):
        user = get_user(user_id)
        language = user['language'] if user else 'pashto'
        texts = TEXTS[language]
        bot.reply_to(message, texts['admin_only'])
        return
    
    user = get_user(user_id)
    language = user['language'] if user else 'pashto'
    texts = TEXTS[language]
    
    # Check command format
    if len(message.text.split()) < 3:
        transfer_help = """
💰 **د پوائنټ لیږد لارښود**

💻 **کارونې:**
`/transfer [پوائنټونه] [د کارن ایدی]`

🔐 **بېلګې:**
`/transfer 100 123456789` - 100 پوائنټونه د 123456789 ایدی کارن ته لیږدي
`/transfer 500 987654321` - 500 پوائنټونه د 987654321 ایدی کارن ته لیږدي

💰 **ستاسو اوسني پوائنټونه:** 999999999999999
"""
        bot.reply_to(message, transfer_help, parse_mode='Markdown')
        return
    
    try:
        points_to_transfer = int(message.text.split()[1])
        target_user_id = int(message.text.split()[2])
        
        # Check if points are valid
        if points_to_transfer <= 0:
            bot.reply_to(message, "❌ **د لیږد لپاره پوائنټونه باید له صفر څخه ډیر وي**")
            return
        
        # Check if target user exists
        target_user = get_user(target_user_id)
        if not target_user:
            bot.reply_to(message, f"❌ **کارن د {target_user_id} ایدی ونه موندل شو**")
            return
        
        # Transfer points (admin has unlimited points)
        update_points(target_user_id, points_to_transfer)
        
        # Get target user's language for notification
        target_language = target_user['language']
        target_texts = TEXTS[target_language]
        
        # Notify target user
        try:
            bot.send_message(
                target_user_id, 
                target_texts['points_added'].format(points=points_to_transfer) + "\n\n👤 **له ادمین څخه**"
            )
        except:
            pass
        
        # Confirm to admin
        new_points = target_user['points'] + points_to_transfer
        success_message = texts['transfer_success'].format(
            user_id=target_user_id,
            points=points_to_transfer,
            new_points=new_points
        )
        
        bot.reply_to(message, success_message, parse_mode='Markdown')
        
    except ValueError:
        bot.reply_to(message, "❌ **پوائنټونه او ایدی باید شمېرې وي**")
    except Exception as e:
        logging.error(f"Transfer error: {e}")
        bot.reply_to(message, "❌ **د لیږد په وخت کې ستونزه راغله**")

# Admin broadcast function
@bot.message_handler(commands=['broadcast'])
def admin_broadcast(message):
    user_id = message.from_user.id
    
    # Check if user is admin
    if not is_admin(user_id):
        user = get_user(user_id)
        language = user['language'] if user else 'pashto'
        texts = TEXTS[language]
        bot.reply_to(message, texts['admin_only'])
        return
    
    if len(message.text.split()) < 2:
        user = get_user(user_id)
        language = user['language'] if user else 'pashto'
        texts = TEXTS[language]
        bot.reply_to(message, texts['broadcast_usage'])
        return
    
    broadcast_text = ' '.join(message.text.split()[1:])
    
    user = get_user(user_id)
    language = user['language'] if user else 'pashto'
    texts = TEXTS[language]
    
    # Send broadcast started message
    bot.reply_to(message, texts['broadcast_started'])
    
    conn = sqlite3.connect('ghost_tracker.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users')
    users = cursor.fetchall()
    conn.close()
    
    success_count = 0
    fail_count = 0
    
    for user_tuple in users:
        try:
            user_id_to_send = user_tuple[0]
            bot.send_message(user_id_to_send, f"📢 **ادمین بروډکاسټ:**\n\n{broadcast_text}", parse_mode='Markdown')
            success_count += 1
            time.sleep(0.1)  # Prevent flooding
        except:
            fail_count += 1
    
    # Send broadcast completion message
    bot.send_message(user_id, texts['broadcast_completed'].format(
        success_count=success_count, 
        fail_count=fail_count
    ))

# Admin stats function
@bot.message_handler(commands=['stats'])
def admin_stats(message):
    user_id = message.from_user.id
    
    # Check if user is admin
    if not is_admin(user_id):
        user = get_user(user_id)
        language = user['language'] if user else 'pashto'
        texts = TEXTS[language]
        bot.reply_to(message, texts['admin_only'])
        return
    
    user = get_user(user_id)
    language = user['language'] if user else 'pashto'
    texts = TEXTS[language]
    
    # Get bot statistics
    stats = get_bot_stats()
    
    # Send stats to admin
    stats_text = texts['admin_stats'].format(
        total_users=stats['total_users'],
        new_users_today=stats['new_users_today'],
        active_today=stats['active_today'],
        total_tracks=stats['total_tracks'],
        total_referrals=stats['total_referrals'],
        user_graph=stats['user_graph']
    )
    
    bot.reply_to(message, stats_text, parse_mode='Markdown')

# د تلیفون تعقیب فعالیت
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    user = get_user(user_id)
    language = user['language'] if user else 'pashto'
    texts = TEXTS[language]
    
    # د تلیفون شمېرې تشخیص
    if message.text and (message.text.startswith('+93') or 
                        message.text.startswith('+92') or 
                        message.text.replace(' ', '').replace('-', '').isdigit() or
                        any(char in message.text for char in ['+', '00'])):
        handle_phone_input(message, user_id, language)
    
    # د IP پتې تشخیص
    elif message.text and ('.' in message.text and 
                          all(part.isdigit() for part in message.text.split('.') if part) and
                          len(message.text.split('.')) == 4):
        handle_ip_input(message, user_id, language)
    
    # د GPS موقعیت تشخیص
    elif message.text and (',' in message.text and 
                          all(part.replace('.', '').isdigit() for part in message.text.split(',') if part.strip())):
        handle_gps_input(message, user_id, language)
    
    # د کارن نوم تشخیص
    elif message.text and not message.text.startswith('/'):
        handle_username_input(message, user_id, language)
    
    else:
        # که چیرې هیڅ یوه ونه تشخیص شوه، اصلی مینو ته بیرته ولاړ شه
        send_welcome(message)

def check_and_deduct_points(user_id, track_type, target, language):
    user = get_user(user_id)
    if not user:
        return False
    
    texts = TEXTS[language]
    
    # Check if free track is available
    if user['free_track_used'] == 0:
        update_points(user_id, 0)  # Mark free track as used
        conn = sqlite3.connect('ghost_tracker.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET free_track_used = 1 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        add_tracking_history(user_id, track_type, target, 0)
        bot.send_message(user_id, texts['free_track_used'])
        return True
    
    # Check if user has enough points
    if user['points'] < 1:
        bot.send_message(user_id, texts['insufficient_points'].format(points=user['points']))
        return False
    
    # Deduct points
    update_points(user_id, -1)
    add_tracking_history(user_id, track_type, target, 1)
    return True

def handle_phone_input(message, user_id, language):
    """د تلیفون شمېرې پروسس کول"""
    try:
        phone_number = message.text.strip()
        texts = TEXTS[language]
        
        # Check points
        if not check_and_deduct_points(user_id, 'phone', phone_number, language):
            return
        
        # د لودینګ پیغام
        loading_msg = bot.send_message(message.chat.id, "📡 **د تلیفون شمېرې تعقیب پیل شو...**\n\n⚙️ *5 ثانیې لودینګ*", parse_mode='Markdown')
        
        # د لودینګ انیمیشن
        for i in range(5):
            time.sleep(1)
            bot.edit_message_text(
                f"📡 **د تلیفون شمېرې تعقیب پیل شو...**\n\n⚙️ *{5-i} ثانیې پاتې*",
                message.chat.id,
                loading_msg.message_id,
                parse_mode='Markdown'
            )
        
        bot.send_chat_action(message.chat.id, 'typing')
        
        # د تلیفون شمېرې تحلیل
        try:
            parsed_number = phonenumbers.parse(phone_number, None)
        except:
            bot.delete_message(message.chat.id, loading_msg.message_id)
            bot.reply_to(message, f"❌ **ستاسو ټارګیټ نمبر:** `{phone_number}`\n\n🛡️ **د تلیفون شمېره غلطه ده**", parse_mode='Markdown')
            return
        
        if not phonenumbers.is_valid_number(parsed_number):
            bot.delete_message(message.chat.id, loading_msg.message_id)
            bot.reply_to(message, f"❌ **ستاسو ټارګیټ نمبر:** `{phone_number}`\n\n🛡️ **د تلیفون شمېره اعتبار نلري**", parse_mode='Markdown')
            return
        
        # د تلیفون معلومات
        region_code = phonenumbers.region_code_for_number(parsed_number)
        provider = carrier.name_for_number(parsed_number, "en")
        location = geocoder.description_for_number(parsed_number, "en")
        timezones = timezone.time_zones_for_number(parsed_number)
        timezone_str = ', '.join(timezones) if timezones else 'ناجوړ'
        
        # د GPS موقعیت اټکل (د تلیفون کوډ پراساس)
        gps_location = estimate_gps_from_phone(region_code)
        
        # د پایلو پیغام
        bot.delete_message(message.chat.id, loading_msg.message_id)
        
        response = f"""
✅ **د تلیفون شمېرې تعقیب بشپړ شو**

📱 **ستاسو ټارګیټ نمبر:** `{phone_number}`

💻 **اساسي معلومات:**
📞 **شمېره:** `{phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)}`
🌍 **هېواد کوډ:** +{parsed_number.country_code}
📍 **سيمه:** {location}
⚙️ **وخت سيمه:** {timezone_str}

📍 **د GPS موقعیت:**
📌 **اټکلي موقع:** {gps_location['city']}
🗺️ **نقشه:** [ګوګل نقشه]({gps_location['map_url']})
🧭 **عرض البلد:** `{gps_location['lat']}`
🧭 **طول البلد:** `{gps_location['lon']}`

📡 **خدمات:**
📶 **تلیفون شرکت:** {provider if provider else 'ناجوړ'}
✅ **معتبره شمېره:** هو
🛰️ **ډول:** سیم کارت

🛡️ *دا معلومات اټکلي دي او د دقیق موقعیت لپاره نورې طریقی کارولای شی*
"""
        bot.reply_to(message, response, parse_mode='Markdown')
        
    except Exception as e:
        logging.error(f"Phone track error: {e}")
        try:
            bot.delete_message(message.chat.id, loading_msg.message_id)
        except:
            pass
        bot.reply_to(message, f"❌ **ستاسو ټارګیټ نمبر:** `{phone_number}`\n\n🛡️ **د تلیفون تعقیب کې ستونزې راغلې**", parse_mode='Markdown')

def handle_ip_input(message, user_id, language):
    """د IP پتې پروسس کول"""
    try:
        ip = message.text.strip()
        texts = TEXTS[language]
        
        # Check points
        if not check_and_deduct_points(user_id, 'ip', ip, language):
            return
        
        # د لودینګ پیغام
        loading_msg = bot.send_message(message.chat.id, "📡 **د IP پتې تعقیب پیل شو...**\n\n⚙️ *5 ثانیې لودینګ*", parse_mode='Markdown')
        
        # د لودینګ انیمیشن
        for i in range(5):
            time.sleep(1)
            bot.edit_message_text(
                f"📡 **د IP پتې تعقیب پیل شو...**\n\n⚙️ *{5-i} ثانیې پاتې*",
                message.chat.id,
                loading_msg.message_id,
                parse_mode='Markdown'
            )
        
        bot.send_chat_action(message.chat.id, 'typing')
        
        req_api = requests.get(f"http://ipwho.is/{ip}")
        
        if req_api.status_code != 200:
            bot.delete_message(message.chat.id, loading_msg.message_id)
            bot.reply_to(message, f"❌ **ستاسو ټارګیټ IP:** `{ip}`\n\n🛡️ **د IP معلومات ترلاسه کولو کې ستونزې**", parse_mode='Markdown')
            return
            
        ip_data = json.loads(req_api.text)
        
        if not ip_data.get('success', True):
            bot.delete_message(message.chat.id, loading_msg.message_id)
            bot.reply_to(message, f"❌ **ستاسو ټارګیټ IP:** `{ip}`\n\n🛡️ **د IP پته ونه موندل شوه**", parse_mode='Markdown')
            return
        
        # د پایلو پیغام
        bot.delete_message(message.chat.id, loading_msg.message_id)
        
        response = f"""
✅ **د IP پتې تعقیب بشپړ شو**

🌐 **ستاسو ټارګیټ IP:** `{ip}`

💻 **موقعیت معلومات:**
🌍 **هېواد:** {ip_data.get('country', 'ناجوړ')}
📍 **ښار:** {ip_data.get('city', 'ناجوړ')}
🗺️ **سيمه:** {ip_data.get('region', 'ناجوړ')}

📍 **د GPS موقعیت:**
🧭 **عرض البلد:** `{ip_data.get('latitude', 'ناجوړ')}`
🧭 **طول البلد:** `{ip_data.get('longitude', 'ناجوړ')}`
🗺️ **نقشه:** [ګوګل نقشه](https://www.google.com/maps/@{ip_data.get('latitude',0)},{ip_data.get('longitude',0)},8z)

📡 **نور معلومات:**
📶 **ISP:** {ip_data.get('connection', {}).get('isp', 'ناجوړ')}
⚙️ **ASN:** {ip_data.get('connection', {}).get('asn', 'ناجوړ')}
⚙️ **وخت سيمه:** {ip_data.get('timezone', {}).get('id', 'ناجوړ')}

🛡️ *یوازې د اخلاقي موخو لپاره وکاروئ*
"""
        bot.reply_to(message, response, parse_mode='Markdown')
        
    except Exception as e:
        logging.error(f"IP track error: {e}")
        try:
            bot.delete_message(message.chat.id, loading_msg.message_id)
        except:
            pass
        bot.reply_to(message, f"❌ **ستاسو ټارګیټ IP:** `{ip}`\n\n🛡️ **د IP تعقیب کې ستونزې راغلې**", parse_mode='Markdown')

def handle_gps_input(message, user_id, language):
    """د GPS موقعیت پروسس کول"""
    try:
        gps_coords = message.text.strip()
        texts = TEXTS[language]
        
        # Check points
        if not check_and_deduct_points(user_id, 'gps', gps_coords, language):
            return
        
        # د لودینګ پیغام
        loading_msg = bot.send_message(message.chat.id, "📡 **د GPS موقعیت تعقیب پیل شو...**\n\n⚙️ *5 ثانیې لودینګ*", parse_mode='Markdown')
        
        # د لودینګ انیمیشن
        for i in range(5):
            time.sleep(1)
            bot.edit_message_text(
                f"📡 **د GPS موقعیت تعقیب پیل شو...**\n\n⚙️ *{5-i} ثانیې پاتې*",
                message.chat.id,
                loading_msg.message_id,
                parse_mode='Markdown'
            )
        
        bot.send_chat_action(message.chat.id, 'typing')
        
        # د GPS تحلیل
        try:
            lat, lon = map(float, gps_coords.split(','))
        except:
            bot.delete_message(message.chat.id, loading_msg.message_id)
            bot.reply_to(message, f"❌ **ستاسو ټارګیټ موقعیت:** `{gps_coords}`\n\n🛡️ **د GPS موقعیت غلطه ده**", parse_mode='Markdown')
            return
        
        # د موقعیت معلومات ترلاسه کول
        location_info = get_location_from_gps(lat, lon)
        
        # د پایلو پیغام
        bot.delete_message(message.chat.id, loading_msg.message_id)
        
        response = f"""
✅ **د GPS موقعیت تعقیب بشپړ شو**

📍 **ستاسو ټارګیټ موقعیت:** `{gps_coords}`

💻 **موقعیت:**
🧭 **عرض البلد:** `{lat}`
🧭 **طول البلد:** `{lon}`
🗺️ **نقشه:** [ګوګل نقشه](https://www.google.com/maps?q={lat},{lon})

📍 **موقعیت معلومات:**
{location_info}

🔗 **د نقشې لینکونه:**
• [ګوګل نقشه](https://www.google.com/maps?q={lat},{lon})
• [اوپن سټریټ نقشه](https://www.openstreetmap.org/?mlat={lat}&mlon={lon})

🛡️ *د دقیقو معلوماتو لپاره د ګوګل نقشې لینک وکاروئ*
"""
        bot.reply_to(message, response, parse_mode='Markdown')
        
    except Exception as e:
        logging.error(f"GPS track error: {e}")
        try:
            bot.delete_message(message.chat.id, loading_msg.message_id)
        except:
            pass
        bot.reply_to(message, f"❌ **ستاسو ټارګیټ موقعیت:** `{gps_coords}`\n\n🛡️ **د GPS تعقیب کې ستونزې راغلې**", parse_mode='Markdown')

def handle_username_input(message, user_id, language):
    """د کارن نوم پروسس کول"""
    try:
        username = message.text.strip()
        texts = TEXTS[language]
        
        # Check points
        if not check_and_deduct_points(user_id, 'username', username, language):
            return
        
        # د لودینګ پیغام
        loading_msg = bot.send_message(message.chat.id, "📡 **د کارن نوم څیړنه پیل شو...**\n\n⚙️ *5 ثانیې لودینګ*", parse_mode='Markdown')
        
        # د لودینګ انیمیشن
        for i in range(5):
            time.sleep(1)
            bot.edit_message_text(
                f"📡 **د کارن نوم څیړنه پیل شو...**\n\n⚙️ *{5-i} ثانیې پاتې*",
                message.chat.id,
                loading_msg.message_id,
                parse_mode='Markdown'
            )
        
        bot.send_chat_action(message.chat.id, 'typing')
        
        social_media = [
            {"url": "https://www.facebook.com/{}", "name": "👤 فیسبوک"},
            {"url": "https://www.twitter.com/{}", "name": "👤 ټویټر"},
            {"url": "https://www.instagram.com/{}", "name": "👤 انسټاګرام"},
            {"url": "https://www.linkedin.com/in/{}", "name": "👤 لنکډان"},
            {"url": "https://www.github.com/{}", "name": "💻 ګیتهاب"},
            {"url": "https://www.youtube.com/{}", "name": "👤 یوټیوب"},
            {"url": "https://www.tiktok.com/@{}", "name": "👤 ټکټاک"},
            {"url": "https://t.me/{}", "name": "👤 تلګرام"}
        ]
        
        results = []
        for site in social_media:
            url = site['url'].format(username)
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    results.append(f"✅ {site['name']}: [لیدل]({url})")
                else:
                    results.append(f"❌ {site['name']}: ونه موندل شو")
            except:
                results.append(f"❌ {site['name']}: د اړیکې ستونزه")
        
        # د پایلو پیغام
        bot.delete_message(message.chat.id, loading_msg.message_id)
        
        response = f"""
✅ **د کارن نوم څیړنه بشپړ شوه**

👤 **ستاسو ټارګیټ کارن نوم:** `{username}`

🔎 **د ټولنیزو رسنیو څیړنه:**
{chr(10).join(results)}

⚙️ **یادونې:**
• دا څیړنه یوازې عامې پلیټفورمونه څیړي
• ممکنې پایلې 100% دقیقې نه وي
• د حریم خصوصي درناوی اخلاقي مسئولیت دی

🛡️ *یوازې د اخلاقي موخو لپاره وکاروئ*
"""
        bot.reply_to(message, response, parse_mode='Markdown')
        
    except Exception as e:
        logging.error(f"Username track error: {e}")
        try:
            bot.delete_message(message.chat.id, loading_msg.message_id)
        except:
            pass
        bot.reply_to(message, f"❌ **ستاسو ټارګیټ کارن نوم:** `{username}`\n\n🛡️ **د کارن نوم څیړنه کې ستونزې راغلې**", parse_mode='Markdown')

def estimate_gps_from_phone(country_code):
    """د تلیفون کوډ څخه د GPS موقعیت اټکل"""
    country_gps = {
        'AF': {'lat': 34.5432, 'lon': 69.1234, 'city': 'کابل, افغانستان'},
        'PK': {'lat': 33.6844, 'lon': 73.0479, 'city': 'اسلام آباد, پاکستان'},
        'IR': {'lat': 35.6892, 'lon': 51.3890, 'city': 'تهران, ایران'},
        'US': {'lat': 38.9072, 'lon': -77.0369, 'city': 'واشنګټن, امریکا'},
        'GB': {'lat': 51.5074, 'lon': -0.1278, 'city': 'لندن, انګلستان'},
        'CN': {'lat': 39.9042, 'lon': 116.4074, 'city': 'بیجنگ, چین'},
        'IN': {'lat': 28.6139, 'lon': 77.2090, 'city': 'نیو دهلي, هند'},
        'SA': {'lat': 24.7136, 'lon': 46.6753, 'city': 'ریاض, سعودي عربستان'}
    }
    
    default = {'lat': 34.5432, 'lon': 69.1234, 'city': 'کابل, افغانستان'}
    
    location = country_gps.get(country_code, default)
    location['map_url'] = f"https://www.google.com/maps?q={location['lat']},{location['lon']}"
    
    return location

def get_location_from_gps(lat, lon):
    """د GPS موقعیت څخه د ځای معلومات ترلاسه کول"""
    try:
        response = requests.get(f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}")
        if response.status_code == 200:
            data = response.json()
            address = data.get('address', {})
            
            country = address.get('country', 'ناجوړ')
            city = address.get('city') or address.get('town') or address.get('village') or 'ناجوړ'
            
            return f"🌍 **هېواد:** {country}\n📍 **ښار:** {city}"
        else:
            return "📍 **موقعیت:** معلومات ترلاسه نشول"
    except:
        return "📍 **موقعیت:** د معلوماتو ترلاسه کولو کې ستونزه"

def main():
    try:
        init_db()
        logging.info("Starting Ghost Tracker Bot with Multi-Language & Points System...")
        bot.polling(none_stop=True)
    except Exception as e:
        logging.error(f"Bot error: {e}")
        main()

if __name__ == '__main__':
    main()