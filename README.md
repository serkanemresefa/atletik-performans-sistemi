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

## 🐳 Docker (Önerilen)

```bash
docker-compose up --build
# veya
docker build -t atletik-performans web_app/
docker run -p 8081:8081 -e SECRET_KEY="your-secret" atletik-performans
```

## 🧪 Test Suite

```bash
pip3 install pytest==8.0.0
pytest tests/test_app.py -v
```

**Uygulama:** http://localhost:8081  
**Demo:** demo / demo123

---

## ⚡ v2.4 Güvenlik & Performans Güncellemesi

### 🔒 Güvenlik İyileştirmeleri
- SHA-256 → bcrypt migration (backward compatible)
- Environment-based SECRET_KEY management
- CORS localhost-only restriction
- Secure cookie settings (HttpOnly, SameSite)

### 🚀 Performans & Kod Kalitesi
- SQLite foreign key constraints + 4 optimized indexes
- JavaScript/CSS modülleştirildi (1680js + 270css lines)
- Duplicate API route handlers konsolidasyonu
- Chart.js version locked (4.4.1)

### 🐳 DevOps & Testing
- Production-ready Dockerfile + docker-compose
- Pytest test suite (10 test cases)
- Health checks + non-root user security

**Son Güncelleme:** 31 Ağustos 2025