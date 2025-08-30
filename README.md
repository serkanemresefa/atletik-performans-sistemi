# ⚽ Atletik Performans Takip Sistemi

Futbol takımlarının oyuncu profillerini yönetip antrenman ve maç performanslarını takip eden web uygulaması.

## 📊 Ana Özellikler

- **Kullanıcı Yönetimi:** Güvenli giriş, profil yönetimi
- **Takım Yönetimi:** Detaylı oyuncu profilleri (22 alan)
- **Performans Takibi:** Antrenman/maç verileri, hız analizi
- **Analiz:** İnteraktif grafik ve raporlama

## 🛠️ Teknoloji

**Backend:** Flask, SQLite, Flask-CORS  
**Frontend:** HTML5/CSS3, JavaScript, Chart.js

## 🚀 Kurulum

```bash
cd atletik-performans-sistemi/web_app
pip install flask flask-cors bcrypt
python3 app.py
```

**Uygulama:** http://localhost:8081  
**Demo:** demo / demo123

## 🎯 Geliştirme Geçmişi

### **v2.3** - UI İyileştirmeleri
- **Aktivite Yönetimi:** Edit/delete fonksiyonları eklendi
- **Saat Desteği:** Aynı gün çoklu aktivite girişi
- **Kilo/Sakatlık Geçmişi:** Modal tabanlı zaman serisi takibi
- **Veri Girişi Entegrasyonu:** Modal içine taşındı
- **UI Temizleme:** İkonlar kaldırıldı, buton renkleri standardize edildi

### **v2.2** - Performans Analizi
- İstatistikler API ve frontend entegrasyonu
- Oyuncu bazlı detaylı performans hesaplamaları
- Antrenman vs maç karşılaştırma sistemi

### **v2.1** - Bug Fixes
- Aktivite görüntüleme sorunları düzeltildi
- API endpoints tamamlandı

### **v2.0** - Takım Yönetimi
- Gelişmiş takım sistemi
- 22 alanlı oyuncu profilleri
- Database migration sistemi

---

**Aktif Versiyon:** v2.3  
**Son Güncelleme:** 30 Ağustos 2025