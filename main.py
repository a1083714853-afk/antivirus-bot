import telebot
import requests
import hashlib
import time
from flask import Flask
import threading

# 1. Sozlamalar
BOT_TOKEN = "8451988332:AAEzIPiJx2VrFMwNJtbsl8haP5iSlGEJJX4"
VT_API_KEY = "771e86962f15f9a2bc4fd49ea82613d03c3f8f4f30b2d74f209d0562bd87ae53"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

# 2. Render o'chib qolmasligi uchun "yolg'ondakam" veb-sahifa
@app.route('/')
def home():
    return "Bot muvaffaqiyatli ishlayapti!"

def run_server():
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# Veb-serverni fonda alohida oqimda yurgizish
threading.Thread(target=run_server).start()

# 3. Botingizning buyruqlari va vazifalari
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Salom, man antivirus botman. Manga fayl yuboring virusni aniqlab beraman")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Fayl xeshini hisoblash
        file_hash = hashlib.sha256(downloaded_file).hexdigest()
        
        # VirusTotal API so'rovi
        url = f"https://www.virustotal.com/api/v3/files/{file_hash}"
        headers = {"x-apikey": VT_API_KEY}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            stats = result['data']['attributes']['last_analysis_stats']
            malicious = stats['malicious']
            undetected = stats['undetected']
            
            if malicious > 0:
                bot.reply_to(message, f"🚨 Diqqat! Faylda virus topildi!\nZararli: {malicious}\nToza: {undetected}")
            else:
                bot.reply_to(message, f"✅ Fayl toza.\nZararli: {malicious}\nToza: {undetected}")
        elif response.status_code == 404:
            bot.reply_to(message, "🔍 Bu fayl VirusTotal bazasida topilmadi. Ammo xavfsiz bo'lishi mumkin.")
        else:
            bot.reply_to(message, "❌ Tekshirishda xatolik yuz berdi.")
            
    except Exception as e:
        bot.reply_to(message, f"Xato yuz berdi: {str(e)}")

# Botni uzluksiz ishga tushirish (Doimo eng oxirida turadi)
if __name__ == "__main__":
    bot.infinity_polling()
