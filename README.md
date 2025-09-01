# ⚽ Atletik Performans Takip Sistemi

Futbol takımlarının oyuncu profillerini yönetip antrenman ve maç performanslarını takip eden güvenli web uygulaması.

## 📊 Ana Özellikler

- **Kullanıcı Yönetimi:** bcrypt hash'li güvenli giriş, profil yönetimi
- **Takım Yönetimi:** 22 alanlı detaylı oyuncu profilleri
- **Performans Takibi:** Antrenman/maç verileri, hız analizi, kilo/sakatlık geçmişi
- **Analiz:** İnteraktif Chart.js grafikleri ve karşılaştırmalı raporlama

## 🛠️ Teknoloji Stack

**Backend:** Flask, SQLite (foreign keys + indexes), bcrypt  
**Frontend:** HTML5/CSS3, JavaScript (modüler), Chart.js v4.4.1  
**Güvenlik:** Restricted CORS, secure sessions, environment variables

## 🚀 Kurulum

```bash
cd atletik-performans-sistemi/web_app
pip3 install -r requirements.txt
export SECRET_KEY="your-secure-random-secret-key"
python3 app.py
```

**Uygulama:** http://localhost:8081  
**Demo:** demo / demo123

---

## 📱 v2.5 Responsive Design İyileştirmeleri

### 🖥️ Çoklu Ekran Desteği
- **Desktop (992px+):** Optimal buton/form boyutları
- **Tablet (768-992px):** Orta boyut responsive layoutlar
- **Mobil (480-768px):** Dokunma dostu UI elementleri
- **Küçük Mobil (480px-):** Tek sütunlu düzen

### 📐 UI/UX Optimizasyonları
- **Buton Boyutları:** Desktop'ta kompakt, mobilde dokunma dostu (44px min-height)
- **Form Kontrolleri:** iOS zoom engellemek için 16px font-size
- **Modal Pencereler:** Responsive genişlik ayarları (%95-98%)
- **Tablo Görünümü:** Yatay kaydırma desteği

### 🎯 Touch Target İyileştirmeleri
- Mobil cihazlarda minimum 44px dokunma alanı
- CSS Specificity düzeltmeleri (cascading sorunları)
- Login/Ana sayfa butonları için ayrı optimizasyonlar

**Son Güncelleme:** 1 Eylül 2025