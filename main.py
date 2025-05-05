import os
import time
import threading
import requests
from flask import Flask
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.error import TelegramError

# Flask uygulaması başlatma
app = Flask(__name__)

# Telegram bot bilgilerinizi burada ayarlayın
TELEGRAM_TOKEN = '7770662830:AAF81ZmkPNNCxV2sUg-0jSVyEb64fTNkBn8'
CHAT_ID = '1476078120'
bot = Bot(token=TELEGRAM_TOKEN)

# Stok kontrolü yapan fonksiyon
def check_stock():
    url = "https://www.tesla.com/tr_TR/inventory/new/my?arrangeby=plh&zip=34025&range=0"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    
    while True:
        try:
            # Sayfayı al
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Sayfa içeriğinde fotoğraf var mı kontrol et
                image_element = soup.find('img')  # Burada img etiketini kontrol ediyoruz
                if image_element:
                    message = "Stokta araç var!"
                    bot.send_message(chat_id=CHAT_ID, text=message)
                    print("Stokta araç var, Telegram'a bildirim gönderildi.")
                else:
                    print("Stokta araç yok.")
            else:
                print("Sayfaya erişim sağlanamadı, tekrar deneniyor...")
        except Exception as e:
            print(f"Bir hata oluştu: {e}")
        
        # 10 saniyede bir kontrol et
        time.sleep(10)

# Flask başlatma ve kontrol fonksiyonunu thread ile çalıştırma
if __name__ == '__main__':
    # Telegram kontrolünü ayrı bir thread'de çalıştırma
    threading.Thread(target=check_stock, daemon=True).start()

    # Flask uygulamasını başlatma
    # Render veya başka bir platform için port ayarları
    port = int(os.environ.get('PORT', 8080))  # Render gibi platformlar için PORT ayarını al
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
@app.route('/')
def home():
    return 'Stok kontrol botu çalışıyor.'
