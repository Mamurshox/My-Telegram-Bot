import logging
import os
import re
from instaloader import Instaloader, Post
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Logging sozlamalari (xatolarni ko'rish uchun)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Instagram'dan video yuklash funksiyasi
def download_instagram_video(shortcode, download_dir="./downloads"):
    """
    Instagram post shortcode'ini olib, video bo'lsa yuklab oladi.
    :param shortcode: str, masalan 'C1234567890'
    :param download_dir: str, yuklash papkasi
    :return: str yoki None, video fayl yo'li
    """
    L = Instaloader(download_videos=True, compress_json=False)
    
    # Agar login kerak bo'lsa (faqat public postlar uchun login kerak emas):
    # L.login("sizning_instagram_username", "sizning_parol")
    # Eslatma: Parolni .env faylidan olish xavfsizroq, masalan: os.getenv('INSTA_PASSWORD')
    
    try:
        post = Post.from_shortcode(L.context, shortcode)
        if not post.is_video:
            logger.info("Bu post video emas!")
            return None
        
        # Papkani yaratish
        os.makedirs(download_dir, exist_ok=True)
        
        # Postni yuklash (faqat video)
        L.download_post(post, target=download_dir)
        
        # Yuklangan video faylni topish
        files = [f for f in os.listdir(download_dir) if f.endswith('.mp4')]
        if files:
            video_path = os.path.join(download_dir, max(files, key=os.path.getctime))
            logger.info(f"Video yuklandi: {video_path}")
            return video_path
        else:
            logger.info("Video fayl topilmadi!")
            return None
            
    except Exception as e:
        logger.error(f"Xato: {e}")
        return None

# /start buyrug'i uchun handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salom! Instagram video URL yuboring, men uni yuklab beraman.\n"
        "Masalan: https://www.instagram.com/p/SHORTCODE/"
    )

# Xabar (URL) kelganda ishlaydigan handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    # Instagram URL'dan shortcode chiqarish
    match = re.search(r'/p/([A-Za-z0-9_-]+)', url)
    if not match:
        await update.message.reply_text("Iltimos, to'g'ri Instagram post URL yuboring! Masalan: https://www.instagram.com/p/SHORTCODE/")
        return
    
    shortcode = match.group(1)
    await update.message.reply_text("Video yuklanmoqda... Iltimos, kuting.")
    
    # Video yuklash
    video_path = download_instagram_video(shortcode)
    if video_path:
        try:
            with open(video_path, 'rb') as video:
                await update.message.reply_video(video=video, caption="Instagram'dan yuklangan video!")
            # Faylni o'chirish (server joyini tejash uchun)
            os.remove(video_path)
            await update.message.reply_text("Video muvaffaqiyatli yuborildi!")
        except Exception as e:
            logger.error(f"Video yuborishda xato: {e}")
            await update.message.reply_text("Video yuborishda xato yuz berdi. Iltimos, qayta urinib ko'ring.")
    else:
        await update.message.reply_text("Video yuklab bo'lmadi. Post public ekanligini va video ekanligini tekshiring.")

# Xato handler'i
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    if update:
        await update.message.reply_text("Nimadir xato ketdi. Iltimos, qayta urinib ko'ring.")

# Asosiy funksiya
def main():
    # Telegram bot tokenini bu yerga qo'ying
    TOKEN = "SIZNING_BOT_TOKENINGIZ"  # BotFather'dan olingan token
    
    # Application yaratish
    application = Application.builder().token(TOKEN).build()
    
    # Handler'larni qo'shish
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    
    # Botni ishga tushirish
    logger.info("Bot ishga tushdi...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()