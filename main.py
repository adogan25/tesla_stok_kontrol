import os
import requests
from bs4 import BeautifulSoup
import telegram
import time
import schedule
from datetime import datetime
from dotenv import load_dotenv
import logging

# Log ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Çevresel değişkenleri yükle
load_dotenv()

# Ayarlar
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
CHECK_INTERVAL_SECONDS = int(os.getenv('CHECK_INTERVAL_SECONDS', 10))  # Varsayılan 10 saniye
REQUEST_TIMEOUT = 10  # İstek timeout süresi (saniye)
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

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
    except Exception as e:
        logger.error(f"Telegram mesaj gönderilemedi: {e}")

def check_tesla_stock():
    global previous_stock, last_notification_time
    
    try:
        headers = {'User-Agent': USER_AGENT}
        
        # Tesla suncularını aşırı yüklememek için rastgele bir bekleme
        time.sleep(1 + (2 * random.random()))  # 1-3 saniye arası rastgele bekleme
        
        logger.info(f"Stok kontrolü başlatılıyor... {datetime.now().strftime('%H:%M:%S')}")
        
        response = requests.get(TESLA_URL, headers=headers, timeout=REQUEST_TIMEOUT)
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
            notification_cooldown = 60  # 1 dakika (aynı değişiklik için tekrar bildirim göndermemek için)
            
            # Son bildirimden belirli süre geçmişse veya ilk defa çalışıyorsa
            if (last_notification_time is None or 
                (datetime.now() - last_notification_time).total_seconds() > notification_cooldown):
                
                if not previous_stock:
                    message = "🚗 Tesla Stok Takip Sistemi Başlatıldı!\n\n"
                    message += f"⏰ Kontrol Aralığı: {CHECK_INTERVAL_SECONDS} saniye\n\n"
                    message += "📢 Mevcut Stok:\n\n"
                    message += "\n\n".join(current_stock) if current_stock else "Stokta araç bulunmamaktadır."
                else:
                    message = "🔄 Tesla Stok Değişikliği Algılandı!\n\n"
                    
                    # Yeni gelen araçlar
                    new_vehicles = [v for v in current_stock if v not in previous_stock]
                    if new_vehicles:
                        message += f"➕ {len(new_vehicles)} Yeni Araç:\n\n"
                        message += "\n\n".join(new_vehicles) + "\n\n"
                    
                    # Stoktan düşen araçlar
                    removed_vehicles = [v for v in previous_stock if v not in current_stock]
                    if removed_vehicles:
                        message += f"➖ {len(removed_vehicles)} Araç Stoktan Düştü:\n\n"
                        message += "\n\n".join(removed_vehicles) + "\n\n"
                    
                    if not new_vehicles and not removed_vehicles:
                        message += "ℹ️ Stok bilgilerinde içerik değişikliği yok, ancak sıralama değişmiş olabilir.\n\n"
                    
                    message += "📋 Güncel Stok Durumu:\n\n"
                    message += "\n\n".join(current_stock) if current_stock else "Stokta araç bulunmamaktadır."
                
                send_telegram_message(message)
                last_notification_time = datetime.now()
        
        previous_stock = current_stock
        
    except requests.RequestException as e:
        logger.error(f"Ağ hatası: {e}")
    except Exception as e:
        logger.error(f"Beklenmeyen hata: {e}")

if __name__ == "__main__":
    import random
    
    # Başlangıç mesajı
    send_telegram_message(f"🔔 Tesla Stok Takip Sistemi Başlatıldı! Her {CHECK_INTERVAL_SECONDS} saniyede bir stok kontrol edilecek.")
    
    # Zamanlayıcıyı ayarla
    schedule.every(CHECK_INTERVAL_SECONDS).seconds.do(check_tesla_stock)
    
    # İlk kontrolü hemen yap
    check_tesla_stock()
    
    # Ana döngü
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Uygulama kapatılıyor...")
            send_telegram_message("🔴 Tesla Stok Takip Sistemi Durduruldu!")
            break
        except Exception as e:
            logger.error(f"Ana döngü hatası: {e}")
            time.sleep(10)  # Hata durumunda 10 saniye bekle
