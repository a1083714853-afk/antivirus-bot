import telebot
import requests
import hashlib
import time

BOT_TOKEN = "8451988332:AAEzIPiJx2VrFMwNJtbsl8haP5iSlGEJJX4"
VT_API_KEY = "771e86962f15f9a2bc4fd49ea82613d03c3f8f4f30b2d74f209d0562bd87ae53"

bot = telebot.TeleBot(BOT_TOKEN)


def get_file_hash(file_bytes):
    return hashlib.sha256(file_bytes).hexdigest()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Salom, man antivirus botman. Manga fayl yuboring virusni aniqlab beraman")

@bot.message_handler(content_types=['document'])
def handle_file(message):
    msg = bot.reply_to(message, "⏳ Fayl tahlil qilinmoqda...")
    try:
        file_info = bot.get_file(message.document.file_id)
        file_bytes = bot.download_file(file_info.file_path)
        file_hash = get_file_hash(file_bytes)
        headers = {"x-apikey": VT_API_KEY}

        # 1. Oldin VirusTotal bazasidan qidiramiz (yuklamaymiz!)
        url_report = f"https://www.virustotal.com/api/v3/files/{file_hash}"
        response = requests.get(url_report, headers=headers)

        if response.status_code == 200:
            stats = response.json()['data']['attributes']['last_analysis_stats']
        else:
            # 2. Agar bazada bo'lmasa, yuklaymiz
            url_upload = "https://www.virustotal.com/api/v3/files"
            files = {"file": (message.document.file_name, file_bytes)}
            up_res = requests.post(url_upload, headers=headers, files=files).json()
            analysis_id = up_res['data']['id']
            time.sleep(15)
            res = requests.get(f"https://www.virustotal.com/api/v3/analyses/{analysis_id}", headers=headers).json()
            stats = res['data']['attributes']['stats']

        report = (f"📊 *Natija:*\n🔴 Virus: {stats.get('malicious', 0)}\n"
                  f"🟢 Xavfsiz: {stats.get('harmless', 0)}\n"
                  f"{'⚠️ DIQQAT! Virus bor!' if stats.get('malicious', 0) > 0 else '✅ Fayl toza!'}")

        bot.edit_message_text(report, message.chat.id, msg.message_id, parse_mode="Markdown")

    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik: {str(e)}", message.chat.id, msg.message_id)


if __name__ == "__main__":
    bot.remove_webhook()
    bot.infinity_polling()
