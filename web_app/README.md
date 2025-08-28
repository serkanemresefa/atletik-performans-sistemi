# ⚽ Atletik Performans Takip Sistemi - Web Uygulaması

Modern web tabanlı atletik performans takip ve analiz sistemi.

## 🚀 Özellikler

- **Web Tabanlı:** Her yerden erişilebilir
- **Responsive Tasarım:** Mobil uyumlu arayüz
- **Gerçek Zamanlı Analiz:** Anında hesaplama ve görselleştirme
- **İnteraktif Grafikler:** Chart.js ile profesyonel grafikler
- **RESTful API:** Modern API yapısı

## 🛠️ Teknolojiler

- **Backend:** Flask (Python)
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Grafik:** Chart.js
- **Veritabanı:** SQLite
- **Deployment:** Railway.app

## 📦 Kurulum

### Lokal Geliştirme

```bash
# Klasöre git
cd web_app

# Gerekli paketleri yükle
pip install -r requirements.txt

# Uygulamayı çalıştır
python app.py
```

Uygulama http://localhost:5000 adresinde çalışacaktır.

### Railway Deployment

1. Railway.app hesabı oluşturun
2. GitHub'a projeyi yükleyin
3. Railway'de "Deploy from GitHub" seçin
4. Repository'yi bağlayın
5. Otomatik deploy başlayacak

## 📊 API Endpoints

### Oyuncular
- `GET /api/players` - Tüm oyuncuları listele
- `POST /api/players` - Yeni oyuncu ekle

### Aktiviteler
- `GET /api/activities` - Aktiviteleri listele (filtreleme mümkün)
- `POST /api/activities` - Yeni aktivite ekle

### Analiz
- `POST /api/analysis` - Performans analizi yap
- `GET /api/dashboard-stats` - Dashboard istatistikleri

## 🎯 Kullanım

1. **Dashboard:** Genel istatistikleri görüntüle
2. **Veri Girişi:** Günlük antrenman/maç verilerini gir
3. **Analiz:** Tarih aralığı seçerek oyuncu performanslarını karşılaştır
4. **Oyuncu Yönetimi:** Yeni oyuncular ekle

## 📱 Mobil Uyumluluk

Uygulama tam responsive tasarıma sahiptir:
- Mobil cihazlarda tek sütun layout
- Touch-friendly butonlar
- Optimize edilmiş form alanları

## 🔧 Geliştirme

Yeni özellik eklemek için:
1. Backend'de yeni endpoint ekleyin (`app.py`)
2. Frontend'de JavaScript fonksiyonu yazın
3. HTML'e gerekli UI elementlerini ekleyin

## 🚨 Sorun Giderme

- Port hatası: `PORT` environment variable'ı kontrol edin
- Database hatası: `atletik_performans.db` dosyasını silin, yeniden oluşturulacak
- CORS hatası: Flask-CORS'un yüklü olduğundan emin olun

## 📈 Gelecek Özellikler

- [ ] Radar grafikleri
- [ ] Excel import/export
- [ ] Takım karşılaştırması
- [ ] Push notification'lar
- [ ] Kullanıcı yetkilendirmesi

## 📞 Destek

Sorularınız için GitHub Issues kullanın veya doğrudan iletişime geçin.