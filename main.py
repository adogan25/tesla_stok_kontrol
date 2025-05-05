import requests
from bs4 import BeautifulSoup
import telegram
import time
import schedule
from datetime import datetime

# Telegram Bot Ayarları
TELEGRAM_BOT_TOKEN = '7770662830:AAF81ZmkPNNCxV2sUg-0jSVyEb64fTNkBn8'
TELEGRAM_CHAT_ID = '1476078120'

# Tesla Envanter URL
TESLA_URL = "https://www.tesla.com/tr_TR/inventory/new/my?arrangeby=plh&zip=34025&range=0"

# Önceki stok bilgisini saklamak için
previous_stock = []

def send_telegram_message(message):
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

def check_tesla_stock():
    global previous_stock
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(TESLA_URL, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Araç bilgilerini çekme (Bu kısım Tesla'ın HTML yapısına göre güncellenmeli)
        vehicles = soup.find_all('div', class_='vehicle-card')  # Örnek class, gerçek class farklı olabilir
        
        current_stock = []
        
        for vehicle in vehicles:
            model = vehicle.find('h3').text.strip() if vehicle.find('h3') else "Bilinmeyen Model"
            price = vehicle.find('div', class_='price').text.strip() if vehicle.find('div', class_='price') else "Fiyat Bilgisi Yok"
            details = vehicle.find('div', class_='details').text.strip() if vehicle.find('div', class_='details') else "Detay Yok"
            
            vehicle_info = f"{model} - {price} - {details}"
            current_stock.append(vehicle_info)
        
        # Stok değişikliklerini kontrol et
        if set(current_stock) != set(previous_stock):
            if not previous_stock:
                message = "🚗 Tesla Stok Takip Sistemi Başlatıldı!\n\n"
                message += "📢 Mevcut Stok:\n"
                message += "\n".join(current_stock) if current_stock else "Stokta araç bulunmamaktadır."
            else:
                message = "🔄 Tesla Stok Değişikliği Algılandı!\n\n"
                
                # Yeni gelen araçlar
                new_vehicles = [v for v in current_stock if v not in previous_stock]
                if new_vehicles:
                    message += "➕ Yeni Araçlar:\n"
                    message += "\n".join(new_vehicles) + "\n\n"
                
                # Stoktan düşen araçlar
                removed_vehicles = [v for v in previous_stock if v not in current_stock]
                if removed_vehicles:
                    message += "➖ Stoktan Düşen Araçlar:\n"
                    message += "\n".join(removed_vehicles) + "\n\n"
                
                if not new_vehicles and not removed_vehicles:
                    message += "Stok bilgilerinde değişiklik yok, ancak sıralama değişmiş olabilir.\n"
                
                message += "📋 Güncel Stok Durumu:\n"
                message += "\n".join(current_stock) if current_stock else "Stokta araç bulunmamaktadır."
            
            send_telegram_message(message)
        
        previous_stock = current_stock
        
    except Exception as e:
        error_message = f"❌ Hata oluştu: {str(e)}"
        send_telegram_message(error_message)

# Her 5 dakikada bir kontrol et
schedule.every(10).seconds.do(check_tesla_stock)

# Başlangıç mesajı
send_telegram_message("🔔 Tesla Stok Takip Sistemi Başlatıldı! Her 5 dakikada bir stok kontrol edilecek.")

# Ana döngü
while True:
    schedule.run_pending()
    time.sleep(1)
