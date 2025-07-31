# My-Telegram-Bot
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters
from yt_dlp import YoutubeDL
import os
import re
import requests

BOT_TOKEN = "BOT_TOKENINGIZ"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎥 Menga YouTube yoki Instagram video ssilkani yuboring.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if "youtube.com" in url or "youtu.be" in url:
        await update.message.reply_text("📥 YouTube videoni yuklab olyapman...")
        try:
            ydl_opts = {
                'outtmpl': 'yt_video.%(ext)s',
                'format': 'mp4',
                'quiet': True,
            }
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            for file in os.listdir():
                if file.startswith("yt_video") and file.endswith(".mp4"):
                    await update.message.reply_video(video=open(file, 'rb'))
                    os.remove(file)
                    break
        except Exception as e:
            await update.message.reply_text(f"❌ Xatolik: {e}")

    elif "instagram.com" in url:
        await update.message.reply_text("📥 Instagram videoni yuklab olyapman...")
        try:
            api_url = f"https://ssstik.io/api/convert?url={url}&format=mp4"
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            resp = requests.get(api_url, headers=headers)
            download_url = re.search(r'https://[^"]+mp4', resp.text)
            if download_url:
                video = requests.get(download_url.group(0))
                with open("insta_video.mp4", "wb") as f:
                    f.write(video.content)
                await update.message.reply_video(video=open("insta_video.mp4", "rb"))
                os.remove("insta_video.mp4")
            else:
                await update.message.reply_text("❌ Yuklab bo‘lmadi. Link noto‘g‘ri yoki video ommaviymi?")
        except Exception as e:
            await update.message.reply_text(f"❌ Xatolik: {e}")

    else:
        await update.message.reply_text("🔗 Faqat YouTube yoki Instagram videosining linkini yuboring.")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()
