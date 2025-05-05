import os
import time
import requests
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread

# Telegram Bot bilgileri
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Kontrol edilecek URL
CAR_URL = os.getenv("https://www.tesla.com/tr_TR/inventory/new/my?arrangeby=plh&zip=34025&range=0")

# Flask uygulaması
app = Flask(__name__)

@app.route("/")
def home():
    return "Araç stok kontrol botu çalışıyor."

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Telegram mesajı gönderilemedi: {e}")

def check_car_stock():
    notified = False
    while True:
        try:
            response = requests.get(CAR_URL, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            image = soup.find("img")
            
            if image and not notified:
                send_telegram_message("Araç stokta! Sayfada fotoğraf bulundu.")
                notified = True
            elif not image:
                notified = False  # tekrar bildirim yapılabilir hale gelsin

        except Exception as e:
            print(f"Kontrol sırasında hata: {e}")

        time.sleep(10)  # 10 saniyede bir kontrol

def run_flask():
    app.run(host="0.0.0.0", port=10000)

# Her iki işlemi aynı anda başlat
if __name__ == "__main__":
    Thread(target=check_car_stock).start()
    run_flask()
