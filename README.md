import os
import logging
import requests
import instaloader
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from urllib.parse import urlparse
import tempfile
import re

# Log konfiguratsiyasi
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(name)

BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
loader = instaloader.Instaloader()

class AdvancedInstagramDownloader:
    @staticmethod
    def validate_instagram_url(url):
        """Instagram URL ni tekshirish"""
        instagram_pattern = r'https?://(www\.)?instagram\.com/(p|reel|stories)/([a-zA-Z0-9_-]+)'
        return re.match(instagram_pattern, url)

    @staticmethod
    def extract_shortcode(url):
        """URL dan shortcode ni ajratib olish"""
        match = AdvancedInstagramDownloader.validate_instagram_url(url)
        if match:
            return match.group(3)
        return None

    @staticmethod
    def download_instagram_media(url):
        """Instagram media (video yoki rasmlar) yuklab olish"""
        try:
            shortcode = AdvancedInstagramDownloader.extract_shortcode(url)
            if not shortcode:
                return None, "Noto'g'ri Instagram linki"
            
            post = instaloader.Post.from_shortcode(loader.context, shortcode)
            
            # Video holati
            if post.is_video:
                return AdvancedInstagramDownloader._download_video(post)
            # Rasm galereya holati
            elif post.mediacount > 1:
                return AdvancedInstagramDownloader._download_carousel(post)
            # Bitta rasm holati
            else:
                return AdvancedInstagramDownloader._download_single_photo(post)
                
        except Exception as e:
            logger.error(f"Xatolik: {str(e)}")
            return None, f"Xatolik yuz berdi: {str(e)}"

    @staticmethod
    def _download_video(post):
        """Videoni yuklab olish"""
        try:
            if not post.video_url:
                return None, "Video URL topilmadi"
            
            response = requests.get(post.video_url, stream=True)
            if response.status_code == 200:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        temp_file.write(chunk)
                    return temp_file.name, "video"
            return None, "Videoni yuklab bo'lmadi"
            
        except Exception as e:
            return None, f"Video yuklash xatosi: {str(e)}"

    @staticmethod
    def _download_single_photo(post):
        """Bitta rasmni yuklab olish"""
        try:
            if not post.url:
                return None, "Rasm URL topilmadi"
            
            response = requests.get(post.url, stream=True)
            if response.status_code == 200:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        temp_file.write(chunk)
                    return temp_file.name, "photo"
            return None, "Rasmni yuklab bo'lmadi"
            
        except Exception as e:
            return None, f"Rasm yuklash xatosi: {str(e)}"

    @staticmethod
    def _download_carousel(post):
        """Galeriyani yuklab olish (faqat birinchi rasm)"""
        try:
            # Faqat birinchi rasmni olish
            for index, node in enumerate(post.get_sidecar_nodes()):
                if index == 0:  # Faqat birinchi element
                    if node.is_video:
                        response = requests.get(node.video_url, stream=True)

suffix = '.mp4'
                        media_type = "video"
                    else:
                        response = requests.get(node.display_url, stream=True)
                        suffix = '.jpg'
                        media_type = "photo"
                    
                    if response.status_code == 200:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                            for chunk in response.iter_content(chunk_size=8192):
                                temp_file.write(chunk)
                            return temp_file.name, media_type
                    break
            return None, "Galereyani yuklab bo'lmadi"
            
        except Exception as e:
            return None, f"Galereya yuklash xatosi: {str(e)}"

# Bot funksiyalari
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = f"""
    👋 Salom {user.first_name}!

    🤖 Instagram Media Downloader Botiga xush kelibsiz!

    📥 Menga Instagram linkini yuboring:
    • Video postlar
    • Rasm postlar  
    • Galereya postlar
    • Reel videolar

    📌 Misol linklar:
    https://www.instagram.com/p/ABC123/
    https://www.instagram.com/reel/DEF456/

    ⚠️ Eslatma: Faqat ochiq profildagi kontentni yuklay olaman.
    """
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text.strip()
    
    if AdvancedInstagramDownloader.validate_instagram_url(message_text):
        await update.message.reply_text("🔄 Media yuklanmoqda... Iltimos kuting!")
        
        file_path, media_type = AdvancedInstagramDownloader.download_instagram_media(message_text)
        
        if isinstance(file_path, str) and os.path.exists(file_path):
            try:
                file_size = os.path.getsize(file_path)
                if file_size > 50 * 1024 * 1024:
                    await update.message.reply_text("❌ Fayl hajmi 50MB dan katta")
                    os.unlink(file_path)
                    return
                
                with open(file_path, 'rb') as media_file:
                    if media_type == "video":
                        await update.message.reply_video(
                            video=InputFile(media_file, filename="instagram_video.mp4"),
                            caption="✅ Instagram videosi yuklandi!\n\n@InstagramDownloaderBot"
                        )
                    else:
                        await update.message.reply_photo(
                            photo=InputFile(media_file, filename="instagram_photo.jpg"),
                            caption="✅ Instagram rasmi yuklandi!\n\n@InstagramDownloaderBot"
                        )
                
                os.unlink(file_path)
                
            except Exception as e:
                logger.error(f"Media yuborishda xatolik: {str(e)}")
                await update.message.reply_text("❌ Media yuborishda xatolik")
                if os.path.exists(file_path):
                    os.unlink(file_path)
        else:
            await update.message.reply_text(f"❌ {media_type}")
    else:
        await update.message.reply_text("❌ Iltimos, to'g'ri Instagram linkini yuboring!")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Bot ishga tushdi...")
    application.run_polling()

if name == 'main':
    main()
