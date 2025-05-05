import time
import requests
from flask import Flask
from urllib.parse import quote  # url_quote yerine quote kullanıyoruz.
import threading

app = Flask(__name__)

# Telegram Bot API bilgilerinizi buraya ekleyin
TELEGRAM_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
CHAT_ID = 'YOUR_CHAT_ID'

# Kontrol etmek istediğiniz URL
URL_TO_CHECK = 'https://www.tesla.com/tr_TR/inventory/new/my?arrangeby=plh&zip=34025&range=0'

# Fotoğraf var mı kontrol fonksiyonu
def check_stock():
    while True:
        try:
            # URL'deki sayfayı kontrol etme
            response = requests.get(URL_TO_CHECK)
            if response.status_code == 200:
                if 'img' in response.text:  # Sayfada resim varsa
                    send_telegram_message('Araç stokta mevcut!')
                else:
                    send_telegram_message('Araç stokta mevcut değil.')
        except Exception as e:
            send_telegram_message(f'Bir hata oluştu: {e}')
        
        time.sleep(10)  # 10 saniyede bir kontrol et

# Telegram mesajı gönderme fonksiyonu
def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = {
        'chat_id': CHAT_ID,
        'text': message
    }
    try:
        response = requests.post(url, data=data)
        if response.status_code != 200:
            print(f'Error: {response.status_code}')
    except Exception as e:
        print(f'Error sending message: {e}')

# Flask uygulaması için ana endpoint
@app.route('/')
def index():
    return 'Flask uygulaması çalışıyor.'

# Flask uygulaması başlatma ve kontrolü çoklu thread ile başlatma
if __name__ == '__main__':
    # Telegram kontrolünü ayrı bir thread'de çalıştırma
    threading.Thread(target=check_stock, daemon=True).start()

    # Flask uygulamasını başlatma
    app.run(debug=True, use_reloader=False)
