# ⚽ Atletik Performans Takip Sistemi

Futbol oyuncularının antrenman ve maç performanslarını takip eden, analiz yapan modern web uygulaması.

## 🎯 Proje Özeti

Bu sistem, atletik performans antrenörleri için geliştirilmiş, oyuncuların günlük antrenman verilerini kaydedip maç performansıyla karşılaştırma yapabilen profesyonel bir araçtır.

## 📊 Temel Özellikler

### ✅ **Tamamlanan Özellikler**
- **Günlük Veri Girişi:** Oyuncu bazlı antrenman/maç verileri
- **Otomatik Analiz:** Antrenman vs Maç yüklenme oranları (%100 referans)
- **İnteraktif Grafikler:** Chart.js ile modern görselleştirme
- **Responsive Tasarım:** Mobil ve masaüstü uyumlu
- **RESTful API:** Modern backend mimari
- **Gerçek Zamanlı Hesaplama:** Anında sonuçlar

### 📈 **Analiz Metrikleri**
- **Toplam Mesafe:** Antrenman/maç karşılaştırması
- **Hız Analizi:** 16+, 18+, 20+, 24+ km/h mesafeleri  
- **İvmelenme Verileri:** Acc/Decc sayıları
- **Metabolik Güç:** Yüksek yoğunluk mesafesi
- **Yüzde Hesaplama:** (Antrenman Ort. ÷ Maç Ort.) × 100

## 🛠️ Teknoloji Stack

### **Backend**
- **Flask:** Python web framework
- **SQLite:** Hafif veritabanı çözümü
- **Flask-CORS:** Cross-origin resource sharing

### **Frontend**  
- **HTML5/CSS3:** Modern web standartları
- **Vanilla JavaScript:** Framework bağımsız
- **Chart.js:** İnteraktif grafik kütüphanesi
- **Gradient Design:** Profesyonel görünüm

### **Deployment**
- **Railway.app:** Cloud hosting platform
- **GitHub:** Versiyon kontrolü ve CI/CD

## 🚀 Kurulum ve Çalıştırma

### **Yerel Geliştirme**
```bash
# Projeyi klonla
git clone https://github.com/YOURUSERNAME/atletik-performans-sistemi.git
cd atletik-performans-sistemi/web_app

# Gerekli paketleri yükle
pip install -r requirements.txt

# Uygulamayı çalıştır
python app.py
```

**Uygulama:** http://localhost:8080

### **Railway Deployment**
1. GitHub'a projeyi yükle
2. Railway.app'te hesap aç
3. "Deploy from GitHub" seç  
4. Repository'yi bağla
5. Otomatik deploy başlar

## 📱 Kullanım Rehberi

### **1. Dashboard (📊)**
- Genel istatistikler görüntüle
- Son aktiviteleri takip et
- Toplam oyuncu/antrenman/maç sayıları

### **2. Veri Girişi (➕)**
- Oyuncu seç
- Tarih ve aktivite türü belirle
- Performans metriklerini gir:
  - Süre ve mesafe
  - Hız verileri (16+, 18+, 20+, 24+ km/h)
  - İvmelenme sayıları
  - Metabolik güç mesafesi

### **3. Analiz (📈)**
- Çoklu oyuncu seçimi
- Tarih aralığı belirleme
- Otomatik yüzde hesaplamaları:
  - **%100 üstü:** Antrenman > Maç (İyi)
  - **%80-100:** Normal seviye
  - **%80 altı:** Antrenman eksikliği
- İnteraktif bar chart
- Detaylı sonuç tablosu

### **4. Oyuncu Yönetimi (👥)**
- Yeni oyuncu ekleme
- Pozisyon belirleme
- Oyuncu listesi görüntüleme

## 📋 Veri Yapısı

### **Oyuncular (Players)**
- ID, İsim, Pozisyon, Kayıt tarihi

### **Aktiviteler (Activities)**
- Oyuncu ID, Tarih, Tür (antrenman/maç)
- Süre, Mesafe, Hız verileri
- İvmelenme, Metabolik güç, Notlar

### **Hesaplanmış Metrikler**
- Ortalama değerler
- Yüzde oranları
- Karşılaştırma sonuçları

## 🔧 API Endpoints

### **Oyuncular**
- `GET /api/players` - Oyuncu listesi
- `POST /api/players` - Yeni oyuncu

### **Aktiviteler** 
- `GET /api/activities` - Aktivite listesi (filtrelenebilir)
- `POST /api/activities` - Yeni aktivite

### **Analiz**
- `POST /api/analysis` - Performans analizi
- `GET /api/dashboard-stats` - Dashboard verileri

## 📈 Proje Geliştirme Süreci

### **Faz 1: Veri Analizi**
- ✅ PDF dosyasından Excel çıktısı
- ✅ Yüzde hesaplama mantığının analizi
- ✅ Veri yapısının belirlenmesi

### **Faz 2: Streamlit Prototipi** 
- ✅ Hızlı prototip geliştirme
- ✅ Temel fonksiyonalite testi
- ✅ Kullanıcı feedback alımı

### **Faz 3: Web Uygulaması**
- ✅ Flask backend geliştirme
- ✅ Modern frontend tasarım
- ✅ Chart.js grafik entegrasyonu
- ✅ Responsive tasarım

### **Faz 4: Deployment**
- ✅ Railway.app konfigürasyonu
- ✅ GitHub entegrasyonu
- ✅ Production hazırlığı

## 🎨 Gelecek Geliştirmeler

- [ ] **Radar Grafikleri:** Çok boyutlu performans analizi
- [ ] **Excel Import/Export:** Toplu veri işleme
- [ ] **Takım Karşılaştırması:** Grup analizleri
- [ ] **Trend Analizi:** Zaman serisi grafikleri
- [ ] **Push Notification:** Performans uyarıları
- [ ] **Kullanıcı Yetkilendirmesi:** Multi-user support
- [ ] **Yaralanma Takibi:** Sakatlık entegrasyonu

## 📞 Destek ve İletişim

- **GitHub Issues:** Hata bildirimleri ve önerilere
- **Email:** Teknik destek için
- **Documentation:** Detaylı kullanım kılavuzu

## 📄 Lisans

Bu proje MIT lisansı altında geliştirilmiştir.

---

**Geliştirici:** Alper - Atletik Performans Antrenörü  
**Teknoloji Partner:** Claude AI  
**Versiyon:** 1.0  
**Son Güncelleme:** Ağustos 2025