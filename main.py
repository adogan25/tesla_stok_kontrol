import os
import logging
import requests
from bs4 import BeautifulSoup
from flask import Flask
import telegram
from time import sleep

# Flask uygulaması başlatma
app = Flask(__name__)

# Telegram Bot Token ve Chat ID
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
bot = telegram.Bot(token=TELEGRAM_TOKEN)

# Telegram'a mesaj gönderme fonksiyonu
def send_telegram_message(message):
    try:
        bot.send_message(chat_id=CHAT_ID, text=message)
    except Exception as e:
        logging.error(f"Telegram mesajı gönderilemedi: {e}")

# Web scraping fonksiyonu
def check_stock(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Sayfada bir fotoğraf var mı kontrol et
        image = soup.find('img')
        if image:
            send_telegram_message(f"Stokta araç var! Sayfa: {url}")
        else:
            send_telegram_message(f"Stokta araç yok. Sayfa: {url}")
    except Exception as e:
        logging.error(f"Web scraping hatası: {e}")
        send_telegram_message(f"Hata oluştu: {e}")

# Flask route - Uygulama başlatıldığında çalışacak
@app.route('/')
def home():
    return "Web Scraper ve Telegram Bot Çalışıyor!"

# Web scraping ve bildirim gönderen fonksiyon çalıştırma
def run_scraping():
    url = 'https://www.tesla.com/tr_TR/inventory/new/my?arrangeby=plh&zip=34025&range=0'  # Web scraping yapılacak URL'yi buraya yazın
    while True:
        check_stock(url)
        sleep(3600)  # Her saat başı kontrol et

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # Web scraping fonksiyonunu başlat
    from threading import Thread
    scraper_thread = Thread(target=run_scraping)
    scraper_thread.start()

    # Flask uygulamasını başlat
    app.run(host='0.0.0.0', port=5000)
