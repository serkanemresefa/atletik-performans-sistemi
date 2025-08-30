# ⚽ Atletik Performans Takip Sistemi

Futbol takımlarının oyuncu profillerini yönetip antrenman ve maç performanslarını takip eden profesyonel web uygulaması.

## 🎯 Proje Özeti

Bu sistem, atletik performans antrenörleri ve takım yöneticileri için geliştirilmiş kapsamlı bir takım yönetim platformudur. Detaylı oyuncu profilleri, antrenman veri takibi ve performans analizi özelliklerini tek bir arayüzde sunar.

## 📊 Ana Özellikler

### ✅ **Kullanıcı Yönetimi**
- **Güvenli Giriş:** Şifreli kullanıcı hesapları ve oturum yönetimi
- **Kullanıcı Profili:** Kişisel bilgiler ve profil güncelleme
- **Multi-User Destek:** Her kullanıcı kendi takımlarını yönetir

### 👥 **Takım Yönetimi**
- **Takım Oluşturma:** Kullanıcı bazlı takım organizasyonu
- **Detaylı Oyuncu Profilleri:** 22 ayrı bilgi alanı ile kapsamlı profil sistemi
- **Oyuncu Kartları:** Görsel oyuncu yönetimi ve hızlı erişim

### 📈 **Performans Takibi**
- **Antrenman/Maç Verisi:** Oyuncu bazlı aktivite kayıtları
- **Hız Analizi:** 16+, 18+, 20+, 24+ km/h mesafe takibi
- **İvmelenme Metrikleri:** Detaylı hareket analizi
- **Görsel Analiz:** İnteraktif grafik ve tablo raporları

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

## 🚀 Kurulum ve Çalıştırma

### **Yerel Geliştirme**
```bash
# Projeyi klonla
git clone [repository-url]
cd atletik-performans-sistemi/web_app

# Gerekli paketleri yükle
pip install flask flask-cors bcrypt

# Uygulamayı çalıştır
python3 app.py
```

**Uygulama:** http://localhost:8081  
**Demo Giriş:** Kullanıcı: `demo` / Şifre: `demo123`

## 📱 Kullanım Rehberi

### **1. Profil Yönetimi (👤)**
- Kullanıcı bilgilerini görüntüle
- Profil güncellemeleri yap
- Toplam takım istatistiklerini takip et

### **2. Takım Yönetimi (👥)**
- **Mevcut Takımlar:** Takım listesi ve istatistikleri
- **Takım Oluşturma:** Ad, lig, sezon, antrenör bilgileri
- **Oyuncu Yönetimi:** 22 alanlı detaylı profil sistemi
  - Kişisel: Ad, soyad, doğum tarihi, uyruk, kan grubu
  - Pozisyon: Ana/yan mevki, tercih edilen ayak, forma no
  - Fiziksel: Boy, kilo, önceki kulüp, sözleşme detayları
  - Sağlık: Sakatlık geçmişi, mevcut durum
  - İletişim: Telefon, email, acil durum kişisi, notlar

### **3. Antrenman Yönetimi (🏃‍♂️)**
- Takım bazlı oyuncu listesi görüntüleme
- Modal ile hızlı veri girişi:
  - Tarih ve aktivite türü
  - Performans metrikleri (süre, mesafe, hız)
  - İvmelenme ve metabolik güç verileri

### **4. Performans Analizi (📈)**
- Çoklu oyuncu seçimi ve tarih filtreleme
- Antrenman vs maç karşılaştırması
- İnteraktif grafik ve detaylı tablolar
- Yüzde bazlı performans değerlendirmesi

## 📋 Veri Yapısı

### **Kullanıcılar (Users)**
- ID, kullanıcı adı, şifre (hash), email, ad/soyad

### **Takımlar (Teams)**
- ID, takım adı, lig, sezon, antrenör adı, açıklama, kullanıcı ID, oluşturma tarihi

### **Oyuncular (Players) - 22 Alan**
- **Temel:** ID, ad, soyad, doğum tarihi, uyruk
- **Pozisyon:** Ana mevki, yan mevkiler, tercih edilen ayak, forma numarası
- **Fiziksel:** Boy (cm), kilo (kg), kan grubu
- **Geçmiş:** Önceki kulüp, kulüp geçmişi, sözleşme tarihleri
- **Sağlık:** Sakatlık geçmişi, mevcut sakatlık durumu
- **İletişim:** Telefon, email, acil durum kişisi, notlar

### **Aktiviteler (Activities)**
- Oyuncu ID, tarih, tür (antrenman/maç)
- Performans metrikleri: süre, mesafe, hız verileri
- İvmelenme sayıları, metabolik güç, notlar

## 🔧 Ana API Endpoints

### **Kimlik Doğrulama**
- `POST /login` - Kullanıcı girişi
- `POST /logout` - Oturum kapatma
- `POST /register` - Yeni kullanıcı kaydı

### **Takım Yönetimi**
- `GET /api/teams` - Kullanıcının takımları
- `POST /api/teams` - Yeni takım oluştur
- `DELETE /api/teams/<id>` - Takım sil

### **Oyuncu Yönetimi**
- `GET /api/players` - Takım oyuncuları
- `POST /api/players` - Yeni oyuncu ekle
- `PUT /api/players/<id>` - Oyuncu güncelle
- `DELETE /api/players/<id>` - Oyuncu sil

### **Performans Takibi**
- `GET /api/activities?player_id=<id>` - Oyuncu aktivite listesi
- `POST /api/activities` - Yeni aktivite kaydet
- `POST /api/analysis` - Performans analizi

## 🚀 Sistem Mimarisi

### **4 Ana Modül**
1. **Profil Yönetimi** - Kullanıcı hesap ve bilgi yönetimi
2. **Takım Yönetimi** - Takım oluşturma ve detaylı oyuncu profilleri
3. **Antrenman Yönetimi** - Performans veri girişi ve takibi
4. **Analiz Modülü** - Grafik ve raporlama

### **Güvenlik Özellikleri**
- Bcrypt şifre hashleme
- Session tabanlı kimlik doğrulama
- Kullanıcı bazlı veri izolasyonu
- CSRF koruması

## 🎨 Son Güncellemeler (v2.2)

### ✅ **Yeni Özellikler (v2.0)**
- **Geliştirilmiş Takım Yönetimi:** Lig, sezon, antrenör bilgileri eklendi
- **Yeniden Düzenlenmiş Arayüz:** 1️⃣ Mevcut Takımlar → 2️⃣ Takım Yönetimi → 3️⃣ Oyuncu Yönetimi
- **Database Migration:** Otomatik veri tabanı güncelleme sistemi
- **Antrenman Yönetimi:** Oyuncu ekleme kaldırıldı, sadece veri girişi odaklı

### 🔧 **Bug Düzeltmeleri (v2.1)**
- **Aktivite Görüntüleme Sorunu:** Frontend'de oyuncu performans geçmişi görüntülenemeyen bug düzeltildi
- **API Endpoint Eksikliği:** `GET /api/activities?player_id=<id>` endpoint'i eklendi
- **Örnek Veri Entegrasyonu:** 504 örnek aktivite verisi (28 oyuncu x 18 aktivite) sisteme entegre edildi
- **Performans Geçmişi Modülü:** Oyuncu detay modalındaki "Performans Geçmişi" sekmesi artık çalışıyor

### 🚀 **Kapsamlı İyileştirmeler (v2.2)**
- **İstatistikler API Endpoint:** `GET /api/players/<id>/statistics` endpoint'i tam olarak implement edildi
- **Kapsamlı İstatistik Analizi:** Oyuncu bazlı detaylı performans istatistikleri hesaplaması
  - Genel istatistikler (toplam aktivite, antrenman/maç sayıları, son aktivite tarihi)
  - Ortalama performans metrikleri (süre, mesafe, hız aralıkları, sprint, AccDecc, metabolik güç)
  - Antrenman vs maç karşılaştırması (süre, mesafe, yüksek hız, sprint değerleri)
- **İstatistikler Tab Implementasyonu:** Frontend'de tam fonksiyonel istatistikler sekmesi
  - Gradient tasarımlı istatistik kartları
  - Responsive grid layout
  - Antrenman vs maç görsel karşılaştırması (yeşil/kırmızı renk kodlaması)
  - Detaylı ortalama değerler bölümü
- **Performans Geçmişi Tab Geliştirmesi:** Aktivite görüntüleme tamamen yenilendi
  - Her aktivite için detaylı metrik gösterimi
  - Antrenman/maç türüne göre farklı gradient renkler
  - Grid layout'da tüm performans verileri (mesafe, hız aralıkları, sprint, AccDecc, metabolik güç)
  - Modern kart tasarımı ve responsive düzen
- **Database Schema Uyumluluğu:** Column adı düzeltmeleri (`position` → `primary_position`)
- **Analysis Endpoint Bug Fix:** Player name fetching sorunu düzeltildi (`name` → `first_name, last_name`)

### 🗃️ **Mevcut Örnek Veriler**
- **2 Takım:** Fenerbahçe U19, Galatasaray A2
- **28 Oyuncu:** Pozisyon bazlı dağılım (kaleci, defans, orta saha, forvet)
- **504 Aktivite:** 30 günlük periyotta antrenman/maç verileri
- **Gerçekçi Metrikler:** Pozisyon bazlı farklılaştırılmış performans değerleri
- **Tam İstatistik Entegrasyonu:** Her oyuncu için hesaplanmış ortalama değerler ve karşılaştırmalar

### 📊 **Yeni API Endpoints**
- `GET /api/players/<id>/statistics` - Oyuncu performans istatistikleri
- `GET /api/activities?player_id=<id>` - Oyuncu aktivite geçmişi (önceden eklenmişti)

### 🎯 **Sistem Durumu**
- **✅ Frontend:** Tam fonksiyonel oyuncu detay modal sistemi
- **✅ Backend:** Komplet API endpoints ve istatistik hesaplamaları
- **✅ Database:** 504 örnek aktivite verisi tam entegrasyon
- **✅ UI/UX:** Modern, responsive ve kullanıcı dostu arayüz
- **✅ Test Edildi:** Browser ve API testleri başarıyla geçti

### 🔄 **Gelecek Geliştirmeler**
- Excel import/export, PDF raporlama, mobil uygulama desteği
- Grafik ve chart entegrasyonları (Chart.js)
- Takım bazlı karşılaştırmalı analizler

---

**Versiyon:** 2.2  
**Son Güncelleme:** 30 Ağustos 2025  
**Son Geliştirme:** Performans istatistikleri ve aktivite geçmişi modülleri tamamen çalışır hale getirildi