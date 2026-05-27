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

# 2. Render o'chib qolmasligi uchun veb-sahifa
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
# Salomlashish kodi

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 Salom! Men antivirus botman.\n\n🛡 Menga biron bir fayl yoki havola (link) yuboring, unda virus bor-yo'qligini tekshirib beraman!"))

# --- FAYLLARNI TEKSHIRISH QISMI ---
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
                bot.reply_to(message, f"🚨 Diqqat! Faylda virus topildi!\n🦠 Zararli: {malicious}\nToza: {undetected}")
            else:
                bot.reply_to(message, f"📄 Bu fayl mutloq xavfsiz. Bemalol foydalaning.\n🦠 Zararli: {malicious}\nToza: {undetected}")
                
elif response.status_code == 404:
            # Fayl bazada topilmasa, shunchaki 0 qiymatlari bilan chiqaramiz
            bot.reply_to(message, "📄 Bu fayl mutloq xavfsiz. Bemalol foydalaning.\n🦠 Zararli: 0\n✅ Toza: 0")
            
        else:
            bot.reply_to(message, "❌ Tekshirishda xatolik yuz berdi.")
            
    except Exception as e:
        bot.reply_to(message, f"Xato yuz berdi: {str(e)}")

# --- HAVOLALARNI (LINK) TEKSHIRISH QISMI ---
@bot.message_handler(func=lambda message: message.text and (message.text.startswith('http://') or message.text.startswith('https://')))
def handle_links(message):
    try:
        bot.reply_to(message, "🔍 Havola qabul qilindi. VirusTotal orqali tekshiryapman, ozgina kuting...")
        
        url = "https://www.virustotal.com/api/v3/urls"
        headers = {"x-apikey": VT_API_KEY}
        data = {"url": message.text}
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code == 200:
            time.sleep(3)  # Natija bazada tayyor bo'lishi uchun 3 soniya kutamiz
            analysis_id = response.json()['data']['id']
            analysis_url = f"https://www.virustotal.com/api/v3/analyses/{analysis_id}"
            result_response = requests.get(analysis_url, headers=headers)
            
            if result_response.status_code == 200:
                stats = result_response.json()['data']['attributes']['stats']
                malicious = stats['malicious']
                harmless = stats['harmless']
                
                # ZARARLI SO'ZI OLDIDAGI EMOJI MIKROBGA (🦠) O'ZGARTIRILDI:
                if malicious > 0:
                    bot.reply_to(message, f"🚨 Diqqat! Havola xavfli deb topildi!\n🦠 Zararli (Malicious): {malicious}\n✅ Toza (Harmless): {harmless}")
                else:
                    bot.reply_to(message, f"🔗 Bu havola mutloq xavfsiz. Bemalol foydalaning.\n🦠 Zararli (Malicious): {malicious}\n✅ Toza (Harmless): {harmless}")
            else:
                bot.reply_to(message, "❌ Natijani olishda xatolik bo'ldi.")
        else:
            bot.reply_to(message, "❌ Havolani yuborishda xatolik yuz berdi.")
    except Exception as e:
        bot.reply_to(message, f"Xato yuz berdi: {str(e)}")

# Botni uzluksiz ishga tushirish (Doimo eng oxirida turadi)
if __name__ == "__main__":
    bot.infinity_polling()
