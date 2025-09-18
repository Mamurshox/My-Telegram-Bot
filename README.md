import telebot, os, subprocess
from telebot import types

BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
CHECK_CHANNEL = "@GodzillaDM_Bot"   # obuna tekshiradigan kanal/guruh username
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# 🔎 Obuna tekshirish
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHECK_CHANNEL, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# ▶ Start
@bot.message_handler(commands=['start'])
def start(msg):
    if not is_subscribed(msg.from_user.id):
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔔 Kanalga obuna bo‘lish",
                                          url=f"https://t.me/{CHECK_CHANNEL.replace('@','')}"))
        bot.reply_to(msg, "❗️Avval kanalga obuna bo‘ling!", reply_markup=kb)
        return
    bot.reply_to(msg, "✅ Xush kelibsiz!\n\n🎵 Qo‘shiq nomi yozing yoki Instagram link yuboring.")

# 🎵 YouTube MP3 qidirish
@bot.message_handler(func=lambda m: not m.text.startswith("http"))
def music(msg):
    if not is_subscribed(msg.from_user.id):
        return
    query = msg.text
    bot.reply_to(msg, "⏳ Qidiryapman...")
    outname = f"{msg.chat.id}.mp3"
    cmd = f'yt-dlp -x --audio-format mp3 -o "{outname}" "ytsearch1:{query}"'
    subprocess.call(cmd, shell=True)
    if os.path.exists(outname):
        with open(outname, 'rb') as audio:
            bot.send_audio(msg.chat.id, audio, title=query)
        os.remove(outname)
    else:
        bot.reply_to(msg, "❌ Topilmadi")

# 📸 Instagram video yuklash
@bot.message_handler(func=lambda m: m.text.startswith("http"))
def insta(msg):
    if not is_subscribed(msg.from_user.id):
        return
    link = msg.text
    bot.reply_to(msg, "⏳ Video yuklanmoqda...")
    outname = f"{msg.chat.id}.mp4"
    cmd = f'yt-dlp -f mp4 -o "{outname}" "{link}"'
    subprocess.call(cmd, shell=True)
    if os.path.exists(outname):
        with open(outname, 'rb') as video:
            bot.send_video(msg.chat.id, video)
        os.remove(outname)
    else:
        bot.reply_to(msg, "❌ Video yuklab bo‘lmadi")

print("Bot ishga tushdi...")
bot.infinity_polling()
