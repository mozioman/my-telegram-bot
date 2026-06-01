"""
╔══════════════════════════════════════════╗
║     ربات مدیریت گروه فارسی - نسخه PRO   ║
║         کد توسط Claude Anthropic          ║
╚══════════════════════════════════════════╝

نیازمندی‌ها:
    pip install pyTelegramBotAPI

اجرا:
    python telegram_bot.py
"""

import telebot
import json
import os
import time
import random
import threading
from telebot import types
from datetime import datetime

# ═══════════════════════════════════════════
#              تنظیمات اصلی
# ═══════════════════════════════════════════
TOKEN = "8236462182:AAHFOyynNepk9KNTPYMJWoDwR4WU1VNMPZ4"   # ← توکن ربات رو اینجا بذار
OWNER_IDS = [8236462182]               # ← آیدی عددی خودت، مثلاً: [123456789]

bot = telebot.TeleBot(TOKEN, parse_mode=None)

# ═══════════════════════════════════════════
#            سیستم ذخیره داده
# ═══════════════════════════════════════════
DATA_FILE = "bot_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "members": {},
        "saved_messages": [],
        "welcome_media": {},   # عکس/گیف خوشامدگویی
        "welcome_text": {},    # متن خوشامدگویی
        "banned_users": {},
        "warned_users": {},
        "muted_users": {},
        "notes": {},
        "filters": {},
        "settings": {},
    }

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

# ═══════════════════════════════════════════
#              ابزارهای کمکی
# ═══════════════════════════════════════════
def is_owner(user_id):
    return user_id in OWNER_IDS

def is_admin(user_id, chat_id):
    if is_owner(user_id):
        return True
    try:
        m = bot.get_chat_member(chat_id, user_id)
        return m.status in ["administrator", "creator"]
    except:
        return False

def is_creator(user_id, chat_id):
    try:
        m = bot.get_chat_member(chat_id, user_id)
        return m.status == "creator"
    except:
        return False

def get_mention(user):
    name = user.first_name or "کاربر"
    if user.username:
        return f"@{user.username}"
    return f"[{name}](tg://user?id={user.id})"

def update_member(chat_id, user):
    cid = str(chat_id)
    uid = str(user.id)
    if cid not in data["members"]:
        data["members"][cid] = {}
    data["members"][cid][uid] = {
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "username": user.username or "",
        "id": user.id,
    }
    save_data()

def remove_member(chat_id, user_id):
    cid = str(chat_id)
    uid = str(user_id)
    if cid in data["members"] and uid in data["members"][cid]:
        del data["members"][cid][uid]
        save_data()

def get_members(chat_id):
    return data["members"].get(str(chat_id), {})

def err_not_admin(msg):
    bot.reply_to(msg, "❌ **فقط ادمین‌ها می‌توانند از این دستور استفاده کنند\\!**", parse_mode="Markdown")

def err_reply_needed(msg):
    bot.reply_to(msg, "⚠️ **روی پیام کاربر ریپلای بزن\\!**", parse_mode="Markdown")

# ═══════════════════════════════════════════
#          خوشامدگویی و خداحافظی
# ═══════════════════════════════════════════
DEFAULT_WELCOMES = [
    "🌟 **سلام {name} عزیز\\!**\nبه گروه ما خوش اومدی 🎉\nامیدواریم وقت خوبی داشته باشی 😊",
    "👋 **{name} جان خوش اومدی\\!**\nخوشحالیم که به جمع ما پیوستی 🤩",
    "🎊 **{name} وارد شد\\!**\nبه هم دیگه خوش بگذره 🙌",
    "💫 **سلام به {name}\\!**\nعضو جدید گروه\\! خوش اومدی 🌈",
]

@bot.message_handler(content_types=["new_chat_members"])
def on_new_member(message):
    for user in message.new_chat_members:
        if user.is_bot:
            continue
        update_member(message.chat.id, user)
        cid = str(message.chat.id)
        name = user.first_name or "دوست"
        mention = get_mention(user)

        # بررسی عکس/گیف سفارشی
        media = data["welcome_media"].get(cid)
        custom_text = data["welcome_text"].get(cid, "")
        
        if custom_text:
            text = custom_text.replace("{name}", mention).replace("{group}", message.chat.title or "گروه")
        else:
            text = random.choice(DEFAULT_WELCOMES).replace("{name}", mention)

        try:
            if media:
                mtype = media.get("type")
                file_id = media.get("file_id")
                if mtype == "photo":
                    bot.send_photo(message.chat.id, file_id, caption=text, parse_mode="Markdown")
                elif mtype == "animation":
                    bot.send_animation(message.chat.id, file_id, caption=text, parse_mode="Markdown")
                else:
                    bot.send_message(message.chat.id, text, parse_mode="Markdown")
            else:
                bot.send_message(message.chat.id, text, parse_mode="Markdown")
        except Exception as e:
            print(f"خطا در خوشامدگویی: {e}")

@bot.message_handler(content_types=["left_chat_member"])
def on_leave(message):
    user = message.left_chat_member
    if user.is_bot:
        return
    remove_member(message.chat.id, user.id)
    name = user.first_name or "دوست"
    bot.send_message(
        message.chat.id,
        f"😢 **{name} گروه رو ترک کرد\\.\\.\\.**\nدلتنگت میشیم\\! 👋",
        parse_mode="Markdown"
    )

# ═══════════════════════════════════════════
#         ردیابی پیام‌ها + مسیریابی
# ═══════════════════════════════════════════
@bot.message_handler(func=lambda m: True, content_types=["text"])
def router(message):
    if message.from_user and not message.from_user.is_bot:
        update_member(message.chat.id, message.from_user)
    
    text = (message.text or "").strip()

    # ─── فیلترهای خودکار ───
    cid = str(message.chat.id)
    filters = data["filters"].get(cid, {})
    for keyword, response in filters.items():
        if keyword.lower() in text.lower():
            bot.send_message(message.chat.id, response, parse_mode="Markdown")
            return

    cmd = text.split()[0].lower().split("@")[0] if text else ""

    # ─── مسیریابی دستورات ───
    routes = {
        "/start": cmd_start,
        "/help": cmd_help,
        "/panel": cmd_panel,
        "/tag": cmd_tag,
        "/tag100": cmd_tag100,
        "/tagadmin": cmd_tagadmin,
        "/ban": cmd_ban,
        "/unban": cmd_unban,
        "/kick": cmd_kick,
        "/mute": cmd_mute,
        "/unmute": cmd_unmute,
        "/warn": cmd_warn,
        "/promote": cmd_promote,
        "/demote": cmd_demote,
        "/del": cmd_del,
        "/save": cmd_save,
        "/saved": cmd_saved,
        "/delsaved": cmd_delsaved,
        "/setwelcome": cmd_setwelcome,
        "/clearwelcome": cmd_clearwelcome,
        "/clear": cmd_clear,
        "/stats": cmd_stats,
        "/info": cmd_info,
        "/ping": cmd_ping,
        "/roll": cmd_roll,
        "/time": cmd_time,
        "/poll": cmd_poll,
        "/rules": cmd_rules,
        "/setrules": cmd_setrules,
        "/addfilter": cmd_addfilter,
        "/delfilter": cmd_delfilter,
        "/filters": cmd_filters,
        "/note": cmd_note,
        "/getnote": cmd_getnote,
        "/id": cmd_id,
        "/adminlist": cmd_adminlist,
    }

    handler = routes.get(cmd)
    if handler:
        handler(message)

# ═══════════════════════════════════════════
#             /start و /help
# ═══════════════════════════════════════════
def cmd_start(message):
    name = message.from_user.first_name or "دوست"
    text = (
        f"🤖 **سلام {name}\\!**\n\n"
        "من ربات مدیریت گروه هستم\\!\n"
        "برای دیدن دستورات بنویس `/help`\n"
        "برای پنل ادمین بنویس `/panel`"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

def cmd_help(message):
    text = (
        "📖 **راهنمای کامل ربات**\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "👑 **دستورات ادمین:**\n"
        "`/panel` — پنل مدیریت\n"
        "`/promote` — ارتقا به ادمین\n"
        "`/demote` — حذف از ادمینی\n"
        "`/ban` — بن کاربر\n"
        "`/unban` — رفع بن\n"
        "`/kick` — اخراج کاربر\n"
        "`/mute` — بی‌صدا کردن\n"
        "`/unmute` — رفع بی‌صدا\n"
        "`/warn` — اخطار دادن\n"
        "`/del` — حذف پیام\n"
        "`/clear [عدد]` — پاکسازی چت\n"
        "\n━━━━━━━━━━━━━━━━\n"
        "🏷 **تگ کردن:**\n"
        "`/tag` — تگ همه اعضا\n"
        "`/tag100` — تگ ۱۰۰ نفر\n"
        "`/tagadmin` — تگ ادمین‌ها\n"
        "\n━━━━━━━━━━━━━━━━\n"
        "👋 **خوشامدگویی:**\n"
        "`/setwelcome [متن]` — تنظیم متن\n"
        "یا روی عکس/گیف ریپلای بزن و بنویس `/setwelcome`\n"
        "`/clearwelcome` — پاک کردن خوشامد\n"
        "\n━━━━━━━━━━━━━━━━\n"
        "💾 **ذخیره سازی:**\n"
        "`/save` — سیو پیام \\(روی پیام ریپلای\\)\n"
        "`/saved` — لیست پیام‌های سیو شده\n"
        "`/delsaved [شماره]` — حذف پیام سیو شده\n"
        "\n━━━━━━━━━━━━━━━━\n"
        "⚙️ **تنظیمات:**\n"
        "`/rules` — نمایش قوانین\n"
        "`/setrules [متن]` — تنظیم قوانین\n"
        "`/addfilter [کلمه] [پاسخ]` — فیلتر\n"
        "`/delfilter [کلمه]` — حذف فیلتر\n"
        "`/filters` — لیست فیلترها\n"
        "`/note [نام] [متن]` — ذخیره نکته\n"
        "`/getnote [نام]` — دریافت نکته\n"
        "\n━━━━━━━━━━━━━━━━\n"
        "🎲 **سرگرمی:**\n"
        "`/roll` — تاس\n"
        "`/time` — ساعت\n"
        "`/poll [سوال]` — نظرسنجی\n"
        "`/ping` — وضعیت ربات\n"
        "`/stats` — آمار گروه\n"
        "`/info` — اطلاعات گروه\n"
        "`/id` — آیدی عددی\n"
        "`/adminlist` — لیست ادمین‌ها\n"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

# ═══════════════════════════════════════════
#                  پنل
# ═══════════════════════════════════════════
def cmd_panel(message):
    if not is_admin(message.from_user.id, message.chat.id):
        # کاربر عادی — منوی محدود
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("📖 راهنما", callback_data="panel_help"),
            types.InlineKeyboardButton("📊 آمار گروه", callback_data="panel_stats"),
            types.InlineKeyboardButton("📋 قوانین", callback_data="panel_rules"),
            types.InlineKeyboardButton("⏰ ساعت", callback_data="panel_time"),
        )
        bot.reply_to(message, "📱 **منوی ربات:**", parse_mode="Markdown", reply_markup=markup)
        return

    # ادمین — پنل کامل
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🏷 تگ همه", callback_data="panel_tag_all"),
        types.InlineKeyboardButton("👑 تگ ادمین‌ها", callback_data="panel_tag_admins"),
        types.InlineKeyboardButton("🚫 بن کردن", callback_data="panel_ban_info"),
        types.InlineKeyboardButton("✅ رفع بن", callback_data="panel_unban_info"),
        types.InlineKeyboardButton("👤 ارتقا ادمین", callback_data="panel_promote_info"),
        types.InlineKeyboardButton("👤 حذف ادمین", callback_data="panel_demote_info"),
        types.InlineKeyboardButton("🗑 پاکسازی ۵۰", callback_data="panel_clear_50"),
        types.InlineKeyboardButton("📊 آمار", callback_data="panel_stats"),
        types.InlineKeyboardButton("📋 قوانین", callback_data="panel_rules"),
        types.InlineKeyboardButton("👋 خوشامد", callback_data="panel_welcome_info"),
        types.InlineKeyboardButton("📖 راهنما", callback_data="panel_help"),
        types.InlineKeyboardButton("❌ بستن", callback_data="panel_close"),
    )

    name = message.from_user.first_name or "ادمین"
    text = (
        f"⚙️ **پنل مدیریت**\n"
        f"👤 ادمین: **{name}**\n"
        f"📅 {datetime.now().strftime('%Y/%m/%d %H:%M')}\n\n"
        "یک گزینه انتخاب کن:"
    )
    bot.reply_to(message, text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("panel_"))
def panel_callback(call):
    cid = call.message.chat.id
    uid = call.from_user.id
    action = call.data

    if action == "panel_close":
        bot.delete_message(cid, call.message.message_id)
        return

    elif action == "panel_help":
        bot.answer_callback_query(call.id, "برو /help بنویس!", show_alert=False)

    elif action == "panel_stats":
        members = get_members(cid)
        try:
            count = bot.get_chat_member_count(cid)
        except:
            count = "؟"
        text = (
            f"📊 **آمار گروه**\n\n"
            f"👥 اعضا: `{count}`\n"
            f"🗄 ذخیره‌شده: `{len(members)}`\n"
            f"💾 پیام‌های سیو: `{len(data['saved_messages'])}`\n"
        )
        bot.answer_callback_query(call.id)
        bot.send_message(cid, text, parse_mode="Markdown")

    elif action == "panel_rules":
        rules = data["settings"].get(str(cid), {}).get("rules", "قوانینی تنظیم نشده\\!")
        bot.answer_callback_query(call.id)
        bot.send_message(cid, f"📋 **قوانین گروه:**\n\n{rules}", parse_mode="Markdown")

    elif action == "panel_time":
        now = datetime.now()
        bot.answer_callback_query(call.id, f"⏰ {now.strftime('%H:%M:%S')}", show_alert=True)

    elif action == "panel_tag_all":
        if not is_admin(uid, cid):
            bot.answer_callback_query(call.id, "❌ فقط ادمین‌ها!", show_alert=True)
            return
        bot.answer_callback_query(call.id, "⏳ در حال تگ کردن...")
        do_tag(cid, None)

    elif action == "panel_tag_admins":
        if not is_admin(uid, cid):
            bot.answer_callback_query(call.id, "❌ فقط ادمین‌ها!", show_alert=True)
            return
        bot.answer_callback_query(call.id)
        do_tag_admins(cid)

    elif action == "panel_clear_50":
        if not is_admin(uid, cid):
            bot.answer_callback_query(call.id, "❌ فقط ادمین‌ها!", show_alert=True)
            return
        bot.answer_callback_query(call.id, "🗑 در حال پاکسازی...")
        do_clear(cid, call.message.message_id, 50)

    elif action in ["panel_ban_info", "panel_unban_info", "panel_promote_info",
                    "panel_demote_info", "panel_welcome_info"]:
        if not is_admin(uid, cid):
            bot.answer_callback_query(call.id, "❌ فقط ادمین‌ها!", show_alert=True)
            return
        tips = {
            "panel_ban_info": "روی پیام کاربر ریپلای بزن و بنویس /ban",
            "panel_unban_info": "روی پیام کاربر ریپلای بزن و بنویس /unban",
            "panel_promote_info": "روی پیام کاربر ریپلای بزن و بنویس /promote",
            "panel_demote_info": "روی پیام کاربر ریپلای بزن و بنویس /demote",
            "panel_welcome_info": "عکس/گیف بفرست یا متن بنویس: /setwelcome [متن]",
        }
        bot.answer_callback_query(call.id, tips.get(action, ""), show_alert=True)

# ═══════════════════════════════════════════
#              تگ کردن
# ═══════════════════════════════════════════
def do_tag(chat_id, limit=None):
    members = get_members(chat_id)
    if not members:
        bot.send_message(chat_id, "⚠️ **هنوز اعضایی ذخیره نشده\\!**", parse_mode="Markdown")
        return

    member_list = list(members.items())
    if limit:
        member_list = member_list[:limit]

    header = "📢 **توجه همه اعضا\\!**\n"
    chunk = header
    count = 0

    for uid, info in member_list:
        username = info.get("username", "")
        fname = info.get("first_name") or "کاربر"
        mention = f"@{username} " if username else f"[{fname}](tg://user?id={uid}) "

        if len(chunk) + len(mention) > 3500:
            bot.send_message(chat_id, chunk, parse_mode="Markdown")
            time.sleep(0.3)
            chunk = mention
        else:
            chunk += mention
        count += 1

    if chunk.strip():
        bot.send_message(chat_id, chunk, parse_mode="Markdown")

    bot.send_message(chat_id, f"✅ **{count} نفر تگ شدند\\!**", parse_mode="Markdown")

def do_tag_admins(chat_id):
    try:
        admins = bot.get_chat_administrators(chat_id)
        msg = "👑 **ادمین‌های گروه:**\n"
        for a in admins:
            if a.user.is_bot:
                continue
            msg += f"• {get_mention(a.user)}\n"
        bot.send_message(chat_id, msg, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(chat_id, f"❌ خطا: `{e}`", parse_mode="Markdown")

def cmd_tag(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return err_not_admin(message)
    do_tag(message.chat.id)

def cmd_tag100(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return err_not_admin(message)
    do_tag(message.chat.id, 100)

def cmd_tagadmin(message):
    do_tag_admins(message.chat.id)

# ═══════════════════════════════════════════
#              مدیریت کاربران
# ═══════════════════════════════════════════
def get_target(message):
    """گرفتن کاربر هدف از ریپلای یا یوزرنیم"""
    if message.reply_to_message:
        return message.reply_to_message.from_user
    parts = message.text.split()
    if len(parts) > 1:
        username = parts[1].replace("@", "")
        try:
            u = bot.get_chat_member(message.chat.id, f"@{username}")
            return u.user
        except:
            pass
    return None

def get_reason(message):
    parts = message.text.split(None, 2)
    return parts[2] if len(parts) > 2 else (parts[1] if len(parts) > 1 and not parts[1].startswith("@") else "دلیلی ذکر نشده")

# ─── BAN ───
def cmd_ban(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return err_not_admin(message)
    target = get_target(message)
    if not target:
        return err_reply_needed(message)
    if is_admin(target.id, message.chat.id):
        bot.reply_to(message, "❌ **نمی‌توان ادمین را بن کرد\\!**", parse_mode="Markdown")
        return
    reason = get_reason(message)
    try:
        bot.ban_chat_member(message.chat.id, target.id)
        cid = str(message.chat.id)
        if cid not in data["banned_users"]:
            data["banned_users"][cid] = {}
        data["banned_users"][cid][str(target.id)] = {
            "name": target.first_name,
            "reason": reason,
            "by": message.from_user.first_name,
            "date": datetime.now().strftime("%Y/%m/%d %H:%M"),
        }
        save_data()
        bot.reply_to(
            message,
            f"🚫 **{get_mention(target)} بن شد\\!**\n"
            f"📝 دلیل: {reason}\n"
            f"👮 توسط: {get_mention(message.from_user)}",
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: `{e}`", parse_mode="Markdown")

# ─── UNBAN ───
def cmd_unban(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return err_not_admin(message)
    target = get_target(message)
    if not target:
        return err_reply_needed(message)
    try:
        bot.unban_chat_member(message.chat.id, target.id)
        cid = str(message.chat.id)
        if cid in data["banned_users"] and str(target.id) in data["banned_users"][cid]:
            del data["banned_users"][cid][str(target.id)]
            save_data()
        bot.reply_to(
            message,
            f"✅ **بن {get_mention(target)} برداشته شد\\!**\n"
            f"👮 توسط: {get_mention(message.from_user)}",
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: `{e}`", parse_mode="Markdown")

# ─── KICK ───
def cmd_kick(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return err_not_admin(message)
    target = get_target(message)
    if not target:
        return err_reply_needed(message)
    if is_admin(target.id, message.chat.id):
        bot.reply_to(message, "❌ **نمی‌توان ادمین را اخراج کرد\\!**", parse_mode="Markdown")
        return
    try:
        bot.ban_chat_member(message.chat.id, target.id)
        time.sleep(0.5)
        bot.unban_chat_member(message.chat.id, target.id)
        bot.reply_to(
            message,
            f"👢 **{get_mention(target)} اخراج شد\\!**\n"
            f"👮 توسط: {get_mention(message.from_user)}",
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: `{e}`", parse_mode="Markdown")

# ─── MUTE / UNMUTE ───
def cmd_mute(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return err_not_admin(message)
    target = get_target(message)
    if not target:
        return err_reply_needed(message)
    try:
        perms = types.ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_other_messages=False,
        )
        bot.restrict_chat_member(message.chat.id, target.id, perms)
        bot.reply_to(
            message,
            f"🔇 **{get_mention(target)} بی\\-صدا شد\\!**\n"
            f"برای رفع بی\\-صدا: `/unmute`\n"
            f"👮 توسط: {get_mention(message.from_user)}",
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: `{e}`", parse_mode="Markdown")

def cmd_unmute(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return err_not_admin(message)
    target = get_target(message)
    if not target:
        return err_reply_needed(message)
    try:
        perms = types.ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
        )
        bot.restrict_chat_member(message.chat.id, target.id, perms)
        bot.reply_to(
            message,
            f"🔊 **بی\\-صدایی {get_mention(target)} برداشته شد\\!**",
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: `{e}`", parse_mode="Markdown")

# ─── WARN ───
def cmd_warn(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return err_not_admin(message)
    target = get_target(message)
    if not target:
        return err_reply_needed(message)
    
    cid = str(message.chat.id)
    uid = str(target.id)
    reason = get_reason(message)

    if cid not in data["warned_users"]:
        data["warned_users"][cid] = {}
    if uid not in data["warned_users"][cid]:
        data["warned_users"][cid][uid] = {"count": 0, "reasons": []}

    data["warned_users"][cid][uid]["count"] += 1
    data["warned_users"][cid][uid]["reasons"].append(reason)
    warn_count = data["warned_users"][cid][uid]["count"]
    save_data()

    if warn_count >= 3:
        try:
            bot.ban_chat_member(message.chat.id, target.id)
            data["warned_users"][cid][uid]["count"] = 0
            save_data()
            bot.reply_to(
                message,
                f"🚫 **{get_mention(target)} بعد از ۳ اخطار بن شد\\!**",
                parse_mode="Markdown"
            )
            return
        except:
            pass

    bot.reply_to(
        message,
        f"⚠️ **اخطار به {get_mention(target)}\\!**\n"
        f"📝 دلیل: {reason}\n"
        f"🔢 اخطارها: `{warn_count}/3`\n"
        f"👮 توسط: {get_mention(message.from_user)}",
        parse_mode="Markdown"
    )

# ─── PROMOTE ───
def cmd_promote(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return err_not_admin(message)
    if not is_creator(message.from_user.id, message.chat.id):
        bot.reply_to(message, "❌ **فقط سازنده گروه می‌تواند ادمین اضافه کند\\!**", parse_mode="Markdown")
        return
    target = get_target(message)
    if not target:
        return err_reply_needed(message)
    try:
        bot.promote_chat_member(
            message.chat.id, target.id,
            can_delete_messages=True,
            can_restrict_members=True,
            can_invite_users=True,
            can_pin_messages=True,
            can_manage_chat=True,
        )
        bot.reply_to(
            message,
            f"👑 **{get_mention(target)} به ادمین ارتقا یافت\\!**\n"
            f"👮 توسط: {get_mention(message.from_user)}",
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: `{e}`", parse_mode="Markdown")

# ─── DEMOTE ───
def cmd_demote(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return err_not_admin(message)
    if not is_creator(message.from_user.id, message.chat.id):
        bot.reply_to(message, "❌ **فقط سازنده گروه می‌تواند ادمین را حذف کند\\!**", parse_mode="Markdown")
        return
    target = get_target(message)
    if not target:
        return err_reply_needed(message)
    try:
        bot.promote_chat_member(
            message.chat.id, target.id,
            can_delete_messages=False,
            can_restrict_members=False,
            can_invite_users=False,
            can_pin_messages=False,
            can_manage_chat=False,
        )
        bot.reply_to(
            message,
            f"📉 **{get_mention(target)} از ادمینی حذف شد\\!**\n"
            f"👮 توسط: {get_mention(message.from_user)}",
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: `{e}`", parse_mode="Markdown")

# ─── DELETE MESSAGE ───
def cmd_del(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return err_not_admin(message)
    if not message.reply_to_message:
        return err_reply_needed(message)
    try:
        bot.delete_message(message.chat.id, message.reply_to_message.message_id)
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: `{e}`", parse_mode="Markdown")

# ─── CLEAR ───
def do_clear(chat_id, from_msg_id, count):
    deleted = 0
    for i in range(count + 2):
        try:
            bot.delete_message(chat_id, from_msg_id - i)
            deleted += 1
            time.sleep(0.04)
        except:
            pass
    msg = bot.send_message(chat_id, f"✅ **{deleted} پیام پاک شد\\!**", parse_mode="Markdown")
    time.sleep(3)
    try:
        bot.delete_message(chat_id, msg.message_id)
    except:
        pass

def cmd_clear(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return err_not_admin(message)
    parts = message.text.split()
    count = 50
    if len(parts) > 1 and parts[1].isdigit():
        count = min(int(parts[1]), 200)
    bot.reply_to(message, f"🗑 **در حال پاکسازی {count} پیام\\.\\.\\.**", parse_mode="Markdown")
    do_clear(message.chat.id, message.message_id, count)

# ═══════════════════════════════════════════
#            خوشامدگویی سفارشی
# ═══════════════════════════════════════════
@bot.message_handler(content_types=["photo", "animation", "document"])
def handle_media(message):
    if message.from_user and not message.from_user.is_bot:
        update_member(message.chat.id, message.from_user)

    text = ""
    if message.photo:
        text = message.caption or ""
    elif message.animation:
        text = message.caption or ""

    if "/setwelcome" in text:
        if not is_admin(message.from_user.id, message.chat.id):
            return err_not_admin(message)
        cid = str(message.chat.id)
        if message.photo:
            data["welcome_media"][cid] = {"type": "photo", "file_id": message.photo[-1].file_id}
        elif message.animation:
            data["welcome_media"][cid] = {"type": "animation", "file_id": message.animation.file_id}
        
        custom_text = text.replace("/setwelcome", "").strip()
        if custom_text:
            data["welcome_text"][cid] = custom_text
        save_data()
        bot.reply_to(message, "✅ **خوشامدگویی سفارشی تنظیم شد\\!**\nاعضای جدید این رسانه رو خواهند دید\\.", parse_mode="Markdown")

def cmd_setwelcome(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return err_not_admin(message)
    cid = str(message.chat.id)
    parts = message.text.split(None, 1)
    if len(parts) > 1:
        data["welcome_text"][cid] = parts[1]
        save_data()
        bot.reply_to(message, "✅ **متن خوشامدگویی تنظیم شد\\!**\n\nمتغیرها:\n`{name}` — نام کاربر\n`{group}` — نام گروه", parse_mode="Markdown")
    else:
        bot.reply_to(
            message,
            "📝 **روش تنظیم خوشامدگویی:**\n\n"
            "1️⃣ متن: `/setwelcome سلام {name} به گروه خوش اومدی`\n"
            "2️⃣ عکس/گیف: عکس/گیف بفرست، کپشنش `/setwelcome [متن]` بنویس",
            parse_mode="Markdown"
        )

def cmd_clearwelcome(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return err_not_admin(message)
    cid = str(message.chat.id)
    data["welcome_media"].pop(cid, None)
    data["welcome_text"].pop(cid, None)
    save_data()
    bot.reply_to(message, "🗑 **خوشامدگویی سفارشی پاک شد\\. از پیش\\-فرض استفاده می\\-شود\\.**", parse_mode="Markdown")

# ═══════════════════════════════════════════
#              سیو پیام
# ═══════════════════════════════════════════
def cmd_save(message):
    if not message.reply_to_message:
        return err_reply_needed(message)
    replied = message.reply_to_message
    saved = {
        "id": len(data["saved_messages"]) + 1,
        "text": replied.text or replied.caption or "[بدون متن]",
        "from": replied.from_user.first_name if replied.from_user else "ناشناس",
        "from_id": replied.from_user.id if replied.from_user else 0,
        "saver": message.from_user.first_name,
        "date": datetime.now().strftime("%Y/%m/%d %H:%M"),
        "chat_id": str(message.chat.id),
    }
    data["saved_messages"].append(saved)
    save_data()
    bot.reply_to(
        message,
        f"💾 **پیام سیو شد\\!**\n🔢 شماره: `{saved['id']}`",
        parse_mode="Markdown"
    )

def cmd_saved(message):
    chat_msgs = [m for m in data["saved_messages"] if m.get("chat_id") == str(message.chat.id)]
    if not chat_msgs:
        bot.reply_to(message, "📂 **هنوز پیامی سیو نشده\\!**", parse_mode="Markdown")
        return
    text = "📂 **پیام‌های سیو شده:**\n\n"
    for m in chat_msgs[-15:]:
        preview = m["text"][:60] + "\\.\\.\\." if len(m["text"]) > 60 else m["text"]
        text += f"🔢 `#{m['id']}` | 👤 {m['from']} | 📅 {m['date']}\n💬 {preview}\n{'─'*20}\n"
    bot.reply_to(message, text, parse_mode="Markdown")

def cmd_delsaved(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return err_not_admin(message)
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        bot.reply_to(message, "⚠️ **مثال:** `/delsaved 5`", parse_mode="Markdown")
        return
    target_id = int(parts[1])
    before = len(data["saved_messages"])
    data["saved_messages"] = [m for m in data["saved_messages"] if m["id"] != target_id]
    save_data()
    if len(data["saved_messages"]) < before:
        bot.reply_to(message, f"✅ **پیام شماره {target_id} حذف شد\\!**", parse_mode="Markdown")
    else:
        bot.reply_to(message, f"⚠️ **پیامی با شماره {target_id} پیدا نشد\\!**", parse_mode="Markdown")

# ═══════════════════════════════════════════
#           قوانین و فیلترها
# ═══════════════════════════════════════════
def cmd_rules(message):
    cid = str(message.chat.id)
    rules = data["settings"].get(cid, {}).get("rules", "قوانینی تنظیم نشده\\! ادمین با `/setrules` تنظیم کند\\.")
    bot.reply_to(message, f"📋 **قوانین گروه:**\n\n{rules}", parse_mode="Markdown")

def cmd_setrules(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return err_not_admin(message)
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ **مثال:** `/setrules قانون ۱: احترام همه`", parse_mode="Markdown")
        return
    cid = str(message.chat.id)
    if cid not in data["settings"]:
        data["settings"][cid] = {}
    data["settings"][cid]["rules"] = parts[1]
    save_data()
    bot.reply_to(message, "✅ **قوانین تنظیم شد\\!**", parse_mode="Markdown")

def cmd_addfilter(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return err_not_admin(message)
    parts = message.text.split(None, 2)
    if len(parts) < 3:
        bot.reply_to(message, "⚠️ **مثال:** `/addfilter سلام سلام عزیزم\\!`", parse_mode="Markdown")
        return
    cid = str(message.chat.id)
    if cid not in data["filters"]:
        data["filters"][cid] = {}
    data["filters"][cid][parts[1]] = parts[2]
    save_data()
    bot.reply_to(message, f"✅ **فیلتر «{parts[1]}» اضافه شد\\!**", parse_mode="Markdown")

def cmd_delfilter(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return err_not_admin(message)
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ **مثال:** `/delfilter سلام`", parse_mode="Markdown")
        return
    cid = str(message.chat.id)
    if cid in data["filters"] and parts[1] in data["filters"][cid]:
        del data["filters"][cid][parts[1]]
        save_data()
        bot.reply_to(message, f"✅ **فیلتر «{parts[1]}» حذف شد\\!**", parse_mode="Markdown")
    else:
        bot.reply_to(message, "⚠️ **این فیلتر وجود ندارد\\!**", parse_mode="Markdown")

def cmd_filters(message):
    cid = str(message.chat.id)
    filters = data["filters"].get(cid, {})
    if not filters:
        bot.reply_to(message, "📝 **هیچ فیلتری تنظیم نشده\\!**", parse_mode="Markdown")
        return
    text = "📝 **فیلترهای فعال:**\n\n"
    for k, v in filters.items():
        preview = v[:40] + "\\.\\.\\." if len(v) > 40 else v
        text += f"• `{k}` ← {preview}\n"
    bot.reply_to(message, text, parse_mode="Markdown")

# ═══════════════════════════════════════════
#                  نکته‌ها
# ═══════════════════════════════════════════
def cmd_note(message):
    if not is_admin(message.from_user.id, message.chat.id):
        return err_not_admin(message)
    parts = message.text.split(None, 2)
    if len(parts) < 3:
        bot.reply_to(message, "⚠️ **مثال:** `/note لینک https://t.me/...`", parse_mode="Markdown")
        return
    cid = str(message.chat.id)
    if cid not in data["notes"]:
        data["notes"][cid] = {}
    data["notes"][cid][parts[1]] = parts[2]
    save_data()
    bot.reply_to(message, f"📌 **نکته «{parts[1]}» ذخیره شد\\!**", parse_mode="Markdown")

def cmd_getnote(message):
    parts = message.text.split()
    if len(parts) < 2:
        cid = str(message.chat.id)
        notes = data["notes"].get(cid, {})
        if not notes:
            bot.reply_to(message, "📌 **نکته‌ای ذخیره نشده\\!**", parse_mode="Markdown")
            return
        text = "📌 **نکته‌های موجود:**\n\n"
        for k in notes:
            text += f"• `{k}`\n"
        text += "\nبرای دریافت: `/getnote نام`"
        bot.reply_to(message, text, parse_mode="Markdown")
        return
    cid = str(message.chat.id)
    note = data["notes"].get(cid, {}).get(parts[1])
    if note:
        bot.reply_to(message, f"📌 **{parts[1]}:**\n\n{note}", parse_mode="Markdown")
    else:
        bot.reply_to(message, f"⚠️ **نکته «{parts[1]}» پیدا نشد\\!**", parse_mode="Markdown")

# ═══════════════════════════════════════════
#              ابزارهای عمومی
# ═══════════════════════════════════════════
def cmd_stats(message):
    members = get_members(message.chat.id)
    try:
        count = bot.get_chat_member_count(message.chat.id)
    except:
        count = "؟"
    try:
        admins = bot.get_chat_administrators(message.chat.id)
        admin_count = len([a for a in admins if not a.user.is_bot])
    except:
        admin_count = "؟"
    saved = len([m for m in data["saved_messages"] if m.get("chat_id") == str(message.chat.id)])
    cid = str(message.chat.id)
    banned = len(data["banned_users"].get(cid, {}))
    bot.reply_to(
        message,
        f"📊 **آمار گروه:**\n\n"
        f"👥 کل اعضا: `{count}`\n"
        f"👑 ادمین‌ها: `{admin_count}`\n"
        f"🗄 ذخیره‌شده: `{len(members)}`\n"
        f"💾 سیو شده: `{saved}`\n"
        f"🚫 بن شده: `{banned}`\n"
        f"📅 زمان: `{datetime.now().strftime('%Y/%m/%d %H:%M')}`",
        parse_mode="Markdown"
    )

def cmd_info(message):
    chat = message.chat
    text = (
        f"ℹ️ **اطلاعات گروه:**\n\n"
        f"📛 نام: `{chat.title or 'نامشخص'}`\n"
        f"🆔 آیدی: `{chat.id}`\n"
        f"📝 نوع: `{chat.type}`\n"
    )
    if chat.username:
        text += f"🔗 لینک: @{chat.username}\n"
    if chat.description:
        desc = chat.description[:150]
        text += f"📋 توضیحات: {desc}\n"
    bot.reply_to(message, text, parse_mode="Markdown")

def cmd_ping(message):
    start = time.time()
    msg = bot.reply_to(message, "🏓 پینگ\\.\\.\\.", parse_mode="Markdown")
    ms = round((time.time() - start) * 1000)
    bot.edit_message_text(
        f"🏓 **پانگ\\!**\n⚡ سرعت: `{ms}ms`\n🤖 ربات فعاله\\!",
        message.chat.id, msg.message_id, parse_mode="Markdown"
    )

def cmd_roll(message):
    n = random.randint(1, 6)
    faces = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
    bot.reply_to(
        message,
        f"🎲 **تاس انداختی\\!**\n{faces[n-1]} **عدد {n} آمد\\!**",
        parse_mode="Markdown"
    )

def cmd_time(message):
    now = datetime.now()
    bot.reply_to(
        message,
        f"🕐 **زمان فعلی:**\n📅 `{now.strftime('%Y/%m/%d')}`\n⏰ `{now.strftime('%H:%M:%S')}`",
        parse_mode="Markdown"
    )

def cmd_poll(message):
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ **مثال:** `/poll بهترین زبان برنامه‌نویسی چیه؟`", parse_mode="Markdown")
        return
    try:
        bot.send_poll(
            message.chat.id,
            question=parts[1][:255],
            options=["👍 بله", "👎 خیر", "🤷 نظری ندارم", "🔄 شاید"],
            is_anonymous=False
        )
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: `{e}`", parse_mode="Markdown")

def cmd_id(message):
    user = message.from_user
    text = f"🆔 **آیدی عددی شما:**\n`{user.id}`\n\n📝 **آیدی گروه:**\n`{message.chat.id}`"
    if message.reply_to_message:
        t = message.reply_to_message.from_user
        text += f"\n\n👤 **آیدی {t.first_name}:**\n`{t.id}`"
    bot.reply_to(message, text, parse_mode="Markdown")

def cmd_adminlist(message):
    try:
        admins = bot.get_chat_administrators(message.chat.id)
        text = "👑 **لیست ادمین‌ها:**\n\n"
        for a in admins:
            if a.user.is_bot:
                continue
            role = "👑 سازنده" if a.status == "creator" else "⭐ ادمین"
            text += f"{role} {get_mention(a.user)}\n"
        bot.reply_to(message, text, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: `{e}`", parse_mode="Markdown")

# ═══════════════════════════════════════════
#                 اجرا
# ═══════════════════════════════════════════
def run():
    print("╔══════════════════════════════╗")
    print("║  ربات فارسی PRO آماده است!  ║")
    print("╚══════════════════════════════╝")
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=30)
        except Exception as e:
            print(f"❌ خطا: {e} — اتصال مجدد در ۵ ثانیه...")
            time.sleep(5)

if __name__ == "__main__":
    run()
