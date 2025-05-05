from flask import Flask
import threading
import time
import schedule
import requests
from bs4 import BeautifulSoup
import telegram
import os
import logging
from datetime import datetime

app = Flask(__name__)

# Log ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ayarlar
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL_MINUTES', 1))  # Dakika cinsinden

# Tesla Envanter URL
TESLA_URL = "https://www.tesla.com/tr_TR/inventory/new/my?arrangeby=plh&zip=34025&range=0"

# Önceki stok bilgisini saklamak için
previous_stock = []
last_notification_time = None

def send_telegram_message(message):
    try:
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info("Telegram mesajı gönderildi")
        return True
    except Exception as e:
        logger.error(f"Telegram mesaj gönderilemedi: {e}")
        return False

def check_tesla_stock():
    global previous_stock, last_notification_time
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        logger.info(f"Stok kontrolü başlatılıyor... {datetime.now().strftime('%H:%M:%S')}")
        
        response = requests.get(TESLA_URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Araç bilgilerini çekme (Tesla'nın güncel HTML yapısına göre güncelleyin)
        vehicles = soup.find_all('div', class_='result')  # Örnek class
        
        current_stock = []
        
        for vehicle in vehicles:
            try:
                model = vehicle.find('h3').text.strip() if vehicle.find('h3') else "Bilinmeyen Model"
                price = vehicle.find('div', class_='final-price').text.strip() if vehicle.find('div', class_='final-price') else "Fiyat Bilgisi Yok"
                details = vehicle.find('div', class_='trim-wrapper').text.strip() if vehicle.find('div', class_='trim-wrapper') else "Detay Yok"
                
                vehicle_info = f"🚗 {model}\n💰 {price}\n🔧 {details}\n—————————"
                current_stock.append(vehicle_info)
            except Exception as veh_error:
                logger.error(f"Araç bilgisi alınırken hata: {veh_error}")
                continue
        
        # Stok değişikliklerini kontrol et
        if set(current_stock) != set(previous_stock):
            notification_cooldown = 300  # 5 dakika (aynı değişiklik için tekrar bildirim göndermemek için)
            
            if (last_notification_time is None or 
                (datetime.now() - last_notification_time).total_seconds() > notification_cooldown):
                
                if not previous_stock:
                    message = "🚗 Tesla Stok Takip Sistemi Başlatıldı!\n\n"
                    message += f"⏰ Kontrol Aralığı: {CHECK_INTERVAL} dakika\n\n"
                    message += "📢 Mevcut Stok:\n\n"
                    message += "\n\n".join(current_stock) if current_stock else "Stokta araç bulunmamaktadır."
                else:
                    message = "🔄 Tesla Stok Değişikliği Algılandı!\n\n"
                    
                    new_vehicles = [v for v in current_stock if v not in previous_stock]
                    if new_vehicles:
                        message += f"➕ {len(new_vehicles)} Yeni Araç:\n\n"
                        message += "\n\n".join(new_vehicles) + "\n\n"
                    
                    removed_vehicles = [v for v in previous_stock if v not in current_stock]
                    if removed_vehicles:
                        message += f"➖ {len(removed_vehicles)} Araç Stoktan Düştü:\n\n"
                        message += "\n\n".join(removed_vehicles) + "\n\n"
                    
                    message += "📋 Güncel Stok Durumu:\n\n"
                    message += "\n\n".join(current_stock) if current_stock else "Stokta araç bulunmamaktadır."
                
                if send_telegram_message(message):
                    last_notification_time = datetime.now()
        
        previous_stock = current_stock
        
    except requests.RequestException as e:
        logger.error(f"Ağ hatası: {e}")
    except Exception as e:
        logger.error(f"Beklenmeyen hata: {e}")

def schedule_checker():
    while True:
        schedule.run_pending()
        time.sleep(1)

@app.route('/')
def home():
    return "Tesla Stok Takip Sistemi Aktif"

def run_scheduler():
    # Başlangıç mesajı
    send_telegram_message(f"🔔 Tesla Stok Takip Sistemi Başlatıldı! Her {CHECK_INTERVAL} dakikada bir stok kontrol edilecek.")
    
    # Zamanlayıcıyı ayarla
    schedule.every(CHECK_INTERVAL).minutes.do(check_tesla_stock)
    
    # İlk kontrolü hemen yap
    check_tesla_stock()
    
    # Zamanlayıcı thread'i başlat
    t = threading.Thread(target=schedule_checker)
    t.daemon = True
    t.start()

# Uygulama başladığında zamanlayıcıyı başlat
run_scheduler()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
