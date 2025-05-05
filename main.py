from flask import Flask
import threading
import time
import requests
from bs4 import BeautifulSoup
import telegram
import os
import logging
from datetime import datetime
import random

app = Flask(__name__)

# Log ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ayarlar
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
CHECK_INTERVAL = 10  # 10 saniye
UPTIMEROBOT_PING_URL = os.getenv('UPTIMEROBOT_PING_URL', '')

# Tesla Envanter URL
TESLA_URL = "https://www.tesla.com/tr_TR/inventory/new/my?arrangeby=plh&zip=34025&range=0"

# Önceki stok bilgisini saklamak için
previous_stock = []
last_notification_time = None
is_active = True

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
    global previous_stock, last_notification_time, is_active
    
    if not is_active:
        return
    
    try:
        # Rastgele bekleme (1-3 sn)
        time.sleep(random.uniform(1, 3))
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        logger.info(f"Stok kontrolü: {datetime.now().strftime('%H:%M:%S')}")
        
        response = requests.get(TESLA_URL, headers=headers, timeout=8)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        vehicles = soup.find_all('div', class_='result')  # Güncel class ismi
        
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
            notification_cooldown = 60  # 1 dakika
            
            if (last_notification_time is None or 
                (datetime.now() - last_notification_time).total_seconds() > notification_cooldown):
                
                message = "🔄 Tesla Stok Değişikliği!\n\n"
                new_vehicles = [v for v in current_stock if v not in previous_stock]
                if new_vehicles:
                    message += f"➕ {len(new_vehicles)} Yeni Araç:\n\n"
                    message += "\n\n".join(new_vehicles) + "\n\n"
                
                removed_vehicles = [v for v in previous_stock if v not in current_stock]
                if removed_vehicles:
                    message += f"➖ {len(removed_vehicles)} Araç Stoktan Düştü:\n\n"
                    message += "\n\n".join(removed_vehicles) + "\n\n"
                
                message += "📋 Güncel Stok:\n\n"
                message += "\n\n".join(current_stock) if current_stock else "Stokta araç yok"
                
                if send_telegram_message(message):
                    last_notification_time = datetime.now()
        
        previous_stock = current_stock
        
    except requests.RequestException as e:
        logger.error(f"Ağ hatası: {e}")
    except Exception as e:
        logger.error(f"Beklenmeyen hata: {e}")

def uptimerobot_ping():
    while True:
        if UPTIMEROBOT_PING_URL:
            try:
                requests.get(UPTIMEROBOT_PING_URL, timeout=5)
                logger.info("UptimeRobot ping gönderildi")
            except:
                logger.warning("UptimeRobot ping gönderilemedi")
        time.sleep(300)  # 5 dakikada bir ping

@app.route('/')
def home():
    global is_active
    return f"Tesla Stok Takip Sistemi (Aktif: {is_active})<br>Son kontrol: {datetime.now().strftime('%H:%M:%S')}"

@app.route('/start')
def start_monitoring():
    global is_active
    is_active = True
    return "Monitoring started"

@app.route('/stop')
def stop_monitoring():
    global is_active
    is_active = False
    return "Monitoring stopped"

@app.route('/check-now')
def manual_check():
    check_tesla_stock()
    return "Manuel kontrol tamamlandı"

def run_monitoring():
    # Başlangıç mesajı
    send_telegram_message("🔔 Tesla Stok Takip Sistemi Başlatıldı! (10s aralık)")
    
    # UptimeRobot ping thread'i
    threading.Thread(target=uptimerobot_ping, daemon=True).start()
    
    # Ana kontrol döngüsü
    while True:
        if is_active:
            check_tesla_stock()
        time.sleep(CHECK_INTERVAL)

# Uygulama başladığında monitoring'i başlat
threading.Thread(target=run_monitoring, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
