# ⚽ Atletik Performans Takip Sistemi

Futbol takımlarının oyuncu profillerini yönetip antrenman ve maç performanslarını takip eden güvenli web uygulaması.

## 📊 Ana Özellikler

- **Kullanıcı Yönetimi:** bcrypt hash'li güvenli giriş, profil yönetimi
- **Takım Yönetimi:** 22 alanlı detaylı oyuncu profilleri
- **Performans Takibi:** Kapsamlı antrenman/maç verileri, hız analizi, özel metrik girişi
- **Maç Analizi:** Devre bazlı (1. devre/2. devre) detaylı performans takibi
- **Analiz:** İnteraktif Chart.js grafikleri ve karşılaştırmalı raporlama

## 🛠️ Teknoloji Stack

**Backend:** Flask, SQLite (foreign keys + indexes), bcrypt  
**Frontend:** HTML5/CSS3, JavaScript (modüler), Chart.js v4.4.1  
**Güvenlik:** Restricted CORS, secure sessions, environment variables

## 🚀 Kurulum

```bash
cd atletik-performans-sistemi/web_app
pip3 install -r requirements.txt
PORT=8080 SECRET_KEY="atletik-performans-secret-key-2025" python3 app.py
```

**Uygulama:** http://127.0.0.1:8080  
**Demo:** demo / demo123

---

## ⚡ v3.0 Gelişmiş Performans Metrikleri (9 Eylül 2025)

### 🏃‍♂️ Yeni Performans Metrikleri
- **Maksimum Sürat:** km/h cinsinden en yüksek hız kaydı
- **Sprint Sayıları:** Farklı hız aralıkları için sprint count (16+, 18+, 20+, 24+ km/h)
- **Yüksek Hız Mesafeleri:** 16, 18, 20, 24 km/h üzeri koşu mesafeleri
- **Metabolik Güç:** Yüksek yoğunluklu aktivite metrikleri
- **İvme/Yavaşlama:** Toplam ve yüksek şiddetli ivme sayıları

### 🎯 Maç Devre Analizi
- **Devre Bazlı Veri Girişi:** 1. devre ve 2. devre için ayrı performans kaydı
- **Kapsamlı Devre Metrikleri:** Her devre için 15+ detaylı performans verisi
- **Devre Karşılaştırması:** 1. devre vs 2. devre analiz grafikleri
- **Süre Takibi:** Dakika bazında devre süresi kayıtları

### 💾 Gelişmiş Veritabanı Şeması
- **match_periods tablosu:** Devre bazlı detaylı performans verileri
- **custom_metrics tablosu:** Kullanıcı tanımlı özel metrikler
- **activities tablosu:** Genişletilmiş performans alanları

### 📊 Veri Giriş İyileştirmeleri
- **Özel Metrik Desteği:** Kullanıcının istediği herhangi bir metrik girişi
- **Otomatik Validasyon:** Sayısal veri doğrulaması ve hata kontrolü
- **Responsive Forms:** Mobil cihazlar için optimize edilmiş form arayüzü

**Son Güncelleme:** 9 Eylül 2025